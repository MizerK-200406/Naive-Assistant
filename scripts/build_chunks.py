"""Sinh index chunk Điều/Khoản từ pages.jsonl."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from naive_assistant.ingest.chunker import chunk_all


PAGES_PATH = Path("data/index/pages.jsonl")
CHUNKS_PATH = Path("data/index/chunks.jsonl")


def load_pages() -> dict[int, str]:
    with PAGES_PATH.open(encoding="utf-8") as source:
        return {
            row["pdf_page"]: row["text"]
            for row in map(json.loads, source)
        }


def main() -> int:
    chunks = chunk_all(load_pages())
    with CHUNKS_PATH.open("w", encoding="utf-8") as output:
        for chunk in chunks:
            output.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")

    counts = Counter(chunk.doc_id for chunk in chunks)
    print(f"TOTAL {len(chunks)}")
    for doc_id, count in counts.items():
        print(f"{doc_id} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
