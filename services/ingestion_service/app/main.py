from typing import List

from fastapi import FastAPI, HTTPException, Path, Query
from sqlmodel import select

from .config import get_settings
from .db import get_session, init_db
from .embeddings import EmbeddingService
from .ingestor import PG19BookIngestor
from .models import Book, Chunk
from .schemas import (
    BookIngestionResponse,
    BookRead,
    ChunkDetail,
    ChunkSummary,
    IndexBookRequest,
    IndexBookResponse,
    IngestBookRequest,
    RAGChunkResult,
    RAGQueryRequest,
    RAGQueryResponse,
)
from .serializers import to_book_read, to_chunk_detail, to_chunk_summary
from .vector_store import VectorStore

app = FastAPI(title="PG19 Ingestion Service")
settings = get_settings()
ingestor = PG19BookIngestor(settings=settings)
embedding_service = EmbeddingService(settings=settings)
vector_store = VectorStore(settings=settings)


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


@app.post("/vector/index", response_model=IndexBookResponse, summary="Embed and index all chunks for a book")
async def index_book(request: IndexBookRequest) -> IndexBookResponse:
    with get_session() as session:
        book = session.get(Book, request.book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        book_id = book.id
        statement = select(Chunk).where(Chunk.book_id == book_id).order_by(Chunk.chunk_index)
        chunks = session.exec(statement).all()
        if not chunks:
            raise HTTPException(status_code=400, detail="Book has no chunks to index")

    if request.reindex:
        vector_store.delete_book(book_id)

    embeddings = embedding_service.embed_texts(chunk.content for chunk in chunks)
    vector_store.upsert_chunks(chunks, embeddings)
    return IndexBookResponse(book_id=book_id, chunks_indexed=len(chunks))


@app.post("/rag/query", response_model=RAGQueryResponse, summary="Query vector store for top-k chunks")
async def rag_query(request: RAGQueryRequest) -> RAGQueryResponse:
    query_vector = embedding_service.embed_text(request.query)
    top_k = request.top_k or settings.rag_top_k
    search_results = vector_store.search(query_vector, top_k)

    rag_results: List[RAGChunkResult] = []
    for point in search_results:
        payload = point.payload or {}
        chunk = ChunkDetail(
            id=int(payload.get("chunk_id") or point.id),
            book_id=int(payload.get("book_id")),
            chunk_index=int(payload.get("chunk_index")),
            start_char=int(payload.get("start_char")),
            end_char=int(payload.get("end_char")),
            content=payload.get("content", ""),
        )
        rag_results.append(RAGChunkResult(chunk=chunk, score=float(point.score)))

    return RAGQueryResponse(query=request.query, results=rag_results)
