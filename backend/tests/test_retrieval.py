import pytest

from native_assistant.rag.chunking import Chunk
from native_assistant.rag.retrieval import (
    bm25_search,
    hybrid_search,
    reciprocal_rank_fusion,
    tokenize,
)


def make_chunk(key: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=key, document_sha256="doc", pdf_page=1, printed_page=1, headings=[], text=text
    )


def test_keyword_matches_vietnamese_and_dates() -> None:
    chunks = [make_chunk("a", "Điện Biên Phủ 1954"), make_chunk("b", "Hà Nội 1945")]
    assert bm25_search(chunks, "Điện Biên 1954") == ["a"]
    assert tokenize("ĐIỆN") == tokenize("Điện")
    assert bm25_search(chunks, "không tồn tại") == []


def test_rrf_merges_and_rejects_duplicates() -> None:
    assert reciprocal_rank_fusion([["a", "b"], ["b", "c"]], 3)[0] == "b"
    with pytest.raises(ValueError, match="Duplicate"):
        reciprocal_rank_fusion([["a", "a"]], 3)


def test_hybrid_returns_original_chunks_and_rejects_stale_index() -> None:
    class Vector:
        def __init__(self, ids):
            self.ids = ids

        def search(self, question, limit=20):
            return self.ids

    chunks = [make_chunk("a", "Điện Biên 1954"), make_chunk("b", "Hà Nội")]
    assert hybrid_search(chunks, Vector(["b", "a"]), "Điện Biên", 2)[0] is chunks[0]
    with pytest.raises(ValueError, match="does not match"):
        hybrid_search(chunks, Vector(["stale"]), "Điện Biên")
