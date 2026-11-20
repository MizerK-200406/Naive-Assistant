"""Persistent local vector index with explicit completion and identity checks."""

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, Field, TypeAdapter
from qdrant_client import QdrantClient

from native_assistant.rag.chunking import Chunk
from native_assistant.rag.retrieval import hybrid_search
from native_assistant.rag.vector_store import Embedder, VectorStore

COLLECTION = "chunks"


class Manifest(BaseModel):
    version: int = 1
    model_name: str = Field(min_length=1)
    dimension: int = Field(gt=0)
    corpus_sha256: str
    chunks: int = Field(gt=0)
    windows: int = Field(gt=0)


def corpus_bytes(chunks: list[Chunk]) -> bytes:
    return json.dumps(
        [chunk.model_dump(mode="json") for chunk in chunks],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def create_index(path: Path, chunks: list[Chunk], embedder: Embedder, model_name: str) -> None:
    if not model_name.strip():
        raise ValueError("Model name required")
    path.mkdir(parents=True, exist_ok=False)
    client = QdrantClient(path=str(path / "qdrant"))
    try:
        store = VectorStore(client, embedder, COLLECTION)
        store.create(chunks)
        windows = client.count(collection_name=COLLECTION, exact=True).count
    finally:
        client.close()
    data = corpus_bytes(chunks)
    manifest = Manifest(
        model_name=model_name,
        dimension=embedder.dimension,
        corpus_sha256=hashlib.sha256(data).hexdigest(),
        chunks=len(chunks),
        windows=windows,
    )
    (path / "chunks.json").write_bytes(data)
    # The manifest is the completion marker. Exclusive create avoids replacing data.
    with (path / "manifest.json").open("x", encoding="utf-8") as file:
        file.write(manifest.model_dump_json(indent=2))


class PersistentIndex:
    def __init__(self, path: Path, embedder: Embedder, model_name: str) -> None:
        self.client: QdrantClient | None = None
        manifest = Manifest.model_validate_json(
            (path / "manifest.json").read_text(encoding="utf-8")
        )
        if (
            manifest.version != 1
            or manifest.model_name != model_name
            or manifest.dimension != embedder.dimension
        ):
            raise ValueError("Index model or format does not match")
        data = (path / "chunks.json").read_bytes()
        if hashlib.sha256(data).hexdigest() != manifest.corpus_sha256:
            raise ValueError("Index corpus hash does not match")
        self.chunks = TypeAdapter(list[Chunk]).validate_json(data)
        if len(self.chunks) != manifest.chunks or len({c.chunk_id for c in self.chunks}) != len(
            self.chunks
        ):
            raise ValueError("Index chunk count or IDs do not match")
        if not (path / "qdrant").is_dir():
            raise ValueError("Index collection missing or incomplete")
        client = QdrantClient(path=str(path / "qdrant"))
        try:
            if (
                not client.collection_exists(COLLECTION)
                or client.count(COLLECTION, exact=True).count != manifest.windows
            ):
                raise ValueError("Index collection missing or incomplete")
            expected_ids = {chunk.chunk_id for chunk in self.chunks}
            found: set[tuple[str, int]] = set()
            offset = None
            while True:
                points, offset = client.scroll(
                    COLLECTION, limit=256, offset=offset, with_payload=True, with_vectors=False
                )
                for point in points:
                    payload = point.payload or {}
                    chunk_id, window = payload.get("chunk_id"), payload.get("window")
                    if (
                        not isinstance(chunk_id, str)
                        or chunk_id not in expected_ids
                        or not isinstance(window, int)
                        or isinstance(window, bool)
                        or window < 0
                        or (chunk_id, window) in found
                    ):
                        raise ValueError("Index vector payload does not match corpus")
                    found.add((chunk_id, window))
                if offset is None:
                    break
            if {chunk_id for chunk_id, _ in found} != expected_ids:
                raise ValueError("Index vector payload does not cover corpus")
        except Exception:
            client.close()
            raise
        self.client = client
        self.store = VectorStore(client, embedder, COLLECTION)

    def search(self, question: str, limit: int = 4) -> list[Chunk]:
        if self.client is None:
            raise ValueError("Index is closed")
        return hybrid_search(
            self.chunks, self.store, question, limit=limit, candidate_limit=max(20, limit)
        )

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
