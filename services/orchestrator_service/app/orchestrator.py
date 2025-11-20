from __future__ import annotations

from datetime import datetime

from .agents import (
    AnalyzerAgent,
    AnswerAgent,
    KGContextAgent,
    RAGRetrievalAgent,
    as_trace_step,
)
from .config import Settings, get_settings
from .schemas import (
    AnalyzerInput,
    AnswerAgentInput,
    ChatQueryRequest,
    ChatQueryResponse,
    KGContextInput,
    RAGRetrievalInput,
)


class AgentOrchestrator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.analyzer = AnalyzerAgent(settings=self.settings)
        self.rag = RAGRetrievalAgent(settings=self.settings)
        self.kg = KGContextAgent(settings=self.settings)
        self.answer = AnswerAgent(settings=self.settings)

    def handle_query(self, request: ChatQueryRequest) -> ChatQueryResponse:
        trace = []

        # Analyzer
        start = datetime.utcnow()
        analyzer_output = self.analyzer.run(AnalyzerInput(question=request.question))
        trace.append(
            as_trace_step(
                "AnalyzerAgent",
                {"question": request.question},
                analyzer_output.dict(),
                start,
                datetime.utcnow(),
            )
        )

        # RAG retrieval
        start = datetime.utcnow()
        top_k = request.top_k or self.settings.rag_top_k
        rag_output = self.rag.run(RAGRetrievalInput(question=request.question, top_k=top_k))
        trace.append(
            as_trace_step(
                "RAGRetrievalAgent",
                {"question": request.question, "top_k": top_k},
                rag_output.dict(),
                start,
                datetime.utcnow(),
            )
        )

        # KG context
        start = datetime.utcnow()
        book_ids = list({chunk.book_id for chunk in rag_output.chunks})
        chunk_ids = [chunk.chunk_id for chunk in rag_output.chunks]
        kg_output = self.kg.run(KGContextInput(book_ids=book_ids, chunk_ids=chunk_ids))
        trace.append(
            as_trace_step(
                "KGContextAgent",
                {"book_ids": book_ids, "chunk_ids": chunk_ids},
                kg_output.dict(),
                start,
                datetime.utcnow(),
            )
        )

        # Answer agent
        start = datetime.utcnow()
        answer_output = self.answer.run(
            AnswerAgentInput(
                question=request.question,
                analyzer=analyzer_output,
                rag_chunks=rag_output.chunks,
                kg_context=kg_output,
            )
        )
        trace.append(
            as_trace_step(
                "AnswerAgent",
                {
                    "question": request.question,
                    "rag_chunks": [chunk.dict() for chunk in rag_output.chunks],
                },
                answer_output.dict(),
                start,
                datetime.utcnow(),
            )
        )

        return ChatQueryResponse(answer=answer_output.answer, trace=trace, citations=answer_output.citations)
