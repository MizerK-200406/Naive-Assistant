import json
from pathlib import Path

import pymupdf
import pytest

from naive_assistant.ingest.extract import (
    PageRecord,
    TEXT_FLAGS,
    extract_pages,
    normalize_text,
    to_printed,
    write_jsonl,
)


def test_to_printed():
    assert to_printed(6) is None
    assert to_printed(7) == 1
    assert to_printed(213) == 207
    assert to_printed(1) is None
    assert to_printed(5) is None
    assert to_printed(8) == 2


def test_text_flags():
    assert TEXT_FLAGS & pymupdf.TEXT_MEDIABOX_CLIP == 0
    assert TEXT_FLAGS == 131


def test_normalize_text():
    assert normalize_text("e\u0301") == "é"
    assert normalize_text("Tiê\u0301ng Viê\u0323t") == "Tiếng Việt"
    assert normalize_text("Dòng 1\nDòng 2") == "Dòng 1\nDòng 2"


def test_page_record_dataclass():
    record = PageRecord(
        pdf_page=7,
        printed_page=1,
        text="Trang 1",
        margin_numbers=[1],
        n_chars=6,
    )
    assert record.pdf_page == 7
    assert record.printed_page == 1
    assert record.text == "Trang 1"
    assert record.margin_numbers == [1]
    assert record.n_chars == 6

    with pytest.raises(Exception):
        record.pdf_page = 8  # Frozen dataclass


def test_write_jsonl(tmp_path: Path):
    records = [
        PageRecord(
            pdf_page=1,
            printed_page=None,
            text="Trang bìa",
            margin_numbers=[],
            n_chars=8,
        ),
        PageRecord(
            pdf_page=7,
            printed_page=1,
            text="Nội dung chính",
            margin_numbers=[1],
            n_chars=13,
        ),
    ]
    out_file = tmp_path / "test_pages.jsonl"
    write_jsonl(records, out_file)

    assert out_file.exists()
    lines = out_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    row1 = json.loads(lines[0])
    assert row1["pdf_page"] == 1
    assert row1["printed_page"] is None
    assert row1["text"] == "Trang bìa"

    row2 = json.loads(lines[1])
    assert row2["pdf_page"] == 7
    assert row2["printed_page"] == 1
    assert row2["text"] == "Nội dung chính"
    assert row2["margin_numbers"] == [1]


def test_extract_pages_synthetic(tmp_path: Path):
    # Tạo PDF giả lập trong bộ nhớ phục vụ test hermetic, không phụ thuộc file PDF thực tế
    doc = pymupdf.open()
    # Trang 1: Bìa
    p1 = doc.new_page(width=500, height=800)
    p1.insert_text((100, 400), "Trang bìa không số")

    # Tạo 6 trang giả để đến trang 7
    for _ in range(5):
        doc.new_page(width=500, height=800)

    # Trang 7: Có số ở lề dưới (y=760 trong vùng 8% dưới: 800 - 64 = 736)
    p7 = doc.new_page(width=500, height=800)
    p7.insert_text((250, 760), "1")
    p7.insert_text((100, 200), "Noi dung trang 1")

    test_pdf_path = tmp_path / "synthetic.pdf"
    doc.save(str(test_pdf_path))
    doc.close()

    records = extract_pages(test_pdf_path)
    assert len(records) == 7
    assert records[0].pdf_page == 1
    assert records[0].printed_page is None
    assert records[0].margin_numbers == []

    assert records[6].pdf_page == 7
    assert records[6].printed_page == 1
    assert records[6].margin_numbers == [1]
