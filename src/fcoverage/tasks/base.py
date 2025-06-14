import os
from typing import List

from fcoverage.utils.prompts import load_prompts
from fcoverage.utils.mongo import MongoDBHelper
from fcoverage.utils.vdb import VectorDBHelper
from langchain.chat_models import init_chat_model


class TasksBase:

    PROMPTS = []

    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.prompts = {}
        self.model = None
        self.code_summary_db = None
        self.vectorstore = None

    def run(self):
        raise NotImplementedError("Subclasses must implement this method")

    def prepare(self):
        pass

    def load_prompts(self, prompts: List[str] = None):
        filepath = os.path.join(
            self.args["project"],
            self.config["prompts-directory"],
        )
        for prompt in prompts or self.PROMPTS:
            self.prompts[prompt] = load_prompts(prompt + ".txt", filepath)

    def load_llm_model(self):
        model_name = self.config.get("llm", {}).get("model", "gemini-2.0-flash")
        model_provider = self.config.get("llm", {}).get("provider", "google-genai")

        self.model = init_chat_model(
            model_name,
            model_provider=model_provider,
        )

    def load_vectordb_helper(self):
        conf_embedding_model = self.config.get("embedding", {}).get(
            "model", "models/gemini-embedding-exp-03-07"
        )
        conf_embedding_provider = self.config.get("embedding", {}).get(
            "provider", "google_genai"
        )
        vdb_save_location = os.path.join(
            self.args["project"], self.config["vector-db-persist-location"]
        )
        self.vectorstore = VectorDBHelper(
            vdb_save_location,
            "fcoverage",
            conf_embedding_model,
            conf_embedding_provider,
        )

    def load_mongodb_helper(self):
        self.code_summary_db = MongoDBHelper(
            self.config["mongo-db-connection-string"],
            self.config["mongo-db-database"],
            self.CHUNK_SOURCE,
        )

    def get_features_content(self):
        filename_json = os.path.join(self.args["project"], self.config["feature-file"])
        with open(filename_json, "r") as f:
            features_content = f.read()
        return features_content
