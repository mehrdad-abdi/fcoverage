import json
import os
import time
from typing import List, Set
from fcoverage.models import ProjectFeatures, TestToFeatures
from tqdm import tqdm
from fcoverage.utils.code.pytest_utils import get_test_files, list_available_fixtures
from fcoverage.utils.prompts import escape_markdown
from fcoverage.utils.vdb import index_all_project
from .base import TasksBase
from langchain_core.prompts import PromptTemplate


class FeatureExtractionTask(TasksBase):

    def __init__(self, args, config):
        super().__init__(args, config)

    def run(self):
        features_list = self.extract_features()
        self.index_source_code()
        self.enrich_with_code_files(features_list)
        self.enrich_with_test_files(features_list)

        out = self.args["out"]
        if not out:
            out = "features-list.json"
        with open(out, "w") as file:
            file.write(json.dumps(features_list.model_dump(mode="json"), indent=2))
        return True

    def load_documents(self):
        result = []
        for doc in self.args["docs"]:
            filename = os.path.join(self.args["project"], doc)
            with open(filename, "r") as file:
                content = file.read()

            result.append(f"File: {filename}")
            result.append("Content:")
            result.append("```")
            result.append(escape_markdown(content))
            result.append("```")

        return "\n".join(result)

    def load_feature_extraction_prompt(self, documents):
        feature_extraction_prompt_template = PromptTemplate.from_template(
            self.load_prompt("feature_extraction.txt")
        )

        prompt_feature_extraction = feature_extraction_prompt_template.invoke(
            {
                "project_name": self.project_name,
                "project_description": self.project_description,
                "documents": documents,
            }
        )
        return prompt_feature_extraction

    def extract_features(self):
        documents = self.load_documents()
        prompt = self.load_feature_extraction_prompt(documents)

        structured_llm = self.model.with_structured_output(ProjectFeatures)
        return structured_llm.invoke(prompt)

    def index_source_code(self):
        index_all_project(
            self.vdb,
            self.args["project"],
            "**/*.py",
            [".py"],
            batch_size=250,
            sleep_seconds=1,
        )

    def enrich_with_test_files(self, features_list: ProjectFeatures):
        for test_file in tqdm(get_test_files(self.project_tests)):
            relation = self.realte_test_file_to_features(test_file)
            for feature in features_list.features:
                if feature.name in relation.related_features:
                    if feature.related_test_files is None:
                        feature.related_test_files = []
                    if test_file not in feature.related_test_files:
                        feature.related_test_files.append(test_file)

            time.sleep(4)  # respect rate-limit

    def realte_test_file_to_features(
        self, test_path: str, features_list
    ) -> TestToFeatures:
        test_to_feature_prompt_template = self.load_prompt("test_to_feature.txt")
        agent_executor = self.get_tool_calling_llm(
            [
                self.search_vector_db,
                self.grep_string,
                self.load_file_section,
            ],
            PromptTemplate.from_template(test_to_feature_prompt_template),
        )

        with open(test_path, "r") as f:
            test_code = f.read()
        test_fixtures = list_available_fixtures(
            os.path.abspath(self.args["project"]), test_path
        )

        response = agent_executor.invoke(
            {
                "project_name": self.project_name,
                "project_description": self.project_description,
                "test_code": test_code,
                "test_fixtures": test_fixtures,
                "features_list": features_list,
                "filename": test_path,
            }
        )

        result = response["output"]
        structured_llm = self.model.with_structured_output(TestToFeatures)
        test_to_features = structured_llm.invoke(result)
        return test_to_features

    def look_up_by_keywords_and_grep(self, keywords: List[str]) -> Set[str]:
        output = set()
        for keyword in keywords:
            result = self.grep_string(keyword)
            for item in result:
                output.add(item["file"])
        return output

    def look_up_by_vector_db(self, queries: List[str]) -> Set[str]:
        output = set()
        for query in queries:
            results = self.vdb.search(query, k=5)
            for item in results:
                output.add(item.metadata.get("source"))
        return output

    def enrich_with_code_files(self, features_list: ProjectFeatures):
        for feature in features_list.features:
            files_1 = self.look_up_by_keywords_and_grep(feature.keywords)
            files_2 = self.look_up_by_vector_db(feature.queries)
            feature.core_code_files = list(files_1.union(files_2))
