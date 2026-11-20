from pathlib import Path

import pytest

from native_assistant.rag.extraction import clean_page, extract_pdf


def test_header_footer_at_start_preserves_body_and_notes() -> None:
    raw = (
        "BÀI GIẢNG LỊCH SỬ ĐẢNG CỘNG SẢN VIỆT NAM\n"
        "BỘ MÔN LÝ LUẬN CHÍNH TRỊ - PTIT Page 4\n"
        "Nội dung năm 1945\n1 Chú thích\n"
    )
    page = clean_page(raw, 6)
    assert page.printed_page == 4
    assert page.clean_text == "Nội dung năm 1945\n1 Chú thích"
    assert page.raw_text == raw


def test_missing_footer_does_not_guess_page() -> None:
    page = clean_page("Nội dung\nPage 2", 10)
    assert page.printed_page is None
    assert "Page 2" in page.clean_text
    assert page.warnings


def test_footer_at_end_and_unicode_normalization() -> None:
    raw = (
        "BÀI GIẢNG LỊCH SỬ ĐẢNG CỘNG SẢN VIỆT NAM\n"
        "Nội dung và chú thích\n"
        "BỘ MÔN LÝ LUẬN CHÍNH TRỊ - PTIT     Page 58"
    )
    page = clean_page(raw, 60)
    assert page.printed_page == 58
    assert page.clean_text == "Nội dung và chú thích"


def test_wide_layout_is_flagged_without_deleting_text() -> None:
    raw = "Left            Right\nAlpha            Beta\nOne            Two\nBody remains"
    page = clean_page(raw, 16)
    assert any("possible diagram" in warning for warning in page.warnings)
    assert page.layout_review == "unreviewed"
    assert "Left Right" in page.clean_text
    assert page.raw_text == raw


def test_unflagged_layout_is_not_automatically_reviewed() -> None:
    page = clean_page("Ordinary text", 1)
    assert page.layout_review == "unreviewed"
    assert not any("possible diagram" in warning for warning in page.warnings)


def test_invalid_pdf(tmp_path: Path) -> None:
    path = tmp_path / "invalid.pdf"
    path.write_text("not a pdf")
    with pytest.raises(ValueError, match="not a PDF"):
        extract_pdf(path)
