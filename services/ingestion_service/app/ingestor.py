from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from sqlmodel import Session, select

from .config import Settings, get_settings
from .models import Book, Chunk
from .schemas import BookMetadataOverrides

_START_MARKER = "*** START"
_END_MARKER = "*** END"


@dataclass
class IngestResult:
    book: Book
    chunks: List[Chunk]
    created: bool


class PG19BookIngestor:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def ingest_from_path(
        self,
        file_path: str,
        session: Session,
        overrides: Optional[BookMetadataOverrides] = None,
    ) -> IngestResult:
        path = self._resolve_path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PG-19 file not found: {path}")

        raw_text = path.read_text(encoding="utf-8", errors="ignore")
        metadata_section, body = self._split_metadata_body(raw_text)
        metadata = self._parse_metadata(metadata_section, path)
        if overrides:
            override_dict = overrides.dict(exclude_unset=True)
            metadata.update({k: v for k, v in override_dict.items() if v is not None})

        checksum = hashlib.sha256(body.encode("utf-8", errors="ignore")).hexdigest()
        existing = session.exec(select(Book).where(Book.checksum == checksum)).first()
        if existing:
            chunks = self._load_chunks(existing.id, session)
            return IngestResult(book=existing, chunks=chunks, created=False)

        words = body.split()
        chunk_models = self._build_chunks(body)
        book = Book(
            pg_id=metadata.get("pg_id"),
            title=metadata.get("title", path.stem),
            author=metadata.get("author"),
            language=metadata.get("language"),
            published_year=metadata.get("published_year"),
            source_path=str(path),
            checksum=checksum,
            word_count=len(words),
            chunk_count=len(chunk_models),
        )
        session.add(book)
        session.commit()
        session.refresh(book)

        for chunk in chunk_models:
            chunk.book_id = book.id
            session.add(chunk)
        session.commit()

        chunks = self._load_chunks(book.id, session)
        return IngestResult(book=book, chunks=chunks, created=True)

    def _load_chunks(self, book_id: int, session: Session) -> List[Chunk]:
        statement = select(Chunk).where(Chunk.book_id == book_id).order_by(Chunk.chunk_index)
        return list(session.exec(statement).all())

    def _build_chunks(self, body: str) -> List[Chunk]:
        size = self.settings.chunk_size
        overlap = min(self.settings.chunk_overlap, size)
        step = max(size - overlap, 1)
        chunks: List[Chunk] = []
        start = 0
        idx = 0
        while start < len(body):
            end = min(start + size, len(body))
            content = body[start:end].strip()
            if not content:
                start += step
                continue
            chunks.append(
                Chunk(
                    book_id=0,  # filled later
                    chunk_index=idx,
                    start_char=start,
                    end_char=end,
                    content=content,
                )
            )
            idx += 1
            start += step
        return chunks

    def _resolve_path(self, file_path: str) -> Path:
        candidate = Path(file_path)
        if candidate.is_absolute():
            return candidate
        return (self.settings.pg19_root / candidate).resolve()

    def _split_metadata_body(self, text: str) -> Tuple[str, str]:
        lowered = text.lower()
        start_idx = lowered.find(_START_MARKER.lower())
        end_idx = lowered.find(_END_MARKER.lower())
        if start_idx != -1:
            # skip marker line entirely
            start_line_end = text.find("\n", start_idx)
            body_start = start_line_end + 1 if start_line_end != -1 else start_idx
            body = text[body_start:]
            metadata_section = text[:start_idx]
        else:
            metadata_section = text[:2000]
            body = text
        if end_idx != -1 and end_idx > start_idx:
            body = text[start_idx:end_idx]
        return metadata_section, body

    def _parse_metadata(self, metadata_section: str, path: Path) -> dict:
        lines = [line.strip() for line in metadata_section.splitlines() if line.strip()]
        meta = {}
        for line in lines[:200]:
            lowered = line.lower()
            if lowered.startswith("title:"):
                meta["title"] = line.split(":", 1)[1].strip()
            elif lowered.startswith("author:"):
                meta["author"] = line.split(":", 1)[1].strip()
            elif lowered.startswith("language:"):
                meta["language"] = line.split(":", 1)[1].strip()
            elif lowered.startswith("release date:"):
                meta["release_date"] = line.split(":", 1)[1].strip()
                year_match = re.search(r"(\d{4})", line)
                if year_match:
                    meta["published_year"] = int(year_match.group(1))
            elif "ebook" in lowered and "#" in line:
                pg_match = re.search(r"#(\d+)", line)
                if pg_match:
                    meta["pg_id"] = pg_match.group(1)

        if "pg_id" not in meta:
            filename_match = re.search(r"(\d+)", path.stem)
            if filename_match:
                meta["pg_id"] = filename_match.group(1)
        if "title" not in meta:
            meta["title"] = path.stem
        return meta
