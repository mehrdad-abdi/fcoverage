from typing import List, Optional
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain.embeddings.base import init_embeddings
from langchain_core.embeddings import Embeddings
from transformers import AutoModel, AutoTokenizer
import torch


class LLMWrapper:
    def __init__(self, config: dict):
        self.model_name = config.get("llm", {}).get("model", "gemini-2.0-flash")
        self.model_provider = config.get("llm", {}).get("provider", "google-genai")

    def prepare(self, prompts: list):
        self.init_model()
        self.prepare_prompt_template([("user", prompts)])

    def init_model(self):
        self.model = init_chat_model(
            self.model_name, model_provider=self.model_provider
        )

    def prepare_prompt_template(self, prompts: list):
        self.prompt_template = ChatPromptTemplate.from_messages(messages=prompts)

    def invoke(self, params: dict):
        prompt = self.prompt_template.invoke(params)

        response = self.model.invoke(prompt)
        return response


class EmbeddingsWrapper:
    def __init__(self, config: dict):
        self.model_name = config.get("embedding", {}).get(
            "model", "models/gemini-embedding-exp-03-07"
        )
        self.model_provider = config.get("embedding", {}).get(
            "provider", "google_genai"
        )
        self.batch_size = config.get("embedding", {}).get("batch_size", 32)
        self.model = None

    def prepare(self):
        if self.model_provider == "offline":
            self.init_model_offline()
        else:
            self.init_model_online()

    def init_model_offline(self):
        self.model = HuggingFaceCodeEmbeddings(self.model_name)

    def init_model_online(self):

        self.model = init_embeddings(
            model=self.model_name, provider=self.model_provider
        )

    def embed_batch(
        self, texts: list, batch_size: Optional[int] = None
    ) -> list[list[float]]:
        if batch_size is None:
            batch_size = self.batch_size
        embeddings = []
        for i in range(0, len(texts), batch_size):
            end = min(i + batch_size, len(texts))
            batch = texts[i:end]
            embeddings.extend(self.model.embed_documents(batch))
        return embeddings


class HuggingFaceCodeEmbeddings(Embeddings):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
            last_hidden_state = (
                outputs.last_hidden_state
            )  # (batch_size, seq_len, hidden_dim)
            cls_embedding = last_hidden_state[:, 0, :]  # CLS token
        return cls_embedding.squeeze().cpu().tolist()
