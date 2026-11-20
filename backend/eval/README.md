# RAG evaluation

`datasets/test.yaml` is the development split: schema 2.0, `split: test`, `usage: development_evaluation`, 40 questions (`T001`–`T040`). It contains 35 answerable and five intentionally unanswerable questions. `datasets/holdout.yaml` is reserved for a final evaluation after configuration and scoring criteria are frozen; do not use it to select prompts, models, or retrieval settings. The holdout content was read during planning, and must not be described as fully blind.

`../../docs/RUBRIC.md` defines the proposed scoring rubric; its pass threshold remains draft. The source PDF is identified by the SHA-256 in the datasets. Do not index either dataset, its answers, or the rubric as assistant knowledge.

From `backend/`, validate the development dataset and stored page metadata without inference:

```sh
uv run rag eval-validate --dataset eval/datasets/test.yaml --pages .local/pages-full.json
```

The page artifact must be generated from the actual source PDF; its own hash must be checked against that file. Validation checks recorded hashes, page labels, dataset counts and unique IDs, not semantic correctness of gold answers or the visual layout of the PDF. Cross-split validation is available through `--other`, but is not part of iterative development; use synthetic holdout fixtures to test isolation without reading the real holdout.

For a fully reviewed and indexed development corpus, `rag eval-retrieval --dataset eval/datasets/test.yaml --index <index-path>` produces per-question page metrics. Page hits alone are not evidence of relevance. All page/evidence metrics are `null` (not applicable) for unanswerable questions; they must not be averaged as zeros or perfect scores. Optional evidence-group rubrics must supply the exact dataset hash, source hash, reviewer, and exactly one entry per answerable question. Omit unanswerable questions instead of inventing evidence groups for them. An absent rubric yields `null` evidence metrics.

## Fixed development retrieval baseline

The offline capture `.local/dev-retrieval-baseline-20261116T180523170513Z.json` contains all 40 current dev queries and their 160 retrieved chunks. Settings were held at MiniLM, top-k 4, candidate limit 20 and RRF constant 60; no defaults or index content changed. All 40 queries completed without errors. Only question text reached retrieval; answer keys and grading metadata were excluded.

| Group | Answerable queries | At least one labelled-page hit | Mean labelled-page coverage |
|---|---:|---:|---:|
| G1: citation lookup | 11 | 10/11 | 86.36% |
| G2: comparison | 8 | 8/8 | 65.83% |
| G3: synthesis | 8 | 8/8 | 48.07% |
| G4: true/false | 8 | 8/8 | 95.83% |
| Overall answerable | 35 | 34/35 | 75.08% |

Mean reciprocal rank is 0.9000 on those 35 queries. T002 is the only labelled-page miss; 18/35 queries cover every labelled page. Five unanswerable queries have not-applicable metrics and are excluded from these averages. Labelled-page coverage is neither semantic evidence sufficiency nor answer accuracy: a hit can contain only a heading or omit required context, and an adequate excerpt need not cover every labelled page.

The artifact records dataset/source/extraction/index/code/script hashes, package versions and hashes of the local embedding snapshot used for queries. Current embedding hashes do not retroactively prove the artifact identity used to build the older index; its manifest does not bind those model files. This is a development baseline, not a frozen configuration or a final evaluation. Machine evidence coverage remains `null` until a reviewed evidence-anchor rubric exists; a separate automated review packet may suggest gaps for human inspection without becoming official scoring.

The separate packet `.local/dev-retrieval-evidence-review-20261116T180835932738Z.json` contains an independent automated preliminary review: 13 answerable queries have excerpts supporting the full question/reference requirements, 19 have partial support, and three (T002, T007, T024) lack concrete requested answer information. Five unanswerable queries are not applicable. The packet retains 83 verbatim retrieved quotes and 14 source excerpts for audit; layout re-extraction on 76 relevant PDF pages matched the saved raw text, without visual verification. Main checked packet provenance, quote/page consistency and the counts, and spot-checked semantic judgments.

These are reference-completeness suggestions requiring human review, not answer scores or an approved evidence-coverage metric. In particular, a `partial` query may still permit a correct concise answer: T035 has enough evidence to refute the claim using the 2045 target, while missing an additional 2025 detail from the development reference. No answering model, refusal evaluation, numeric rubric grading or final acceptance is represented by this packet.

## Offline same-page context experiment

`.local/dev-neighbor-context-20261116T181543159319Z.json` compares the fixed baseline against a predefined context policy on all 40 queries, without reranking or new embedding calls. Preserve the four seed chunks in their original order; visit each seed's immediate corpus predecessor and successor, in seed-rank order; append unseen chunks only from the same document and PDF page. Limits are 12 chunks and 1,000 whitespace-delimited evidence-text units. Candidates that do not fit are skipped; oversized seeds would be preserved without additions. Original chunk text and provenance are retained separately, without concatenation or truncation. Corpus adjacency can cross a reviewed exclusion, so it is not a claim of uninterrupted source text.

