import os

from fcoverage.utils import prompts
from .base import TasksBase
from fcoverage.utils.llm import LLMWrapper
from fcoverage.utils.http import get_github_repo_details


class FeatureExtractionTask(TasksBase):
    """
    This class is responsible for extracting features from the documents specified in the configuration.
    It uses the LLMWrapper class to interact with a language model for feature extraction.
    """

    PROMPT_NAME = "feature_extraction.txt"

    def __init__(self, args, config):
        super().__init__(args, config)
        self.documents = []
        self.llm = LLMWrapper(config)
        self.github_details = None

    def prepare(self):
        self.load_documents()
        self.load_feature_extraction_prompt()
        self.llm.prepare(self.feature_extraction_prompt)
        if "github" in self.args:
            self.github_details = get_github_repo_details(self.args["github"])

    def load_documents(self):
        """
        Load documents from the specified directorieis in config.
        """
        docs = self.config["documents"]
        print(type(docs))
        for doc in docs:
            filename = os.path.join(self.args["project"], doc)
            with open(filename, "r") as file:
                content = file.read()
                self.documents.append((doc, content))

    def load_feature_extraction_prompt(self):
        """
        Load the feature extraction prompt from the config.
        """
        filepath = os.path.join(
            self.args["project"],
            self.config["prompts-directory"],
            self.PROMPT_NAME,
        )
        if not os.path.exists(filepath):
            self.feature_extraction_prompt = prompts.get_prompt_for_feature_extraction()
        else:
            with open(filepath, "r") as file:
                self.feature_extraction_prompt = file.read()

    def invoke_llm(self):
        project_name = "not available"
        project_description = "not available"
        documents = "\n\n".join([f"{doc[0]}\n{doc[1]}" for doc in self.documents])

        if self.github_details:
            project_name = self.github_details["repo_name"]
            project_description = self.github_details["description"]

        return self.llm.invoke(
            {
                "project_name": project_name,
                "project_description": project_description,
                "documents": documents,
            }
        )

    def write_response_to_file(self, response):
        filename = os.path.join(self.args["project"], self.config["feature-file"])
        with open(
            filename,
            "w",
        ) as file:
            file.write(response)
        print(f"Feature extraction results written to {filename}")

    def run(self):
        response = self.invoke_llm()
        self.write_response_to_file(response.content)
        print("Feature extraction completed successfully.")
        return True
