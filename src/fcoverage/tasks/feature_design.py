from .base import TasksBase
from fcoverage.models import FeatureItem
from langchain_core.prompts import PromptTemplate
from fcoverage.utils.prompts import escape_markdown


class FeatureDesignTask(TasksBase):

    def __init__(self, args):
        super().__init__(args)

    def prepare(self):
        super().prepare()

    def run(self):
        feature_item = self.load_feature_item()
        self.explain_feature_implementaion(feature_item)
        return True

    def load_feature_item():
        pass

    def explain_feature_implementaion(self, feature_item: FeatureItem):
        feature_implementaion_prompt_template = self.load_prompt("feature_design.txt")
        agent_executor = self.get_tool_calling_llm(
            [
                self.search_vector_db,
                self.grep_string,
                self.load_file_section,
                self.list_directory,
            ],
            PromptTemplate.from_template(feature_implementaion_prompt_template),
        )
        ls_output = self.get_ls_output()
        core_files = self.get_core_files_context(feature_item)
        response = agent_executor.invoke(
            {
                "project_name": self.project_name,
                "project_description": self.project_description,
                "feature_definition": feature_item.name,
                "feature_description": feature_item.description,
                "feature_entry_point": feature_item.entry_point,
                "core_files": core_files,
                "ls_output": ls_output,
            }
        )

        return response

    def get_ls_output(self):
        return f"""#### list_directory({self.project_src}):

{self.list_directory(self.project_src)}
"""

    def get_core_files_context(self, feature_item: FeatureItem):
        result = []
        for file in feature_item.core_code_files:
            result.append(f"File: {file}")
            with open(file, "w") as f:
                content = f.read()
            result.append(f"```")
            result.append(escape_markdown(content))
            result.append(f"```")

        return "\n".join(result)
