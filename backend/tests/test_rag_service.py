from native_assistant.ai.provider import GenerationResult
from native_assistant.rag.chunking import Chunk
from native_assistant.services.rag import RagService


class Retriever:
    def search(self, question, limit=4):
        return [
            Chunk(
                chunk_id="one",
                document_sha256="doc",
                pdf_page=3,
                printed_page=1,
                headings=[],
                text="Bầu trời màu xanh.",
            )
        ]


class Provider:
    def generate(self, request):
        if "sufficient" in request.json_schema["properties"]:
            return GenerationResult(model="fake", content='{"sufficient": true}')
        return GenerationResult(
            model="fake",
            content='{"claims": [{"text":"Màu xanh.", "chunk_id":"one", "quote":"màu xanh"}]}',
        )


def test_service_connects_retrieval_to_citations():
    result = RagService(Retriever(), Provider()).answer("Bầu trời màu gì?")
    assert result.text == "Màu xanh."
    assert result.citations[0].pdf_page == 3
