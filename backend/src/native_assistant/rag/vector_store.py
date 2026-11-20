"""Qdrant Local vector index with injectable embeddings."""

from collections.abc import Sequence
from typing import Protocol
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from native_assistant.rag.chunking import Chunk


class Embedder(Protocol):
    dimension: int

    def windows(self, text: str) -> list[str]: ...

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class VectorStore:
    def __init__(self, client: QdrantClient, embedder: Embedder, collection: str) -> None:
        self.client = client
        self.embedder = embedder
        self.collection = collection

    def create(self, chunks: Sequence[Chunk]) -> None:
        if not chunks:
            raise ValueError("Cannot index an empty corpus")
        if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
            raise ValueError("Duplicate chunk IDs")
        if self.client.collection_exists(self.collection):
            raise ValueError("Collection exists; use a new collection name")
        window_records = [
            (chunk.chunk_id, index, window)
            for chunk in chunks
            for index, window in enumerate(
                self.embedder.windows("\n".join([*chunk.headings, chunk.text]))
            )
        ]
        if not window_records or {item[0] for item in window_records} != {
            chunk.chunk_id for chunk in chunks
        }:
            raise ValueError("Each chunk must produce at least one window")
        texts = [item[2] for item in window_records]
        vectors = self.embedder.embed_documents(texts)
        if len(vectors) != len(texts) or any(len(v) != self.embedder.dimension for v in vectors):
            raise ValueError("Embedding dimensions or count do not match")
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=models.VectorParams(
                size=self.embedder.dimension, distance=models.Distance.COSINE
            ),
        )
        self.client.upsert(
            collection_name=self.collection,
            points=[
                models.PointStruct(
                    id=str(uuid5(NAMESPACE_URL, f"{chunk_id}:{index}")),
                    vector=vector,
                    payload={"chunk_id": chunk_id, "window": index},
                )
                for (chunk_id, index, _), vector in zip(window_records, vectors, strict=True)
            ],
            wait=True,
        )

    def search(self, question: str, limit: int = 20) -> list[str]:
        if limit <= 0 or not question.strip():
            raise ValueError("Question and positive limit are required")
        vector = self.embedder.embed_query(question)
        if len(vector) != self.embedder.dimension:
            raise ValueError("Query embedding dimension does not match")
        count = self.client.count(collection_name=self.collection, exact=True).count
        if not count:
            return []
        points = self.client.query_points(
            collection_name=self.collection, query=vector, limit=count, with_payload=True
        ).points
        # Qdrant returns windows in descending score order; first hit per chunk is its maximum.
        ranked: list[str] = []
        seen: set[str] = set()
        for point in points:
            if not point.payload or not isinstance(point.payload.get("chunk_id"), str):
                raise ValueError("Invalid vector index payload")
            chunk_id = point.payload["chunk_id"]
            if chunk_id not in seen:
                ranked.append(chunk_id)
                seen.add(chunk_id)
                if len(ranked) == limit:
                    break
        return ranked
