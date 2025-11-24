import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .config import get_settings
from .history import HistoryStore
from .orchestrator import AgentOrchestrator
from .schemas import ChatQueryRequest, ChatQueryResponse


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
logger = logging.getLogger("orchestrator.api")

app = FastAPI(title="PG19 Agent Orchestrator")
settings = get_settings()
history_store = HistoryStore(settings.history_path)
orchestrator = AgentOrchestrator(settings=settings, history_store=history_store)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/chat/query", response_model=ChatQueryResponse)
async def chat_query(payload: ChatQueryRequest, request: Request) -> ChatQueryResponse:
    trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
    logger.info("chat_query start", extra={"trace_id": trace_id, "question": payload.question})
    resp = orchestrator.handle_query(payload, trace_id=trace_id)
    logger.info("chat_query end", extra={"trace_id": trace_id})
    return resp


@app.post("/chat/query/stream")
async def chat_query_stream(payload: ChatQueryRequest, request: Request) -> StreamingResponse:
    trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
    logger.info("chat_query_stream start", extra={"trace_id": trace_id, "question": payload.question})
    stream = orchestrator.stream_query(payload, trace_id=trace_id)
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
