import json
import os

from fcoverage.utils.code.python_utils import get_all_python_files, process_python_file
from fcoverage.utils.llm import EmbeddingsWrapper
from .base import TasksBase
import hashlib
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


class SourceCodeEmbeddingTask(TasksBase):

    def __init__(self, args, config):
        super().__init__(args, config)
        self.documents = dict()
        self.embeddings_wrapper = None
        self.rag_save_location = os.path.join(
            self.args["project"], self.config["rag-save-location"]
        )
        self.meta_data_path = os.path.join(
            self.args["project"], self.config["rag-save-location"], "metadata.json"
        )
        self.vectorstore = None

    def prepare(self):
        os.makedirs(self.rag_save_location, exist_ok=True)
        self.embeddings_wrapper = EmbeddingsWrapper(self.config)
        if os.path.exists(os.path.join(self.rag_save_location, "faiss_index.faiss")):
            self.vectorstore = FAISS.load_local(
                self.rag_save_location, self.embeddings_wrapper.model
            )
        else:
            self.vectorstore = None

    def run(self):
        self.build_chunks_for_python_source()
        self.build_index()
        return True

    def build_chunks_for_python_source(self):
        source_folder = os.path.join(self.args["project"], self.config["src"])
        file_path_list = get_all_python_files(source_folder)
        for file_path in file_path_list:
            chunks = process_python_file(file_path)
            for chunk in chunks:
                hash_id = self.hash_chunk(chunk["code"])
                metadata = {
                    "id": hash_id,
                    "path": chunk["path"],
                    "defined_function": chunk["function_name"],
                    "qualified_name": chunk["qualified_name"],
                    "chunk_type": chunk["type"],
                    "chunk_name": chunk["name"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                }
                self.documents[hash_id] = Document(
                    page_content=chunk["code"], metadata=metadata
                )

    def hash_chunk(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

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

        for hash_id, document in self.documents:
            if hash_id not in prev_metadata:
                new_docs.append(document)

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
                self.vectorstore = FAISS.from_documents(
                    new_docs, self.embeddings_wrapper.model
                )

        # Save
        self.vectorstore.save_local(self.rag_save_location)
        self.save_metadata(new_metadata)
        print(f"Updated vectorstore: {len(new_metadata)} chunks tracked")
