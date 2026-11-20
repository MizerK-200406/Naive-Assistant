# Native Assistant — completed development milestones

These milestones summarize completed work evidenced by the source and local artifacts.
The workspace has no accessible Git history. Dates refer to saved runs and handoffs.

| Milestone | Completed work | Evidence |
|---|---|---|
| Dev evaluation compatibility, by 2026-11-16 | Added schema 2.0 support, split isolation, source validation, null retrieval metrics for unanswerable questions and regression tests for citation failures. | `backend/src/native_assistant/rag/evaluation.py`, `backend/tests/test_evaluation.py`, `backend/tests/test_answer.py` |
| Retrieval baseline, 2026-11-16 | Measured MiniLM top-4 on all 40 dev questions. The trace located T002's source in the corpus and isolated a ranking miss. | `backend/.local/dev-retrieval-baseline-20261116T180523170513Z.json` |
| Reviewed neighbors, 2026-11-19 | An experimental same-fragment guard reduced six cross-exclusion additions to zero. An offline replay verified seed order and page metrics on all 40 queries. | `backend/.local/dev-neighbor-context-guarded-20261118T203253585716Z.json` |
| Token fit, 2026-11-19 | Measured all three possible request stages. Every guarded prompt fit the 4,096-token window with 768 tokens reserved for output. | `backend/.local/dev-guarded-token-fit-20261118T204041526218Z.json` |
| Paired live diagnostic, 2026-11-19 | Compared four fixed questions under both context policies. Guarded expansion failed on all four selected runs. A duplicate interrupted the primary run; latency comparisons were excluded. | `backend/.local/dev-guarded-live-20261118T211306148371Z.json`, `backend/.local/dev-guarded-live-recovery-20261118T211650026722Z.json` |
| Full dev verification, 2026-11-19 | Reproduced extraction/chunking, compared four retrieval settings, built a snapshot-bound MPNet index and captured all 40 dev answers/errors. The clean batch separated retrieval and generation after an earlier OOM. A review packet and a technical freeze candidate were produced. | [Dev review packet](../backend/.local/dev-human-review-mpnet-k4-20261119.md), [candidate manifest](../backend/.local/m7-candidate-native-assistant-v1.json) |
