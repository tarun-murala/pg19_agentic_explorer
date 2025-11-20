from typing import List

from fastapi import FastAPI, HTTPException, Path, Query
from sqlmodel import select

from .config import get_settings
from .db import get_session, init_db
from .ingestor import PG19BookIngestor
from .models import Book, Chunk
from .schemas import (
    BookIngestionResponse,
    BookRead,
    ChunkDetail,
    ChunkSummary,
    IngestBookRequest,
)
from .serializers import to_book_read, to_chunk_detail, to_chunk_summary

app = FastAPI(title="PG19 Ingestion Service")
settings = get_settings()
ingestor = PG19BookIngestor(settings=settings)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health", summary="Healthcheck")
async def healthcheck() -> dict:
    return {"status": "ok"}


@app.post(
    "/ingest/book",
    summary="Trigger ingestion for a PG-19 book",
    response_model=BookIngestionResponse,
)
async def ingest_book(request: IngestBookRequest) -> BookIngestionResponse:
    try:
        with get_session() as session:
            result = ingestor.ingest_from_path(
                file_path=request.file_path,
                session=session,
                overrides=request.overrides,
            )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    book_payload = to_book_read(result.book)
    chunk_payload = [to_chunk_summary(chunk) for chunk in result.chunks]
    return BookIngestionResponse(book=book_payload, chunks=chunk_payload, created=result.created)


@app.get("/books", response_model=List[BookRead])
async def list_books(limit: int = Query(25, ge=1, le=200)) -> List[BookRead]:
    with get_session() as session:
        statement = select(Book).order_by(Book.created_at.desc()).limit(limit)
        books = session.exec(statement).all()
        return [to_book_read(book) for book in books]


@app.get("/books/{book_id}", response_model=BookRead)
async def get_book(book_id: int = Path(..., ge=1)) -> BookRead:
    with get_session() as session:
        book = session.get(Book, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return to_book_read(book)


@app.get("/books/{book_id}/chunks", response_model=List[ChunkDetail])
async def get_book_chunks(
    book_id: int = Path(..., ge=1),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[ChunkDetail]:
    with get_session() as session:
        book = session.get(Book, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        statement = (
            select(Chunk)
            .where(Chunk.book_id == book_id)
            .order_by(Chunk.chunk_index)
            .offset(offset)
            .limit(limit)
        )
        chunks = session.exec(statement).all()
        return [to_chunk_detail(chunk) for chunk in chunks]
