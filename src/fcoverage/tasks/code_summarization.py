import json
import os
from pathlib import Path

from fcoverage.models.code_summary import ModuleSummary
from fcoverage.utils.code.python_utils import get_all_python_files
from .base import TasksBase
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from typing import Sequence

from langchain_core.messages import BaseMessage
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from fcoverage.utils.vdb import VectorDBHelper


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    summary: ModuleSummary


class CodeSummarizationTask(TasksBase):

    def __init__(self, args, config):
        super().__init__(args, config)
        self.summaries = []
        self.vectorstore = None

    def prepare(self):
        self.load_llm_model()
        self.structured_llm = self.model.with_structured_output(ModuleSummary)
        self.system_prompt_1 = SystemMessage(
            self.load_prompt("code_summarization_1_system.txt")
        )
        self.system_prompt_2 = SystemMessage(
            self.load_prompt("code_summarization_2_system.txt")
        )
        self.prepare_workflow_app()
        self.vectorstore = VectorDBHelper(
            self.vdb_save_location,
            "fcoverage",
            self.conf_embedding_model,
            self.conf_embedding_provider,
        )

    def prepare_workflow_app(self):
        self.workflow = StateGraph(state_schema=State)
        self.workflow.add_node("summarize_file", self.summarize_file)
        self.workflow.add_node("relate_to_features", self.relate_to_features)

        self.workflow.add_edge(START, "summarize_file")
        self.workflow.add_edge("summarize_file", "relate_to_features")

        memory = MemorySaver()
        self.workflow_app = self.workflow.compile(checkpointer=memory)

    def summarize_file(self, state: State):
        response = self.model.invoke(state["messages"])
        return {"messages": response}

    def relate_to_features(self, state: State):
        filename_json = os.path.join(self.args["project"], self.config["feature-file"])
        with open(filename_json, "r") as f:
            features_content = f.read()

        input_messages = state["messages"] + [
            self.system_prompt_2,
            HumanMessage(
                """Features list: 
```
{features_content}
```""".format(
                    features_content=str(features_content)
                )
            ),
        ]

        response = self.structured_llm.invoke(input_messages)
        return {"summary": response}

    def run_summarize_by_single_file(self, file_path):
        config = {"configurable": {"thread_id": "1"}}
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        filename = Path(file_path).relative_to(self.args["project"])
        input_messages = [
            self.system_prompt_1,
            HumanMessage(
                """Filename: `{filename}`
File content:
```python
{file_content}
```""".format(
                    filename=str(filename), file_content=source_code
                )
            ),
        ]
        output = self.workflow_app.invoke({"messages": input_messages}, config)
        return output["summary"]

    def run_summarize_by_modules(self):
        file_path_list = get_all_python_files(
            os.path.join(self.args["project"], self.config["source"])
        )
        self.summaries = []
        for file_path in file_path_list:
            if self.args["only_file"] is not None:
                if self.args["only_file"] != file_path:
                    continue
            self.summaries.append(self.run_summarize_by_single_file(file_path))

    def summary_to_document(self, summary: ModuleSummary):
        documents = []
        # first process components
        for component in summary["components"]:
            model = component.model_dump()
            content = model["summary"]
            model["chunk_type"] = "summary"
            del model["summary"]
            documents.append(Document(page_content=content, metadata=model))
        del summary["components"]
        model = summary.model_dump()
        model["chunk_type"] = "summary"
        model["type"] = "module"
        content = model["summary"]
        del model["summary"]
        documents.append(Document(page_content=content, metadata=model))
        return documents

    def persist_documents(self):
        documents = []
        for s in self.summaries:
            documents.extend(self.summary_to_document(s))

        self.vectorstore.sync_documents(documents)

    def run(self):
        self.run_summarize_by_modules()
        self.persist_documents()
        return True
