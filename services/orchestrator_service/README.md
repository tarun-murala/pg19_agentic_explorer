# Agent Orchestrator Service

Front-door FastAPI API that coordinates four agents (Analyzer, RAG Retrieval, KG Context, and Answer Generator) to answer chat-style queries using the PG-19 knowledge base.

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

Pre-reqs:
- Ingestion/vector service running (`http://localhost:8001`) to serve `/rag/query`.
- KG builder service running (`http://localhost:8002`) to serve `/kg/entities`.
- Local `ollama` runtime with the configured model (default `codellama:latest`).

## Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `ORCH_INGESTION_SERVICE_URL` | Base URL for ingestion/vector API | `http://localhost:8001` |
| `ORCH_KG_SERVICE_URL` | Base URL for KG builder API | `http://localhost:8002` |
| `ORCH_LLM_MODEL` | Ollama model used by Analyzer + Answer agents | `codellama:latest` |
| `ORCH_OLLAMA_BASE_URL` | Ollama HTTP endpoint | `http://localhost:11434` |
| `ORCH_RAG_TOP_K` | Default chunk count for retrieval | `4` |

## API

`POST /chat/query`

```jsonc
{
  "question": "How does the narrator describe the city?",
  "top_k": 4
}
```

Response:

```jsonc
{
  "answer": "...",
  "citations": [34, 35],
  "trace": [
    {
      "agent": "AnalyzerAgent",
      "input": {"question": "..."},
      "output": {"intent": "analyze", "entities": ["city"], "detail_level": "medium"},
      "started_at": "2024-05-22T12:00:00Z",
      "finished_at": "2024-05-22T12:00:01Z"
    },
    ...
  ]
}
```

Trace steps expose the inputs/outputs per agent so the UI can visualize the orchestration flow end-to-end.

## Agent flow

1. **Analyzer Agent** – categorizes the question, extracts named entities, and infers desired detail level with an LLM prompt.
2. **RAG Retrieval Agent** – calls the ingestion service `/rag/query` endpoint to fetch the top-k scored chunks.
3. **KG Context Agent** – queries the KG builder for entities/relations related to the retrieved chunk(s) (prefers chunk scope, falls back to book scope).
4. **Answer Agent** – synthesizes the final answer using chunk content + KG hints via the LLM, returning answer text + chunk ID citations.

The orchestrator stitches these agents in sequence and returns the full trace for observability.
