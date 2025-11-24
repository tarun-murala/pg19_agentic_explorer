from __future__ import annotations

import json
import logging
import textwrap
from typing import Tuple

from shared.clients.llm_client import LLMClient, LLMRequest

from .config import Settings, get_settings
from .schemas import Entity, Relation

_PROMPT_TEMPLATE = """
You are an expert literary analyst that produces structured knowledge graphs.
Given a book chunk (with title and chunk index), identify up to {max_entities} key named entities and any explicit
relationships between them. Use concise names and categorize the entity type (person, location, object, event, other).

Return JSON with the following shape:
{{
  "entities": [{{"name": "...", "type": "person", "description": "...", "aliases": ["..."]}}],
  "relations": [{{"source": "Entity Name", "target": "Entity Name", "type": "relationship", "description": "..."}}]
}}

Chunk metadata:
- Book title: {book_title}
- Chunk index: {chunk_index}

Chunk content:
{chunk}

Respond with ONLY the JSON.
"""


class KGExtractor:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = LLMClient(base_url=self.settings.ollama_base_url)
        self.logger = logging.getLogger("kg_builder.extractor")

    def extract(
        self, *, chunk_content: str, book_title: str | None, chunk_index: int | None, trace_id: str | None = None
    ) -> Tuple[list[Entity], list[Relation]]:
        prompt = _PROMPT_TEMPLATE.format(
            max_entities=self.settings.max_entities,
            book_title=book_title or "Unknown",
            chunk_index=chunk_index if chunk_index is not None else "Unknown",
            chunk=textwrap.dedent(chunk_content).strip(),
        )
        self.logger.info(
            "LLM extract call",
            extra={"trace_id": trace_id, "book_title": book_title, "chunk_index": chunk_index},
        )
        response = self.client.generate(
            LLMRequest(
                prompt=prompt,
                model=self.settings.llm_model,
                temperature=0.2,
                max_tokens=512,
            )
        )
        data = self._parse_json(response.output)
        entities = [Entity(**item) for item in data.get("entities", [])]
        relations = [Relation(**item) for item in data.get("relations", [])]
        self.logger.info(
            "LLM extract parsed",
            extra={
                "trace_id": trace_id,
                "entities": len(entities),
                "relations": len(relations),
            },
        )
        return entities, relations

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if not text:
            return {"entities": [], "relations": []}
        if text.startswith("{") and text.endswith("}"):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        # Try to recover JSON substring
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                return {"entities": [], "relations": []}
        return {"entities": [], "relations": []}
