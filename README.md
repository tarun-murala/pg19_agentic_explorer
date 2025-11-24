# PG19-Agentic-Explorer

PG19-Agentic-Explorer is a local, agentic RAG stack over the PG-19 Project Gutenberg corpus. The system ingests and chunks the long-form books, indexes them into vector stores, builds a knowledge graph (KG), then orchestrates a panel of specialized agents that retrieve, analyze, and answer user questions through a transparent UI.

## Monorepo layout

```
services/
  ingestion_service/
  kg_builder_service/
  orchestrator_service/
  ui/
shared/
  clients/
    llm_client/
docs/
```

- Each backend service is a small FastAPI app exposing dedicated responsibilities.
- The UI service (Next.js) consumes the orchestrator API and visualizes agent traces + KG context.
- Shared packages host cross-cutting modules like the thin `llm_client` abstraction that speaks to the local `ollama` runtime.

## Getting started

1. Ensure Python 3.11+ and Node 18+ are installed locally along with Docker/Qdrant/Neo4j as needed.
2. Launch shared infrastructure with `docker compose up -d ingestion-db qdrant ingestion-service orchestrator-service ui-service` (brings up Postgres, Qdrant, ingestion/vector API, orchestrator, and the Next.js UI). Ensure `./data/pg19` contains PG-19 texts and `./data/orchestrator` exists for trace persistence.
3. Install per-service dependencies (see each service README) and run them individually during development.
4. Use `.env` files per service (templates provided inside each service directory) to configure Postgres, Qdrant/Chroma, Neo4j, and the Ollama base URL.
   - If Ollama runs on the host while services run in Docker, point `*_OLLAMA_BASE_URL` at `http://host.docker.internal:11434` (the compose file already does this) so containers can reach it.

### Exporting PG-19 from Hugging Face shards

If you downloaded the dataset via `datasets.save_to_disk`, convert it into plain `.txt` files for the ingestion service using:

```bash
pip install datasets
python scripts/export_pg19_from_hf.py data/pg19_train_hf data/pg19
```

Optional: `--limit 10` to export a subset for smoke tests. The script writes Gutenberg-style headers and book text into `data/pg19/*.txt` so the ingestion service can pick them up.

Detailed component responsibilities and data flow diagrams live in [`ARCHITECTURE.md`](ARCHITECTURE.md).
