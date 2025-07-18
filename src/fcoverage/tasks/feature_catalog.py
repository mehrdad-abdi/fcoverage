import json
import os
import time
from typing import List, Literal, Set
from pydantic import BaseModel, Field
from tqdm import tqdm
from fcoverage.utils.code.pytest_utils import get_test_files, list_available_fixtures
from fcoverage.utils.prompts import escape_markdown
from fcoverage.utils.vdb import index_all_project
from .base import TasksBase
from fcoverage.utils.http import get_github_repo_details
from langchain_core.prompts import PromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor


class FeatureItem(BaseModel):
    name: str = Field(description="A short name or title for the feature.")
    description: str = Field(
        description="Provide a clear and complete explanation and answer these questions for the feature: what the feature is, how it works, who it is for, and the value it provides. Include all important details and use complete sentences that are informative, avoiding overly brief explanations."
    )
    entry_point: str = Field(
        description="A description of how a user might access this feature (e.g., 'Through the 'Export' button on the user profile page', or 'Via the `/api/v2/report` endpoint'). If unknown, state 'Unknown'."
    )
    keywords: List[str] = Field(
        description="list of relevant searchable keywords. You expect to see these keywords in the name of related files, classes, methods, functions. To be used in find or grep to discover these code portions."
    )
    queries: List[str] = Field(
        description="list of relevant RAG queries to use similarity search for retrieve related production code."
    )
    priority: Literal["High", "Medium", "Low"] = Field(
        description="Testing priority for this feature: High, Medium, or Low.",
        enum=["High", "Medium", "Low"],
    )
    related_test_files: List[str] = Field(
        description="This field will be used to store the list of test files related to this feature. Ignore it."
    )
    core_code_files: List[str] = Field(
        description="This field will be used to store the list of core source code files related to this feature. Ignore it."
    )


class ProjectFeatures(BaseModel):
    project_name: str = Field(
        description="The official or working name of the software project."
    )
    project_description: str = Field(
        description="The full description or summary of the project."
    )
    features: List[FeatureItem] = Field(
        description="A list of structured feature records."
    )


class TestToFeatures(BaseModel):
    related_features: List[str] = Field(
        description="The list of feature names (exact name according the List of features) that the test tries to cover. Leave it empty if you couldn't relate the test to any feature."
    )


class FeatureCatalogTask(TasksBase):

    def __init__(self, args, config):
        super().__init__(args, config)
        self.project_name = "not available"
        self.project_description = "not available"

    def prepare(self):
        self.load_llm_model()
        self.load_vector_db_helper()

    def run(self):
        features_list = self.extract_features()
        self.index_source_code()
        self.enrich_with_code_files(features_list)
        self.enrich_with_test_files(features_list)

        out = self.args["out"]
        if not out:
            out = "feature-catalog.json"
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

        if "github" in self.args:
            github_details = get_github_repo_details(self.args["github"])
            self.project_name = github_details["repo_name"]
            self.project_description = github_details["description"]

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
        test_folder = os.path.join(self.args["project"], self.args["test-path"])

        for test_file in tqdm(get_test_files(test_folder)):
            relation = self.realte_test_file_to_features(test_file)
            for feature in features_list.features:
                if feature.name in relation.related_features:
                    if feature.related_test_files is None:
                        feature.related_test_files = []
                    if test_file not in feature.related_test_files:
                        feature.related_test_files.append(test_file)

            time.sleep(4)  # respect rate-limit

    def realte_test_file_to_features(
        self, test_path: str, features_list, verbose=False
    ) -> TestToFeatures:
        test_to_feature_prompt_template = self.load_prompt("test_to_feature.txt")
        tools = [
            self.search_vector_db,
            self.grep_string,
            self.load_file_section,
        ]
        agent = create_tool_calling_agent(
            llm=self.model,
            tools=tools,
            prompt=PromptTemplate.from_template(test_to_feature_prompt_template),
        )
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=verbose)

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
