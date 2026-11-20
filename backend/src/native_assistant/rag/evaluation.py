"""Deterministic dataset validation and retrieval metrics; no model judging."""

import hashlib
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, StrictBool, model_validator

from native_assistant.rag.chunking import Chunk
from native_assistant.rag.extraction import ExtractedDocument


class Source(BaseModel):
    document: str = Field(min_length=1)
    pdf_pages: list[int]
    printed_pages: list[int]

    @model_validator(mode="after")
    def valid_pages(self) -> "Source":
        if any(page < 1 for page in self.pdf_pages + self.printed_pages):
            raise ValueError("Page numbers must be positive")
        if len(self.pdf_pages) != len(self.printed_pages):
            raise ValueError("PDF and printed page lists must have matching lengths")
        return self


class Question(BaseModel):
    id: str = Field(min_length=1)
    chapter: str = Field(min_length=1)
    difficulty: str = Field(min_length=1)
    question: str = Field(min_length=1)
    category: Literal[
        "definition",
        "enumeration",
        "comparison",
        "cause_effect",
        "event_fact",
        "policy",
        "chronology",
        "citation_lookup",
        "synthesis",
        "true_false",
        "unanswerable",
    ]
    gold_answer: str = Field(min_length=1)
    required_facts: list[str] = Field(min_length=1)
    source: Source
    answerable: StrictBool
    group: str | None = None
    statement: str | None = None
    expected_label: str | None = None
    grading_notes: str | None = None

    @model_validator(mode="after")
    def facts_nonempty(self) -> "Question":
        if any(not fact.strip() for fact in self.required_facts):
            raise ValueError("Required facts cannot be empty")
        if self.answerable and not self.source.pdf_pages:
            raise ValueError("Answerable questions require source pages")
        return self


class Dataset(BaseModel):
    schema_version: Literal["1.0", "2.0"]
    dataset: str
    split: Literal["questions", "test", "holdout"]
    usage: Literal["development_evaluation", "final_holdout_only"]
    source_document: str
    source_edition: int
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_reference: str
    total_questions: int = Field(gt=0)
    questions: list[Question]
    group_counts: dict[str, int] | None = None
    group_definitions: dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_questions(self) -> "Dataset":
        if len(self.questions) != self.total_questions:
            raise ValueError("Question count does not match total_questions")
        if len({item.id for item in self.questions}) != len(self.questions):
            raise ValueError("Duplicate question IDs")
        if any(item.source.document != self.source_document for item in self.questions):
            raise ValueError("Question source document does not match dataset")
        if (self.schema_version, self.split, self.usage) not in {
            ("1.0", "questions", "development_evaluation"),
            ("1.0", "holdout", "final_holdout_only"),
            ("2.0", "test", "development_evaluation"),
            ("2.0", "holdout", "final_holdout_only"),
        }:
            raise ValueError("Dataset schema, split and usage do not match")
        if self.group_counts is not None:
            counts: dict[str, int] = {}
            for item in self.questions:
                if item.group is None:
                    raise ValueError("Questions must have groups when group_counts is present")
                counts[item.group] = counts.get(item.group, 0) + 1
            if counts != self.group_counts:
                raise ValueError("Group counts do not match questions")
        if self.group_definitions is not None and (
            self.group_counts is None or set(self.group_definitions) != set(self.group_counts)
        ):
            raise ValueError("Group definitions do not match group counts")
        return self

    @property
    def is_development(self) -> bool:
        return (self.schema_version, self.split, self.usage) in {
            ("1.0", "questions", "development_evaluation"),
            ("2.0", "test", "development_evaluation"),
        }


def load_dataset(path: Path) -> tuple[Dataset, str]:
    data = path.read_bytes()
    return Dataset.model_validate(yaml.safe_load(data)), hashlib.sha256(data).hexdigest()


def validate_sources(dataset: Dataset, document: ExtractedDocument) -> None:
    if dataset.source_sha256 != document.sha256 or dataset.source_document != document.source_name:
        raise ValueError("Dataset source does not match extracted document")
    pages = {page.pdf_page: page for page in document.pages}
    for question in dataset.questions:
        for pdf_page, printed_page in zip(
            question.source.pdf_pages, question.source.printed_pages, strict=True
        ):
            if pdf_page not in pages or pages[pdf_page].printed_page != printed_page:
                raise ValueError(f"Source page mismatch for {question.id}, PDF page {pdf_page}")


