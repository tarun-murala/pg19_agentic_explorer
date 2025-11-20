from dataclasses import dataclass
from typing import Any, Dict

import httpx


@dataclass
class LLMRequest:
    prompt: str
    model: str = "codellama:latest"
    temperature: float = 0.1
    max_tokens: int = 512


@dataclass
class LLMResponse:
    output: str
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
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        response = self._client.post("/api/generate", json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return LLMResponse(output=data.get("response", ""), raw=data)
