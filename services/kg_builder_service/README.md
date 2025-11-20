# KG Builder Service

FastAPI microservice that extracts entities/relationships from ingested PG-19 chunks and syncs them to Neo4j.

## Dev setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

## TODO
- Connect to ingestion metadata stream
- Implement LLM-backed entity extraction via `llm_client`
- Upsert nodes/edges into Neo4j
