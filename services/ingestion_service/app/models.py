from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pg_id: Optional[str] = Field(default=None, index=True)
    title: str
    author: Optional[str] = Field(default=None)
    language: Optional[str] = Field(default=None)
    published_year: Optional[int] = Field(default=None)
    source_path: str
    checksum: str = Field(index=True, unique=True)
    word_count: int
    chunk_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    chunk_index: int
    start_char: int
    end_char: int
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
