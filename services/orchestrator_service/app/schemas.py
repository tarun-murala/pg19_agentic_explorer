from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AnalyzerInput(BaseModel):
    question: str


class AnalyzerOutput(BaseModel):
    intent: str
    entities: List[str]
    detail_level: str


class RAGRetrievalInput(BaseModel):
    question: str
    top_k: int


class ChunkContext(BaseModel):
    chunk_id: int
    book_id: int
    chunk_index: int
    content: str
    score: float


class RAGRetrievalOutput(BaseModel):
    chunks: List[ChunkContext]


class KGContextInput(BaseModel):
    book_ids: List[int]
    chunk_ids: List[int]


class KGEntity(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    mentions: Optional[int] = None


class KGRelation(BaseModel):
    source: str
    target: str
    type: str
    description: Optional[str] = None
    chunk_ids: List[int] = Field(default_factory=list)


class KGContextOutput(BaseModel):
    entities: List[KGEntity]
    relations: List[KGRelation]


class AnswerAgentInput(BaseModel):
    question: str
    analyzer: AnalyzerOutput
    rag_chunks: List[ChunkContext]
    kg_context: KGContextOutput


class AnswerAgentOutput(BaseModel):
    answer: str
    citations: List[int]


class TraceStep(BaseModel):
    agent: str
    input: dict
    output: dict
    started_at: datetime
    finished_at: datetime


class ChatQueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = None


class ChatQueryResponse(BaseModel):
    conversation_id: str
    answer: str
    trace: List[TraceStep]
    citations: List[int]


class HistoryEntry(BaseModel):
    id: str
    question: str
    answer: str
    citations: List[int]
    trace: List[TraceStep]
    created_at: datetime


class HistorySummary(BaseModel):
    id: str
    question: str
    answer: str
    citations: List[int]
    created_at: datetime
