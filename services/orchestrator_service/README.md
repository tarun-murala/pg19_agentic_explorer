# Agent Orchestrator Service

Front-door FastAPI API that coordinates ingestion assets, KG knowledge, and specialized agents to answer chat-style questions.

## Dev setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## TODO
- Implement Analyzer/Retriever/KG/Answer agents
- Persist traces/results in Postgres
- Integrate shared `llm_client`
