import os
from .base import TasksBase
from fcoverage.lib.llm import LLMWrapper

class FeatureExtractionTask(TasksBase):

    def __init__(self, args, config):
        super().__init__(args, config)
        self.documents = []
        self.llm = LLMWrapper(args, config)

    def prepare(self):
        self.load_documents()
        self.load_feature_extraction_prompt()
        self.llm.prepare(self.feature_extraction_prompt)

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
        filepath = os.path.join(self.args.project, self.config["prompts-directory"], "feature_extraction.txt")
        with open(filepath, "r") as file:
            self.feature_extraction_prompt = file.read()

    def join_documents(self):
        """
        Join the documents into a single string for processing.
        """
        return "\n\n".join([f"{doc[0]}\n{doc[1]}" for doc in self.documents])
        
    def run(self):
        self.llm.invoke({
            "documents": self.join_documents(),
        })
