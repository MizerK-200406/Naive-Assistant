from hashlib import sha256

import pytest

from native_assistant.rag.chunking import build_chunks
from native_assistant.rag.extraction import ExtractedDocument, clean_page
from native_assistant.rag.review import DocumentReview, Exclusion, PageReview


def test_review_gate_and_region_provenance() -> None:
    page = clean_page("Chương 1 Đề mục\nI. Bối cảnh\nBefore DIAGRAM After", 1)
    doc = ExtractedDocument(source_name="x.pdf", sha256="abc", page_count=1, pages=[page])
    with pytest.raises(ValueError, match="explicit layout review"):
        build_chunks(doc, DocumentReview(source_sha256="abc", pages=[]))
    start = page.clean_text.index("DIAGRAM")
    review = PageReview(
        pdf_page=1,
        status="reviewed",
        text_sha256=sha256(page.clean_text.encode()).hexdigest(),
        exclusions=[Exclusion(start=start, end=start + 7, reason="diagram")],
    )
    chunks = build_chunks(doc, DocumentReview(source_sha256="abc", pages=[review]))
    assert [chunk.text for chunk in chunks] == ["Chương 1 Đề mục", "I. Bối cảnh Before", "After"]
    assert chunks[-1].pdf_page == 1 and len(chunks[-1].headings) == 2


def test_standalone_chapter_and_missing_level_keep_heading_hierarchy() -> None:
    page = clean_page("Chương 1\n1. Mục đầu\na. Chi tiết\nNội dung\n2. Mục kế\nThông tin", 1)
    doc = ExtractedDocument(source_name="x.pdf", sha256="abc", page_count=1, pages=[page])
    review = PageReview(
        pdf_page=1, status="reviewed", text_sha256=sha256(page.clean_text.encode()).hexdigest()
    )
    chunks = build_chunks(doc, DocumentReview(source_sha256="abc", pages=[review]))
    assert chunks[-1].headings == ["Chương 1", "2. Mục kế"]
    assert "2. Mục kế" in chunks[-1].text
    assert any(chunk.headings == ["Chương 1", "1. Mục đầu", "a. Chi tiết"] for chunk in chunks)


def test_rejects_nonconsecutive_pages_before_heading_carryover() -> None:
    pages = [clean_page("Chương 1\nNội dung", 1), clean_page("Nội dung khác", 3)]
    doc = ExtractedDocument(source_name="x.pdf", sha256="abc", page_count=3, pages=pages)
    with pytest.raises(ValueError, match="consecutive"):
        build_chunks(doc, DocumentReview(source_sha256="abc", pages=[]))


def test_comma_subsection_heading_from_source() -> None:
    page = clean_page("Chương 1\nI. Mục\n1. Phần\na, Chức năng nhận thức:\nNội dung.", 1)
    doc = ExtractedDocument(source_name="x.pdf", sha256="abc", page_count=1, pages=[page])
    review = PageReview(
        pdf_page=1, status="reviewed", text_sha256=sha256(page.clean_text.encode()).hexdigest()
    )
    chunks = build_chunks(doc, DocumentReview(source_sha256="abc", pages=[review]))
    assert chunks[-1].headings == ["Chương 1", "I. Mục", "1. Phần", "a, Chức năng nhận thức:"]


def test_footnote_page_number_does_not_replace_section_heading() -> None:
    pages = [
        clean_page("Chương 1\n1. Section\nFootnote continues\n258.", 1),
        clean_page("Next page text", 2),
    ]
    doc = ExtractedDocument(source_name="x.pdf", sha256="abc", page_count=2, pages=pages)
    reviews = [
        PageReview(
            pdf_page=p.pdf_page,
            status="reviewed",
            text_sha256=sha256(p.clean_text.encode()).hexdigest(),
        )
        for p in pages
    ]
    chunks = build_chunks(doc, DocumentReview(source_sha256="abc", pages=reviews))
    assert chunks[-1].headings == ["Chương 1", "1. Section"]
    assert any("258." in chunk.text for chunk in chunks)


def test_wrapped_heading_is_preserved_without_joining_unrelated_prose() -> None:
    page = clean_page(
        "I. Lịch sử của\nĐảng\n1. Một mục\nVăn bản tiếp theo.\n"
        "2. Chủ trương và\nMột dòng văn xuôi rất dài không phải phần tiếp nối của tiêu đề này. ",
        1,
    )
    doc = ExtractedDocument(source_name="x.pdf", sha256="abc", page_count=1, pages=[page])
    review = PageReview(
        pdf_page=1, status="reviewed", text_sha256=sha256(page.clean_text.encode()).hexdigest()
    )
    chunks = build_chunks(doc, DocumentReview(source_sha256="abc", pages=[review]))
    assert chunks[0].headings == ["I. Lịch sử của Đảng"]
    assert chunks[-1].headings[-1] == "2. Chủ trương và"
    assert "I. Lịch sử của Đảng" in chunks[0].text


def test_bibliography_entries_are_not_headings_across_pages() -> None:
    pages = [
        clean_page("Chương 3\n1. Nội dung\nTÀI LIỆU THAM KHẢO\n1. Tác giả một", 1),
        clean_page("2. Tác giả hai\n3. Tác giả ba", 2),
    ]
    doc = ExtractedDocument(source_name="x.pdf", sha256="abc", page_count=2, pages=pages)
    reviews = [
        PageReview(
            pdf_page=p.pdf_page,
            status="reviewed",
            text_sha256=sha256(p.clean_text.encode()).hexdigest(),
        )
        for p in pages
    ]
    chunks = build_chunks(doc, DocumentReview(source_sha256="abc", pages=reviews))
    assert chunks[-1].headings == ["TÀI LIỆU THAM KHẢO"]
    assert "2. Tác giả hai" in chunks[-1].text
