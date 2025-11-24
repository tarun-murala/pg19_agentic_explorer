from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ingestion_service_url: str = Field(default="http://localhost:8001", description="Chunk metadata + rag endpoint")
    kg_service_url: str = Field(default="http://localhost:8002", description="KG builder/query service")
    llm_model: str = Field(default="codellama:7b", description="Model used for analyzer/answer agents")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama HTTP endpoint",
    )
    rag_top_k: int = Field(default=4, description="Default top-k chunks to request from ingestion service")
    history_path: str = Field(default="data/orchestrator_history.json", description="Path for conversation history persistence")

    class Config:
        env_prefix = "ORCH_"
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
