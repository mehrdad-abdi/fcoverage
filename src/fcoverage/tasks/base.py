import os

from fcoverage.utils import prompts
from langchain.chat_models import init_chat_model


class TasksBase:
    def __init__(self, args, config):
        self.args = args
        self.config = config

    def prepare(self):
        raise NotImplementedError("Subclasses must implement this method")

    def run(self):
        raise NotImplementedError("Subclasses must implement this method")

    def load_prompt(self, prompt_filename):
        """
        Load the feature extraction prompt from the config.
        """
        filepath = os.path.join(
            self.args["project"],
            self.config["prompts-directory"],
            prompt_filename,
        )
        if not os.path.exists(filepath):
            return prompts.read_prompt_file(prompt_filename)
        else:
            with open(filepath, "r") as file:
                return file.read()

    def load_llm_model(self):
        model_name = self.config.get("llm", {}).get("model", "gemini-2.0-flash")
        model_provider = self.config.get("llm", {}).get("provider", "google-genai")

        self.model = init_chat_model(
            model_name,
            model_provider=model_provider,
        )
