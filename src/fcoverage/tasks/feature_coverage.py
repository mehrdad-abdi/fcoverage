import os
import uuid

from fcoverage.utils.prompts import escape_markdown, wrap_in_code_block
from .base import TasksBase
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import SystemMessagePromptTemplate, ChatPromptTemplate


class FeatureCoverageTask(TasksBase):

    def __init__(self, args):
        super().__init__(args)
        self.feature_item = None
        self.feature_implementation = None
        self.test_cases = None

    def prepare(self):
        super().prepare()
        self.feature_item = self.load_feature_item()
        self.feature_implementation = self.load_feature_implementation()
        self.test_cases = self.load_test_cases()

    def run(self):
        report = self.create_testing_report()
        self.write_to_file(report)
        return True

    def write_to_file(self, report):
        folder_name = os.path.join(
            self.args["out"], self.feature_item.name.replace(" ", "_")
        )
        os.makedirs(folder_name, exist_ok=True)

        with open(os.path.join(folder_name, "test_coverage.md"), "w") as file:
            file.write(report)

    def build_related_tests_chunk(self):
        result = []
        for test_file in self.feature_item.related_test_files:
            with open(test_file, "r") as f:
                test_code = f.read()
            result.append(f"Test file: {test_file}")
            result.append("```python")
            result.append(escape_markdown(test_code))
            result.append("```")
            result.append("")

        return "\n".join(result)

    def create_testing_report(self) -> str:
        feature_coverage_system_message_template = (
            SystemMessagePromptTemplate.from_template(
                self.load_prompt("feature_tests_system.txt")
            )
        )
        str_related_tests = self.build_related_tests_chunk()
        system_message = feature_coverage_system_message_template.format(
            project_name=self.project_name,
            project_description=self.project_description,
            feature_definition=self.feature_item.name,
            feature_description=self.feature_item.description,
            feature_entry_point=self.feature_item.entry_point,
            feature_implementation=wrap_in_code_block(self.feature_implementation),
            ideal_test_cases=wrap_in_code_block(self.test_cases),
            actual_related_tests=str_related_tests,
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                system_message,
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        agent_executor = self.get_tool_calling_llm(
            tools=[
                self.tool_search_vector_db(),
                self.tool_grep_string(),
                self.tool_load_file_section(),
            ],
            prompt_template=prompt,
            memory=memory,
        )

        self.invoke_with_retry(
            agent_executor,
            {"input": self.load_prompt("feature_tests_coverage.txt")},
        )
        self.invoke_with_retry(
            agent_executor,
            {"input": self.load_prompt("feature_tests_improvements.txt")},
        )
        response = self.invoke_with_retry(
            agent_executor,
            {"input": self.load_prompt("feature_tests_report.txt")},
        )
        return response["output"]
