from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from .config import get_settings
from .history import HistoryStore
from .orchestrator import AgentOrchestrator
from .schemas import ChatQueryRequest, ChatQueryResponse

app = FastAPI(title="PG19 Agent Orchestrator")
settings = get_settings()
history_store = HistoryStore(settings.history_path)
orchestrator = AgentOrchestrator(settings=settings, history_store=history_store)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/chat/query", response_model=ChatQueryResponse)
async def chat_query(request: ChatQueryRequest) -> ChatQueryResponse:
    return orchestrator.handle_query(request)


@app.post("/chat/query/stream")
async def chat_query_stream(request: ChatQueryRequest) -> StreamingResponse:
    stream = orchestrator.stream_query(request)
    return StreamingResponse(stream, media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.get("/history")
async def history(limit: int = 20):
    return history_store.list_entries(limit)


@app.get("/trace/{trace_id}")
async def get_trace(trace_id: str) -> JSONResponse:
    entry = history_store.get_entry(trace_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Trace not found")
    return JSONResponse(
        content=entry.model_dump(),
        headers={"Content-Disposition": f"attachment; filename=trace-{trace_id}.json"},
    )
