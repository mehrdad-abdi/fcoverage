import os
import time
from typing import List
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from tqdm import tqdm


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
        self.vectorstore.add_documents(documents)

    def search(self, query: str, k: int = 5) -> List[Document]:
        return self.vectorstore.similarity_search(query, k=k)

    def get_retriever(self):
        return self.vectorstore.as_retriever()


def index_all_project(
    vdb: VectorDBHelper, project_root, glob, suffixes, batch_size=250, sleep_seconds=1
):
    loader = GenericLoader.from_filesystem(
        project_root,
        glob=glob,
        suffixes=suffixes,
        parser=LanguageParser(),
    )
    docs = loader.load()

    for i in tqdm(range(0, len(docs), batch_size)):
        batch = docs[i : i + batch_size]
        vdb.add_documents(batch)
        time.sleep(sleep_seconds)
