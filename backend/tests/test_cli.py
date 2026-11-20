import hashlib
import json
import subprocess
import sys

import pytest
import yaml


def test_cli_help() -> None:
    result = subprocess.run(["rag", "--help"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "Local document intelligence" in result.stdout


def test_package_import() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import native_assistant"], capture_output=True, check=False
    )
    assert result.returncode == 0


def test_heldout_cannot_be_used_for_retrieval_tuning(tmp_path) -> None:
    dataset = tmp_path / "holdout.yaml"
    dataset.write_text(
        "schema_version: '1.0'\ndataset: x\nsplit: holdout\nusage: final_holdout_only\nsource_document: x.pdf\nsource_edition: 2021\n"
        + "source_sha256: "
        + "a" * 64
        + "\n"
        "page_reference: pdf\ntotal_questions: 1\nquestions:\n"
        "- id: H1\n  chapter: c\n  difficulty: easy\n  question: q\n"
        "  category: definition\n  gold_answer: a\n  required_facts: [a]\n  answerable: true\n"
        "  source:\n    document: x.pdf\n    pdf_pages: [1]\n    printed_pages: [1]\n"
    )
    result = subprocess.run(
        ["rag", "eval-retrieval", "--dataset", str(dataset), "--index", str(tmp_path / "unused")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "Only the dev split" in result.stderr


@pytest.mark.parametrize("schema", ["1.0", "2.0"])
@pytest.mark.parametrize("command", ["eval-retrieval", "eval-capture", "eval-score", "eval-batch"])
def test_synthetic_holdout_is_rejected_before_opening_inputs_or_outputs(tmp_path, schema, command):
    dataset = tmp_path / "synthetic.yaml"
    dataset.write_text(
        f"schema_version: '{schema}'\ndataset: x\nsplit: holdout\n"
        "usage: final_holdout_only\nsource_document: x.pdf\nsource_edition: 2021\n"
        + "source_sha256: "
        + "a" * 64
        + "\n"
        "page_reference: pdf\ntotal_questions: 1\nquestions:\n"
        "- id: H1\n  chapter: c\n  difficulty: easy\n  question: q\n"
        "  category: definition\n  gold_answer: a\n  required_facts: [a]\n  answerable: true\n"
        "  source:\n    document: x.pdf\n    pdf_pages: [1]\n    printed_pages: [1]\n"
    )
    output = tmp_path / "output.json"
    unused = tmp_path / "does-not-exist"
    args = {
        "eval-retrieval": ["--index", str(unused)],
        "eval-capture": ["--index", str(unused), "--question-id", "H1", "--output", str(output)],
        "eval-score": ["--assessment", str(unused)],
        "eval-batch": ["--index", str(unused), "--output", str(output)],
    }[command]
    result = subprocess.run(
        ["rag", command, "--dataset", str(dataset), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "Only development questions" in result.stderr or "Only the dev split" in result.stderr
    assert not output.exists() and not unused.exists()


@pytest.fixture
def mixed_retrieval_cli(tmp_path, monkeypatch, capsys):
    from native_assistant import cli
    from native_assistant.rag import embeddings, persistent_index
    from native_assistant.rag.chunking import Chunk

    source_hash = "a" * 64
    question = {
        "id": "T1",
        "chapter": "c",
        "difficulty": "easy",
        "category": "citation_lookup",
        "question": "A question?",
        "gold_answer": "gold",
        "required_facts": ["fact"],
        "answerable": True,
        "source": {"document": "doc.pdf", "pdf_pages": [1], "printed_pages": [1]},
    }
    missing = question | {
        "id": "T2",
        "category": "unanswerable",
        "question": "An unrelated question?",
        "answerable": False,
        "source": {"document": "doc.pdf", "pdf_pages": [], "printed_pages": []},
    }
    dataset = {
        "schema_version": "2.0",
        "dataset": "x",
        "split": "test",
        "usage": "development_evaluation",
        "source_document": "doc.pdf",
        "source_edition": 2021,
        "source_sha256": source_hash,
        "page_reference": "pdf",
        "total_questions": 2,
        "questions": [question, missing],
    }
    path = tmp_path / "synthetic-dev.yaml"
    path.write_text(yaml.safe_dump(dataset), encoding="utf-8")
    entry = {"id": "T1", "groups": [{"alternatives": [{"pdf_page": 1, "excerpt": "evidence"}]}]}
    rubric = {
        "source_sha256": source_hash,
        "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "reviewed_by": "reviewer",
        "questions": [entry],
    }
    chunk = Chunk(
        chunk_id="chunk",
        document_sha256=source_hash,
        pdf_page=1,
        printed_page=1,
        headings=[],
        text="evidence",
    )

    class FakeIndex:
        def __init__(self, *args):
            self.chunks = [chunk]

        def search(self, question, limit):
            return [chunk]

        def close(self):
            pass

    monkeypatch.setattr(embeddings, "FastEmbedder", lambda *args: object())
    monkeypatch.setattr(persistent_index, "PersistentIndex", FakeIndex)

    def run(data):
        rubric_path = tmp_path / "synthetic-rubric.yaml"
        rubric_path.write_text(yaml.safe_dump(data), encoding="utf-8")
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "rag",
                "eval-retrieval",
                "--dataset",
                str(path),
                "--index",
                str(tmp_path / "fake"),
                "--rubric",
                str(rubric_path),
            ],
        )
        cli.main()
        return json.loads(capsys.readouterr().out)

    return run, rubric, entry


def test_schema2_cli_rubric_covers_only_answerable_questions(mixed_retrieval_cli):
    run, rubric, _ = mixed_retrieval_cli
    results = run(rubric)["results"]
    assert results[0]["id"] == "T1" and results[0]["evidence_complete"] is True
    assert results[1]["id"] == "T2"
    assert all(value is None for key, value in results[1].items() if key != "id")


@pytest.mark.parametrize(
    "kind", ["missing", "unanswerable", "unknown", "duplicate", "dataset_hash", "source_hash"]
)
def test_schema2_cli_rejects_invalid_rubric(mixed_retrieval_cli, kind):
    run, rubric, entry = mixed_retrieval_cli
    if kind == "missing":
        rubric["questions"] = []
    elif kind in {"unanswerable", "unknown"}:
        rubric["questions"].append(entry | {"id": "T2" if kind == "unanswerable" else "T3"})
    elif kind == "duplicate":
        rubric["questions"].append(entry)
    elif kind == "dataset_hash":
        rubric["dataset_sha256"] = "b" * 64
    else:
        rubric["source_sha256"] = "b" * 64
    with pytest.raises(SystemExit) as exc:
        run(rubric)
    assert exc.value.code == 1


@pytest.mark.parametrize("digest_changes", [False, True])
def test_dev_batch_checkpoints_every_question_and_checks_model(
    mixed_retrieval_cli, tmp_path, monkeypatch, digest_changes
):
    from native_assistant.ai.provider import GenerationResult
    from native_assistant.rag import dev_batch

    index = tmp_path / "batch-index"
    index.mkdir()
    (index / "manifest.json").write_text("{}")
    output = tmp_path / "batch.jsonl"
    monkeypatch.setattr(dev_batch, "_retrieve_in_worker", dev_batch._retrieve)
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    digests = iter(["a" * 64, ("b" if digest_changes else "a") * 64])
    monkeypatch.setattr(dev_batch, "local_model_digest", lambda _: next(digests))

    class OfflineProvider:
        def __init__(self, *args, **kwargs):
            pass

        def generate(self, request):
            data = json.loads(request.prompt)
            assert set(data) == {"question", "evidence"}
            assert data["evidence"] == [{"chunk_id": "chunk", "text": "evidence"}]
            return GenerationResult(model="mock", content='{"sufficient":false}')

    monkeypatch.setattr(dev_batch, "OllamaProvider", OfflineProvider)
    args = (tmp_path / "synthetic-dev.yaml", index, "fake", tmp_path, "mock", 4, output)
    if digest_changes:
        with pytest.raises(ValueError, match="changed"):
            dev_batch.run_dev_batch(*args)
    else:
        dev_batch.run_dev_batch(*args)
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert [r["question_id"] for r in rows if r["kind"] == "record"] == ["T1", "T2"]
    assert (rows[-1]["kind"] == "complete") == (not digest_changes)
    with pytest.raises(ValueError, match="exists"):
        dev_batch.run_dev_batch(*args)
