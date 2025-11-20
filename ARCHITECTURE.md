# PG19-Agentic-Explorer Architecture

## High-level system

```
+-----------------+        +-----------------+        +-------------------+
| Ingestion       |  ETL   | KG Builder      |  KG    | Agent Orchestrator|
| Service         +------->| Service         +------->| / API Gateway      +--+
| (PG-19 -> Vect) |        | (Neo4j nodes)   |        | (Agents & Routing) |  |
+-----------------+        +-----------------+        +-------------------+  |
                                                                            v
                                                   +------------------------------+
                                                   | React/Next.js UI             |
                                                   | - Chat / Trace visualizer    |
                                                   | - KG highlights              |
                                                   +------------------------------+
```

## Service responsibilities

### Ingestion Service
- **Purpose**: Download/manage PG-19 texts, chunk them, embed chunks, and push them into a vector DB while storing metadata in Postgres.
- **Tech**: Python, FastAPI, async ingestion workers.
- **Persistence**: Postgres for document metadata, Qdrant/Chroma for vectors, shared object store (local disk/S3-compatible) for raw texts.
- **Interfaces**:
  - `POST /ingest/book`: trigger ingestion for a PG-19 file.
  - `GET /status/{job_id}`: fetch ingestion progress.

### KG Builder Service
- **Purpose**: Consume normalized book metadata/chunks, extract entities/relations with the LLM, and upsert nodes/edges into Neo4j.
- **Tech**: Python, FastAPI worker.
- **Persistence**: Neo4j/Aura or local container.
- **Interfaces**:
  - `POST /kg/build`: build/refresh KG slice for a book.
  - `GET /kg/entities`: query for nodes/relations.

### Agent Orchestrator
- **Purpose**: Front-door API for the UI; orchestrates Analyzer, Retriever, KG Agent, and Answer Generator steps using the shared `llm_client`.
- **Tech**: Python, FastAPI, Async orchestration layer.
- **Persistence**: Reads from Postgres, Qdrant, and Neo4j.
- **Interfaces**:
  - `POST /chat/query`: run the multi-agent workflow and return answer + trace.
  - `GET /trace/{id}`: fetch stored trace for replay/debugging.

### UI Service
- **Purpose**: Professional React/Next.js front-end that offers chat, trace timeline, and KG visualization components.
- **Tech**: Next.js 14 app router, Tailwind/Chakra for layout, D3/vis-network for KG viz.
- **Interfaces**:
  - Talks to orchestrator via REST/WebSocket; no direct DB access.

## Cross-cutting packages

- `shared/clients/llm_client`: thin typed layer around `ollama` HTTP API; keeps the rest of the code decoupled from vendor specifics.
- Future additions: telemetry, schema models, prompt templates.

## Data flow overview

1. **Ingestion** pulls a PG-19 text, normalizes it, persists metadata to Postgres, chunks text, and stores embeddings in Qdrant/Chroma.
2. **KG Builder** subscribes to ingestion events, calls the LLM (via `llm_client`) for entity extraction, then stores nodes/edges in Neo4j.
3. **Agent Orchestrator** handles chat queries by:
   - Analyzer agent: understand intent + constraints.
   - Retriever agent: query vector DB for relevant chunks.
   - KG agent: fetch related entities/relations.
   - Answer generator: synthesize final response referencing retrieved context.
   - Trace persistence: each agent step is stored for UI playback.
4. **UI** displays chat, agent timeline, and KG subgraph returned by the orchestrator.

## Local development workflow

- Run infra dependencies (Postgres, Qdrant, Neo4j) via docker-compose (to be added in later phases).
- Start each FastAPI service via `uvicorn` with hot reload.
- Start the Next.js dev server under `services/ui`.
- Shared packages can be installed with editable mode (e.g., `pip install -e shared/clients/llm_client`).
