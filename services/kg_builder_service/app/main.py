from fastapi import FastAPI, HTTPException, Query

from .config import get_settings
from .extractor import KGExtractor
from .graph_store import GraphStore
from .schemas import KGBuildRequest, KGBuildResponse, KGQueryResponse

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
async def build_kg(request: KGBuildRequest) -> KGBuildResponse:
    entities, relations = extractor.extract(
        chunk_content=request.chunk_content,
        book_title=request.book_title,
        chunk_index=request.chunk_index,
    )
    graph_store.upsert(
        book_id=request.book_id,
        book_title=request.book_title,
        chunk_id=request.chunk_id,
        chunk_index=request.chunk_index or -1,
        entities=entities,
        relations=relations,
    )
    return KGBuildResponse(
        book_id=request.book_id,
        chunk_id=request.chunk_id,
        entities_created=len(entities),
        relations_created=len(relations),
        entities=entities,
        relations=relations,
    )


@app.get("/kg/entities", response_model=KGQueryResponse)
async def list_entities(
    book_id: int | None = Query(default=None, description="Filter entities for book"),
    chunk_id: int | None = Query(default=None, description="Filter entities for chunk"),
) -> KGQueryResponse:
    if book_id is None and chunk_id is None:
        raise HTTPException(status_code=400, detail="Provide either book_id or chunk_id")
    return graph_store.query(book_id=book_id, chunk_id=chunk_id)
