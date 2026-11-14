"""Đối chiếu registry văn bản với index trang đã trích xuất."""

from __future__ import annotations

import json
import re
from pathlib import Path

from naive_assistant.ingest.registry import REGISTRY, validate_registry


PAGES_PATH = Path("data/index/pages.jsonl")


def compact_whitespace(text: str) -> str:
    return " ".join(text.split())


def load_pages() -> dict[int, dict[str, object]]:
    with PAGES_PATH.open(encoding="utf-8") as source:
        return {row["pdf_page"]: row for row in map(json.loads, source)}


def first_nonempty_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def main() -> int:
    pages = load_pages()
    issues = validate_registry()
    if issues:
        print("VALIDATE FAIL | " + " | ".join(issues))
    else:
        print("VALIDATE OK")

    for spec in REGISTRY:
        text = str(pages[spec.start_pdf_page]["text"])
        reason: str | None = None
        if spec.start_marker is not None:
            marker = re.compile(spec.start_marker)
            matches = sum(
                1 for line in text.splitlines() if marker.search(line.strip())
            )
            if matches != 1:
                reason = f"marker_matches={matches}"
        elif spec.probe is None:
            reason = "missing_probe"
        else:
            head = compact_whitespace(text)[:700]
            if spec.probe not in head:
                reason = "probe_not_found"

        status = "OK" if reason is None else f"FAIL {reason}"
        print(f"{status} {spec.doc_id} | decision={spec.decision}")

    for previous, current in zip(REGISTRY, REGISTRY[1:]):
        if current.start_pdf_page > previous.end_pdf_page + 1:
            print(
                f"GAP {previous.end_pdf_page + 1}-{current.start_pdf_page - 1} "
                f"| {previous.doc_id}->{current.doc_id}"
            )

    mismatches: list[tuple[int, str]] = []
    matched = 0
    for pdf_page in range(7, 214):
        text = str(pages[pdf_page]["text"])
        first_line = first_nonempty_line(text)
        printed_page = pdf_page - 6
        pattern = re.compile(rf"-?\s*{printed_page}\s*-?")
        if pattern.fullmatch(first_line):
            matched += 1
        else:
            mismatches.append((pdf_page, first_line))

    print(f"PAGE_NUMBERS {matched}/207")
    for pdf_page, first_line in mismatches[:20]:
        print(f"NO_PAGE_NUMBER {pdf_page} | {first_line[:40]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
