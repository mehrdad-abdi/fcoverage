import json
import os
from pathlib import Path
from typing import Any, Dict, List, Set
from fcoverage.models import (
    FeatureItem,
    ProjectFeatures,
    TestToFeatures,
    FeatureManifest,
)
from tqdm import tqdm
from fcoverage.utils.code.pytest_utils import get_test_files
from fcoverage.utils.prompts import escape_markdown
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
        structured_llm = self.model_with_retry(
            self.model.with_structured_output(ProjectFeatures)
        )
        return structured_llm.invoke(prompt_feature_extraction)

    def extract_test_files(
        self, features_list: ProjectFeatures
    ) -> Dict[str, List[str]]:
        test_to_feature = dict()
        features_list_minimized = self.get_features_list_minimized(features_list)
        for test_file in tqdm(get_test_files(self.project_tests)):
            relation = self.realte_test_file_to_features(test_file, features_list_minimized)
            test_to_feature[self.relative_path(test_file)] = relation.related_features
            self.zzz()

        feature_to_test: Dict[str, List[str]] = dict()
        for feature in features_list.features:
            feature_to_test[feature.name] = []
        for test, features in test_to_feature.items():
            for feature_name in features:
                if feature_name not in feature_to_test:
                    print(f"Skipping unknown feature {test} -> {feature_name}")
                    continue
                if test not in feature_to_test[feature_name]:
                    feature_to_test[feature_name].append(test)

        return feature_to_test

    def get_features_list_minimized(self, features_list: ProjectFeatures):
        items = []
        for feature in features_list.features:
            dump = json.dumps(feature.model_dump(mode="json"), indent=2)        
            # delete queries and keywords. extra information may confuse the model
            del dump["keywords"]
            del dump["queries"]
            items.append(dump)
        return items

    def realte_test_file_to_features(
        self, test_path: str, features_list_minimized: List[Dict[str, Any]]
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

        response = self.invoke_with_retry(
            agent_executor,
            {
                "project_name": self.project_name,
                "project_description": self.project_description,
                "test_code": test_code,
                "features_list": features_list_minimized,
                "filename": self.relative_path(test_path),
            },
        )

        result = response["output"]
        structured_llm = self.model_with_retry(
            self.model.with_structured_output(TestToFeatures)
        )
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
        files = [self.relative_path(f) for f in files_1.union(files_2)]
        return files
