import os
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
        self.llm = LLMWrapper(args, config)
        self.github_details = None

    def prepare(self):
        self.load_documents()
        self.load_feature_extraction_prompt()
        self.llm.prepare(self.feature_extraction_prompt)
        if self.args.github:
            self.github_details = get_github_repo_details(self.args.github)

    def load_documents(self):
        """
        Load documents from the specified directorieis in config.
        """
        docs = self.config["documents"]
        for doc in docs:
            with open(os.path.join(self.args.project, doc), "r") as file:
                content = file.read()
                self.documents.append((doc, content))

    def load_feature_extraction_prompt(self):
        """
        Load the feature extraction prompt from the config.
        """
        filepath = os.path.join(
            self.args.project,
            self.config["prompts-directory"],
            self.PROMPT_NAME,
        )
        with open(filepath, "r") as file:
            self.feature_extraction_prompt = file.read()

    def join_documents(self):
        """
        Join the documents into a single string for processing.
        """
        return "\n\n".join([f"{doc[0]}\n{doc[1]}" for doc in self.documents])

    def run(self):
        project_name = "not available"
        project_description = "not available"
        if self.github_details:
            project_name = self.github_details["name"]
            project_description = self.github_details["description"]

        self.llm.invoke(
            {
                "project_name": project_name,
                "project_description": project_description,
                "documents": self.join_documents(),
            }
        )
