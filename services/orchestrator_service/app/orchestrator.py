from __future__ import annotations

import json
from datetime import datetime
import logging
from uuid import uuid4

from .agents import AnalyzerAgent, AnswerAgent, KGContextAgent, RAGRetrievalAgent, as_trace_step
from .config import Settings, get_settings
from .history import HistoryStore
from .schemas import (
    AnalyzerInput,
    AnswerAgentInput,
    ChatQueryRequest,
    ChatQueryResponse,
    KGContextInput,
    RAGRetrievalInput,
    TraceStep,
)


class AgentOrchestrator:
    def __init__(self, settings: Settings | None = None, history_store: HistoryStore | None = None) -> None:
        self.settings = settings or get_settings()
        self.analyzer = AnalyzerAgent(settings=self.settings)
        self.rag = RAGRetrievalAgent(settings=self.settings)
        self.kg = KGContextAgent(settings=self.settings)
        self.answer = AnswerAgent(settings=self.settings)
        self.history_store = history_store
        self.logger = logging.getLogger("orchestrator")

    def handle_query(self, request: ChatQueryRequest, trace_id: str | None = None) -> ChatQueryResponse:
        trace_id = trace_id or str(uuid4())
        trace: list[TraceStep] = []

        analyzer_output, analyzer_step = self._run_analyzer(request, trace_id)
        trace.append(analyzer_step)

        rag_output, rag_step = self._run_rag(request, analyzer_output, trace_id)
        trace.append(rag_step)

        kg_output, kg_step = self._run_kg(rag_output, trace_id)
        trace.append(kg_step)

        answer_output, answer_step = self._run_answer(request, analyzer_output, rag_output, kg_output, trace_id)
        trace.append(answer_step)

        conversation_id = ""
        if self.history_store:
            entry = self.history_store.add_entry(
                question=request.question,
                answer=answer_output.answer,
                citations=answer_output.citations,
                trace=trace,
            )
            conversation_id = entry.id

        return ChatQueryResponse(
            conversation_id=conversation_id,
            answer=answer_output.answer,
            trace=trace,
            citations=answer_output.citations,
        )

    def stream_query(self, request: ChatQueryRequest, trace_id: str | None = None):
        trace_id = trace_id or str(uuid4())

        def format_event(payload: dict) -> str:
            return f"data: {json.dumps(payload, default=str)}\n\n"

        trace: list[TraceStep] = []
        try:
            analyzer_output, analyzer_step = self._run_analyzer(request, trace_id)
            trace.append(analyzer_step)
            yield format_event({"type": "step", "payload": analyzer_step.dict()})

            rag_output, rag_step = self._run_rag(request, analyzer_output, trace_id)
            trace.append(rag_step)
            yield format_event({"type": "step", "payload": rag_step.dict()})

            kg_output, kg_step = self._run_kg(rag_output, trace_id)
            trace.append(kg_step)
            yield format_event({"type": "step", "payload": kg_step.dict()})

            answer_output, answer_step = self._run_answer(request, analyzer_output, rag_output, kg_output, trace_id)
            trace.append(answer_step)
            yield format_event({"type": "step", "payload": answer_step.dict()})

            entry = None
            if self.history_store:
                entry = self.history_store.add_entry(
                    question=request.question,
                    answer=answer_output.answer,
                    citations=answer_output.citations,
                    trace=trace,
                )

            payload = ChatQueryResponse(
                conversation_id=entry.id if entry else "",
                answer=answer_output.answer,
                trace=trace,
                citations=answer_output.citations,
            )
            yield format_event({"type": "final", "payload": payload.dict()})
            self.logger.info("chat_query_stream complete", extra={"trace_id": trace_id})
        except Exception as exc:  # pragma: no cover - streaming error propagation
            self.logger.exception("chat_query_stream error", extra={"trace_id": trace_id})
            yield format_event({"type": "error", "message": str(exc)})

    def _run_analyzer(self, request: ChatQueryRequest, trace_id: str):
        start = datetime.utcnow()
        analyzer_output = self.analyzer.run(AnalyzerInput(question=request.question), trace_id=trace_id)
        step = as_trace_step(
            "AnalyzerAgent",
            {"question": request.question},
            analyzer_output.dict(),
            start,
            datetime.utcnow(),
        )
        self.logger.info(
            "AnalyzerAgent complete",
            extra={"trace_id": trace_id, "duration_ms": (step.finished_at - step.started_at).total_seconds() * 1000},
        )
        return analyzer_output, step

    def _run_rag(self, request: ChatQueryRequest, _analyzer_output, trace_id: str) -> tuple:
        start = datetime.utcnow()
        top_k = request.top_k or self.settings.rag_top_k
        rag_output = self.rag.run(RAGRetrievalInput(question=request.question, top_k=top_k), trace_id=trace_id)
        step = as_trace_step(
            "RAGRetrievalAgent",
            {"question": request.question, "top_k": top_k},
            rag_output.dict(),
            start,
            datetime.utcnow(),
        )
        self.logger.info(
            "RAGRetrievalAgent complete",
            extra={
                "trace_id": trace_id,
                "duration_ms": (step.finished_at - step.started_at).total_seconds() * 1000,
                "chunks": len(rag_output.chunks),
            },
        )
        return rag_output, step

    def _run_kg(self, rag_output, trace_id: str) -> tuple:
        start = datetime.utcnow()
        book_ids = list({chunk.book_id for chunk in rag_output.chunks})
        chunk_ids = [chunk.chunk_id for chunk in rag_output.chunks]
        kg_output = self.kg.run(KGContextInput(book_ids=book_ids, chunk_ids=chunk_ids), trace_id=trace_id)
        step = as_trace_step(
            "KGContextAgent",
            {"book_ids": book_ids, "chunk_ids": chunk_ids},
            kg_output.dict(),
            start,
            datetime.utcnow(),
        )
        self.logger.info(
            "KGContextAgent complete",
            extra={
                "trace_id": trace_id,
                "duration_ms": (step.finished_at - step.started_at).total_seconds() * 1000,
                "entities": len(kg_output.entities),
                "relations": len(kg_output.relations),
            },
        )
        return kg_output, step

    def _run_answer(self, request, analyzer_output, rag_output, kg_output, trace_id: str):
        start = datetime.utcnow()
        answer_output = self.answer.run(
            AnswerAgentInput(
                question=request.question,
                analyzer=analyzer_output,
                rag_chunks=rag_output.chunks,
                kg_context=kg_output,
            ),
            trace_id=trace_id,
        )
        step = as_trace_step(
            "AnswerAgent",
            {
                "question": request.question,
                "rag_chunks": [chunk.dict() for chunk in rag_output.chunks],
            },
            answer_output.dict(),
            start,
            datetime.utcnow(),
        )
        self.logger.info(
            "AnswerAgent complete",
            extra={
                "trace_id": trace_id,
                "duration_ms": (step.finished_at - step.started_at).total_seconds() * 1000,
                "citations": len(answer_output.citations),
            },
        )
        return answer_output, step
