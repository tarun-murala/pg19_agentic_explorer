from __future__ import annotations

from datetime import datetime
from typing import List

import httpx

from shared.clients.llm_client import LLMClient, LLMRequest

from .config import Settings, get_settings
from .schemas import (
    AnalyzerInput,
    AnalyzerOutput,
    AnswerAgentInput,
    AnswerAgentOutput,
    ChunkContext,
    KGContextInput,
    KGContextOutput,
    KGEntity,
    KGRelation,
    RAGRetrievalInput,
    RAGRetrievalOutput,
    TraceStep,
)


class AnalyzerAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.llm = LLMClient(base_url=self.settings.ollama_base_url)

    def run(self, payload: AnalyzerInput) -> AnalyzerOutput:
        prompt = (
            "You analyze literary questions. Identify the primary intent (summarize, analyze, compare, fact-check, other), "
            "list key named entities mentioned, and the desired detail level (short, medium, in-depth).\n"
            f"Question: {payload.question}\n"
            "Return JSON as {\"intent\":str, \"entities\":[], \"detail_level\":str}."
        )
        response = self.llm.generate(
            LLMRequest(prompt=prompt, model=self.settings.llm_model, temperature=0.1, max_tokens=256)
        )
        data = self._safe_json(response.output)
        return AnalyzerOutput(
            intent=data.get("intent", "other"),
            entities=data.get("entities", []),
            detail_level=data.get("detail_level", "medium"),
        )

    def _safe_json(self, text: str) -> dict:
        import json

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    return {}
        return {}


class RAGRetrievalAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = httpx.Client(base_url=self.settings.ingestion_service_url)

    def run(self, payload: RAGRetrievalInput) -> RAGRetrievalOutput:
        resp = self.client.post(
            "/rag/query",
            json={"query": payload.question, "top_k": payload.top_k},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        chunks: List[ChunkContext] = []
        for result in data.get("results", []):
            chunk = result["chunk"]
            chunks.append(
                ChunkContext(
                    chunk_id=chunk["id"],
                    book_id=chunk["book_id"],
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    score=result.get("score", 0.0),
                )
            )
        return RAGRetrievalOutput(chunks=chunks)


class KGContextAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = httpx.Client(base_url=self.settings.kg_service_url)

    def run(self, payload: KGContextInput) -> KGContextOutput:
        params = {}
        if payload.chunk_ids:
            params["chunk_id"] = payload.chunk_ids[0]
        elif payload.book_ids:
            params["book_id"] = payload.book_ids[0]
        else:
            return KGContextOutput(entities=[], relations=[])
        resp = self.client.get("/kg/entities", params=params, timeout=60)
        if resp.status_code == 400:
            return KGContextOutput(entities=[], relations=[])
        resp.raise_for_status()
        data = resp.json()
        entities = [KGEntity(**entity) for entity in data.get("entities", [])]
        relations = [KGRelation(**relation) for relation in data.get("relations", [])]
        return KGContextOutput(entities=entities, relations=relations)


class AnswerAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.llm = LLMClient(base_url=self.settings.ollama_base_url)

    def run(self, payload: AnswerAgentInput) -> AnswerAgentOutput:
        citations = [chunk.chunk_id for chunk in payload.rag_chunks]
        context_blocks = []
        for idx, chunk in enumerate(payload.rag_chunks, 1):
            context_blocks.append(f"Chunk {idx} (id={chunk.chunk_id}, score={chunk.score:.3f}):\n{chunk.content}\n")
        kg_entities = ", ".join(f"{entity.name} ({entity.type})" for entity in payload.kg_context.entities[:10])
        kg_relations = "; ".join(
            f"{rel.source}-{rel.type}->{rel.target}" for rel in payload.kg_context.relations[:10]
        )
        prompt = (
            "You are a PG-19 expert agent. Answer the user question using ONLY the provided chunk context and KG hints.\n"
            "If unsure, say you don't know. Cite chunk IDs in square brackets.\n"
            f"Question: {payload.question}\n"
            f"Intent: {payload.analyzer.intent}, Detail: {payload.analyzer.detail_level}\n"
            f"Chunk Context:\n{''.join(context_blocks)}\n"
            f"KG Entities: {kg_entities}\n"
            f"KG Relations: {kg_relations}\n"
            "Answer:"
        )
        response = self.llm.generate(
            LLMRequest(prompt=prompt, model=self.settings.llm_model, temperature=0.2, max_tokens=512)
        )
        answer = response.output.strip()
        return AnswerAgentOutput(answer=answer, citations=citations)


def as_trace_step(agent: str, input_payload: dict, output_payload: dict, started_at: datetime, finished_at: datetime) -> TraceStep:
    return TraceStep(agent=agent, input=input_payload, output=output_payload, started_at=started_at, finished_at=finished_at)
