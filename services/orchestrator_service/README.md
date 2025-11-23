# Agent Orchestrator Service

Front-door FastAPI API that coordinates four agents (Analyzer, RAG Retrieval, KG Context, and Answer Generator) to answer chat-style queries using the PG-19 knowledge base. The service persists conversation history + traces and exposes streaming endpoints for real-time UI updates.

## Dev setup

```bash
cd services/orchestrator_service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../../shared/clients/llm_client
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

To run via Docker Compose (with dependencies), use `docker compose up -d orchestrator-service` from the repo root.

### Pre-reqs
- Ingestion/vector service (`http://localhost:8001`) exposing `/rag/query`.
- KG builder service (`http://localhost:8002`) exposing `/kg/entities`.
- Local `ollama` runtime with the configured model (default `codellama:latest`).

## Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `ORCH_INGESTION_SERVICE_URL` | Base URL for ingestion/vector API | `http://localhost:8001` |
| `ORCH_KG_SERVICE_URL` | Base URL for KG builder API | `http://localhost:8002` |
| `ORCH_LLM_MODEL` | Ollama model used by Analyzer + Answer agents | `codellama:latest` |
| `ORCH_OLLAMA_BASE_URL` | Ollama HTTP endpoint | `http://localhost:11434` |
| `ORCH_RAG_TOP_K` | Default chunk count for retrieval | `4` |
| `ORCH_HISTORY_PATH` | JSON file used to persist history/traces | `data/orchestrator_history.json` |

## API surface

| Endpoint | Description |
| --- | --- |
| `POST /chat/query` | Runs the full agent pipeline and returns the answer, citations, trace, and `conversation_id`. |
| `POST /chat/query/stream` | Server-sent events stream delivering per-agent trace steps followed by the final payload. |
| `GET /history?limit=20` | Lists recent conversation summaries from the persisted history store. |
| `GET /trace/{trace_id}` | Downloads the full trace (as JSON) for a historical conversation. |
| `GET /health` | Basic service healthcheck. |

`/chat/query/stream` emits events shaped as:

```jsonc
{ "type": "step", "payload": TraceStep }
{ "type": "final", "payload": ChatQueryResponse }
{ "type": "error", "message": "..." }
```

This allows the UI to render partial results while the analyzer/retriever/KG/answer agents finish.

## Agent flow

1. **Analyzer Agent** – LLM prompt that infers intent, relevant entities, and required detail level.
2. **RAG Retrieval Agent** – Calls ingestion `/rag/query` to grab the top-k scored chunks.
3. **KG Context Agent** – Queries the KG builder for entities/relations tied to the retrieved chunk/book ids.
4. **Answer Agent** – Synthesizes the final response with chunk context + KG hints; returns answer text + chunk citations.

Each agent produces a structured `TraceStep` that is persisted alongside the conversation, powering downloadable traces and detailed UI timelines.
