import pytest

from native_assistant.ai.provider import GenerationResult, ProviderError
from native_assistant.rag.chunking import Chunk
from native_assistant.rag.eval_run import capture_dev_question
from native_assistant.rag.evaluation import Dataset, Question, Source, validate_disjoint


def fixture_dataset(split="questions"):
    q = Question(
        id="Q1",
        chapter="intro",
        difficulty="easy",
        category="definition",
        question="question?",
        gold_answer="SECRET_GOLD",
        required_facts=["SECRET_FACT"],
        source=Source(document="doc.pdf", pdf_pages=[1], printed_pages=[1]),
        answerable=True,
    )
    dataset = Dataset(
        schema_version="1.0",
        dataset="x",
        split=split,
        usage="development_evaluation" if split == "questions" else "final_holdout_only",
        source_document="doc.pdf",
        source_edition=2021,
        source_sha256="a" * 64,
        page_reference="pdf",
        total_questions=1,
        questions=[q],
    )
    return dataset, q


class Retrieval:
    def search(self, question, limit=4):
        assert question == "question?"
        return [
            Chunk(
                chunk_id="a",
                document_sha256="a" * 64,
                pdf_page=1,
                printed_page=1,
                headings=[],
                text="some evidence",
            )
        ]


class Provider:
    def generate(self, request):
        assert "SECRET_GOLD" not in request.prompt and "SECRET_FACT" not in request.prompt
        if "sufficient" in request.json_schema["properties"]:
            return GenerationResult(model="test", content='{"sufficient": true}')
        return GenerationResult(
            model="test",
            content='{"claims":[{"text":"answer", "chunk_id":"a", "quote":"some evidence"}]}',
        )


def test_dev_capture_does_not_leak_gold() -> None:
    dataset, q = fixture_dataset()
    record = capture_dev_question(dataset, q, Retrieval(), Provider(), 4)
    assert record.retrieval_metrics.page_hit and record.answer.text == "answer"
    assert record.error_stage is None


def test_capture_records_provider_failure_and_rejects_holdout() -> None:
    dataset, q = fixture_dataset()

    class FailingProvider:
        def generate(self, request):
            raise ProviderError("private payload")

    record = capture_dev_question(dataset, q, Retrieval(), FailingProvider(), 4)
    assert record.error_stage == "generation" and record.error_type == "ProviderError"
    assert "private payload" not in record.model_dump_json()
    heldout, q = fixture_dataset("holdout")
    with pytest.raises(ValueError, match="development"):
        capture_dev_question(heldout, q, Retrieval(), Provider(), 4)


def test_schema2_capture_keeps_reference_metadata_out_of_model_and_retriever() -> None:
    old, original = fixture_dataset()
    question = original.model_copy(
        update={
            "category": "true_false",
            "group": "G1",
            "statement": "question?",
            "expected_label": "SECRET_LABEL",
            "grading_notes": "SECRET_NOTES",
        }
    )
    dataset = Dataset.model_validate(
        old.model_dump()
        | {
            "schema_version": "2.0",
            "split": "test",
            "questions": [question],
            "group_counts": {"G1": 1},
            "group_definitions": {"G1": "group"},
        }
    )

    class GuardedProvider(Provider):
        def generate(self, request):
            for secret in ("SECRET_GOLD", "SECRET_FACT", "SECRET_LABEL", "SECRET_NOTES"):
                assert secret not in request.prompt and secret not in request.system
            return super().generate(request)

    record = capture_dev_question(dataset, question, Retrieval(), GuardedProvider(), 4)
    assert record.error_stage is None and record.answer.text == "answer"


def test_schema2_unanswerable_capture_still_generates_without_page_metrics() -> None:
    old, original = fixture_dataset()
    question = original.model_copy(
        update={
            "category": "unanswerable",
            "answerable": False,
            "source": Source(document="doc.pdf", pdf_pages=[], printed_pages=[]),
        }
    )
    dataset = Dataset.model_validate(
        old.model_dump()
        | {
            "schema_version": "2.0",
            "split": "test",
            "questions": [question],
        }
    )
    record = capture_dev_question(dataset, question, Retrieval(), Provider(), 4)
    assert record.error_stage is None and record.answer.text == "answer"
    assert all(value is None for value in record.retrieval_metrics.model_dump().values())


def test_legacy_and_new_dev_splits_are_not_disjoint_holdout() -> None:
    legacy, _ = fixture_dataset()
    current = Dataset.model_validate(
        legacy.model_dump() | {"schema_version": "2.0", "split": "test"}
    )
    with pytest.raises(ValueError, match="different splits"):
        validate_disjoint(legacy, current)
