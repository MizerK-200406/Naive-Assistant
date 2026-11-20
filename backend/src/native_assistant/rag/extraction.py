"""Extract page-level text without inferring missing printed page numbers."""

import hashlib
import re
import unicodedata
from pathlib import Path

from pydantic import BaseModel
from pypdf import PdfReader

HEADER = "BÀI GIẢNG LỊCH SỬ ĐẢNG CỘNG SẢN VIỆT NAM"
FOOTER = re.compile(r"^BỘ MÔN LÝ LUẬN CHÍNH TRỊ\s*-\s*PTIT\s+Page\s+(\d+)\s*$", re.IGNORECASE)


class Page(BaseModel):
    pdf_page: int
    printed_page: int | None
    raw_text: str
    clean_text: str
    warnings: list[str]
    layout_review: str = "unreviewed"


class ExtractedDocument(BaseModel):
    source_name: str
    sha256: str
    page_count: int | None = None
    pages: list[Page]


def clean_page(raw: str, pdf_page: int) -> Page:
    # Wide interior gaps can indicate parallel columns or a diagram. This is a
    # review hint, not proof that other pages are safe for retrieval.
    wide_lines = sum(
        bool(re.search(r"\S {12,}\S", line))
        for line in raw.splitlines()
        if not FOOTER.fullmatch(unicodedata.normalize("NFC", line).strip())
    )
    lines = [unicodedata.normalize("NFC", line).strip() for line in raw.splitlines()]
    nonempty = [i for i, line in enumerate(lines) if line]
    printed = None
    warnings: list[str] = []
    if nonempty and lines[nonempty[0]] == HEADER:
        lines[nonempty[0]] = ""
    for position in nonempty[:2] + nonempty[-1:]:
        match = FOOTER.fullmatch(lines[position])
        if match:
            printed = int(match.group(1))
            lines[position] = ""
            break
    if printed is None:
        warnings.append("printed page number not found")
    cleaned = "\n".join(re.sub(r"[ \t]+", " ", line) for line in lines).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    if not cleaned:
        warnings.append("no extractable text")
    if wide_lines >= 3:
        warnings.append("possible diagram or multiple columns; review original page")
    return Page(
        pdf_page=pdf_page, printed_page=printed, raw_text=raw, clean_text=cleaned, warnings=warnings
    )


def extract_pdf(path: Path) -> ExtractedDocument:
    if path.suffix.lower() != ".pdf" or not path.is_file():
        raise ValueError("Input must be an existing PDF file")
    data = path.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise ValueError("Input is not a PDF")
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported")
    pages = [
        clean_page(page.extract_text(extraction_mode="layout") or "", index)
        for index, page in enumerate(reader.pages, 1)
    ]
    if not pages:
        raise ValueError("PDF has no pages")
    return ExtractedDocument(
        source_name=path.name,
        sha256=hashlib.sha256(data).hexdigest(),
        page_count=len(pages),
        pages=pages,
    )
