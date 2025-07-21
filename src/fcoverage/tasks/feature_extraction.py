import json
import os
from typing import List, Set
from fcoverage.models import (
    FeatureItem,
    ProjectFeatures,
    TestToFeatures,
    FeatureManifest,
)
from tqdm import tqdm
from fcoverage.utils.code.pytest_utils import get_test_files
from fcoverage.utils.prompts import escape_markdown
from fcoverage.utils.vdb import index_all_project
from .base import TasksBase
from langchain_core.prompts import PromptTemplate


class FeatureExtractionTask(TasksBase):

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        print("FeatureExtractionTask starts:")
        features_list = self.extract_features()
        test_to_features = self.extract_test_files(features_list)
        for feature in features_list.features:
            code_files = self.extract_code_files(feature)
            feature_manifest = FeatureManifest(
                name=feature.name,
                description=feature.description,
                entry_point=feature.entry_point,
                core_code_files=code_files,
                related_test_files=test_to_features[feature.name],
            )
            self.write_to_file(feature_manifest)
        print("FeatureExtractionTask finished.")
        return True

    def write_to_file(self, feature_manifest: FeatureManifest):
        print(f"write_to_file: {feature_manifest.name}")

        name = feature_manifest.name.replace(" ", "_")
        filename = f"features-definition-{name}.json"
        with open(os.path.join(self.args["out"], filename), "w") as file:
            file.write(json.dumps(feature_manifest.model_dump(mode="json"), indent=2))

    def load_documents(self):
        result = []
        docs = [d.strip() for d in self.args["docs"].split(",")]
        for doc in docs:
            filename = doc
            with open(filename, "r") as file:
                content = file.read()

            result.append(f"File: {filename}")
            result.append("Content:")
            result.append("```")
            result.append(escape_markdown(content))
            result.append("```")

        return "\n".join(result)

    def extract_features(self) -> ProjectFeatures:
        print("extract_features")
        feature_extraction_prompt_template = PromptTemplate.from_template(
            self.load_prompt("feature_extraction.txt")
        )
        documents = self.load_documents()
        prompt_feature_extraction = feature_extraction_prompt_template.invoke(
            {
                "project_name": self.project_name,
                "project_description": self.project_description,
                "documents": documents,
                "n_features": self.args["max_features"],
            }
        )
        structured_llm = self.model.with_structured_output(ProjectFeatures)
        return structured_llm.invoke(prompt_feature_extraction)

    def index_source_code(self):
        print("index_source_code")
        index_all_project(
            self.vdb,
            self.args["project"],
            "**/*.py",
            [".py"],
            batch_size=250,
            sleep_seconds=1,
        )

    def extract_test_files(self, features_list: ProjectFeatures):
        test_to_feature = dict()
        for test_file in tqdm(get_test_files(self.project_tests)):
            relation = self.realte_test_file_to_features(test_file, features_list)
            test_to_feature[test_file] = relation
            self.zzz()

        feature_to_test = dict()
        for feature in features_list:
            feature_to_test[feature.name] = []
        for test, features in test_to_feature.items():
            for feature in features:
                if test not in feature_to_test[feature]:
                    feature_to_test[feature].append(test)

        return feature_to_test

    def realte_test_file_to_features(
        self, test_path: str, features_list
    ) -> TestToFeatures:
        print(f"realte_test_file_to_features: {test_path}")
        test_to_feature_prompt_template = self.load_prompt("test_to_feature.txt")
        agent_executor = self.get_tool_calling_llm(
            [
                self.tool_search_vector_db(),
                self.tool_grep_string(),
                self.tool_load_file_section(),
                self.tool_list_directory(),
            ],
            PromptTemplate.from_template(test_to_feature_prompt_template),
        )

        with open(test_path, "r") as f:
            test_code = f.read()

        response = agent_executor.invoke(
            {
                "project_name": self.project_name,
                "project_description": self.project_description,
                "test_code": test_code,
                "features_list": features_list,
                "filename": test_path,
            }
        )

        result = response["output"]
        structured_llm = self.model.with_structured_output(TestToFeatures)
        self.zzz()
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

    def extract_code_files(self, feature: FeatureItem):
        print(f"extract_code_files: {feature.name}")
        files_1 = self.look_up_by_keywords_and_grep(feature.keywords)
        files_2 = self.look_up_by_vector_db(feature.queries)
        return list(files_1.union(files_2))
