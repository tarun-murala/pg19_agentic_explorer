import logging
import uuid

from fastapi import FastAPI, HTTPException, Query, Request

from .config import get_settings
from .extractor import KGExtractor
from .graph_store import GraphStore
from .schemas import KGBuildRequest, KGBuildResponse, KGQueryResponse


LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] trace_id=%(trace_id)s %(message)s"


class SafeTraceFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "trace_id"):
            record.trace_id = "-"
        return super().format(record)


logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
formatter = SafeTraceFormatter(LOG_FORMAT)
for handler in logging.getLogger().handlers:
    handler.setFormatter(formatter)
logger = logging.getLogger("kg_builder.api")

app = FastAPI(title="PG19 KG Builder Service")
settings = get_settings()
extractor = KGExtractor(settings=settings)
graph_store = GraphStore(settings=settings)


@app.on_event("shutdown")
def shutdown_event() -> None:
    graph_store.close()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/kg/build", response_model=KGBuildResponse)
async def build_kg(payload: KGBuildRequest, request: Request) -> KGBuildResponse:
    trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
    logger.info(
        "kg_build start",
        extra={
            "trace_id": trace_id,
            "book_id": payload.book_id,
            "chunk_id": payload.chunk_id,
            "chunk_index": payload.chunk_index,
        },
    )
    entities, relations = extractor.extract(
        chunk_content=payload.chunk_content,
        book_title=payload.book_title,
        chunk_index=payload.chunk_index,
        trace_id=trace_id,
    )
    graph_store.upsert(
        book_id=payload.book_id,
        book_title=payload.book_title,
        chunk_id=payload.chunk_id,
        chunk_index=payload.chunk_index or -1,
        entities=entities,
        relations=relations,
        trace_id=trace_id,
    )
    logger.info(
        "kg_build complete",
        extra={
            "trace_id": trace_id,
            "entities_created": len(entities),
            "relations_created": len(relations),
        },
    )
    return KGBuildResponse(
        book_id=payload.book_id,
        chunk_id=payload.chunk_id,
        entities_created=len(entities),
        relations_created=len(relations),
        entities=entities,
        relations=relations,
    )


@app.get("/kg/entities", response_model=KGQueryResponse)
async def list_entities(
    request: Request,
    book_id: int | None = Query(default=None, description="Filter entities for book"),
    chunk_id: int | None = Query(default=None, description="Filter entities for chunk"),
) -> KGQueryResponse:
    if book_id is None and chunk_id is None:
        raise HTTPException(status_code=400, detail="Provide either book_id or chunk_id")
    trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
    logger.info(
        "kg_entities query",
        extra={"trace_id": trace_id, "book_id": book_id, "chunk_id": chunk_id},
    )
    return graph_store.query(book_id=book_id, chunk_id=chunk_id, trace_id=trace_id)
