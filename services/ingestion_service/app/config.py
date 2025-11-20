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
    timezone: Optional[str] = Field(default="UTC", description="Timezone for timestamps")

    class Config:
        env_prefix = "INGESTION_"
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
