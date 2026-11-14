from __future__ import annotations

import json
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

import pymupdf

PAGE_OFFSET: int = 6
FIRST_INDEXED_PDF_PAGE: int = 7


def to_printed(pdf_page: int, offset: int = PAGE_OFFSET) -> int | None:
    """Chuyển đổi số trang PDF sang số trang in thực tế.
    None nếu pdf_page < FIRST_INDEXED_PDF_PAGE; ngược lại pdf_page - offset.
    """
    if pdf_page < FIRST_INDEXED_PDF_PAGE:
        return None
    return pdf_page - offset


def normalize_text(s: str) -> str:
    """Chuẩn hóa NFC, giữ nguyên ký tự xuống dòng."""
    return unicodedata.normalize("NFC", s)


@dataclass(frozen=True)
class PageRecord:
    pdf_page: int  # bắt đầu từ 1
    printed_page: int | None
    text: str  # NFC, từ get_text("text")
    margin_numbers: list[int]
    n_chars: int  # số ký tự không phải khoảng trắng


def extract_pages(pdf_path: Path) -> list[PageRecord]:
    """Trích xuất danh sách PageRecord từ file PDF sử dụng PyMuPDF."""
    doc = pymupdf.open(str(pdf_path))
    records: list[PageRecord] = []

    try:
        for idx in range(len(doc)):
            pdf_page = idx + 1
            page = doc[idx]

            raw_text = page.get_text("text")
            text = normalize_text(raw_text)

            printed_page = to_printed(pdf_page)

            # Tính toán lề trên và lề dưới (8% chiều cao trang)
            h = page.rect.height
            top_limit = page.rect.y0 + 0.08 * h
            bottom_limit = page.rect.y1 - 0.08 * h

            words = page.get_text("words")
            margin_numbers: list[int] = []
            for w in words:
                word_text = str(w[4]).strip()
                if word_text.isdigit() and 1 <= len(word_text) <= 3:
                    y0, y1 = w[1], w[3]
                    is_top = (y0 >= page.rect.y0) and (y1 <= top_limit)
                    is_bottom = (y0 >= bottom_limit) and (y1 <= page.rect.y1 + 1e-2)
                    if is_top or is_bottom:
                        margin_numbers.append(int(word_text))

            n_chars = sum(1 for c in text if not c.isspace())

            records.append(
                PageRecord(
                    pdf_page=pdf_page,
                    printed_page=printed_page,
                    text=text,
                    margin_numbers=margin_numbers,
                    n_chars=n_chars,
                )
            )
    finally:
        doc.close()

    return records


def write_jsonl(records: list[PageRecord], out_path: Path) -> None:
    """Ghi danh sách PageRecord vào file jsonl, mỗi dòng một JSON, ensure_ascii=False."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for record in records:
            line = json.dumps(asdict(record), ensure_ascii=False)
            f.write(line + "\n")
