from fastapi import FastAPI

app = FastAPI(title="PG19 Agent Orchestrator")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/chat/query")
async def chat_query() -> dict:
    # TODO: implement agent orchestration pipeline
    return {
        "answer": "placeholder",
        "trace": [],
    }


@app.get("/trace/{trace_id}")
async def get_trace(trace_id: str) -> dict:
    # TODO: load trace from persistence
    return {"trace_id": trace_id, "steps": []}
