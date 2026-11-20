from hashlib import sha256

import pytest

from native_assistant.rag.extraction import clean_page
from native_assistant.rag.review import Exclusion, PageReview, reviewed_fragments


def make_review(text: str, exclusions: list[Exclusion]) -> PageReview:
    return PageReview(
        pdf_page=1,
        text_sha256=sha256(text.encode()).hexdigest(),
        status="reviewed",
        exclusions=exclusions,
    )


def test_excluded_regions_are_not_joined() -> None:
    page = clean_page("Before [diagram] After", 1)
    review = make_review(page.clean_text, [Exclusion(start=7, end=16, reason="diagram")])
    assert reviewed_fragments(page, review) == ["Before", "After"]


def test_stale_review_and_overlapping_ranges_are_rejected() -> None:
    page = clean_page("some text", 1)
    with pytest.raises(ValueError, match="match"):
        reviewed_fragments(page, make_review("old text", []))
    review = make_review(
        page.clean_text,
        [Exclusion(start=0, end=5, reason="x"), Exclusion(start=4, end=6, reason="y")],
    )
    with pytest.raises(ValueError, match="overlap"):
        reviewed_fragments(page, review)


def test_add_review_rejects_duplicate_and_invalid_ranges() -> None:
    from native_assistant.rag.extraction import ExtractedDocument
    from native_assistant.rag.review import DocumentReview, add_page_review

    page = clean_page("Before diagram after", 1)
    doc = ExtractedDocument(source_name="test.pdf", sha256="hash", pages=[page])
    initial = DocumentReview(source_sha256="hash", pages=[])
    result = add_page_review(doc, initial, 1, [Exclusion(start=7, end=14, reason="diagram")])
    assert not initial.pages
    assert reviewed_fragments(page, result.pages[0]) == ["Before", "after"]
    with pytest.raises(ValueError, match="already reviewed"):
        add_page_review(doc, result, 1, [])
    with pytest.raises(ValueError, match="exceed"):
        add_page_review(doc, initial, 1, [Exclusion(start=0, end=100, reason="diagram")])
