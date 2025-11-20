"""Thin abstraction for talking to local LLM runtimes (Ollama)."""

from .client import (
    EmbeddingRequest,
    EmbeddingResponse,
    LLMClient,
    LLMRequest,
    LLMResponse,
)

__all__ = [
    "LLMClient",
    "LLMRequest",
    "LLMResponse",
    "EmbeddingRequest",
    "EmbeddingResponse",
]
