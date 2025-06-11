import os
from pathlib import Path

from fcoverage.models.tests_summary import (
    TestFileSummary,
    TestMethodSummary,
    TestUtilsFileSummary,
    TestUtilsSummary,
)
from fcoverage.utils.code.pytest_utils import get_test_files
from fcoverage.utils.code.python_utils import (
    CodeType,
    build_chunks_from_python_file,
    get_qualified_name,
)
from .base import TasksBase
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Sequence

from langchain_core.messages import BaseMessage
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    summary: TestFileSummary
    filepath: str


PROMPT_TEST_SUMMARY = "tests_summarization_1_system"
PROMPT_FEATURE_MAP = "tests_summarization_2_system"
PROMPT_TEST_UTILS = "test_utils_summarization"


class TestsSummarizationTask(TasksBase):

    CHUNK_SOURCE = "tests-summary"
    PROMPTS = [
        PROMPT_TEST_SUMMARY,
        PROMPT_FEATURE_MAP,
        PROMPT_TEST_UTILS,
    ]

    def __init__(self, args, config):
        super().__init__(args, config)
        self.tests_list = []
        self.utils_list = []

    def prepare(self):
        self.load_llm_model()
        self.load_vectordb_helper()
        self.load_mongodb_helper()
        self.load_prompts()
        self.tests_list, self.utils_list = get_test_files(
            os.path.join(self.args["project"], self.config["tests"])
        )

    def run(self):
        self.run_utils()
        self.run_tests()
        return True

    def run_utils(self):
        summaries = dict()
        for file_path in self.utils_list:
            if self.args["only_file"] is not None:
                if self.args["only_file"] != file_path:
                    continue
            summaries[file_path] = self.run_summarize_util_file(file_path)
        docs_vectordb, docs_mongodb = self.util_models_to_documents(summaries)
        self.vectorstore.sync_documents(docs_vectordb)
        self.code_summary_db.sync_documents(docs_mongodb)

    def run_summarize_util_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        filename = Path(file_path).relative_to(self.args["project"])
        input_messages = [
            SystemMessage(self.load_prompt(PROMPT_TEST_UTILS)),
            HumanMessage(
                """Filename: `{filename}`
File content:
```python
{file_content}
```""".format(
                    filename=filename, file_content=source_code
                )
            ),
        ]

        structured_llm = self.model.with_structured_output(TestUtilsFileSummary)
        return structured_llm.invoke(input_messages)

    def util_models_to_documents(self, summaries: Dict[str, TestUtilsFileSummary]):
        docs_chroma = []
        docs_mongo = []

        for file_path, summary in summaries.items():
            file_chunks, file_hash = build_chunks_from_python_file(file_path)

            for helper in summary.components:
                doc_vdb = Document(
                    page_content=helper.summary,
                    metadata={
                        "source": self.CHUNK_SOURCE,
                        "code_type": helper.type,
                        "name": helper.name,
                    },
                )
                qualified_name = self.get_object_qualified_name(
                    helper.name, helper.type, file_path
                )
                chunk = file_chunks[qualified_name]
                doc_vdb.metadata["id"] = chunk["hash"]

                item = helper.model_dump(mode="json")
                doc_mongo = {
                    "_id": chunk["hash"],
                    "imports": item["imports"],
                    "name": chunk["name"],
                    "type": chunk["type"],
                    "class_name": chunk["class_name"],
                    "qualified_name": chunk["qualified_name"],
                    "path": chunk["path"],
                }

                docs_chroma.append(doc_vdb)
                docs_mongo.append(doc_mongo)

        return docs_chroma, docs_mongo

    def run_tests(self):
        tests_workflow_app = self.init_workflow_app_tests()
        summaries = dict()
        for file_path in self.tests_list:
            if self.args["only_file"] is not None:
                if self.args["only_file"] != file_path:
                    continue
            summaries[file_path] = self.run_summarize_test_file(
                file_path, tests_workflow_app
            )
        docs_vectordb, docs_mongodb = self.test_models_to_documents(summaries)
        self.vectorstore.sync_documents(docs_vectordb)
        self.code_summary_db.sync_documents(docs_mongodb)

    def init_workflow_app_tests(self):
        self.workflow = StateGraph(state_schema=State)
        self.workflow.add_node("summarize_test_file", self.summarize_test_file)
        self.workflow.add_node("relate_to_features", self.relate_to_features)

        self.workflow.add_edge(START, "summarize_test_file")
        self.workflow.add_edge("summarize_test_file", "relate_to_features")
        self.workflow.add_edge("relate_to_features", END)

        memory = MemorySaver()
        self.workflow_app = self.workflow.compile(checkpointer=memory)

    def run_summarize_test_file(self, file_path, workflow_app):
        filename = Path(file_path).relative_to(self.args["project"])
        config = {"configurable": {"thread_id": filename}}

        output = workflow_app.invoke({"filename": filename}, config)
        return output["summary"]

    def summarize_test_file(self, state: State):
        with open(state["filename"], "r", encoding="utf-8") as f:
            source_code = f.read()

        input_messages = [
            SystemMessage(self.load_prompt(PROMPT_TEST_SUMMARY)),
            HumanMessage(
                """Filename: `{filename}`
File content:
```python
{file_content}
```""".format(
                    filename=str(state["filename"]), file_content=source_code
                )
            ),
        ]
        response = self.model.invoke(input_messages)
        return {"messages": response}

    def summarize_util_file(self, state: State):
        with open(state["filename"], "r", encoding="utf-8") as f:
            source_code = f.read()

        input_messages = [
            SystemMessage(self.load_prompt(PROMPT_TEST_SUMMARY)),
            HumanMessage(
                """Filename: `{filename}`
File content:
```python
{file_content}
```""".format(
                    filename=str(state["filename"]), file_content=source_code
                )
            ),
        ]
        response = self.model.invoke(input_messages)
        return {"messages": response}

    def relate_to_features(self, state: State):
        structured_llm = self.model.with_structured_output(TestFileSummary)
        features_content = self.get_features_content()

        input_messages = state["messages"] + [
            SystemMessage(self.prompts(PROMPT_FEATURE_MAP)),
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

    def models_to_documents(self, summaries: Dict[str, TestFileSummary]):
        for file_path, summary in summaries.items():
            docs_chroma = self.summary_to_document(summary)
            file_chunks, file_hash = build_chunks_from_python_file(file_path)

            # we need unique ids to track changes
            # If a code is not changed, it  will have its old id, hence we don't update it in vector db
            # first item belongs to module document
            docs_chroma[0].metadata["id"] = file_hash
            # adding id to components
            self.add_components_unique_ids(file_path, docs_chroma[1:], file_chunks)

            self.docs_mongodb.append(
                self.extra_information_module(summary, module_hash, file_path)
            )
            for component in summary.components:
                qualified_name = self.get_object_qualified_name(
                    component.name, component.type, file_path
                )
                self.docs_mongodb.append(
                    self.extra_information_component(
                        component, file_chunks[qualified_name]
                    )
                )

            self.docs_vectordb.extend(docs_chroma)

    def summary_to_document(self, summary: TestFileSummary):
        documents = []
        documents.append(
            Document(
                page_content=summary.summary,
                metadata={
                    "chunk_type": self.CHUNK_SOURCE,
                    "code_type": CodeType.TEST_FILE,
                },
            )
        )
        for component in summary.components:
            documents.append(
                Document(
                    page_content=component.summary,
                    metadata={
                        "chunk_type": self.CHUNK_SOURCE,
                        "code_type": component.type,
                        "name": component.name,
                    },
                )
            )
        return documents

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

    def add_components_unique_ids(self, file_path, summaries, file_chunks):
        for doc in summaries:
            qualified_name = self.get_object_qualified_name(
                doc.metadata["name"], doc.metadata["code_type"], file_path
            )
            chunk = file_chunks[qualified_name]
            doc.metadata["id"] = chunk["hash"]

    def extra_information_module(
        self, summary: TestFileSummary, module_hash, file_path
    ):
        item = summary.model_dump(mode="json")
        return {
            "_id": module_hash,
            "type": CodeType.MODULE,
            "path": file_path,
            "imports": item["imports"],
            "exports": item["exports"],
            "features_mapping": item["features_mapping"],
        }

    def extra_information_component(self, component: TestMethodSummary, chunk):
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
