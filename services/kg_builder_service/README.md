# KG Builder Service

FastAPI microservice that extracts entities/relationships from PG-19 book chunks using the local LLM (Ollama) and stores them in Neo4j. The service exposes endpoints to run extraction for a specific chunk and to query the resulting graph for entities/relations tied to a book or chunk.

## Dev setup

```bash
cd services/kg_builder_service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../../shared/clients/llm_client
cp .env.example .env  # update Neo4j creds + Ollama URL
uvicorn app.main:app --reload --port 8002
```

Ensure you have:
- A running Neo4j instance (e.g., `docker run -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.21`).
- `ollama` running locally with the configured extraction model (default `codellama:latest`).

## Configuration

Environment variables (prefix `KG_`, see `.env.example`):

| Variable | Description | Default |
| --- | --- | --- |
| `NEO4J_URI` | Bolt connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `password` |
| `LLM_MODEL` | Ollama model to use for extraction | `codellama:latest` |
| `OLLAMA_BASE_URL` | Ollama HTTP endpoint | `http://localhost:11434` |
| `MAX_ENTITIES` | Hint to LLM for entity cap per chunk | `10` |

## REST surface

- `POST /kg/build` – body:

```jsonc
{
  "book_id": 1,
  "book_title": "Example Book",
  "chunk_id": 42,
  "chunk_index": 5,
  "chunk_content": "Paragraph text ..."
}
```

Runs entity/relation extraction for the chunk, upserts nodes/edges into Neo4j, and returns the extracted payload.

- `GET /kg/entities?book_id=1` – list unique entities/relations for the specified book.
- `GET /kg/entities?chunk_id=42` – same but scoped to one chunk.

`KGQueryResponse` includes `entities` with mention counts plus `relations` that describe edges and the chunk IDs that established them.

## Usage workflow

1. Ensure Neo4j + Ollama are running.
2. Ingest PG-19 books via the ingestion service and grab `book_id`, `chunk_id`, `chunk_content` for the chunk you want to map.
3. Call the build endpoint:

```bash
curl -X POST http://localhost:8002/kg/build \
  -H 'content-type: application/json' \
  -d '{"book_id": 1, "book_title": "Example", "chunk_id": 42, "chunk_index": 0, "chunk_content": "..."}'
```

4. Query the graph for that book/chunk:

```bash
curl 'http://localhost:8002/kg/entities?book_id=1'
```

This service will later be invoked by the orchestration pipeline to keep the KG in sync as new chunks are ingested.
