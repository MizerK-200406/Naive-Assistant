import pytest

from native_assistant.rag.embeddings import FastEmbedder


class FakeModel:
    def token_count(self, text):
        return 128 if text == "long" else 2

    def embed(self, texts, batch_size):
        import numpy as np

        return iter([np.array([1.0, 2.0]) for _ in texts])


def test_embedding_refuses_possible_truncation() -> None:
    adapter = FastEmbedder.__new__(FastEmbedder)
    adapter.dimension = 2
    adapter.max_tokens = 128
    adapter.model = FakeModel()
    assert adapter.embed_query("short") == [1.0, 2.0]
    with pytest.raises(ValueError, match="truncated"):
        adapter.embed_query("long")


def test_windows_cover_all_words_without_truncation() -> None:
    class CountingModel:
        def token_count(self, text):
            return len(text.split()) + 2

    adapter = FastEmbedder.__new__(FastEmbedder)
    adapter.max_tokens = 6
    adapter.model = CountingModel()
    text = "một hai ba bốn năm sáu bảy"
    windows = adapter.windows(text)
    assert " ".join(windows) == text
    assert all(adapter.model.token_count(window) < adapter.max_tokens for window in windows)
