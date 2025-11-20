from fastapi import FastAPI

from .config import get_settings
from .orchestrator import AgentOrchestrator
from .schemas import ChatQueryRequest, ChatQueryResponse

app = FastAPI(title="PG19 Agent Orchestrator")
settings = get_settings()
orchestrator = AgentOrchestrator(settings=settings)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/chat/query", response_model=ChatQueryResponse)
async def chat_query(request: ChatQueryRequest) -> ChatQueryResponse:
    return orchestrator.handle_query(request)
