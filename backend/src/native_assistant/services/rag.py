"""Application boundary connecting retrieval and grounded generation."""

from typing import Protocol

from native_assistant.ai.provider import LlmProvider
from native_assistant.rag.chunking import Chunk
from native_assistant.services.answer import Answer, answer_question


class Retriever(Protocol):
    def search(self, question: str, limit: int = 4) -> list[Chunk]: ...


class RagService:
    def __init__(self, retriever: Retriever, provider: LlmProvider) -> None:
        self.retriever = retriever
        self.provider = provider

    def retrieve(self, question: str, limit: int = 4) -> list[Chunk]:
        if not question.strip() or limit < 1:
            raise ValueError("Question and positive limit are required")
        return self.retriever.search(question, limit)

    def answer(self, question: str, limit: int = 4) -> Answer:
        return answer_question(question, self.retrieve(question, limit), self.provider)
