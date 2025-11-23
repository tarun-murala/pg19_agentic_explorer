from __future__ import annotations

from typing import List, Sequence

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from .config import Settings, get_settings
from .models import Chunk


class VectorStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = QdrantClient(host=self.settings.vector_host, port=self.settings.vector_port)
        self._http = httpx.Client(
            base_url=f"http://{self.settings.vector_host}:{self.settings.vector_port}", timeout=30
        )

    def ensure_collection(self, vector_size: int) -> None:
        name = self.settings.vector_collection
        if self._client.collection_exists(name):
            return
        self._client.create_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )

    def upsert_chunks(self, chunks: Sequence[Chunk], embeddings: Sequence[List[float]], batch_size: int = 128) -> None:
        if not chunks:
            return
        vector_size = len(embeddings[0])
        self.ensure_collection(vector_size)
        batch: list[qmodels.PointStruct] = []
        for chunk, vector in zip(chunks, embeddings):
            payload = {
                "chunk_id": chunk.id,
                "book_id": chunk.book_id,
                "chunk_index": chunk.chunk_index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "content": chunk.content,
            }
            batch.append(
                qmodels.PointStruct(
                    id=chunk.id,
                    vector=vector,
                    payload=payload,
                )
            )
            if len(batch) >= batch_size:
                self._client.upsert(
                    collection_name=self.settings.vector_collection,
                    points=batch,
                    wait=False,
                )
                batch = []
        if batch:
            self._client.upsert(
                collection_name=self.settings.vector_collection,
                points=batch,
                wait=False,
            )

    def search(self, vector: List[float], top_k: int) -> List[qmodels.ScoredPoint]:
        self.ensure_collection(len(vector))
        payload = {
            "vector": vector,
            "limit": top_k,
            "with_payload": True,
            "with_vectors": False,
        }
        resp = self._http.post(f"/collections/{self.settings.vector_collection}/points/search", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return [qmodels.ScoredPoint(**item) for item in data.get("result", [])]
