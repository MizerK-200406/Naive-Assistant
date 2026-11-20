from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from native_assistant.rag.chunking import Chunk
from native_assistant.rag.evaluation import (
    Dataset,
    EvidenceAlternative,
    EvidenceGroup,
    Question,
    QuestionRubric,
    Source,
    load_dataset,
    score_retrieval,
)


def test_current_dev_schema_loads_and_preserves_metadata() -> None:
    path = Path(__file__).resolve().parents[1] / "eval/datasets/test.yaml"
    dataset, _ = load_dataset(path)
    assert dataset.schema_version == "2.0" and dataset.is_development
    assert dataset.total_questions == len(dataset.questions) == 40
    assert sum(not q.answerable for q in dataset.questions) == 5
    assert dataset.group_counts and dataset.group_definitions
    assert all(q.group for q in dataset.questions)
    assert all(
        q.statement in q.question and q.expected_label for q in dataset.questions if q.statement
    )
    assert any(q.grading_notes for q in dataset.questions)


def test_schema_split_usage_and_group_counts_are_validated() -> None:
    question = Question(
        id="T1",
        chapter="c",
        difficulty="easy",
        category="citation_lookup",
        question="q",
        gold_answer="gold",
        required_facts=["fact"],
        answerable=True,
        group="G1",
        source=Source(document="doc.pdf", pdf_pages=[1], printed_pages=[1]),
    )
    data = {
        "schema_version": "2.0",
        "dataset": "x",
        "split": "test",
        "usage": "development_evaluation",
        "source_document": "doc.pdf",
        "source_edition": 2021,
        "source_sha256": "a" * 64,
        "page_reference": "pdf",
        "total_questions": 1,
        "questions": [question],
        "group_counts": {"G1": 1},
        "group_definitions": {"G1": "description"},
    }
    assert Dataset(**data).is_development
    for changes in (
        {"schema_version": "1.0"},
        {"split": "holdout"},
        {"usage": "final_holdout_only"},
        {"group_counts": {"G1": 2}},
        {"group_definitions": {"G2": "other"}},
    ):
        with pytest.raises(ValidationError):
            Dataset(**(data | changes))


def test_unanswerable_empty_source_metrics_are_not_applicable() -> None:
    from native_assistant.rag.evaluation import HumanAssessment, score_assessment

    fields = {
        "id": "T1",
        "chapter": "c",
        "difficulty": "hard",
        "category": "unanswerable",
        "question": "q",
        "gold_answer": "gold",
        "required_facts": ["fact"],
        "source": Source(document="doc.pdf", pdf_pages=[], printed_pages=[]),
    }
    question = Question(**fields, answerable=False)
    result = score_retrieval(question, [])
    assert all(value is None for value in result.model_dump().values())
    assessment = HumanAssessment(
        question_id="T1",
        reviewer="r",
        accuracy_a=4,
        citation_b=4,
        groundedness_d=4,
        clarity_e=4,
        covered_facts=[True],
        critical_error=False,
    )
    with pytest.raises(ValueError, match="approved rubric"):
        score_assessment(question, assessment)
    with pytest.raises(ValidationError, match="source pages"):
        Question(**fields, answerable=True)
    with pytest.raises(ValidationError):
        Question(**fields, answerable="false")
    with pytest.raises(ValidationError):
        Source(document="doc.pdf", pdf_pages=[], printed_pages=[1])


def test_page_hit_does_not_mean_evidence_hit() -> None:
    q = Question(
        id="Q1",
        chapter="a",
        difficulty="easy",
        question="q",
        category="definition",
        gold_answer="a",
        required_facts=["a"],
        answerable=True,
        source=Source(document="doc.pdf", pdf_pages=[3, 4], printed_pages=[1, 2]),
    )
    chunk = Chunk(
        chunk_id="x",
        document_sha256="x",
        pdf_page=3,
        printed_page=1,
        headings=[],
        text="wrong paragraph",
    )
    rubric = QuestionRubric(
        id="Q1",
        groups=[
            EvidenceGroup(alternatives=[EvidenceAlternative(pdf_page=3, excerpt="correct passage")])
        ],
    )
    result = score_retrieval(q, [chunk], rubric)
    assert result.page_hit and result.page_coverage == 0.5 and not result.evidence_complete
    assert score_retrieval(q, [chunk]).evidence_complete is None


def test_dataset_rejects_unsafe_yaml_and_bad_page(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text('!!python/object/apply:os.system ["false"]')
    with pytest.raises(yaml.YAMLError):
        load_dataset(path)
    with pytest.raises(ValueError):
        Question(
            id="Q",
            chapter="a",
            difficulty="x",
            question="q",
            category="definition",
            gold_answer="a",
            required_facts=["a"],
            answerable=True,
            source=Source(document="doc.pdf", pdf_pages=[0], printed_pages=[1]),
        )


def test_draft_scoring_obeys_coverage_and_critical_error() -> None:
    from native_assistant.rag.evaluation import HumanAssessment, Source, score_assessment

    q = Question(
        id="Q1",
        chapter="a",
        difficulty="easy",
        category="definition",
        question="q",
        gold_answer="a",
        required_facts=["1", "2", "3", "4"],
        source=Source(document="d", pdf_pages=[1], printed_pages=[1]),
        answerable=True,
    )
    result = score_assessment(
        q,
        HumanAssessment(
            question_id="Q1",
            reviewer="reviewer",
            accuracy_a=4,
            citation_b=4,
            groundedness_d=4,
            clarity_e=4,
            covered_facts=[True, True, True, False],
            critical_error=False,
        ),
    )
    assert result.completeness_c == 3 and result.score_100 == 96.25
    assert result.proposed_pass and result.threshold_status == "draft"
    blocked = score_assessment(
        q,
        HumanAssessment(
            question_id="Q1",
            reviewer="reviewer",
            accuracy_a=4,
            citation_b=4,
            groundedness_d=4,
            clarity_e=4,
            covered_facts=[True] * 4,
            critical_error=True,
        ),
    )
    assert blocked.score_100 == 100 and not blocked.proposed_pass
    with pytest.raises(ValueError):
        HumanAssessment(
            question_id="Q1",
            reviewer="r",
            accuracy_a=4,
            citation_b=4,
            groundedness_d=4,
            clarity_e=4,
            covered_facts=["yes"],
            critical_error=False,
        )


def test_source_page_labels_are_checked() -> None:
    from native_assistant.rag.evaluation import Dataset, Source, validate_sources
    from native_assistant.rag.extraction import ExtractedDocument, clean_page

    page = clean_page("BỘ MÔN LÝ LUẬN CHÍNH TRỊ - PTIT Page 4\nBody", 6)
    source = Source(document="doc.pdf", pdf_pages=[6], printed_pages=[4])
    question = Question(
        id="Q1",
        chapter="a",
        difficulty="easy",
        category="definition",
        question="q",
        gold_answer="a",
        required_facts=["fact"],
        source=source,
        answerable=True,
    )
    dataset = Dataset(
        schema_version="1.0",
        dataset="x",
        split="questions",
        usage="development_evaluation",
        source_document="doc.pdf",
        source_edition=2021,
        source_sha256="a" * 64,
        page_reference="x",
        total_questions=1,
        questions=[question],
    )
    doc = ExtractedDocument(source_name="doc.pdf", sha256="a" * 64, pages=[page])
    validate_sources(dataset, doc)
    changed = question.model_copy(
        update={"source": source.model_copy(update={"printed_pages": [5]})}
    )
    with pytest.raises(ValueError, match="page mismatch"):
        validate_sources(dataset.model_copy(update={"questions": [changed]}), doc)
