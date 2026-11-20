"""Command-line entry point for local document intelligence."""

import argparse
import json
import sys
from pathlib import Path

import yaml
from pydantic import TypeAdapter, ValidationError
from pypdf.errors import PdfReadError

from native_assistant.ai.provider import ProviderError
from native_assistant.rag.chunking import Chunk, build_chunks
from native_assistant.rag.extraction import ExtractedDocument, extract_pdf
from native_assistant.rag.review import DocumentReview, Exclusion, add_page_review, validate_review

DEFAULT_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main() -> None:
    parser = argparse.ArgumentParser(prog="rag", description="Local document intelligence tools.")
    commands = parser.add_subparsers(dest="command")
    extract = commands.add_parser("extract", help="Extract PDF pages into a local JSON artifact")
    extract.add_argument("--pdf", type=Path, required=True)
    extract.add_argument("--output", type=Path, default=Path(".local/pages.json"))
    inspect = commands.add_parser("inspect-pages", help="Show raw and cleaned text for PDF pages")
    inspect.add_argument("--input", type=Path, default=Path(".local/pages.json"))
    inspect.add_argument(
        "--pdf-pages", required=True, help="Comma-separated 1-based PDF page numbers"
    )
    chunk = commands.add_parser("chunk", help="Chunk a fully reviewed extraction")
    chunk.add_argument("--input", type=Path, required=True)
    chunk.add_argument("--review", type=Path, required=True)
    chunk.add_argument("--output", type=Path, required=True)
    chunk.add_argument("--size", type=int, default=160)
    review = commands.add_parser("review-page", help="Record an explicitly reviewed page")
    review.add_argument("--input", type=Path, required=True)
    review.add_argument("--review", type=Path, help="Previous review artifact, if any")
    review.add_argument("--output", type=Path, required=True)
    review.add_argument("--page", type=int, required=True)
    review.add_argument(
        "--exclude", nargs=3, action="append", metavar=("START", "END", "REASON"), default=[]
    )
    status = commands.add_parser("review-status", help="List reviewed and outstanding PDF pages")
    status.add_argument("--input", type=Path, required=True)
    status.add_argument("--review", type=Path, required=True)
    inspect.add_argument("--offsets", action="store_true", help="Show clean-text line offsets")
    validate = commands.add_parser(
        "eval-validate", help="Validate dataset without running inference"
    )
    validate.add_argument("--dataset", type=Path, required=True)
    validate.add_argument("--pages", type=Path, help="Extracted source pages to verify references")
    validate.add_argument("--other", type=Path, help="Other split to verify disjoint questions")
    evaluate = commands.add_parser("eval-retrieval", help="Evaluate retrieval on the dev split")
    evaluate.add_argument("--dataset", type=Path, required=True)
    evaluate.add_argument("--index", type=Path, required=True)
    evaluate.add_argument("--model", default=DEFAULT_EMBEDDING)
    evaluate.add_argument("--model-cache", type=Path, default=Path(".local/models"))
    evaluate.add_argument("--rubric", type=Path)
    evaluate.add_argument("--limit", type=int, default=4)
    scoring = commands.add_parser("eval-score", help="Calculate draft score from human assessment")
    scoring.add_argument("--dataset", type=Path, required=True)
    scoring.add_argument("--assessment", type=Path, required=True)
    capture = commands.add_parser("eval-capture", help="Capture one development question")
    capture.add_argument("--dataset", type=Path, required=True)
    capture.add_argument("--index", type=Path, required=True)
    capture.add_argument("--question-id", required=True)
    capture.add_argument("--output", type=Path, required=True)
    capture.add_argument("--model", default=DEFAULT_EMBEDDING)
    capture.add_argument("--model-cache", type=Path, default=Path(".local/models"))
    capture.add_argument("--llm-model", default="qwen3:4b")
    capture.add_argument("--limit", type=int, default=4)
    batch = commands.add_parser("eval-batch", help="Capture all development questions locally")
    batch.add_argument("--dataset", type=Path, required=True)
    batch.add_argument("--index", type=Path, required=True)
    batch.add_argument("--model", default=DEFAULT_EMBEDDING)
    batch.add_argument("--model-cache", type=Path, default=Path(".local/models"))
    batch.add_argument("--llm-model", default="qwen3:4b")
    batch.add_argument("--limit", type=int, default=4)
    batch.add_argument("--output", type=Path, required=True)
    for name in ("index", "search", "ask"):
        command = commands.add_parser(name, help=f"{name.title()} a local reviewed corpus")
        command.add_argument("--index", type=Path, required=True)
        command.add_argument("--model", default=DEFAULT_EMBEDDING)
        command.add_argument("--model-cache", type=Path, default=Path(".local/models"))
        if name == "index":
            command.add_argument("--chunks", type=Path, required=True)
        else:
            command.add_argument("--question", required=True)
            command.add_argument("--limit", type=int, default=4)
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return
    try:
        if args.command == "eval-batch":
            from native_assistant.rag.dev_batch import run_dev_batch

            run_dev_batch(
                args.dataset,
                args.index,
                args.model,
                args.model_cache,
                args.llm_model,
                args.limit,
                args.output,
            )
        elif args.command == "extract":
            document = extract_pdf(args.pdf)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as output:
                output.write(document.model_dump_json(indent=2))
            warned = sum(bool(page.warnings) for page in document.pages)
            print(
                f"Extracted {len(document.pages)} pages to {args.output}; {warned} pages with warnings."
            )
        elif args.command in {"eval-validate", "eval-retrieval", "eval-score", "eval-capture"}:
            from native_assistant.rag.evaluation import (
                HumanAssessment,
                Rubric,
                load_dataset,
                score_assessment,
                score_retrieval,
                validate_disjoint,
                validate_sources,
            )

            dataset, digest = load_dataset(args.dataset)
            if args.command == "eval-validate":
                if args.pages:
                    document = ExtractedDocument.model_validate_json(args.pages.read_bytes())
                    validate_sources(dataset, document)
                if args.other:
                    other, _ = load_dataset(args.other)
                    validate_disjoint(dataset, other)
                print(
                    json.dumps(
                        {
                            "dataset": dataset.dataset,
                            "split": dataset.split,
                            "questions": len(dataset.questions),
                            "sha256": digest,
                            "source_verified": bool(args.pages),
                            "splits_disjoint": bool(args.other),
                        }
                    )
                )
            elif args.command == "eval-capture":
                import hashlib
                import inspect

                from native_assistant.ai.ollama import OllamaProvider
                from native_assistant.rag.embeddings import FastEmbedder
                from native_assistant.rag.eval_run import capture_dev_question
                from native_assistant.rag.persistent_index import PersistentIndex
                from native_assistant.services import answer as answer_module

                if not dataset.is_development:
                    raise ValueError("Only development questions may be captured")
                question = next((q for q in dataset.questions if q.id == args.question_id), None)
                if question is None:
                    raise ValueError("Question ID not found")
                if args.output.exists():
                    raise ValueError("Output already exists")
                manifest_bytes = (args.index / "manifest.json").read_bytes()
                index = PersistentIndex(
                    args.index, FastEmbedder(args.model, args.model_cache), args.model
                )
                try:
                    if {chunk.document_sha256 for chunk in index.chunks} != {dataset.source_sha256}:
                        raise ValueError("Dataset does not match the indexed source")
                    record = capture_dev_question(
                        dataset, question, index, OllamaProvider(args.llm_model), args.limit
                    )
                finally:
                    index.close()
                output = {
                    "split": dataset.split,
                    "dataset_sha256": digest,
                    "source_sha256": dataset.source_sha256,
                    "index_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                    "embedding_model": args.model,
                    "llm_model": args.llm_model,
                    "model_digests": None,
                    "top_k": args.limit,
                    "answer_code_sha256": hashlib.sha256(
                        inspect.getsource(answer_module).encode()
                    ).hexdigest(),
                    "record": record.model_dump(mode="json"),
                }
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with args.output.open("x", encoding="utf-8") as file:
                    json.dump(output, file, ensure_ascii=False, indent=2)
                if record.error_stage:
                    raise ValueError(f"Capture failed at {record.error_stage}; recorded in output")
                print(
                    f"Captured {question.id} to {args.output}; model digests are not yet recorded."
                )
            elif args.command == "eval-score":
                if not dataset.is_development:
                    raise ValueError(
                        "Only the dev split may be scored before the frozen final evaluation"
                    )
                assessment = HumanAssessment.model_validate(
                    yaml.safe_load(args.assessment.read_bytes())
                )
                question = next(
                    (q for q in dataset.questions if q.id == assessment.question_id), None
                )
                if question is None:
                    raise ValueError("Assessment question ID not found")
                print(score_assessment(question, assessment).model_dump_json(indent=2))
            else:
                if not dataset.is_development:
                    raise ValueError("Only the dev split may be used for retrieval tuning")
                from native_assistant.rag.embeddings import FastEmbedder
                from native_assistant.rag.persistent_index import PersistentIndex

                rubric = (
                    Rubric.model_validate(yaml.safe_load(args.rubric.read_bytes()))
                    if args.rubric
                    else None
                )
                if rubric and (
                    rubric.dataset_sha256 != digest
                    or {x.id for x in rubric.questions}
                    != {x.id for x in dataset.questions if x.answerable}
                ):
                    raise ValueError("Rubric dataset hash or question IDs do not match")
                index = PersistentIndex(
                    args.index, FastEmbedder(args.model, args.model_cache), args.model
                )
                try:
                    if {chunk.document_sha256 for chunk in index.chunks} != {dataset.source_sha256}:
                        raise ValueError("Dataset does not match the indexed source")
                    if rubric and {chunk.document_sha256 for chunk in index.chunks} != {
                        rubric.source_sha256
                    }:
                        raise ValueError("Rubric does not match the indexed source")
                    rubrics = {item.id: item for item in rubric.questions} if rubric else {}
                    results = [
                        {
                            "id": item.id,
                            **score_retrieval(
                                item, index.search(item.question, args.limit), rubrics.get(item.id)
                            ).model_dump(),
                        }
                        for item in dataset.questions
                    ]
                    print(
                        json.dumps(
                            {
                                "split": dataset.split,
                                "dataset_sha256": digest,
                                "k": args.limit,
                                "rubric_reviewer": rubric.reviewed_by if rubric else None,
                                "results": results,
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                finally:
                    index.close()
        elif args.command == "review-status":
            document = ExtractedDocument.model_validate_json(args.input.read_bytes())
            review = DocumentReview.model_validate_json(args.review.read_bytes())
            validate_review(document, review)
            reviewed = {entry.pdf_page for entry in review.pages}
            print(
                json.dumps(
                    {
                        "source_sha256": document.sha256,
                        "declared_pages": document.page_count,
                        "reviewed": sorted(reviewed),
                        "remaining": [
                            page.pdf_page
                            for page in document.pages
                            if page.pdf_page not in reviewed
                        ],
                    },
                    indent=2,
                )
            )
        elif args.command == "review-page":
            document = ExtractedDocument.model_validate_json(args.input.read_text(encoding="utf-8"))
            current = (
                DocumentReview.model_validate_json(args.review.read_text(encoding="utf-8"))
                if args.review
                else DocumentReview(source_sha256=document.sha256, pages=[])
            )
            excluded = [Exclusion(start=int(a), end=int(b), reason=c) for a, b, c in args.exclude]
            updated = add_page_review(document, current, args.page, excluded)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as output:
                output.write(updated.model_dump_json(indent=2))
            print(f"Reviewed {len(updated.pages)} of {len(document.pages)} pages.")
        elif args.command in {"index", "search", "ask"}:
            from native_assistant.ai.ollama import OllamaProvider
            from native_assistant.rag.embeddings import FastEmbedder
            from native_assistant.rag.persistent_index import PersistentIndex, create_index
            from native_assistant.services.rag import RagService

            embedder = FastEmbedder(args.model, args.model_cache)
            if args.command == "index":
                chunks = TypeAdapter(list[Chunk]).validate_json(args.chunks.read_bytes())
                create_index(args.index, chunks, embedder, args.model)
                print(f"Indexed {len(chunks)} chunks.")
            else:
                index = PersistentIndex(args.index, embedder, args.model)
                try:
                    if args.command == "search":
                        print(
                            TypeAdapter(list[Chunk])
                            .dump_json(index.search(args.question, args.limit), indent=2)
                            .decode()
                        )
                    else:
                        print(
                            RagService(index, OllamaProvider())
                            .answer(args.question, args.limit)
                            .model_dump_json(indent=2)
                        )
                finally:
                    index.close()
        elif args.command == "chunk":
            document = ExtractedDocument.model_validate_json(args.input.read_text(encoding="utf-8"))
            review = DocumentReview.model_validate_json(args.review.read_text(encoding="utf-8"))
            chunks = build_chunks(document, review, args.size)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("xb") as output:
                output.write(TypeAdapter(list[Chunk]).dump_json(chunks, indent=2))
            print(f"Created {len(chunks)} chunks in {args.output}.")
        else:
            document = ExtractedDocument.model_validate_json(args.input.read_text(encoding="utf-8"))
            numbers = [int(value) for value in args.pdf_pages.split(",")]
            if not numbers or any(number < 1 or number > len(document.pages) for number in numbers):
                raise ValueError("Page number outside document")
            for number in numbers:
                page = document.pages[number - 1]
                print(
                    f"\nPDF {number}; printed {page.printed_page}; "
                    f"layout: {page.layout_review}; warnings: {page.warnings}"
                )
                print(f"--- RAW ---\n{page.raw_text}\n--- CLEAN ---\n{page.clean_text}")
                if args.offsets:
                    offset = 0
                    for line in page.clean_text.splitlines(keepends=True):
                        print(f"[{offset}:{offset + len(line)}] {line.rstrip()}")
                        offset += len(line)
    except (
        OSError,
        ValueError,
        ValidationError,
        PdfReadError,
        ProviderError,
        yaml.YAMLError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
