"""Tách văn bản có cấu trúc thành chunk theo Điều và Khoản."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, replace

from naive_assistant.ingest.clean import strip_page_number
from naive_assistant.ingest.extract import to_printed
from naive_assistant.ingest.registry import REGISTRY, DocSpec


TITLE_RE = re.compile(r"^Điều\s+(\d+)\s*[.:]\s*(\S.*)?$")
CHAPTER_RE = re.compile(r"^(?:Chương|CHƯƠNG)\s+([IVXLC]+)\s*[.:]?\s*(.*)$")
KHOAN_RE = re.compile(r"^(\d+)\.\s")
MAX_CHARS = 1800

HE_LABELS = {
    "dai_tra": "hệ đại trà",
    "chat_luong_cao": "hệ chất lượng cao",
}


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    short_name: str
    he: str | None
    chuong: str | None
    dieu: int
    dieu_title: str
    khoan: str | None
    printed_page_start: int
    printed_page_end: int
    pdf_page_start: int
    pdf_page_end: int
    text: str
    embed_text: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class _Line:
    pdf_page: int
    text: str


@dataclass(frozen=True)
class _Article:
    number: int
    title: str
    chuong: str | None
    lines: tuple[_Line, ...]
    warnings: tuple[str, ...]


def _next_spec(spec: DocSpec) -> DocSpec | None:
    for index, candidate in enumerate(REGISTRY):
        if candidate.doc_id == spec.doc_id:
            if index + 1 < len(REGISTRY):
                return REGISTRY[index + 1]
            return None
    return None


def _marker_index(lines: list[_Line], marker: str) -> int:
    pattern = re.compile(marker)
    matches = [index for index, line in enumerate(lines) if pattern.search(line.text)]
    if len(matches) != 1:
        raise ValueError(f"marker phải khớp đúng một dòng, nhận được {len(matches)}: {marker}")
    return matches[0]


def _document_lines(spec: DocSpec, pages: dict[int, str]) -> list[_Line]:
    result: list[_Line] = []
    following = _next_spec(spec)

    for pdf_page in range(spec.start_pdf_page, spec.end_pdf_page + 1):
        cleaned = strip_page_number(pages[pdf_page], to_printed(pdf_page))
        lines = [
            _Line(pdf_page, raw.strip())
            for raw in cleaned.splitlines()
            if raw.strip()
        ]

        if pdf_page == spec.start_pdf_page and spec.start_marker is not None:
            lines = lines[_marker_index(lines, spec.start_marker) :]

        if (
            following is not None
            and following.start_marker is not None
            and pdf_page == spec.end_pdf_page == following.start_pdf_page
        ):
            lines = lines[: _marker_index(lines, following.start_marker)]

        result.extend(lines)

    return result


def _parse_articles(lines: list[_Line]) -> list[_Article]:
    articles: list[_Article] = []
    current_lines: list[_Line] = []
    current_number: int | None = None
    current_title = ""
    current_chapter: str | None = None
    chapter: str | None = None
    previous_number: int | None = None
    seen_numbers: set[int] = set()

    def finish_article() -> None:
        nonlocal current_lines, current_number, current_title, previous_number
        if current_number is None:
            return

        warnings: list[str] = []
        if previous_number is not None and current_number != previous_number + 1:
            warnings.append(f"NON_SEQUENTIAL {previous_number}->{current_number}")
        if current_number in seen_numbers:
            warnings.append(f"DUPLICATE_DIEU {current_number}")
        if len(current_lines) == 1:
            warnings.append("EMPTY_BODY")

        articles.append(
            _Article(
                number=current_number,
                title=current_title,
                chuong=current_chapter,
                lines=tuple(current_lines),
                warnings=tuple(warnings),
            )
        )
        seen_numbers.add(current_number)
        previous_number = current_number
        current_lines = []
        current_number = None
        current_title = ""

    for line in lines:
        title_match = TITLE_RE.fullmatch(line.text)
        if title_match:
            finish_article()
            current_number = int(title_match.group(1))
            current_title = title_match.group(2) or ""
            current_chapter = chapter
            current_lines = [line]
            continue

        chapter_match = CHAPTER_RE.fullmatch(line.text)
        if chapter_match:
            finish_article()
            chapter = chapter_match.group(1)
            continue

        if current_number is not None:
            current_lines.append(line)

    finish_article()
    return articles


def _joined(lines: list[_Line] | tuple[_Line, ...]) -> str:
    return "\n".join(line.text for line in lines)


def _split_by_line(article: _Article) -> list[tuple[list[_Line], str | None]]:
    header = article.lines[0]
    body = list(article.lines[1:])
    if not body:
        return [([header], None)]

    groups: list[tuple[list[_Line], str | None]] = []
    current: list[_Line] = []
    for line in body:
        candidate = [header, *current, line]
        if current and len(_joined(candidate)) > MAX_CHARS:
            groups.append(([header, *current], None))
            current = [line]
        else:
            current.append(line)
    if current:
        groups.append(([header, *current], None))
    return groups


def _split_article(
    article: _Article,
) -> tuple[list[tuple[list[_Line], str | None]], bool]:
    if len(_joined(article.lines)) <= MAX_CHARS:
        return [(list(article.lines), None)], False

    body = list(article.lines[1:])
    starts = [index for index, line in enumerate(body) if KHOAN_RE.match(line.text)]
    if not starts:
        return _split_by_line(article), True

    segments: list[tuple[str, list[_Line]]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(body)
        segment = body[start:end]
        if position == 0 and start > 0:
            segment = body[:start] + segment
        number_match = KHOAN_RE.match(body[start].text)
        assert number_match is not None
        segments.append((number_match.group(1), segment))

    header = article.lines[0]
    if any(len(_joined([header, *segment])) > MAX_CHARS for _, segment in segments):
        return _split_by_line(article), True

    groups: list[tuple[list[_Line], str | None]] = []
    current_numbers: list[str] = []
    current_lines: list[_Line] = []
    for number, segment in segments:
        candidate = [header, *current_lines, *segment]
        if current_lines and len(_joined(candidate)) > MAX_CHARS:
            khoan = (
                current_numbers[0]
                if len(current_numbers) == 1
                else f"{current_numbers[0]}-{current_numbers[-1]}"
            )
            groups.append(([header, *current_lines], khoan))
            current_numbers = [number]
            current_lines = list(segment)
        else:
            current_numbers.append(number)
            current_lines.extend(segment)

    khoan = (
        current_numbers[0]
        if len(current_numbers) == 1
        else f"{current_numbers[0]}-{current_numbers[-1]}"
    )
    groups.append(([header, *current_lines], khoan))
    return groups, False


def _make_chunk(
    spec: DocSpec,
    article: _Article,
    lines: list[_Line],
    khoan: str | None,
    split_by_line: bool,
) -> Chunk:
    pdf_page_start = lines[0].pdf_page
    pdf_page_end = lines[-1].pdf_page
    printed_page_start = to_printed(pdf_page_start)
    printed_page_end = to_printed(pdf_page_end)
    assert printed_page_start is not None and printed_page_end is not None

    prefix = spec.short_name
    if spec.he is not None:
        prefix += f" | {HE_LABELS.get(spec.he, spec.he)}"
    body = _joined(lines[1:])
    embed_text = f"[{prefix}] Điều {article.number}. {article.title}\n{body}"
    warnings = article.warnings
    if split_by_line:
        warnings += ("SPLIT_BY_LINE",)

    base_id = f"{spec.doc_id}:d{article.number}"
    if khoan is not None:
        base_id += f":k{khoan}"

    return Chunk(
        chunk_id=base_id,
        doc_id=spec.doc_id,
        short_name=spec.short_name,
        he=spec.he,
        chuong=article.chuong,
        dieu=article.number,
        dieu_title=article.title,
        khoan=khoan,
        printed_page_start=printed_page_start,
        printed_page_end=printed_page_end,
        pdf_page_start=pdf_page_start,
        pdf_page_end=pdf_page_end,
        text=_joined(lines),
        embed_text=embed_text,
        warnings=warnings,
    )


def chunk_document(spec: DocSpec, pages: dict[int, str]) -> list[Chunk]:
    """Tách một văn bản thành các chunk Điều/Khoản, không đọc file."""
    articles = _parse_articles(_document_lines(spec, pages))
    chunks: list[Chunk] = []
    for article in articles:
        groups, split_by_line = _split_article(article)
        for lines, khoan in groups:
            chunks.append(_make_chunk(spec, article, lines, khoan, split_by_line))

    base_counts = Counter(chunk.chunk_id for chunk in chunks)
    base_positions: defaultdict[str, int] = defaultdict(int)
    unique_chunks: list[Chunk] = []
    for chunk in chunks:
        if base_counts[chunk.chunk_id] == 1:
            unique_chunks.append(chunk)
            continue
        base_positions[chunk.chunk_id] += 1
        unique_chunks.append(
            replace(chunk, chunk_id=f"{chunk.chunk_id}:p{base_positions[chunk.chunk_id]}")
        )
    return unique_chunks


def chunk_all(pages: dict[int, str]) -> list[Chunk]:
    """Tách tất cả văn bản trong registry có cấu trúc Điều."""
    chunks: list[Chunk] = []
    for spec in REGISTRY:
        if spec.has_articles:
            chunks.extend(chunk_document(spec, pages))

    identifiers = [chunk.chunk_id for chunk in chunks]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("chunk_id không duy nhất trên toàn registry")
    return chunks
