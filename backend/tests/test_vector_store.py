import pytest
from qdrant_client import QdrantClient

from native_assistant.rag.chunking import Chunk
from native_assistant.rag.vector_store import VectorStore


class FakeEmbedder:
    dimension = 2

    def windows(self, text):
        return text.split("|")

    def embed_documents(self, texts):
        return [[1.0, 0.0] if "alpha" in text else [0.0, 1.0] for text in texts]

    def embed_query(self, text):
        return [1.0, 0.0] if "alpha" in text else [0.0, 1.0]


def test_local_index_and_existing_collection_protection() -> None:
    client = QdrantClient(":memory:")
    store = VectorStore(client, FakeEmbedder(), "test")
    chunks = [
        Chunk(
            chunk_id="a", document_sha256="x", pdf_page=1, printed_page=1, headings=[], text="alpha"
        ),
        Chunk(
            chunk_id="b", document_sha256="x", pdf_page=2, printed_page=2, headings=[], text="beta"
        ),
    ]
    store.create(chunks)
    assert store.search("alpha", 1) == ["a"]
    with pytest.raises(ValueError, match="exists"):
        store.create(chunks)
    client.close()


def test_deduplicates_windows_before_applying_chunk_limit() -> None:
    client = QdrantClient(":memory:")
    store = VectorStore(client, FakeEmbedder(), "windows")
    chunks = [
        Chunk(
            chunk_id="a",
            document_sha256="x",
            pdf_page=1,
            printed_page=1,
            headings=[],
            text="alpha|alpha|beta",
        ),
        Chunk(
            chunk_id="b", document_sha256="x", pdf_page=2, printed_page=2, headings=[], text="beta"
        ),
    ]
    store.create(chunks)
    assert store.search("alpha", 2) == ["a", "b"]
    client.close()
