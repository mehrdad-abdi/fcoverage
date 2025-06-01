import os

from fcoverage.utils import prompts
from .base import TasksBase
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
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
        self.model = init_chat_model(
            config.get("llm", {}).get("model", "gemini-2.0-flash"),
            model_provider=config.get("llm", {}).get("provider", "google-genai"),
        )
        self.prompt_template = None
        self.project_name = "not available"
        self.project_description = "not available"

    def prepare(self):
        self.load_documents()
        self.load_feature_extraction_prompt()
        if "github" in self.args:
            github_details = get_github_repo_details(self.args["github"])
            self.project_name = github_details["repo_name"]
            self.project_description = github_details["description"]

    def load_documents(self):
        """
        Load documents from the specified directorieis in config.
        """
        docs = self.config["documents"]
        for doc in docs:
            filename = os.path.join(self.args["project"], doc)
            with open(filename, "r") as file:
                content = file.read()
                self.documents.append((doc, content))

    def load_feature_extraction_prompt(self):
        feature_extraction_prompt = prompts.get_prompt_for_feature_extraction(
            os.path.join(
                self.args["project"],
                self.config["prompts-directory"],
                self.PROMPT_NAME,
            )
        )
        self.prompt_template = ChatPromptTemplate.from_messages(
            messages=[("user", feature_extraction_prompt)]
        )

    def invoke_llm(self):
        documents = "\n\n".join([f"{doc[0]}\n{doc[1]}" for doc in self.documents])
        prompt = self.prompt_template.invoke(
            {
                "project_name": self.project_name,
                "project_description": self.project_description,
                "documents": documents,
            }
        )
        return self.model.invoke(prompt)

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
