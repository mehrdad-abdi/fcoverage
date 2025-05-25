import os
from .base import TasksBase
from fcoverage.utils.llm import LLMWrapper


class FeatureTestMappingTask(TasksBase):

    PROMPT_NAME = "feature_test_mapping.txt"

    def __init__(self, args, config):
        super().__init__(args, config)
        self.llm = LLMWrapper(args, config)
        self.prompt_template = None

    def prepare(self):
        self.load_prompt(self.PROMPT_NAME)
        self.llm.prepare(self.prompt_template)

    def run(self):
        pass

    def foo(self):
        """
        Placeholder method for future implementation.
        """
        "features_list"
        "test_code"
        "fixture_code"
        "method_code"

        pass
