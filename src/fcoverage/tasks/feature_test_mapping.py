import os

from fcoverage.models.feature_list import ProjectFeatureAnalysis
from .base import TasksBase
from fcoverage.utils.llm import LLMWrapper


class FeatureTestMappingTask(TasksBase):

    PROMPT_NAME = "feature_test_mapping.txt"

    def __init__(self, args, config):
        super().__init__(args, config)
        self.llm = LLMWrapper(args, config)
        self.prompt_template = None
        self.features_list = None

    def prepare(self):
        self.load_prompt(self.PROMPT_NAME)
        self.llm.prepare(self.prompt_template)
        self.parse_feature_list_file()

    def run(self):
        pass
        

    def parse_feature_list_file(self):
        filename = os.path.join(self.args["project"], self.config["feature-file"])
        with open(filename, "r") as file:
            content = file.read()
        self.features_list = self.llm.structured_output(content, ProjectFeatureAnalysis)


    def foo(self):
        """
        Placeholder method for future implementation.
        """
        "features_list"
        "test_code"
        "fixture_code"
        "method_code"

        pass
