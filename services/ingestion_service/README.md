# Ingestion Service

FastAPI microservice that ingests PG-19 texts from disk, normalizes metadata, chunks books, and stores persisted `Book`/`Chunk` entities for downstream services.

## Dev setup

```bash
# boot Postgres + Qdrant for metadata/vector storage (from repo root)
docker compose up -d ingestion-db qdrant

cd services/ingestion_service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../../shared/clients/llm_client
cp .env.example .env  # edit values if needed
export PYTHONPATH=$(git rev-parse --show-toplevel)
uvicorn app.main:app --reload --port 8001
```

Ensure `ollama` is running locally and the configured embedding model (default `nomic-embed-text`) is available (`ollama pull nomic-embed-text`).

### Running via Docker Compose

To run the ingestion service inside Docker (talking to the shared Postgres container):

```bash
# ensure PG-19 texts are available on the host under ./data/pg19
docker compose up -d ingestion-service
```

The compose file mounts `./data/pg19` into the container at `/data/pg19` and exposes the FastAPI server at `http://localhost:8001`.

Environment variables (prefix `INGESTION_`) control runtime settings (see `.env.example`):

| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy URL for metadata storage | `postgresql+psycopg://pg19:pg19pass@localhost:5433/pg19_ingestion` |
| `PG19_ROOT` | Directory containing PG-19 `.txt` files | `./data/pg19` |
| `CHUNK_SIZE` | Character length per chunk | `1200` |
| `CHUNK_OVERLAP` | Character overlap between chunks | `200` |
| `EMBEDDING_MODEL` | Ollama embedding model name | `nomic-embed-text` |
| `VECTOR_HOST` | Qdrant host | `localhost` |
| `VECTOR_PORT` | Qdrant REST port | `6333` |
| `VECTOR_COLLECTION` | Qdrant collection name | `pg19_chunks` |
| `RAG_TOP_K` | Default top-k for `/rag/query` | `5` |
| `OLLAMA_BASE_URL` | Base URL for Ollama runtime | `http://localhost:11434` (Docker: `http://host.docker.internal:11434`) |

> When running via Docker Compose the service overrides DB + vector env vars to talk to the `ingestion-db` (Postgres) and `qdrant` containers and maps `INGESTION_PG19_ROOT` to `/data/pg19` (mounted from `./data/pg19`).

## REST surface

- `POST /ingest/book` – body `{ "file_path": "relative/or/absolute.txt", "overrides": { ... } }`. Loads the PG-19 file, parses metadata, chunks the body, stores `Book` and `Chunk` rows, and returns the normalized entities.
- `GET /books` – list most recent books.
- `GET /books/{book_id}` – fetch normalized metadata for a book.
- `GET /books/{book_id}/chunks` – paginated chunk metadata + content for debugging.
- `POST /vector/index` – body `{ "book_id": 1, "reindex": false }`. Embeds every chunk with the configured Ollama model and upserts them into Qdrant.
- `POST /rag/query` – body `{ "query": "...", "top_k": 5 }`. Embeds the query and returns the highest scoring chunks from Qdrant.

## Book & Chunk schema

```jsonc
Book: {
  "id": 1,
  "pg_id": "12345",
  "title": "Example Title",
  "author": "Author Name",
  "language": "English",
  "published_year": 1908,
  "source_path": "/abs/path/book.txt",
  "checksum": "sha256...",
  "word_count": 104523,
  "chunk_count": 212,
  "created_at": "2024-05-21T18:01:03.511Z"
}
Chunk: {
  "id": 10,
  "book_id": 1,
  "chunk_index": 0,
  "start_char": 0,
  "end_char": 1200,
  "content": "First chunk..."
}
```

These entities will later back both the retriever vectorization pipeline and KG extraction workflows.

## Usage workflow

1. Place PG-19 `.txt` files inside `data/pg19/` (configurable via `INGESTION_PG19_ROOT`).
2. Hit `POST /ingest/book` with the file path, e.g.

```bash
curl -X POST http://localhost:8001/ingest/book \
  -H 'content-type: application/json' \
  -d '{"file_path": "pg19/pg01234.txt"}'
```

3. Inspect stored metadata via `GET /books` or `GET /books/{id}/chunks`.

## Vector indexing & RAG queries

1. Ensure `ollama` is running locally with an embedding-capable model (e.g. `nomic-embed-text`):

```bash
ollama pull nomic-embed-text
```

2. Index a book's chunks into Qdrant:

```bash
curl -X POST http://localhost:8001/vector/index \
  -H 'content-type: application/json' \
  -d '{"book_id": 1, "reindex": true}'
```

3. Run a quick RAG-style search:

```bash
curl -X POST http://localhost:8001/rag/query \
  -H 'content-type: application/json' \
  -d '{"query": "How does the protagonist escape?", "top_k": 3}'
```

The `/rag/query` response returns chunk metadata/content plus cosine similarity scores; downstream services can feed this into answer-generation agents.
