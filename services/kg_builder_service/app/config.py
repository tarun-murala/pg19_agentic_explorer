from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for the KG builder service."""

    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="password", description="Neo4j password")
    llm_model: str = Field(default="codellama:7b", description="Model used for entity extraction")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama",
    )
    max_entities: int = Field(default=10, description="Max entities to request per chunk")
    chunk_request_timeout: int = Field(default=60, description="Timeout for LLM calls")
    timezone: Optional[str] = Field(default="UTC")

    class Config:
        env_prefix = "KG_"
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
