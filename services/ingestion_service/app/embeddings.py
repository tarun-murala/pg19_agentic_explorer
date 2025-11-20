from __future__ import annotations

from typing import Iterable, List

from shared.clients.llm_client import EmbeddingRequest, LLMClient

from .config import Settings, get_settings


class EmbeddingService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = LLMClient(base_url=self.settings.ollama_base_url)

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            request = EmbeddingRequest(prompt=text, model=self.settings.embedding_model)
            response = self.client.embed(request)
            vectors.append(response.embedding)
        return vectors

    def embed_text(self, text: str) -> List[float]:
        request = EmbeddingRequest(prompt=text, model=self.settings.embedding_model)
        response = self.client.embed(request)
        return response.embedding
