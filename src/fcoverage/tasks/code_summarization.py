import os

from fcoverage.utils import prompts
from .base import TasksBase


class CodeSummarizationTask(TasksBase):

    def __init__(self, args, config):
        super().__init__(args, config)
        self.documents = []

    def prepare(self):
        self.load_prompts()

    def load_prompts(self):
        self.summarize_module_prompt = prompts.get_prompt_for_code_summarization_module(
            os.path.join(
                self.args["project"],
                self.config["prompts-directory"],
                "code_summarization_module.txt",
            )
        )
        self.summarize_package_prompt = (
            prompts.get_prompt_for_code_summarization_module(
                os.path.join(
                    self.args["project"],
                    self.config["prompts-directory"],
                    "code_summarization_package.txt",
                )
            )
        )

    def run(self):
        return super().run()
