import json
import os

from fcoverage.utils.code.pytest_utils import (
    get_test_files,
    list_fixtures_used_in_test,
    run_test_and_collect_function_coverage,
)
from fcoverage.utils.code.python_utils import (
    get_all_python_files,
    build_chunks_from_python_file,
)
from .base import TasksBase
import hashlib
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.embeddings.base import init_embeddings


class CodeAnalysisTask(TasksBase):

    def __init__(self, args, config):
        super().__init__(args, config)
        self.documents = dict()
        self.embeddings_model = None
        self.conf_embedding_model = config.get("embedding", {}).get(
            "model", "models/gemini-embedding-exp-03-07"
        )
        self.conf_embedding_provider = config.get("embedding", {}).get(
            "provider", "google_genai"
        )

        self.rag_save_location = os.path.join(
            self.args["project"], self.config["rag-save-location"]
        )
        self.meta_data_path = os.path.join(
            self.args["project"], self.config["rag-save-location"], "metadata.json"
        )
        self.faiss_index_path = os.path.join(
            self.rag_save_location, "faiss_index.faiss"
        )
        self.vectorstore = None

    def prepare(self):
        os.makedirs(self.rag_save_location, exist_ok=True)
        self.embeddings_model = init_embeddings(
            model=self.conf_embedding_model,
            provider=self.conf_embedding_provider,
        )
        if os.path.exists(self.faiss_index_path):
            self.vectorstore = FAISS.load_local(
                self.rag_save_location, self.embeddings_model
            )
        else:
            self.vectorstore = None

    def run(self):
        self.build_chunks(
            os.path.join(self.args["project"], self.config["source"]), "source_code"
        )
        self.build_chunks(
            os.path.join(self.args["project"], self.config["tests"]), "test_code"
        )
        self.add_pytest_metadata()
        self.build_index()
        return True

    def build_chunks(self, source_folder, chunk_type):
        file_path_list = get_all_python_files(source_folder)
        for file_path in file_path_list:
            chunks = build_chunks_from_python_file(file_path)
            for chunk in chunks:
                hash_id = self.hash_chunk(chunk["code"])
                metadata = {
                    "id": hash_id,
                    "path": chunk["path"],
                    "defined_function": chunk["function_name"],
                    "qualified_name": chunk["qualified_name"],
                    "chunk_type": chunk_type,
                    "chunk_name": chunk["function_name"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                }
                self.documents[hash_id] = Document(
                    page_content=chunk["code"], metadata=metadata
                )

    def add_pytest_metadata(self):
        project_root = self.args["project"]
        test_path = os.path.join(project_root, self.config["tests"])
        source_path = os.path.join(project_root, self.config["source"])
        test_docs_by_path = {}
        for doc in self.documents.values():
            if doc.metadata["chunk_type"] == "test_code":
                if doc.metadata["path"] not in test_docs_by_path:
                    test_docs_by_path[doc.metadata["path"]] = []
                test_docs_by_path[doc.metadata["path"]].append(doc)

        documents_by_qualified_name = {
            doc.metadata["qualified_name"]: doc for doc in self.documents.values()
        }

        self.add_fixture_requests_metadata(
            project_root,
            test_path,
            source_path,
            test_docs_by_path,
            documents_by_qualified_name,
        )
        self.add_function_coverage_metadata(
            project_root,
            test_path,
            source_path,
            test_docs_by_path,
            documents_by_qualified_name,
        )

    def add_function_coverage_metadata(
        self,
        project_root,
        test_path,
        source_path,
        test_docs_by_path,
        documents_by_qualified_name,
    ):
        for document in self.documents.values():
            if document.metadata["chunk_type"] == "source_code":
                document.metadata["covered_by"] = []
            if document.metadata["chunk_type"] == "test_code":
                document.metadata["covers"] = []

        test_files = get_test_files(test_path)
        for test_file in test_files:
            covered_functions = run_test_and_collect_function_coverage(
                project_root, source_path, test_file
            )
            for coverage_file, function_name in covered_functions:
                qualified_name = (
                    f"{os.path.join(project_root,coverage_file)}:{function_name}"
                )
                if qualified_name in documents_by_qualified_name:
                    document = documents_by_qualified_name[qualified_name]
                    document.metadata["covered_by"].append(test_file)
                if test_file in test_docs_by_path:
                    documents = test_docs_by_path[test_file]
                    for document in documents:
                        document.metadata["covers"].append(qualified_name)

    def add_fixture_requests_metadata(
        self,
        project_root,
        test_path,
        source_path,
        test_docs_by_path,
        documents_by_qualified_name,
    ):
        for document in self.documents.values():
            # initilaize metadata for test documents
            if document.metadata["chunk_type"] == "test_code":
                document.metadata["fixture_requested_by"] = []
                document.metadata["fixture_requests"] = []

        test_files = get_test_files(test_path)

        for test_file in test_files:
            fixtures = list_fixtures_used_in_test(project_root, test_file, source_path)
            for fixture_name, fixture_location in fixtures.items():
                qualified_name = f"{os.path.join(project_root,fixture_location['path'])}:{fixture_name}"
                if qualified_name in documents_by_qualified_name:
                    document = documents_by_qualified_name[qualified_name]
                    document.metadata["fixture_requested_by"].append(test_file)
                if test_file in test_docs_by_path:
                    documents = test_docs_by_path[test_file]
                    for document in documents:
                        document.metadata["fixture_requests"].append(qualified_name)

    def hash_chunk(self, text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def load_metadata(self):
        if os.path.exists(self.meta_data_path):
            with open(self.meta_data_path) as f:
                return json.load(f)
        return {}

    def save_metadata(self, metadata: dict):
        with open(self.meta_data_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def build_index(self):
        new_docs = []
        new_metadata = {}
        prev_metadata = self.load_metadata()

        for hash_id, document in self.documents.items():
            if hash_id not in prev_metadata:
                new_docs.append(document)

            # TODO compare the metadata. If the metadata is changed, we need to update the document

            new_metadata[hash_id] = {"text": document.page_content, **document.metadata}

        # Remove deleted hashes
        removed_hashes = set(prev_metadata.keys()) - set(new_metadata.keys())
        if self.vectorstore and removed_hashes:
            self.vectorstore.delete(list(removed_hashes))

        # Add new/updated
        if new_docs:
            if self.vectorstore:
                self.vectorstore.add_documents(new_docs)
            else:
                self.vectorstore = FAISS.from_documents(new_docs, self.embeddings_model)

        # Save
        self.vectorstore.save_local(self.rag_save_location)
        self.save_metadata(new_metadata)
        print(f"Updated vectorstore: {len(new_metadata)} chunks tracked")
