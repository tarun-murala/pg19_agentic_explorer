from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for the ingestion service."""

    database_url: str = Field(
        default="sqlite:///./ingestion.db",
        description="SQLAlchemy URL for metadata storage",
    )
    pg19_root: Path = Field(
        default=Path("./data/pg19"),
        description="Root directory containing PG-19 text files",
    )
    chunk_size: int = Field(default=1200, description="Chunk size in characters")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    embedding_model: str = Field(default="nomic-embed-text", description="Ollama embedding model")
    vector_collection: str = Field(default="pg19_chunks", description="Qdrant collection name")
    vector_host: str = Field(default="localhost", description="Qdrant host")
    vector_port: int = Field(default=6333, description="Qdrant gRPC/REST port")
    vector_grpc_port: int = Field(default=6334, description="Qdrant gRPC port")
    rag_top_k: int = Field(default=5, description="Default number of chunks to return for RAG query")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for the local Ollama runtime",
    )
    timezone: Optional[str] = Field(default="UTC", description="Timezone for timestamps")

    class Config:
        env_prefix = "INGESTION_"
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
