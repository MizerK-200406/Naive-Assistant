# RUBRIC.md — Evaluation Rubric for Party History RAG (PTIT 2021)

- **Version:** 1.0 (proposed, **pending user approval**)
- **Sole reference source:** `BAI GIANG LSĐ 2021.pdf` — *Lecture Notes on the History of the Communist Party of Vietnam*, Posts and Telecommunications Institute of Technology, 2021.
- **Development set:** `backend/eval/datasets/test.yaml` — schema 2.0, 40 questions (`T001`–`T040`), `split: test`, `usage: development_evaluation`.
- **Final test set:** `backend/eval/datasets/holdout.yaml` — 10 reserved questions, `split: holdout`, `usage: final_holdout_only`. Its contents were not inspected for this compatibility update.
- **Purpose:** Evaluate whether the RAG assistant answers **accurately according to the lecture content, covers all key points, provides verifiable citations, and does not fabricate facts**.

> The development set contains 35 answerable questions and five intentionally unanswerable questions (`T036`–`T040`). The A–E weights, threshold and blocking rules below remain unchanged and pending approval. They currently apply only to answerable questions. Dedicated refusal-scoring rules are not approved; numeric scoring of unanswerable questions is blocked. Dataset compatibility does not establish answer quality or refusal capability.

## 1. Standard Data Structure

Each YAML record contains the following fields:

| Field | Required | Meaning |
|---|---|---|
| `id` | Yes | Unique identifier, e.g., development `T001`. |
| `group` | Schema 2.0 | Development group `G1`–`G5`; evaluator metadata. |
| `chapter` | Yes | `nhap_mon`, `chuong_1`, `chuong_2`, `chuong_3`. |
| `difficulty` | Yes | `easy`, `medium`, `hard` as categorized during authoring. |
| `category` | Yes | Current dev categories: `citation_lookup`, `comparison`, `synthesis`, `true_false`, `unanswerable`. |
| `question` | Yes | The question submitted to the RAG system. |
| `gold_answer` | Yes | The standard answer based on the lecture content. |
| `required_facts` | Yes | List of independent points that must be semantically accurate. |
| `source.document` | Yes | Name of the source PDF. |
| `source.pdf_pages` | Yes | PDF page numbers **1-indexed** (the first page is the cover); empty for current unanswerable examples. |
| `source.printed_pages` | Yes | Corresponding printed page numbers; empty for current unanswerable examples. |
| `answerable` | Yes | Whether the question can be answered solely based on the source document. |
| `statement` | For true/false examples | Statement under evaluation; already included in current question text. |
| `expected_label` | For true/false examples | Evaluator-only reference label; never send to the answering model. |
| `grading_notes` | Optional | Evaluator-only notes; never send to the answering model. |

**Note on pagination:** For the source PDF, printed pages generally use the offset `printed_page = pdf_page - 2`; validate recorded labels against the extracted artifact instead of inferring evidence from this offset. When reading with a 0-indexed programming library, use `page_index = pdf_page - 1`.

`gold_answer` expresses the comprehensive answer; `required_facts` are granular points used to score **completeness**. The AI's response is not required to match word-for-word. An answer with equivalent meaning can still achieve the maximum score.

**Schema changes:** Schema 2.0 development uses `split: test`, metadata `group_counts`/`group_definitions`, and the question metadata above. `gold_answer` and nested `source.pdf_pages`/`source.printed_pages` remain. Preserve evaluator metadata without adding it to retrieval queries or answer prompts.

## 2. Evaluation Preparation

