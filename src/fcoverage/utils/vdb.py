import os
from typing import List
from langchain_chroma import Chroma
from langchain.schema import Document


class VectorDBHelper:
    def __init__(
        self,
        persist_directory: str,
        collection_name: str,
        embedding_model: str,
        embedding_provider: str,
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.embedding_provider = embedding_provider

        self.init_embeddings()
        os.makedirs(self.persist_directory, exist_ok=True)

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

    def init_google_genai(self):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        self.embeddings = GoogleGenerativeAIEmbeddings(model=self.embedding_model)

    def init_embeddings_generic(self):
        from langchain.embeddings.base import init_embeddings

        self.embeddings = init_embeddings(
            model=self.embedding_model,
            provider=self.embedding_provider,
        )

    def init_embeddings(self):
        match self.embedding_provider:
            case "google_genai":
                self.init_google_genai()
            case _:
                self.init_embeddings_generic()

    def add_documents(self, documents: List[Document]):
        ids_ = [doc.metadata["id"] for doc in documents]
        self.vectorstore.add_documents(documents, ids=ids_)

    def search(self, query: str, k: int = 5) -> List[Document]:
        return self.vectorstore.similarity_search(query, k=k)

    def get_retriever(self):
        return self.vectorstore.as_retriever()

    def clear(self):
        # WARNING: This deletes the local vector DB
        import shutil

        shutil.rmtree(self.persist_directory, ignore_errors=True)

    def sync_documents(self, documents: List[Document]):
        current_ids = [d.metadata["id"] for d in documents]

        # 1. Get all existing IDs from the DB
        existing_ids = self.vectorstore.get()["ids"]

        # 2. Identify what to delete and what to add
        ids_to_add = [id_ for id_ in current_ids if id_ not in existing_ids]
        ids_to_delete = [id_ for id_ in existing_ids if id_ not in current_ids]

        # 3. Delete obsolete entries
        if ids_to_delete:
            self.vectorstore.delete(ids=ids_to_delete)

        # 4. Add new entries
        if ids_to_add:
            docs_to_add = []
            for doc in documents:
                if doc.metadata["id"] in ids_to_add:
                    docs_to_add.append(doc)

            self.add_documents(docs_to_add)
