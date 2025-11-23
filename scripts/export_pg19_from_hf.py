#!/usr/bin/env python3
"""Export PG-19 HF dataset shards into plain-text files for the ingestion service."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

try:
    from datasets import load_from_disk
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit("Install `datasets` (pip install datasets) before running this script") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "hf_path",
        help="Path passed to datasets.load_from_disk (e.g., data/pg19_train_hf)",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="data/pg19",
        help="Directory to write .txt files (default: data/pg19)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max number of records to export for smoke testing",
    )
    return parser.parse_args()


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9-_]+", "_", name).strip("_")
    return cleaned or "pg19_book"


def format_header(row: dict) -> str:
    header_lines = [
        f"Title: {row.get('short_book_title') or row.get('title') or 'Unknown Title'}",
        f"Book ID: {row.get('book_id') or row.get('id') or 'unknown-id'}",
        f"Authors: {', '.join(row.get('authors', [])) if isinstance(row.get('authors'), list) else row.get('authors', 'Unknown')}",
        "*** START OF PG19 BOOK ***",
    ]
    return "\n".join(header_lines) + "\n\n"


def export_records(dataset, output_dir: Path, limit: int | None = None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    total = len(dataset)
    indices: Iterable[int] = range(total if limit is None else min(limit, total))

    for idx in indices:
        row = dataset[idx]
        book_id = row.get("book_id") or f"pg19_{idx:05d}"
        filename = f"{sanitize_filename(book_id)}.txt"
        content = row.get("text") or ""
        if not content:
            continue
        header = format_header(row)
        path = output_dir / filename
        path.write_text(header + content, encoding="utf-8")
        print(f"Wrote {path}")


def main() -> None:
    args = parse_args()
    dataset = load_from_disk(args.hf_path)
    export_records(dataset, Path(args.output_dir), args.limit)


if __name__ == "__main__":
    main()
