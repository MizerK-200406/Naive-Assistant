"""CPU FastEmbed adapter with a conservative no-truncation guard."""

from collections.abc import Sequence
from pathlib import Path

from fastembed import TextEmbedding

MODELS = {
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": (384, 128),
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": (768, 512),
}


class FastEmbedder:
    def __init__(self, model_name: str, cache_dir: Path) -> None:
        if model_name not in MODELS:
            raise ValueError("Unsupported embedding model")
        self.dimension, self.max_tokens = MODELS[model_name]
        self.model = TextEmbedding(
            model_name=model_name, cache_dir=str(cache_dir), cuda=False, threads=2
        )

    def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        for text in texts:
            if not text.strip():
                raise ValueError("Cannot embed empty text")
            # FastEmbed's tokenizer may itself truncate. Reject counts at the limit,
            # because such a count cannot distinguish an exact fit from truncation.
            if self.model.token_count(text) >= self.max_tokens:
                raise ValueError("Text may be truncated; split into smaller embedding windows")
        return [vector.tolist() for vector in self.model.embed(list(texts), batch_size=8)]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(texts)

    def windows(self, text: str) -> list[str]:
        """Split without losing words; each emitted window passes the token guard."""
        words = text.split()
        if not words:
            raise ValueError("Cannot embed empty text")
        result: list[str] = []
        current: list[str] = []
        for word in words:
            candidate = " ".join([*current, word])
            if self.model.token_count(candidate) >= self.max_tokens:
                if not current:
                    raise ValueError("Single word exceeds the embedding token limit")
                result.append(" ".join(current))
                current = [word]
                if self.model.token_count(word) >= self.max_tokens:
                    raise ValueError("Single word exceeds the embedding token limit")
            else:
                current.append(word)
        if current:
            result.append(" ".join(current))
        return result

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]