| Cost across 40 queries | Baseline | Expanded |
|---|---:|---:|
| Evidence chunks | 160 | 299 |
| Mean chunks per query | 4 | 7.475 |
| Evidence whitespace units | 23,085 | 36,703 |
| Answer-input JSON UTF-8 bytes | 165,753 | 262,679 |

All page metrics are identical by design: the seeds and set of retrieved pages are unchanged. The experiment adds 139 chunks; 63 candidate visits are skipped for the whitespace budget, 67 for page boundaries and 51 for duplicate IDs. No query exceeds 999 whitespace units. These counts do not establish token usage or fit in Ollama's context window. This is a comparison with more context, not an equal-budget ranking improvement. No production configuration or index was changed and no answers were generated.

Tester and Main independently found six accepted neighbors on the other side of a reviewed exclusion: T006/PDF 53, T015/33, T017/80, T019/95, T034/80 and T036/31. Each retained chunk remains reviewed source text with its own citation identity; the intervening excluded text is not restored. The experiment does not establish continuity across those gaps. A production context selector needs a reviewed-fragment boundary guard before adoption; the fixed experiment was preserved rather than changed after observing results.

The independent preliminary comparison is `.local/dev-neighbor-context-review-20261116T181950450954Z.json`. Under the same full question/reference-completeness criterion as the baseline review, suggested counts change from 13 sufficient / 19 partial / 3 none to 21 sufficient / 13 partial / 1 none among 35 answerable questions; five unanswerable queries remain not applicable. Eight suggestions become sufficient (T007, T008, T018, T022, T028, T030, T031, T035), and T024 changes from none to partial. T002 still lacks the requested function list. The audit verifies 83 inherited and 24 new verbatim quotes. These suggestions need human review; the superset of evidence does not establish better generated answers under added noise, token-window safety or official acceptance. Machine evidence metrics remain null, and the prototype has not been integrated into production.

## Answer capture and draft scoring

`rag eval-score --dataset eval/datasets/test.yaml --assessment <assessment.yaml>` calculates the unchanged draft A–E rubric for answerable questions from human judgments, not from the model's self-assessment. The YAML must contain `question_id`, `reviewer`, integer scores `accuracy_a`, `citation_b`, `groundedness_d`, `clarity_e`, one boolean in `covered_facts` per required fact, and `critical_error`. Optional `notes` can record reasoning. The output is labelled `draft`; it is not official acceptance. Numeric scoring of unanswerable questions is refused until a dedicated rubric is approved. This command refuses the holdout split until a separate frozen final-evaluation workflow exists.

Once a reviewed corpus has been chunked and indexed, capture one dev example locally with:

```sh
uv run rag eval-capture --dataset eval/datasets/test.yaml --index <index-path> --question-id T001 --output .local/eval/t001.json
```

The record contains retrieved chunks, page metrics, response/citations or a sanitized error stage, and configuration hashes. Only question text and retrieved PDF evidence reach the answering model: gold answers, required facts, expected labels, grading notes and group definitions remain evaluator metadata. Unanswerable examples follow the same retrieval/generation path; their labels never force a refusal. Output is created exclusively: use a new path for another run. Model artifact digests are not recorded yet, so this is not a frozen or fully reproducible evaluation run. Capture, retrieval tuning and scoring refuse holdout before opening an index or invoking models.

For layout review, re-extract the PDF with the current `rag extract` before chunking; older page artifacts without `page_count` cannot pass the full-document chunking gate. For example:

```sh
uv run rag review-status --input .local/pages-full.json --review .local/review-sample.json
uv run rag inspect-pages --input .local/pages-full.json --pdf-pages 16 --offsets
```

Review status validates document and page hashes but does not verify the reviewer's visual judgment. The chunker requires the declared full consecutive page range and an explicit review of every page. A declared count is metadata from extraction, not independent proof that an artifact has not been altered.

### Full development capture

From `backend/`, run `rag eval-batch --dataset eval/datasets/test.yaml --index <index-path> --model <indexed-embedding-model> --limit 4 --output .local/dev-batch.jsonl`.
The embeddings must be cached locally. Use a new output path. Each JSONL record
contains retrieved evidence, page metrics, and the validated response or error
stage. The completion record is written only after verifying the local Ollama
tag digest again. Preserve incomplete files as partial runs. Prompt evaluation
and reference-based grading are separate steps.
