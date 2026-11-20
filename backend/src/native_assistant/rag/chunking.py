"""Chunk reviewed page text while retaining explicit source provenance."""

import hashlib
import re

from pydantic import BaseModel

from native_assistant.rag.extraction import ExtractedDocument, Page
from native_assistant.rag.review import DocumentReview, reviewed_fragments, validate_review

HEADING = re.compile(
    r"^(?!(?:[IVX]+|\d+|[a-z])[.,]$)"
    r"(Chương\s+(?:nhập môn|\d+)|(?-i:[IVX]+)\.|\d+\.|(?-i:[a-z])[.,])(?:\s+.+)?$",
    re.IGNORECASE,
)
WRAPPED_END = re.compile(
    r"(?:\b(?:của|và|về|cho|trong|đến|các|những|là|một|theo|với|hiện)|-)$", re.IGNORECASE
)


class Chunk(BaseModel):
    chunk_id: str
    document_sha256: str
    pdf_page: int
    printed_page: int | None
    headings: list[str]
    text: str


def append_chunk(
    chunks: list[Chunk],
    buffer: list[str],
    document: ExtractedDocument,
    page: Page,
    headings: list[str],
) -> None:
    if not buffer:
        return
    text = " ".join(buffer)
    key = f"{document.sha256}:{page.pdf_page}:{len(chunks)}:{text}"
    chunks.append(
        Chunk(
            chunk_id=hashlib.sha256(key.encode()).hexdigest(),
            document_sha256=document.sha256,
            pdf_page=page.pdf_page,
            printed_page=page.printed_page,
            headings=headings.copy(),
            text=text,
        )
    )
    buffer.clear()


def build_chunks(
    document: ExtractedDocument, review: DocumentReview, size: int = 160
) -> list[Chunk]:
    if size < 20:
        raise ValueError("Chunk size must be at least 20 whitespace units")
    page_numbers = [page.pdf_page for page in document.pages]
    if document.page_count is None or page_numbers != list(range(1, document.page_count + 1)):
        raise ValueError("Document must include the declared full consecutive page range")
    validate_review(document, review)
    entries = {item.pdf_page: item for item in review.pages}
    if set(entries) != {page.pdf_page for page in document.pages}:
        raise ValueError("All pages require explicit layout review")
    chunks: list[Chunk] = []
    headings: dict[int, str] = {}
    bibliography = False
    for page in document.pages:
        fragments = reviewed_fragments(page, entries[page.pdf_page])
        for fragment in fragments:
            buffer: list[str] = []

            lines = [line.strip() for line in fragment.splitlines()]
            index = 0
            while index < len(lines):
                line = lines[index]
                index += 1
                if line.casefold() == "tài liệu tham khảo":
                    append_chunk(chunks, buffer, document, page, list(headings.values()))
                    headings = {0: line}
                    bibliography = True
                    buffer.extend(line.split())
                    continue
                match = HEADING.match(line)
                if match and bibliography and not match.group(1).lower().startswith("chương"):
                    match = None
                if match:
                    append_chunk(chunks, buffer, document, page, list(headings.values()))
                    marker = match.group(1)
                    if marker.lower().startswith("chương"):
                        bibliography = False
                    level = (
                        0
                        if marker.lower().startswith("chương")
                        else (
                            1
                            if re.fullmatch(r"[IVX]+\.", marker)
                            else 2
                            if marker[0].isdigit()
                            else 3
                        )
                    )
                    headings = {key: value for key, value in headings.items() if key < level}
                    heading = line
                    if (
                        level > 0
                        and WRAPPED_END.search(line)
                        and index < len(lines)
                        and lines[index]
                        and len(lines[index]) <= 45
                        and not HEADING.match(lines[index])
                    ):
                        heading += " " + lines[index]
                        buffer.extend(line.split())
                        line = lines[index]
                        index += 1
                    headings[level] = heading
                    buffer.extend(line.split())
                    continue
                for word in line.split():
                    buffer.append(word)
                    if len(buffer) >= size:
                        append_chunk(chunks, buffer, document, page, list(headings.values()))
            append_chunk(chunks, buffer, document, page, list(headings.values()))
    return chunks
