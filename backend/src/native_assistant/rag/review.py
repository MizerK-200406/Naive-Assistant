"""Review annotations for excluding unreliable text regions from evidence."""

from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from native_assistant.rag.extraction import ExtractedDocument, Page


class Exclusion(BaseModel):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_bounds(self) -> "Exclusion":
        if self.end <= self.start:
            raise ValueError("Exclusion end must be after start")
        return self


class PageReview(BaseModel):
    pdf_page: int = Field(ge=1)
    text_sha256: str
    status: Literal["reviewed"]
    exclusions: list[Exclusion] = Field(default_factory=list)


class DocumentReview(BaseModel):
    source_sha256: str
    pages: list[PageReview]


def reviewed_fragments(page: Page, review: PageReview) -> list[str]:
    """Return separated text fragments, never joining across excluded regions."""
    actual = sha256(page.clean_text.encode("utf-8")).hexdigest()
    if review.pdf_page != page.pdf_page or review.text_sha256 != actual:
        raise ValueError("Review does not match page content")
    cursor = 0
    fragments = []
    for region in sorted(review.exclusions, key=lambda item: item.start):
        if region.start < cursor or region.end > len(page.clean_text):
            raise ValueError("Exclusions overlap or exceed page length")
        text = page.clean_text[cursor : region.start].strip()
        if text:
            fragments.append(text)
        cursor = region.end
    tail = page.clean_text[cursor:].strip()
    if tail:
        fragments.append(tail)
    return fragments


def validate_review(document: ExtractedDocument, review: DocumentReview) -> None:
    if document.sha256 != review.source_sha256:
        raise ValueError("Review does not match document")
    by_number = {page.pdf_page: page for page in document.pages}
    seen: set[int] = set()
    for entry in review.pages:
        if entry.pdf_page in seen or entry.pdf_page not in by_number:
            raise ValueError("Duplicate or unknown page in review")
        seen.add(entry.pdf_page)
        reviewed_fragments(by_number[entry.pdf_page], entry)


def add_page_review(
    document: ExtractedDocument,
    review: DocumentReview,
    page_number: int,
    exclusions: list[Exclusion],
) -> DocumentReview:
    """Add one explicitly reviewed page; never replace an existing review."""
    validate_review(document, review)
    pages = {page.pdf_page: page for page in document.pages}
    if page_number not in pages:
        raise ValueError("Unknown page")
    if any(entry.pdf_page == page_number for entry in review.pages):
        raise ValueError("Page already reviewed")
    page = pages[page_number]
    entry = PageReview(
        pdf_page=page_number,
        text_sha256=sha256(page.clean_text.encode("utf-8")).hexdigest(),
        status="reviewed",
        exclusions=exclusions,
    )
    reviewed_fragments(page, entry)
    return review.model_copy(update={"pages": [*review.pages, entry]})
