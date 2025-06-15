import os
from pathlib import Path

from fcoverage.models.tests_summary import (
    TestFileSummary,
    TestMethodSummary,
    TestUtilsFileSummary,
)
from fcoverage.utils.code.pytest_utils import (
    get_test_files,
    list_fixtures_used_in_test,
    run_test_and_collect_function_coverage,
)
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


PROMPT_TEST_SUMMARY = "tests_summarization_1_system"
PROMPT_FEATURE_MAP = "tests_summarization_2_system"
PROMPT_TEST_UTILS = "test_utils_summarization"


class TestUtilsSummarizationTask(TasksBase):
    CHUNK_SOURCE = "test-utils-summary"

    def __init__(
        self, args, config, model, vectorstore, code_summary_db, prompts, utils_list
    ):
        super().__init__(args, config)
        self.model = model
        self.vectorstore = vectorstore
        self.code_summary_db = code_summary_db
        self.prompts = prompts
        self.utils_list = utils_list

    def run(self):
        summaries = dict()
        for file_path in self.utils_list:
            if self.args["only_file"] is not None:
                if self.args["only_file"] != file_path:
                    continue
            summaries[file_path] = self.run_summarize_file(file_path)
        docs_vectordb, docs_mongodb = self.models_to_documents(summaries)
        self.vectorstore.sync_documents(docs_vectordb)
        self.code_summary_db.sync_documents(docs_mongodb)

    def run_summarize_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        filename = Path(file_path).relative_to(self.args["project"])
        input_messages = [
            SystemMessage(self.prompts[PROMPT_TEST_UTILS]),
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

    def models_to_documents(self, summaries: Dict[str, TestUtilsFileSummary]):
        docs_chroma = []
        docs_mongo = []

        for file_path, summary in summaries.items():
            file_chunks, file_hash = build_chunks_from_python_file(file_path)

            for helper in summary.components:
                qualified_name = self.get_object_qualified_name(
                    helper.name, helper.type, file_path
                )
                chunk = file_chunks[qualified_name]

                doc_vdb = Document(
                    page_content=helper.summary,
                    metadata={
                        "source": self.CHUNK_SOURCE,
                        "code_type": helper.type,
                        "name": helper.name,
                        "id": chunk["hash"],
                    },
                )

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


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    summary: TestFileSummary
    file_path: str


class TestFilesSummarizationTask(TasksBase):
    CHUNK_SOURCE = "test-files-summary"

    def __init__(
        self, args, config, model, vectorstore, code_summary_db, prompts, tests_list
    ):
        super().__init__(args, config)
        self.model = model
        self.vectorstore = vectorstore
        self.code_summary_db = code_summary_db
        self.prompts = prompts
        self.tests_list = tests_list
        self.workflow_app = self.init_workflow_app()

    def run(self):
        summaries = dict()
        fixtures = dict()
        covered_functions = dict()
        for file_path in self.tests_list:
            if self.args["only_file"] is not None:
                if self.args["only_file"] != file_path:
                    continue
            summaries[file_path] = self.run_summarize_file(file_path)
            fixtures[file_path] = list_fixtures_used_in_test(
                self.args["project"], file_path, self.args["source"]
            )
            covered_functions[file_path] = run_test_and_collect_function_coverage(
                self.args["project"], self.args["source"], file_path
            )
        docs_vectordb, docs_mongodb = self.models_to_documents(summaries)
        self.vectorstore.sync_documents(docs_vectordb)
        self.code_summary_db.sync_documents(docs_mongodb)
        self.update_coverage()

    def init_workflow_app(self):
        workflow = StateGraph(state_schema=State)
        workflow.add_node("summarize_test_file", self.summarize_test_file)
        workflow.add_node("relate_to_features", self.relate_to_features)

        workflow.add_edge(START, "summarize_test_file")
        workflow.add_edge("summarize_test_file", "relate_to_features")
        workflow.add_edge("relate_to_features", END)

        memory = MemorySaver()
        self.workflow_app = workflow.compile(checkpointer=memory)

    def run_summarize_file(self, file_path):
        config = {"configurable": {"thread_id": file_path}}
        output = self.workflow_app.invoke({"filename": file_path}, config)
        return output["summary"]

    def summarize_test_file(self, state: State):
        filename = Path(state["file_path"]).relative_to(self.args["project"])
        with open(state["file_path"], "r", encoding="utf-8") as f:
            source_code = f.read()

        input_messages = [
            SystemMessage(self.prompts[PROMPT_TEST_SUMMARY]),
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
        response = self.model.invoke(input_messages)
        return {"messages": response}

    def relate_to_features(self, state: State):
        structured_llm = self.model.with_structured_output(TestFileSummary)
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

    def models_to_documents(self, summaries: Dict[str, TestFileSummary]):
        for file_path, summary in summaries.items():
            file_chunks, module_hash = build_chunks_from_python_file(file_path)
            fixtures = list_fixtures_used_in_test(
                self.args["project"], file_path, self.args["source"]
            )

            self.docs_vectordb.append(
                self.test_file_summary_to_document(summary, module_hash)
            )
            self.docs_mongodb.append(
                self.extra_information_test_files(
                    summary, module_hash, file_path, fixtures
                )
            )
            for component in summary.components:
                qualified_name = self.get_object_qualified_name(
                    component.name, component.type, file_path
                )
                chunk = file_chunks[qualified_name]
                self.docs_vectordb.append(
                    self.test_method_summary_to_document(component, chunk["hash"])
                )
                self.docs_mongodb.append(
                    self.extra_information_test_method(component, chunk)
                )

    def test_file_summary_to_document(self, summary: TestFileSummary, hash: str):
        return Document(
            page_content=summary.summary,
            metadata={
                "source": self.CHUNK_SOURCE,
                "code_type": CodeType.MODULE,
                "id": hash,
            },
        )

    def test_method_summary_to_document(self, component: TestMethodSummary, hash: str):
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

    def extra_information_test_files(
        self, summary: TestFileSummary, module_hash, file_path, fixtures
    ):
        item = summary.model_dump(mode="json")
        fixture_requests = []
        for fixture_name, fixture_location in fixtures.items():
            fixture_requests.append(
                self.get_object_qualified_name(
                    fixture_name,
                    None,
                    os.path.join(self.args["project"], fixture_location["path"]),
                )
            )
        return {
            "_id": module_hash,
            "type": CodeType.MODULE,
            "path": file_path,
            "imports": item["imports"],
            "exports": item["exports"],
            "features_mapping": item["features_mapping"],
            "fixture_requests": fixture_requests,
        }

    def extra_information_test_method(
        self, component: TestMethodSummary, chunk, fixtures
    ):
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
        self.utils_task = None
        self.tests_task = None

    def prepare(self):
        self.load_llm_model()
        self.load_vectordb_helper()
        self.load_mongodb_helper()
        self.load_prompts()
        self.tests_list, self.utils_list = get_test_files(
            os.path.join(self.args["project"], self.config["tests"])
        )
        self.utils_task = TestUtilsSummarizationTask()
        self.tests_task = TestFilesSummarizationTask()

    def run(self):
        result1 = self.utils_task.run()
        result2 = self.tests_task.run()
        return result1 and result2
