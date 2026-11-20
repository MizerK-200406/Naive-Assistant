"""In-process keyword search and deterministic rank fusion."""

import re
import unicodedata
from collections.abc import Sequence
from typing import Protocol

from rank_bm25 import BM25Okapi

from native_assistant.rag.chunking import Chunk


class VectorSearch(Protocol):
    def search(self, question: str, limit: int = 20) -> list[str]: ...


def tokenize(text: str) -> list[str]:
    """Keep Vietnamese accents and numeric tokens; do not apply English stemming."""
    return re.findall(r"[^\W_]+", unicodedata.normalize("NFC", text).lower(), re.UNICODE)


def bm25_search(chunks: Sequence[Chunk], question: str, limit: int = 20) -> list[str]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    query = tokenize(question)
    if not chunks or not query:
        return []
    if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
        raise ValueError("Duplicate chunk IDs")
    corpus = [tokenize(" ".join([*chunk.headings, chunk.text])) for chunk in chunks]
    if not any(corpus):
        return []
    scores = BM25Okapi(corpus).get_scores(query)
    # Only include documents containing a query token; BM25 can return negative scores.
    query_set = set(query)
    ranked = sorted(
        (index for index, tokens in enumerate(corpus) if query_set.intersection(tokens)),
        key=lambda index: (-scores[index], chunks[index].chunk_id),
    )
    return [chunks[index].chunk_id for index in ranked[:limit]]


def reciprocal_rank_fusion(rankings: Sequence[Sequence[str]], limit: int, k: int = 60) -> list[str]:
    if limit <= 0 or k <= 0:
        raise ValueError("limit and k must be positive")
    scores: dict[str, float] = {}
    for ranking in rankings:
        seen: set[str] = set()
        for rank, item in enumerate(ranking, 1):
            if item in seen:
                raise ValueError("Duplicate ID in ranking")
            seen.add(item)
            scores[item] = scores.get(item, 0.0) + 1 / (k + rank)
    return sorted(scores, key=lambda item: (-scores[item], item))[:limit]


def hybrid_search(
    chunks: Sequence[Chunk],
    vector: VectorSearch,
    question: str,
    limit: int = 4,
    candidate_limit: int = 20,
) -> list[Chunk]:
    if not question.strip() or limit <= 0 or candidate_limit < limit:
        raise ValueError("Question and valid limits are required")
    by_id = {chunk.chunk_id: chunk for chunk in chunks}
    if len(by_id) != len(chunks):
        raise ValueError("Duplicate chunk IDs")
    keywords = bm25_search(chunks, question, candidate_limit)
    dense = vector.search(question, candidate_limit)
    if any(chunk_id not in by_id for chunk_id in dense):
        raise ValueError("Vector index does not match the chunk corpus")
    return [by_id[key] for key in reciprocal_rank_fusion([keywords, dense], limit)]
