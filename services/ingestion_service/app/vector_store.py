from __future__ import annotations

from typing import Iterable, List, Sequence

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from .config import Settings, get_settings
from .models import Chunk


class VectorStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = QdrantClient(host=self.settings.vector_host, port=self.settings.vector_port)

    def ensure_collection(self, vector_size: int) -> None:
        name = self.settings.vector_collection
        if self._client.collection_exists(name):
            return
        self._client.create_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )

    def upsert_chunks(self, chunks: Sequence[Chunk], embeddings: Sequence[List[float]]) -> None:
        if not chunks:
            return
        vector_size = len(embeddings[0])
        self.ensure_collection(vector_size)
        points = []
        for chunk, vector in zip(chunks, embeddings):
            payload = {
                "chunk_id": chunk.id,
                "book_id": chunk.book_id,
                "chunk_index": chunk.chunk_index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "content": chunk.content,
            }
            points.append(
                qmodels.PointStruct(
                    id=chunk.id,
                    vector=vector,
                    payload=payload,
                )
            )
        self._client.upsert(collection_name=self.settings.vector_collection, points=points)

    def search(self, vector: List[float], top_k: int) -> List[qmodels.ScoredPoint]:
        self.ensure_collection(len(vector))
        return self._client.search(
            collection_name=self.settings.vector_collection,
            query_vector=vector,
            limit=top_k,
            with_payload=True,
        )

    def delete_book(self, book_id: int) -> None:
        if not self._client.collection_exists(self.settings.vector_collection):
            return
        self._client.delete(
            collection_name=self.settings.vector_collection,
            filter=qmodels.Filter(
                must=[qmodels.FieldCondition(key="book_id", match=qmodels.MatchValue(value=book_id))]
            ),
        )
