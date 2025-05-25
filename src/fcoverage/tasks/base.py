import os

from fcoverage.utils import prompts


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
