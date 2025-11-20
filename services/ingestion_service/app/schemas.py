from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class BookMetadataOverrides(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    published_year: Optional[int] = None
    pg_id: Optional[str] = None


class IngestBookRequest(BaseModel):
    file_path: str
    overrides: Optional[BookMetadataOverrides] = None


class ChunkSummary(BaseModel):
    id: int
    book_id: int
    chunk_index: int
    start_char: int
    end_char: int


class BookRead(BaseModel):
    id: int
    pg_id: Optional[str]
    title: str
    author: Optional[str]
    language: Optional[str]
    published_year: Optional[int]
    source_path: str
    checksum: str
    word_count: int
    chunk_count: int
    created_at: datetime


class BookIngestionResponse(BaseModel):
    book: BookRead
    chunks: List[ChunkSummary]
    created: bool


class ChunkDetail(ChunkSummary):
    content: str
