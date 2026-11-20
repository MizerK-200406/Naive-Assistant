"""Run a development batch through the same retrieval and answer paths as the CLI."""

import hashlib
import json
import os
import re
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from multiprocessing import get_context
from pathlib import Path
from time import monotonic

import httpx

from native_assistant.ai import ollama
from native_assistant.ai.ollama import OllamaProvider
from native_assistant.rag import retrieval
from native_assistant.rag.eval_run import DevRecord, _answer_record, retrieve_dev_question
from native_assistant.rag.evaluation import Dataset, load_dataset
from native_assistant.services import answer


def local_model_digest(model: str) -> str:
    try:
        response = httpx.get("http://127.0.0.1:11434/api/tags", trust_env=False, timeout=5)
        response.raise_for_status()
        matches = [r["digest"] for r in response.json()["models"] if r["name"] == model]
    except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
        raise ValueError("Cannot verify installed local model") from exc
    if (
        len(matches) != 1
        or not isinstance(matches[0], str)
        or not re.fullmatch("[a-f0-9]{64}", matches[0])
    ):
        raise ValueError("Expected exactly one installed local model with a digest")
    return matches[0]


def _retrieve(
    dataset: Dataset, index_path: Path, model: str, cache: Path, limit: int
) -> list[DevRecord]:
    os.environ["HF_HUB_OFFLINE"] = "1"
    from native_assistant.rag.embeddings import FastEmbedder
    from native_assistant.rag.persistent_index import PersistentIndex

    index = PersistentIndex(index_path, FastEmbedder(model, cache), model)
    try:
        if {c.document_sha256 for c in index.chunks} != {dataset.source_sha256}:
            raise ValueError("Index source differs from dataset")
        return [retrieve_dev_question(dataset, q, index, limit) for q in dataset.questions]
    finally:
        index.close()


def _retrieve_in_worker(
    dataset: Dataset, index_path: Path, model: str, cache: Path, limit: int
) -> list[DevRecord]:
    # Release the embedding runtime and all native allocations before generation.
    with ProcessPoolExecutor(max_workers=1, mp_context=get_context("spawn")) as pool:
        return pool.submit(_retrieve, dataset, index_path, model, cache, limit).result()


def run_dev_batch(
    dataset_path: Path,
    index_path: Path,
    model: str,
    cache: Path,
    llm: str,
    limit: int,
    output: Path,
) -> None:
    dataset, dataset_hash = load_dataset(dataset_path)
    if not dataset.is_development:
        raise ValueError("Only development questions may be captured")
    if limit < 1:
        raise ValueError("Batch limit must be positive")
    if output.exists():
        raise ValueError("Output already exists")
    retrieved = _retrieve_in_worker(dataset, index_path, model, cache, limit)
    llm_hash = local_model_digest(llm)
    provider = OllamaProvider(llm, timeout=120)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:

        def write(value: dict) -> None:
            stream.write(json.dumps(value, ensure_ascii=False) + "\n")
            stream.flush()

        write(
            {
                "kind": "start",
                "split": dataset.split,
                "dataset_sha256": dataset_hash,
                "source_sha256": dataset.source_sha256,
                "llm_digest": llm_hash,
                "llm": llm,
                "embedding_model": model,
                "limit": limit,
                "created": datetime.now(UTC).isoformat(),
                "manifest_sha256": hashlib.sha256(
                    (index_path / "manifest.json").read_bytes()
                ).hexdigest(),
                "code_sha256": {
                    m.__name__: hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
                    for m in (answer, ollama, retrieval)
                },
            }
        )
        for question, record in zip(dataset.questions, retrieved, strict=True):
            started = monotonic()
            result = _answer_record(question, record, provider)
            write(
                {
                    "kind": "record",
                    "generation_elapsed_s": monotonic() - started,
                    **result.model_dump(mode="json"),
                }
            )
            print(
                question.id,
                result.answer.status if result.answer else result.error_stage,
                flush=True,
            )
        if local_model_digest(llm) != llm_hash:
            raise ValueError("Ollama model changed during capture")
        write({"kind": "complete", "records": len(dataset.questions), "llm_digest": llm_hash})
