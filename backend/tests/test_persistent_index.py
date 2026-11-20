from pathlib import Path

import pytest

from native_assistant.rag.chunking import Chunk
from native_assistant.rag.persistent_index import PersistentIndex, create_index


class Embedder:
    dimension = 2

    def windows(self, text):
        return [text]

    def embed_documents(self, texts):
        return [[1.0, 0.0] if "alpha" in text else [0.0, 1.0] for text in texts]

    def embed_query(self, text):
        return [1.0, 0.0] if "alpha" in text else [0.0, 1.0]


def test_persist_reopen_and_reject_wrong_model(tmp_path: Path) -> None:
    chunks = [
        Chunk(
            chunk_id="a",
            document_sha256="hash",
            pdf_page=1,
            printed_page=1,
            headings=[],
            text="alpha",
        )
    ]
    path = tmp_path / "index"
    create_index(path, chunks, Embedder(), "fake-v1")
    with pytest.raises(ValueError, match="model"):
        PersistentIndex(path, Embedder(), "other")
    index = PersistentIndex(path, Embedder(), "fake-v1")
    assert index.search("alpha")[0].chunk_id == "a"
    index.close()
    with pytest.raises(ValueError, match="closed"):
        index.search("alpha")
    (path / "chunks.json").write_text("[]")
    with pytest.raises(ValueError, match="hash"):
        PersistentIndex(path, Embedder(), "fake-v1")


def test_incomplete_index_is_not_opened(tmp_path: Path) -> None:
    path = tmp_path / "partial"
    path.mkdir()
    with pytest.raises(FileNotFoundError):
        PersistentIndex(path, Embedder(), "fake")
    with pytest.raises(FileExistsError):
        create_index(path, [], Embedder(), "fake")


def test_rejects_vector_payload_for_another_corpus(tmp_path: Path) -> None:
    from qdrant_client import QdrantClient

    path = tmp_path / "index"
    chunk = Chunk(
        chunk_id="a", document_sha256="hash", pdf_page=1, printed_page=1, headings=[], text="alpha"
    )
    create_index(path, [chunk], Embedder(), "fake-v1")
    client = QdrantClient(path=str(path / "qdrant"))
    points, _ = client.scroll("chunks", limit=1)
    client.set_payload("chunks", payload={"chunk_id": "stale"}, points=[points[0].id], wait=True)
    client.close()
    with pytest.raises(ValueError, match="payload"):
        PersistentIndex(path, Embedder(), "fake-v1")
