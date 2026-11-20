## Overview

Native Assistant targets offline desktop use on a CPU-only test machine with 8 GB of RAM, with a bundled model and an optional web demo.
The current milestone is local CLI question answering over one Vietnamese PDF, pending quality acceptance.

## Completed

- Reviewed all 169 PDF pages and indexed 657 chunks from 166 content pages, preserving source page references.
  Source PDF — `BAI GIANG LSĐ 2021.pdf`
  SHA-256 — `af67469a87f286e0f1da81c0258544488c1d83a953d7af283b2eed5c7f5d711d`
- The CLI supports search, local answers through Ollama, citation checks, and abstention when evidence is insufficient. MiniLM is the default embedding model.
- Evaluated 40 development questions using MPNet top-4 and `qwen3:4b`. Retrieval found at least one reference page for all 35 answerable questions. The system correctly abstained on all five unanswerable questions.
- The latest verification passed all 79 tests and both Ruff checks (lint and formatting).

## In Progress and Blockers

- Of the 35 answerable questions, the system answered 13, abstained on eight, and failed during generation on 14. Replaying those failures reproduced nine answers cut off at 768 tokens, three question echoes, and two non-verbatim quotations.
- Across seven reviewed multi-part questions, the index contains evidence for all 16 points missed by automated retrieval. Adding two to four evaluator-selected chunks per question supplied the missing evidence within the context budget. The evidence map is kept locally.
- A verbatim quotation can refer to the wrong event. Some chunks end mid-sentence, and some extracted words contain stray spaces.
- M6 awaits approval of the scoring rubric and abstention rules. The M7 final evaluation is pending. The final report must disclose that the 10 holdout questions were seen during planning.

## Next Steps

1. Test splitting multi-part questions into separate queries using only the question text. Compare evidence coverage and token cost against top-4 retrieval on all 40 development questions.
2. Use T012 and T034 to test generation when sufficient evidence is available. Check answer completeness, truncation, and whether each quotation supports its claim.
3. Approve the [rubric](docs/RUBRIC.md) and freeze the configuration using development results. Run the holdout once and review the answers manually.
