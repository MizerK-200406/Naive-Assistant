"""Kiểm tra độc lập index chunk và sinh mẫu kiểm tay."""

from __future__ import annotations

import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

from naive_assistant.ingest.chunker import MAX_CHARS, TITLE_RE
from naive_assistant.ingest.clean import strip_page_number
from naive_assistant.ingest.extract import to_printed
from naive_assistant.ingest.registry import REGISTRY, DocSpec


PAGES_PATH = Path("data/index/pages.jsonl")
CHUNKS_PATH = Path("data/index/chunks.jsonl")
REVIEW_PATH = Path("data/index/review_sample.md")


def load_pages() -> dict[int, str]:
    with PAGES_PATH.open(encoding="utf-8") as source:
        return {
            row["pdf_page"]: row["text"]
            for row in map(json.loads, source)
        }


def load_chunks() -> list[dict[str, object]]:
    with CHUNKS_PATH.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source]


def next_spec(spec: DocSpec) -> DocSpec | None:
    index = REGISTRY.index(spec)
    return REGISTRY[index + 1] if index + 1 < len(REGISTRY) else None


def source_lines(spec: DocSpec, pages: dict[int, str]) -> list[str]:
    """Cắt biên độc lập với triển khai trong chunker.py."""
    result: list[str] = []
    following = next_spec(spec)
    for pdf_page in range(spec.start_pdf_page, spec.end_pdf_page + 1):
        text = strip_page_number(pages[pdf_page], to_printed(pdf_page))
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        if pdf_page == spec.start_pdf_page and spec.start_marker is not None:
            marker = re.compile(spec.start_marker)
            positions = [i for i, line in enumerate(lines) if marker.search(line)]
            if len(positions) != 1:
                raise ValueError(f"marker đầu không duy nhất: {spec.doc_id}")
            lines = lines[positions[0] :]

        if (
            following is not None
            and following.start_marker is not None
            and pdf_page == spec.end_pdf_page == following.start_pdf_page
        ):
            marker = re.compile(following.start_marker)
            positions = [i for i, line in enumerate(lines) if marker.search(line)]
            if len(positions) != 1:
                raise ValueError(f"marker cuối không duy nhất: {spec.doc_id}")
            lines = lines[: positions[0]]
        result.extend(lines)
    return result


def write_review(chunks: list[dict[str, object]]) -> None:
    indexes = [round(i * (len(chunks) - 1) / 19) for i in range(20)]
    sections: list[str] = ["# Mẫu kiểm tay chunk", ""]
    for index in indexes:
        chunk = chunks[index]
        sections.extend(
            [
                f"## {chunk['chunk_id']}",
                "",
                f"- doc: {chunk['doc_id']}",
                f"- trang in: {chunk['printed_page_start']}-{chunk['printed_page_end']}",
                f"- khoản: {chunk['khoan']}",
                "",
                str(chunk["text"]),
                "",
            ]
        )
    REVIEW_PATH.write_text("\n".join(sections), encoding="utf-8")


def main() -> int:
    pages = load_pages()
    chunks = load_chunks()
    by_doc: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for chunk in chunks:
        by_doc[str(chunk["doc_id"])].append(chunk)

    remaining_uncovered = 20
    for spec in (item for item in REGISTRY if item.has_articles):
        doc_chunks = by_doc[spec.doc_id]
        dieus = {int(chunk["dieu"]) for chunk in doc_chunks}
        warning_count = sum(bool(chunk["warnings"]) for chunk in doc_chunks)
        source_count = sum(bool(TITLE_RE.fullmatch(line)) for line in source_lines(spec, pages))
        match_status = "KHỚP" if source_count == len(dieus) else f"LỆCH {spec.doc_id} {source_count - len(dieus):+d}"

        covered: set[int] = set()
        for chunk in doc_chunks:
            covered.update(
                range(int(chunk["pdf_page_start"]), int(chunk["pdf_page_end"]) + 1)
            )
        uncovered = [
            page
            for page in range(spec.start_pdf_page, spec.end_pdf_page + 1)
            if page not in covered
        ]
        shown = uncovered[:remaining_uncovered]
        remaining_uncovered -= len(shown)
        uncovered_text = ",".join(map(str, shown)) if shown else "-"
        if len(shown) < len(uncovered):
            uncovered_text += f" (+{len(uncovered) - len(shown)})"

        minimum = min(dieus) if dieus else "-"
        maximum = max(dieus) if dieus else "-"
        print(
            f"DOC {spec.doc_id} chunks={len(doc_chunks)} dieus={len(dieus)} "
            f"range={minimum}-{maximum} warnings={warning_count} | {match_status} "
            f"| uncovered={uncovered_text}"
        )

    lengths = sorted(len(str(chunk["text"])) for chunk in chunks)
    over_limit = sum(length > MAX_CHARS * 1.1 for length in lengths)
    p90 = lengths[math.ceil(0.9 * len(lengths)) - 1]
    print(f"OVER_110_PERCENT {over_limit}")
    print(
        f"LENGTH min={lengths[0]} median={statistics.median(lengths):g} "
        f"p90={p90} max={lengths[-1]} under80={sum(length < 80 for length in lengths)}"
    )
    for chunk in [item for item in chunks if len(str(item["text"])) < 80][:15]:
        print(f"SHORT {chunk['chunk_id']}")

    identifiers = [str(chunk["chunk_id"]) for chunk in chunks]
    print(f"CHUNK_ID_UNIQUE {len(identifiers) == len(set(identifiers))}")

    non_sequential_lines = 0
    for chunk in chunks:
        for warning in chunk["warnings"]:
            if str(warning).startswith("NON_SEQUENTIAL") and non_sequential_lines < 25:
                print(f"WARNING {chunk['doc_id']} {chunk['chunk_id']} {warning}")
                non_sequential_lines += 1

    boundary_lines = 0
    for chunk in chunks:
        if boundary_lines >= 12:
            break
        if int(chunk["pdf_page_start"]) <= 191 <= int(chunk["pdf_page_end"]) or int(
            chunk["pdf_page_start"]
        ) <= 193 <= int(chunk["pdf_page_end"]):
            preview = " ".join(str(chunk["text"]).split())[:60]
            print(
                f"BOUNDARY {chunk['chunk_id']} {chunk['doc_id']} "
                f"{chunk['printed_page_start']}-{chunk['printed_page_end']} | {preview}"
            )
            boundary_lines += 1

    write_review(chunks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