1. Index **only the source PDF content** into the retrieval system; **do not** index `test.yaml`, `holdout.yaml`, `gold_answer`, `required_facts`, expected labels, grading notes, or the rubric as knowledge documents for the assistant.
2. For each question, log `prediction` (the AI's response), the list of retrieved segments (`retrieved_chunks`), the citations provided by the AI (`predicted_citations`), model version, retrieval configuration, and timestamp.
3. Score based on **question + `gold_answer` + `required_facts` + original PDF pages + predicted answer**. Do not use the AI's own answer as self-verification.
4. When the system fails to retrieve sources, log a separate error (`retrieval_error`) and score the response based on actual data; do not award citation points automatically.
5. An automated evaluator may be used to suggest scores, but questions with borderline scores, incorrect dates, missing citations, or contradictions must be manually reviewed.

## 3. 100-Point Total Rubric

Score each criterion on an integer scale of **0–4**, then multiply by its weight. Criterion score = `(achieved_level / 4) * weight`.

| Code | Criterion | Weight | Evaluation Criteria |
|---|---|---:|---|
| A | **Historical Factual Accuracy** | 40 | Names, dates, figures, resolution/policy contents, and cause–effect relationships must match the PDF. |
| B | **Grounding and Source Citation** | 25 | Accurately cites the document and page actually containing the asserted information. |
| C | **Completeness of Required Facts** | 15 | Covers `required_facts`; equivalent phrasing is accepted. |
| D | **Non-Fabrication and Claim Control** | 15 | Does not add false or out-of-source historical information as if confirmed by the source. |
| E | **Clarity and Focus** | 5 | Answers directly, clearly, in the proper language, and addresses the prompt's requirements. |
| | **Total** | **100** | |

### A — Historical Factual Accuracy (0–4)

- **4:** All key facts are accurate and consistent with the document.
- **3:** Accurate in essence; phrasing is slightly imprecise without altering the meaning.
- **2:** Contains one inaccurate or confused key fact that significantly reduces accuracy.
- **1:** Contains multiple inaccurate key facts, though a partially correct element is recognizable.
- **0:** Completely wrong, reverses the core meaning, or fails to provide the required facts.

**Dates/years, document titles, historical figures, and roles distinguishing the two regions (North/South)** are considered key facts. For questions asking for a single date, providing the wrong date results in A = 0.

### B — Grounding and Source Citation (0–4)

- **4:** Accurately cites the document and **exact PDF page(s)** supporting all main assertions; verifiable by the reader.
- **3:** Provides accurate pages supporting the answer but misses a page for a minor point or lacks citation detail.
- **2:** Identifies the correct PDF, but page references are missing/unclear or include one non-corresponding reference.
- **1:** Mentions the source too generally, insufficient to verify specific content.
- **0:** No citations provided; or citations are non-existent/fabricated.

**Recommended format:** `BAI GIANG LSĐ 2021.pdf, PDF tr. 69 (trang in 67)`. Citations using printed page numbers are acceptable if clearly converted and verifiable. Citing every page in `source.pdf_pages` is not required if a single page fully substantiates everything the AI states.

### C — Completeness of Required Facts (0–4)

For each item in `required_facts`, mark `covered = true` when the information is answered **semantically accurately**. A point that appears with factual errors is counted as **not covered**.

Let `coverage = covered_facts_count / total_required_facts`:

- **4:** `coverage = 100%`.
- **3:** `75% <= coverage < 100%`.
- **2:** `50% <= coverage < 75%`.
- **1:** `0% < coverage < 50%`.
- **0:** `coverage = 0%`.

Do not score based on response length. For questions with only one required fact, C can only be 0 or 4.

### D — Non-Fabrication and Claim Control (0–4)

- **4:** No significant factual claims beyond the PDF evidence; no fabricated citations.
- **3:** Contains unnecessary minor details that do not affect the main point and are not falsely presented as cited from the source.
- **2:** Contains details unsupported by the PDF stated with high certainty, though without altering the main conclusion.
- **1:** Contains multiple ungrounded details or major inferences presented as facts from the lecture notes.
- **0:** Fabricates multiple key facts, uses fake citations, or deliberately presents unverified data as confirmed by the document.

If a question asks "according to the lecture notes," **the PDF content is the sole authority**. Do not alter content to match common external knowledge. If differences with external sources must be noted, separate them clearly and do not use them to replace `gold_answer`.

### E — Clarity and Focus (0–4)

- **4:** Direct, easy to understand, well-organized, without rambling.
- **3:** Clear, with minor redundancies or slight formatting flaws.
- **2:** Understandable, but wordy or poorly structured, making the answer hard to locate.
- **1:** Vague, hard to read, or significantly off-target from the prompt.
- **0:** Fails to answer the question or the text is incomprehensible.

## 4. Formula, Pass Threshold, and Blocking Rules

```text
score_100 = (A / 4) * 40
          + (B / 4) * 25
          + (C / 4) * 15
          + (D / 4) * 15
          + (E / 4) *  5

individual_pass = (
    score_100 >= 80
    and A >= 3
    and B >= 3
    and D >= 3
    and critical_error == false
)
```

**Critical error (`critical_error = true`):** Fabricating source/page citations, or misstating a central fact in a way that reverses the meaning of the answer (e.g., wrong single requested date, wrong key document title, confusing the most decisive vs. direct role). These cases **fail** regardless of how high the total score may be.

The **80/100 threshold and blocking conditions** are initial proposals requiring project owner approval before becoming official. They may be calibrated after trial scoring on answerable development questions in `test.yaml`; **do not adjust thresholds to achieve favorable results on the holdout set**.

## 5. Per-Question Result Logging Format

**Structural illustration** example, not an actual AI run result:

```yaml
question_id: Q001
prediction: "A political platform is a document outlining the goals, guidelines, tasks, and revolutionary methods during a specific period. [BAI GIANG LSĐ 2021.pdf, PDF tr. 6]"
score:
  factual_accuracy_A: 4
  citation_B: 4
  completeness_C: 4
  hallucination_D: 4
  clarity_E: 4
  total_100: 100.0
covered_facts: [true, true, true]
critical_error: false
passed: true
notes: "Simulated example to illustrate the scoring format."
```

Do not let an **LLM self-generate `covered_facts` and treat it as evidence**: the evaluator must compare each point against the gold answer and the PDF, and save audit traces for human verification.

## 6. Reporting Results by Split

- **Development (`test.yaml`):** For answerable questions, report mean `score_100`, `individual_pass` rate, mean scores for A–E, list of failed questions, and breakdowns by `chapter`, `difficulty`, `category`, and `group`. Identify excluded/unscored unanswerable examples explicitly; do not imply a complete 40-question score. These results may be used to refine retrieval/prompts/code.
- **Holdout (`holdout.yaml`):** Evaluate only after **freezing** the model, prompt, index, hyperparameters, and scoring thresholds. Report the mean score, number of passed questions `/10`, critical errors, and configuration details. Do not use holdout results for further tuning in the same cycle while claiming them as an independent test result.
- **Do not merge 40 dev + 10 holdout into a single score** when reporting performance on unseen data.
- Current dev includes five `answerable: false` examples. Preserve these records; dedicated scoring rules require separate approval. Capture actual model behavior without using the answerability label to force an answer or refusal. Retrieval page/evidence metrics for these examples are `null` (not applicable), excluded from numeric averages.

## 7. Pre-Run Validation Checks

- Development question count: `test.yaml` has exactly **40**, with 35 answerable and five unanswerable examples. The project reserves **10** holdout questions; verify that split only within the authorized final workflow, not while tuning development behavior.
- All `id` values are unique; no overlapping questions between the two splits.
- `gold_answer` and `required_facts` are non-empty.
- `source.document` matches the PDF filename; answerable questions have source pages within the 169-page PDF, and current unanswerable questions have empty page lists.
- Printed page numbers and PDF page numbers align; verify the exact **2021** edition document is used.
- Verify `source_sha256` matches the PDF under evaluation to prevent updating the document without updating answers.
- RAG system chunks retain document metadata and PDF page numbers, and strictly exclude gold answers from the YAML files.

## 8. Unaddressed Scope

The development YAML provides source labels for its 35 answerable questions and empty page lists for five unanswerable questions; another 10 questions are reserved as holdout. These labels **do not replace** building a *document index / vector index* across all 169 pages of the PDF for the RAG system. Verifying question source pages also does not prove that the entire PDF has been successfully chunked/indexed.

To complete the RAG milestone: build a dedicated document index, verify coverage across all content pages, measure the proportion of chunks with valid metadata, and test retrieving each source page prior to running the evaluation.

---

**Rubric status:** `DRAFT — PENDING USER APPROVAL`. Once the project owner approves the criteria/thresholds, change the status to `APPROVED`, lock the version, and make no further modifications during the holdout evaluation run.
