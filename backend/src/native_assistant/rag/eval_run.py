"""Capture dev retrieval and generation with no reference answer in model inputs."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel

from native_assistant.ai.provider import LlmProvider, ProviderError
from native_assistant.rag.chunking import Chunk
from native_assistant.rag.evaluation import Dataset, Question, RetrievalMetrics, score_retrieval
from native_assistant.services.answer import Answer, answer_question
from native_assistant.services.rag import Retriever


class DevRecord(BaseModel):
    question_id: str
    captured_at: datetime
    retrieval: list[Chunk]
    retrieval_metrics: RetrievalMetrics | None
    answer: Answer | None
    error_stage: Literal["retrieval", "generation"] | None
    error_type: str | None


def retrieve_dev_question(
    dataset: Dataset, question: Question, retriever: Retriever, limit: int
) -> DevRecord:
    if not dataset.is_development:
        raise ValueError("Evaluation capture accepts only the development split")
    if not any(item == question for item in dataset.questions):
        raise ValueError("Question does not belong to dataset")
    if limit < 1:
        raise ValueError("Limit must be positive")
    captured = datetime.now(UTC)
    try:
        chunks = retriever.search(question.question, limit)
        if any(chunk.document_sha256 != dataset.source_sha256 for chunk in chunks):
            raise ValueError("Retrieved chunk does not match source")
        metrics = score_retrieval(question, chunks)
    except (ValueError, OSError, RuntimeError) as exc:
        return DevRecord(
            question_id=question.id,
            captured_at=captured,
            retrieval=[],
            retrieval_metrics=None,
            answer=None,
            error_stage="retrieval",
            error_type=type(exc).__name__,
        )
    return DevRecord(
        question_id=question.id,
        captured_at=captured,
        retrieval=chunks,
        retrieval_metrics=metrics,
        answer=None,
        error_stage=None,
        error_type=None,
    )


def _answer_record(question: Question, record: DevRecord, provider: LlmProvider) -> DevRecord:
    if record.error_stage:
        return record
    try:
        result = answer_question(question.question, record.retrieval, provider)
    except (ProviderError, ValueError, OSError, RuntimeError) as exc:
        return record.model_copy(
            update={"error_stage": "generation", "error_type": type(exc).__name__}
        )
    return record.model_copy(update={"answer": result})


def capture_dev_question(
    dataset: Dataset, question: Question, retriever: Retriever, provider: LlmProvider, limit: int
) -> DevRecord:
    record = retrieve_dev_question(dataset, question, retriever, limit)
    return _answer_record(question, record, provider)