def validate_disjoint(first: Dataset, second: Dataset) -> None:
    if first.is_development == second.is_development or first.source_sha256 != second.source_sha256:
        raise ValueError("Datasets must be different splits of the same source")
    if {q.id for q in first.questions} & {q.id for q in second.questions}:
        raise ValueError("Question IDs overlap between splits")

    def normalize(q: str) -> str:
        return " ".join(q.casefold().split())

    if {normalize(q.question) for q in first.questions} & {
        normalize(q.question) for q in second.questions
    }:
        raise ValueError("Question text overlaps between splits")


class EvidenceAlternative(BaseModel):
    pdf_page: int = Field(ge=1)
    excerpt: str = Field(min_length=1)


class EvidenceGroup(BaseModel):
    alternatives: list[EvidenceAlternative] = Field(min_length=1)


class QuestionRubric(BaseModel):
    id: str = Field(min_length=1)
    groups: list[EvidenceGroup] = Field(min_length=1)


class Rubric(BaseModel):
    source_sha256: str = Field(min_length=1)
    dataset_sha256: str = Field(min_length=1)
    reviewed_by: str = Field(min_length=1)
    questions: list[QuestionRubric]

    @model_validator(mode="after")
    def unique_questions(self) -> "Rubric":
        if len({item.id for item in self.questions}) != len(self.questions):
            raise ValueError("Duplicate rubric question IDs")
        return self


class RetrievalMetrics(BaseModel):
    page_hit: bool | None
    page_coverage: float | None
    reciprocal_rank: float | None
    evidence_coverage: float | None
    evidence_complete: bool | None


class HumanAssessment(BaseModel):
    question_id: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    accuracy_a: int = Field(ge=0, le=4, strict=True)
    citation_b: int = Field(ge=0, le=4, strict=True)
    groundedness_d: int = Field(ge=0, le=4, strict=True)
    clarity_e: int = Field(ge=0, le=4, strict=True)
    covered_facts: list[StrictBool] = Field(min_length=1)
    critical_error: bool = Field(strict=True)
    notes: str = ""


class ProposedScore(BaseModel):
    question_id: str
    reviewer: str
    completeness_c: int
    score_100: float
    proposed_pass: bool
    threshold_status: Literal["draft"] = "draft"


def score_assessment(question: Question, assessment: HumanAssessment) -> ProposedScore:
    """Apply draft rubric to human decisions, never infer semantic scores from keywords."""
    if not question.answerable:
        raise ValueError("Scoring unanswerable questions requires an approved rubric")
    if assessment.question_id != question.id or len(assessment.covered_facts) != len(
        question.required_facts
    ):
        raise ValueError("Assessment question or fact count does not match dataset")
    covered, total = sum(assessment.covered_facts), len(assessment.covered_facts)
    completeness = (
        4
        if covered == total
        else 3
        if 4 * covered >= 3 * total
        else 2
        if 2 * covered >= total
        else 1
        if covered
        else 0
    )
    score = (
        assessment.accuracy_a * 40
        + assessment.citation_b * 25
        + completeness * 15
        + assessment.groundedness_d * 15
        + assessment.clarity_e * 5
    ) / 4
    proposed_pass = (
        score >= 80
        and assessment.accuracy_a >= 3
        and assessment.citation_b >= 3
        and assessment.groundedness_d >= 3
        and not assessment.critical_error
    )
    return ProposedScore(
        question_id=question.id,
        reviewer=assessment.reviewer,
        completeness_c=completeness,
        score_100=score,
        proposed_pass=proposed_pass,
    )


def score_retrieval(
    question: Question, chunks: list[Chunk], rubric: QuestionRubric | None = None
) -> RetrievalMetrics:
    if not question.answerable:
        if rubric is not None and rubric.id != question.id:
            raise ValueError("Rubric question does not match")
        return RetrievalMetrics(
            page_hit=None,
            page_coverage=None,
            reciprocal_rank=None,
            evidence_coverage=None,
            evidence_complete=None,
        )
    expected = set(question.source.pdf_pages)
    found = {chunk.pdf_page for chunk in chunks} & expected
    first_rank = next((i for i, chunk in enumerate(chunks, 1) if chunk.pdf_page in expected), None)
    coverage = None
    complete = None
    if rubric is not None:
        if rubric.id != question.id:
            raise ValueError("Rubric question does not match")
        hits = [
            any(
                chunk.pdf_page == alternative.pdf_page and alternative.excerpt in chunk.text
                for alternative in group.alternatives
                for chunk in chunks
            )
            for group in rubric.groups
        ]
        coverage = sum(hits) / len(hits)
        complete = all(hits)
    return RetrievalMetrics(
        page_hit=bool(found),
        page_coverage=len(found) / len(expected),
        reciprocal_rank=1 / first_rank if first_rank else 0.0,
        evidence_coverage=coverage,
        evidence_complete=complete,
    )
