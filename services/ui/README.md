# UI Service

Next.js 14 (App Router + Tailwind) interface for PG19-Agentic-Explorer. The UI exposes:
- **Chat panel** to submit questions.
- **Agent timeline** showing Analyzer/RAG/KG/Answer steps.
- **KG snapshot widget** (list + vis-network graph).
- **Dataset status card** to verify/download PG-19 from Hugging Face into `data/pg19`.
- **Conversation history** with trace downloads and streaming updates while agents run.

## Dev setup

```bash
cd services/ui
cp .env.example .env.local  # set ORCHESTRATOR_URL if not localhost:8000
npm install
npm run dev
```

Open http://localhost:3000 and ensure the orchestrator (and upstream ingestion/KG/Ollama) are running.

### Docker Compose

The repo-level `docker compose` stack now ships the UI container. Run:

```bash
docker compose up -d ui-service
```

This will also start the orchestrator container (plus the ingestion/Qdrant stack if not already running) so the UI can proxy API calls internally via `http://orchestrator-service:8000`.

## Streaming + history API usage

- `/api/dataset` checks/downloads PG-19 (via git clone) into the configured `DATASET_DIR`.
- `/api/chat/stream` proxies `${ORCHESTRATOR_URL}/chat/query/stream` for SSE events.
- `/api/history` lists persisted conversations; `/api/trace/[id]` downloads traces.

## Project structure

```
app/
  api/chat/route.ts        # blocking chat proxy
  api/chat/stream/route.ts # SSE proxy
  api/history/route.ts     # history
  api/dataset/route.ts     # dataset check/download
  api/trace/[id]/route.ts  # trace download
  page.tsx                 # main layout
components/
  ChatPanel.tsx
  AgentTimeline.tsx
  KGWidget.tsx (with KGGraph)
  DatasetStatus.tsx
```

## Production build

```bash
npm run build
npm start
```

Serve behind Next.js standalone output or integrate with your platform of choice. Ensure `ORCHESTRATOR_URL` is reachable from the UI host.
