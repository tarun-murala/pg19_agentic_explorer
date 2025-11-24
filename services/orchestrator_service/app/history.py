from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import List, Optional
from uuid import uuid4

from .schemas import HistoryEntry, HistorySummary, TraceStep


class HistoryStore:
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._entries: List[HistoryEntry] = self._load()

    def _load(self) -> List[HistoryEntry]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text())
            return [HistoryEntry(**entry) for entry in raw]
        except json.JSONDecodeError:
            return []

    def _persist(self) -> None:
        data = [entry.model_dump() for entry in self._entries]
        self._path.write_text(json.dumps(data, indent=2, default=str))

    def add_entry(
        self,
        *,
        question: str,
        answer: str,
        citations: List[int],
        trace: List[TraceStep],
    ) -> HistoryEntry:
        with self._lock:
            entry = HistoryEntry(
                id=str(uuid4()),
                question=question,
                answer=answer,
                citations=citations,
                trace=trace,
                created_at=datetime.utcnow(),
            )
            self._entries.append(entry)
            self._persist()
            return entry

    def get_entry(self, entry_id: str) -> Optional[HistoryEntry]:
        with self._lock:
            for entry in self._entries:
                if entry.id == entry_id:
                    return entry
        return None

    def list_entries(self, limit: int = 20) -> List[HistorySummary]:
        with self._lock:
            ordered = sorted(self._entries, key=lambda e: e.created_at, reverse=True)[:limit]
            return [
                HistorySummary(
                    id=entry.id,
                    question=entry.question,
                    answer=entry.answer,
                    citations=entry.citations,
                    created_at=entry.created_at,
                )
                for entry in ordered
            ]
