import os
from pathlib import Path

from fcoverage.models.code_summary import ComponentSummary, ModuleSummary
from fcoverage.utils.code.python_utils import (
    CodeType,
    get_all_python_files,
    build_chunks_from_python_file,
    get_qualified_name,
)
from .base import TasksBase
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Sequence, Dict

from langchain_core.messages import BaseMessage
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    summary: ModuleSummary
    file_path: str
    hash: str


PROMPT_CODE_SUMMARY = "code_summarization_1_system"
PROMPT_FEATURE_MAP = "code_summarization_2_system"


class CodeSummarizationTask(TasksBase):

    CHUNK_SOURCE = "code-summary"
    PROMPTS = [PROMPT_CODE_SUMMARY, PROMPT_FEATURE_MAP]

    def __init__(self, args, config):
        super().__init__(args, config)
        self.docs_vectordb = []
        self.docs_mongodb = []

    def prepare(self):
        self.load_llm_model()
        self.load_vectordb_helper()
        self.load_mongodb_helper()
        self.load_prompts()

    def run(self):
        summaries = self.run_summarize()
        self.models_to_documents(summaries)
        self.vectorstore.sync_documents(self.docs_vectordb)
        self.code_summary_db.sync_documents(self.docs_mongodb)
        return True

    def run_summarize(self):
        workflow_app = self.init_workflow_app()
        summaries = dict()
        file_path_list = get_all_python_files(
            os.path.join(self.args["project"], self.config["source"])
        )
        for file_path in file_path_list:
            if self.args["only_file"] is not None:
                if self.args["only_file"] != file_path:
                    continue
            summaries[file_path] = self.run_summarize_by_single_file(
                file_path, workflow_app
            )
        return summaries

    def init_workflow_app(self):
        workflow = StateGraph(state_schema=State)
        workflow.add_node("summarize_file", self.summarize_file)
        workflow.add_node("relate_to_features", self.relate_to_features)

        workflow.add_edge(START, "summarize_file")
        workflow.add_edge("summarize_file", "relate_to_features")
        workflow.add_edge("relate_to_features", END)

        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    def run_summarize_by_single_file(self, file_path, workflow_app):
        # TODO run in parallel
        config = {"configurable": {"thread_id": file_path}}
        output = workflow_app.invoke({"file_path": file_path}, config)
        return output["summary"]

    def summarize_file(self, state: State):
        filename = Path(state["file_path"]).relative_to(self.args["project"])
        with open(state["file_path"], "r", encoding="utf-8") as f:
            source_code = f.read()

        input_messages = [
            SystemMessage(self.prompts[PROMPT_CODE_SUMMARY]),
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
        response = self.model.invoke(input_messages)
        return {"messages": response}

    def relate_to_features(self, state: State):
        structured_llm = self.model.with_structured_output(ModuleSummary)
        features_content = self.get_features_content()

        input_messages = state["messages"] + [
            SystemMessage(self.prompts[PROMPT_FEATURE_MAP]),
            HumanMessage(
                """Features list: 
```
{features_content}
```""".format(
                    features_content=str(features_content)
                )
            ),
        ]

        response = structured_llm.invoke(input_messages)
        return {"summary": response}

    def models_to_documents(self, summaries: Dict[str, ModuleSummary]):
        for file_path, summary in summaries.items():
            file_chunks, module_hash = build_chunks_from_python_file(file_path)

            self.docs_vectordb.append(
                self.module_summary_to_document(summary, module_hash)
            )
            self.docs_mongodb.append(
                self.extra_information_module(summary, module_hash, file_path)
            )
            for component in summary.components:
                qualified_name = self.get_object_qualified_name(
                    component.name, component.type, file_path
                )
                chunk = file_chunks[qualified_name]
                self.docs_vectordb.append(
                    self.component_summary_to_document(component, chunk["hash"])
                )
                self.docs_mongodb.append(
                    self.extra_information_component(component, chunk)
                )

    def module_summary_to_document(self, summary: ModuleSummary, hash: str):
        return Document(
            page_content=summary.summary,
            metadata={
                "source": self.CHUNK_SOURCE,
                "code_type": CodeType.MODULE,
                "id": hash,
            },
        )

    def component_summary_to_document(self, component: ComponentSummary, hash: str):
        return Document(
            page_content=component.summary,
            metadata={
                "source": self.CHUNK_SOURCE,
                "code_type": component.type,
                "name": component.name,
                "id": hash,
            },
        )

    def get_object_qualified_name(self, object_name, object_type, file_path):
        qualified_name = None
        if object_type == CodeType.CLASS_METHOD:
            class_name, method_name = object_name.split(":")
            qualified_name = get_qualified_name(
                file_path, class_name, method_name, CodeType.CLASS_METHOD
            )
        else:
            qualified_name = get_qualified_name(
                file_path, None, object_name, object_type
            )

        return qualified_name

    def extra_information_module(self, summary: ModuleSummary, module_hash, file_path):
        item = summary.model_dump(mode="json")
        return {
            "_id": module_hash,
            "type": CodeType.MODULE,
            "path": file_path,
            "imports": item["imports"],
            "exports": item["exports"],
            "features_mapping": item["features_mapping"],
        }

    def extra_information_component(self, component: ComponentSummary, chunk):
        item = component.model_dump(mode="json")
        return {
            "_id": chunk["hash"],
            "imports": item["imports"],
            "features_mapping": item["features_mapping"],
            "tags": item["tags"],
            "name": chunk["name"],
            "type": chunk["type"],
            "class_name": chunk["class_name"],
            "qualified_name": chunk["qualified_name"],
            "path": chunk["path"],
        }
