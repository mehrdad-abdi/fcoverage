import os
from .base import TasksBase
from fcoverage.models import FeatureManifest
from langchain_core.prompts import PromptTemplate
from fcoverage.utils.prompts import escape_markdown


class FeatureDesignTask(TasksBase):

    def __init__(self, args):
        super().__init__(args)
        self.feature_item: None | FeatureManifest = None

    def prepare(self):
        super().prepare()
        self.feature_item = self.load_feature_item()

    def run(self):
        feature_implementation = self.explain_feature_implementaion()
        feature_testcases = self.identify_feature_testcases(feature_implementation)

        self.write_to_file(feature_implementation, feature_testcases)
        return True

    def write_to_file(self, feature_implementation, feature_testcases):
        folder_name = os.path.join(
            self.args["out"], self.feature_item.name.repalce(" ", "_")
        )
        os.makedirs(folder_name, exist_ok=True)

        for filename, content in [
            ("design.md", feature_implementation),
            ("test_cases.md", feature_testcases),
        ]:
            with open(os.path.join(folder_name, filename), "w") as file:
                file.write(content)

    def explain_feature_implementaion(self):
        feature_implementaion_prompt_template = self.load_prompt("feature_design.txt")
        agent_executor = self.get_tool_calling_llm(
            [
                self.tool_search_vector_db(),
                self.tool_grep_string(),
                self.tool_load_file_section(),
                self.tool_list_directory(),
            ],
            PromptTemplate.from_template(feature_implementaion_prompt_template),
        )
        ls_output = self.get_ls_output()
        core_files = self.get_core_files_context()
        response = self.invoke_with_retry(
            agent_executor,
            {
                "project_name": self.project_name,
                "project_description": self.project_description,
                "feature_definition": self.feature_item.name,
                "feature_description": self.feature_item.description,
                "feature_entry_point": self.feature_item.entry_point,
                "core_files": core_files,
                "ls_output": ls_output,
            },
        )

        return response["output"]

    def get_ls_output(self):
        return f"""#### list_directory({self.project_src}):

{self.list_directory(self.project_src)}
"""

    def get_core_files_context(self):
        result = []
        for file in self.feature_item.core_code_files:
            if not os.path.exists(file):
                print(f"File not found: {file}")
                continue
            result.append(f"File: {file}")
            with open(file, "r") as f:
                content = f.read()
            result.append("```")
            result.append(escape_markdown(content))
            result.append("```")

        return "\n".join(result)

    def identify_feature_testcases(self, feature_item, feature_implementation):
        feature_implementaion_prompt_template = self.load_prompt(
            "feature_generate_ideal_test_cases.txt"
        )
        agent_executor = self.get_tool_calling_llm(
            [
                self.tool_search_vector_db(),
                self.tool_grep_string(),
                self.tool_load_file_section(),
                self.tool_list_directory(),
            ],
            PromptTemplate.from_template(feature_implementaion_prompt_template),
        )
        response = agent_executor.invoke(
            {
                "project_name": self.project_name,
                "project_description": self.project_description,
                "feature_definition": feature_item.name,
                "feature_description": feature_item.description,
                "feature_entry_point": feature_item.entry_point,
                "feature_implementation": feature_implementation,
            }
        )

        return response["output"]
