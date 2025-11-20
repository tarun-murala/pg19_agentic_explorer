from fastapi import FastAPI

app = FastAPI(title="PG19 KG Builder Service")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/kg/build")
async def build_kg() -> dict:
    # TODO: implement KG construction pipeline
    return {"status": "accepted", "job_id": "kg-demo"}


@app.get("/kg/entities")
async def list_entities() -> dict:
    # TODO: fetch from Neo4j
    return {"entities": []}
