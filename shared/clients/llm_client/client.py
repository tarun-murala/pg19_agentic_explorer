from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

import httpx


@dataclass
class LLMRequest:
    prompt: str
    model: str = "codellama:7b"
    temperature: float = 0.1
    max_tokens: int = 512


@dataclass
class LLMResponse:
    output: str
    raw: Dict[str, Any]


@dataclass
class EmbeddingRequest:
    prompt: str
    model: str = "nomic-embed-text"


@dataclass
class EmbeddingResponse:
    embedding: List[float]
    raw: Dict[str, Any]


class LLMClient:
    """Simple synchronous Ollama HTTP client."""

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self._base_url)

    def generate(self, request: LLMRequest) -> LLMResponse:
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            # Use non-streaming responses so we can parse JSON in one shot
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        response = self._client.post("/api/generate", json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return LLMResponse(output=data.get("response", ""), raw=data)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        payload = {
            "model": request.model,
            "prompt": request.prompt,
        }
        response = self._client.post("/api/embeddings", json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        embedding = data.get("embedding") or data.get("data", [{}])[0].get("embedding", [])
        return EmbeddingResponse(embedding=list(embedding), raw=data)

    def embed_batch(self, prompts: Iterable[str], model: str | None = None) -> List[List[float]]:
        vectors: List[List[float]] = []
        for prompt in prompts:
            response = self.embed(EmbeddingRequest(prompt=prompt, model=model or "nomic-embed-text"))
            vectors.append(response.embedding)
        return vectors
