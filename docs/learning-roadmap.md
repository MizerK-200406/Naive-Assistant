# Lộ trình học AI Engineer (miễn phí) gắn với Naive-Assistant

Cập nhật: 2026-11-11. Thay thế bản PDF "Lộ trình AI Engineer miễn phí" (10/11/2026).
Nguồn khung: repo [Ultimate-AI-Engineer-Roadmap-2026](https://github.com/PrinceSinghhub/Ultimate-AI-Engineer-Roadmap-2026) (số mục như 8.5, 12.9 là số mục trong README của repo).

## 0. Cách dùng

- **Cột sống là Naive-Assistant** (`docs/plan.md`). Mỗi giai đoạn học trùng với một giai đoạn của dự án. Không làm dự án thứ hai.
- **30% học, 70% build.** Chỉ học thứ cần cho giai đoạn đang làm, kiểm chứng bằng chính dự án.
- **Giả định thời gian:** khoảng 3 giờ/ngày, 6 ngày/tuần (~18 giờ/tuần). Nếu chỉ có 10 giờ/tuần thì nhân đôi số tuần.
- **Cổng chuyển giai đoạn:** chỉ sang giai đoạn sau khi đạt dòng "Xong khi". Tick `[x]` ngay trong file này.
- **Khái niệm trước, công cụ sau.** Công cụ đổi rất nhanh. Mỗi công cụ bạn chọn phải có một file ngắn trong `docs/decisions/` ghi lý do và ngày kiểm tra.

## 1. Bạn đang ở đâu

| | Nội dung |
|---|---|
| Đã học (lý thuyết) | API, git/GitHub, uv, LLM application, Transformers, tool calling, AI agents, MCP |
| Chưa build | RAG thật, FastAPI, evaluation, observability, production, local LLM, fine-tuning, system design |

"Đã học" khác với "đã làm". Cả lộ trình giả định bạn bắt đầu build từ đầu, không giả định đã có sẵn dự án nào.

## 2. Công cụ miễn phí và ràng buộc

| Cần | Dùng miễn phí | Ghi chú |
|---|---|---|
| LLM qua API | NVIDIA API (build.nvidia.com), Gemini free tier, Groq free tier | Giới hạn của Gemini/Groq chưa được kiểm tra, xem trang chính thức. Dùng 2–3 provider để thực hành fallback |
| LLM local | Ollama, llama.cpp | Chạy trên GPU của LOQ. VRAM giới hạn, ưu tiên model nhỏ đã quantize |
| GPU để fine-tune | Colab, Kaggle | Hạn mức thay đổi, kiểm tra trước khi lên kế hoạch |
| Vector store | Chroma hoặc Qdrant chạy local; pgvector để so sánh | Chọn một làm chính |
| Evaluation | Ragas, DeepEval, Promptfoo | Cả ba chạy được local/CI không cần dịch vụ trả phí |
| Observability | Log SQLite trước; Langfuse self-host hoặc Phoenix khi cần | Self-host đỡ tiền license nhưng tốn công vận hành (database, backup, nâng cấp) |
| Deploy | Docker, GitHub Actions, Hugging Face Spaces; Kubernetes chỉ thử trên kind | Xem lưu ý NVIDIA bên dưới |

**Lưu ý về NVIDIA API (quan trọng cho giai đoạn deploy):**
- Truy cập miễn phí qua NVIDIA Developer Program, dùng cho prototyping, nghiên cứu, phát triển và kiểm thử; dùng "production" cần giấy phép NVIDIA AI Enterprise; NVIDIA có thể ngừng dịch vụ bất cứ lúc nào.
- Nhiều người dùng trên diễn đàn NVIDIA báo giới hạn khoảng 40 request/phút, và nhân viên cho biết không nâng được giới hạn cho tài khoản free. Con số này do người dùng báo, hãy tự kiểm tra trên tài khoản của bạn.
- Hệ quả: (1) client phải có rate limiter, backoff và cache ngay từ đầu; (2) chưa nên mở một demo công khai chạy thẳng bằng key NVIDIA của bạn. Đọc kỹ điều khoản trước. Phương án an toàn: demo công khai bằng video, hoặc bằng model local/phiên bản có giới hạn, key NVIDIA chỉ dùng cho phát triển.

## 3. Lộ trình theo giai đoạn (22 tuần + nhánh mở rộng)

### GĐ -1 và 0: Nền và khởi động (tuần 1)
Repo: 1.12, 5.4, 5.6, 6.1
- [ ] **Tuần 1.** Học: async Python (`asyncio`, `httpx`); tokenization; sampling; KV cache và context window (6.1); mini-GPT của Karpathy là *tùy chọn*, không bắt buộc vì bạn đã học Transformers. Build: hoàn thành 40 câu hỏi test, tạo repo, `uv init`, `.env`.
  Xong khi: giải thích được KV cache và vì sao context dài tốn bộ nhớ; có `questions.yaml` và `holdout.yaml`; `uv run` chạy.

### GĐ1: RAG cơ bản (tuần 2–3)
Repo: 6.2–6.4, 8.1–8.5
- [ ] **Tuần 2.** Học: embeddings, chunking theo cấu trúc (không theo số ký tự), metadata, FastAPI cơ bản, Pydantic. Build: nạp PDF, chunk theo Điều/Khoản, lưu kèm điều/khoản/trang.
  Xong khi: kiểm tay 20 chunk, metadata đúng.
- [ ] **Tuần 3.** Học: gọi NVIDIA API (tương thích OpenAI), rate limit, backoff, cache; prompt có trích dẫn. Build: hỏi một câu ra đáp án kèm nguồn.
  Xong khi: 10 câu chạy end-to-end, có bảng điểm nháp.

### GĐ2: Agent và lớp LLM đa nhà cung cấp (tuần 4–5)
Repo: 6.2–6.5, 7.2–7.3, 7.5, 9.1–9.3
- [ ] **Tuần 4.** Học: schema tool calling, ReAct, structured output, LangGraph cơ bản. Build: agent có các tool `search_handbook`, `get_article`.
  Xong khi: ≥ 5/10 câu nhóm B đúng; agent có giới hạn số bước.
- [ ] **Tuần 5.** Học: retry với exponential backoff + jitter, fallback chain, circuit breaker; LiteLLM (đọc tài liệu). Build: lớp LLM đổi được provider: NVIDIA, Gemini/Groq, Ollama.
  Xong khi: cố tình làm hỏng NVIDIA (sai key) thì hệ thống tự chuyển provider khác và có log.

### GĐ3: MCP server (tuần 6)
Repo: 7.4
- [ ] **Tuần 6.** Học: khóa MCP miễn phí (xem mục Tài liệu), bảo mật MCP (tool poisoning, quyền tối thiểu). Build: MCP server có 2 tool đọc.
  Xong khi: Claude/Codex gọi được tool; tool chỉ đọc và kiểm tra đầu vào.

### GĐ4: Evaluation (tuần 7–9)
Repo: 8.5, 12.4
- [ ] **Tuần 7.** Học: faithfulness, context precision/recall; Ragas, DeepEval, Promptfoo; phát triển dựa trên eval (viết eval trước khi tối ưu). Build: lệnh chạy bộ 30 câu, ghi kết quả vào `evals/runs/`.
  Xong khi: có điểm baseline lưu lại.
- [ ] **Tuần 8.** Học: LLM-as-judge và hiệu chuẩn. Build: chấm tay 20 mẫu, so với judge.
  Xong khi: biết độ khớp giữa judge và người (%), biết nhóm câu nào không nên tin judge.
- [ ] **Tuần 9.** Học: hybrid BM25 + vector, reranker, HyDE, multi-query (8.5). Build: mỗi vòng chỉ thêm *một* thay đổi và đo.
  Xong khi: ≥ 2 vòng cải tiến có bảng trước/sau; chạy holdout đúng một lần.

### GĐ5: Observability và context engineering (tuần 10–11)
Repo: 9.2, 12.8, 13.4
- [ ] **Tuần 10.** Học: trace/span, độ trễ, token, chi phí/lượt gọi. Build: log mỗi bước của agent.
  Xong khi: chỉ ra được một câu hỏi chậm ở bước nào.
- [ ] **Tuần 11.** Học: chọn, nén và quản lý ngữ cảnh; memory; cache chính xác và ngữ nghĩa. Build: cache + giới hạn ngữ cảnh.
  Xong khi: giảm số lượt gọi API mà điểm eval không tụt (có số đo).

### GĐ6: Production, bảo mật, cloud (tuần 12–14)
Repo: 12.6, 12.7, 12.9, 12.10, 17.2, 17.4, Phase 14 (tùy chọn)
- [ ] **Tuần 12.** Học: Docker, Compose, thiết kế API. Build: API FastAPI hoàn chỉnh.
  Xong khi: `docker compose up` chạy được từ máy sạch.
- [ ] **Tuần 13.** Học: CI/CD cho AI (eval trong CI), prompt injection gián tiếp (PDF có thể chứa chỉ dẫn độc), che PII. Build: GitHub Actions chạy bộ eval nhỏ; thêm test tấn công injection.
  Xong khi: push làm tụt điểm thì CI đỏ. Lưu ý: rate limit nên CI dùng bộ nhỏ hoặc judge local.
- [ ] **Tuần 14.** Học: khái niệm cloud (object storage, IAM, container serverless); dùng free tier nếu không phải đăng ký thẻ, nếu không thì thực hành khái niệm trên máy local. Tùy chọn: so sánh pgvector với vector store đang dùng. Build: cách demo hợp điều khoản (xem mục 2).
  Xong khi: có link hoặc video demo chạy thật, không vi phạm điều khoản của API đang dùng.

### GĐ7: Local LLM (tuần 15–16)
Repo: Phase 15
- [ ] **Tuần 15.** Học: Ollama, llama.cpp, GGUF, quantization. Build: chạy 40 câu bằng model local qua tầng LLM đã có.
  Xong khi: chạy xong 40 câu không lỗi.
- [ ] **Tuần 16.** Học: benchmark chất lượng, tốc độ, bộ nhớ; thử vLLM nếu VRAM đủ. Build: bảng so sánh API và local ở các mức quantize.
  Xong khi: bảng có đủ cột chất lượng, tốc độ, bộ nhớ.

### GĐ8: Fine-tuning (tuần 17–20)
Repo: Phase 10, 16, 6.1
- [ ] **Tuần 17.** Học: khi nào nên fine-tune (10.1), chuẩn bị dữ liệu. Build: tập cặp (câu hỏi, đoạn đúng) từ Sổ tay. **Không dùng câu trong `questions.yaml` và `holdout.yaml`** để tránh rò rỉ.
  Xong khi: dữ liệu tách train/val, không trùng bộ test.
- [ ] **Tuần 18.** Học: fine-tune embedding/reranker (Sentence-Transformers) trên Colab/Kaggle. Build: mô hình mới nối vào retrieval.
  Xong khi: có số recall@k trước và sau; "không cải thiện" cũng là kết quả hợp lệ.
- [ ] **Tuần 19.** Học: LoRA/QLoRA (PEFT hoặc Unsloth). Build: adapter cho một việc nhỏ (ví dụ phân loại loại câu hỏi để định tuyến).
  Xong khi: bảng so sánh model gốc và model fine-tune.
- [ ] **Tuần 20.** Học: SFT, DPO, GRPO khác nhau thế nào (6.1, Phase 16). Tùy chọn: một thí nghiệm DPO nhỏ bằng TRL.
  Xong khi: giải thích được khác biệt SFT/DPO/GRPO bằng lời của bạn.

### GĐ9: System design và hoàn thiện (tuần 21–22)
Repo: 13.1–13.6
- [ ] **Tuần 21.** Học: khung thiết kế hệ thống AI, đánh đổi chi phí/độ trễ/độ tin cậy. Build: design doc và các ADR.
  Xong khi: có sơ đồ, đánh đổi, ước tính chi phí, cách mở rộng 10 lần.
- [ ] **Tuần 22.** Build: README, video dưới 3 phút, dọn repo.
  Xong khi: người khác đọc README là chạy lại được hệ thống.

### Sau tuần 22: nhánh mở rộng (chọn 1–2)
- [ ] Multimodal và voice (Phase 11)
- [ ] Bảo mật và quản trị AI (Phase 17), red teaming cho agent
- [ ] RL sâu hơn (Phase 16) hoặc suy luận (reasoning models)
- [ ] Đóng góp một PR nhỏ cho dự án mã nguồn mở bạn đã dùng

## 4. Kỹ năng ngoài repo (hiện tại và tương lai)

Danh sách này một phần dựa trên số liệu tin tuyển dụng và blog ngành, nên là xu hướng chứ không phải chắc chắn. Nhiều nguồn là blog của chính các nhà cung cấp công cụ.

| Kỹ năng | Vì sao | Học ở giai đoạn |
|---|---|---|
| Python + LLM + retrieval + cloud | Một khảo sát 3.449 tin AI Engineer (tháng 5/2026) cho thấy Python ~71%, LLM ~66%; tin điển hình ghép Python, LLM, retrieval và cloud | GĐ1–6 |
| Eval-driven development | Công cụ đánh giá và "dataset + regression" là phần chuẩn của pipeline | GĐ4 |
| Context engineering | Nhiều blog ngành 2026 coi nó quan trọng hơn viết prompt; có khóa miễn phí của Hugging Face (rất mới, cần kiểm chứng) | GĐ5 |
| Observability cho agent | Agent có thể trả lời sai mà không báo lỗi, cần trace và theo dõi hành vi | GĐ5 |
| Bảo mật agent | Indirect prompt injection, tool poisoning qua MCP, quyền tối thiểu, sandbox khi chạy mã | GĐ3, 6 |
| Giao thức mở giữa agent và công cụ | MCP đã thành hạ tầng mở; theo dõi chuẩn mới | GĐ3 + radar |
| Model nhỏ chạy local | Tối ưu chi phí, độ trễ, quyền riêng tư | GĐ7 |
| Làm việc với công cụ lập trình AI | Kỹ năng nền, nhưng bạn phải tự giải thích được code | Mọi giai đoạn |
| Cloud cơ bản | Có trong tin tuyển dụng, bản lộ trình cũ bỏ sót | GĐ6 |

## 5. Radar để không lỗi thời

- **Mỗi tháng 2 giờ:** đọc changelog/blog của 5–6 nguồn bạn chọn; ghi vào `docs/radar.md` điều đáng thử.
- **Bộ eval là tài sản bền nhất.** Khi có model hoặc công cụ mới, chạy lại bộ eval và so sánh. Đó là cách thay thành phần mà không đoán mò.
- **Trước khi nhận một công cụ mới:** kiểm tra ngày cập nhật gần nhất, giấy phép, giới hạn gói free.
- **Mỗi quý:** làm một "spike" nửa ngày với một công nghệ mới, không đưa vào dự án chính trừ khi đo được lợi ích.

## 6. Chỗ cần cẩn thận khi đọc repo gốc

- pgvector: `<->` là L2, `<=>` là cosine (repo ghi ngược).
- Bảng ghi Gemini là encoder-decoder; theo hiểu biết của mình thì Gemini là decoder-only (kiểm chứng lại).
- Phần LangChain dạy các lớp cũ (`LLMChain`, `SequentialChain`, `RetrievalQA`); hướng hiện tại là LCEL và LangGraph.
- Ví dụ xử lý lỗi bắt `APIError` trước `RateLimitError` nên nhánh sau không chạy.
- Tên model, giá và số liệu "market demand" đã cũ hoặc không có nguồn.
- Bỏ qua: Phase 2–4 (ngoài phần ôn nền), Phase 12.1–12.3, Kubernetes ngoài kind, multi-tenant và Kafka.

## 7. Tài liệu học miễn phí

| Chủ đề | Tài liệu | Ghi chú |
|---|---|---|
| Nền | 3Blue1Brown, Karpathy Zero to Hero | Có trong danh sách repo |
| LLM | Hugging Face LLM Course | ~15–20 giờ theo một trang đánh giá |
| Agent | Hugging Face Agents Course (có chứng chỉ miễn phí) | ~20–30 giờ theo một trang đánh giá |
| MCP | Hugging Face MCP Course (~10–15 giờ); khóa MCP của Anthropic trên DeepLearning.AI (~90 phút) | |
| Context engineering | Hugging Face Context Course | Mới, kiểm chứng nội dung trước khi theo |
| Prompt, API | Anthropic Prompt Engineering Guide, tài liệu NVIDIA/Gemini/Groq | |
| RAG, agent | Tài liệu LlamaIndex, LangGraph | |
| MLOps | Made With ML | |
| Sách | AI Engineering và Designing ML Systems (Chip Huyen) | Có thể không miễn phí; tìm ở thư viện |

Thời lượng khóa lấy từ trang đánh giá bên thứ ba, hãy xem trang chính thức.

## 8. Nhật ký tuần

| Tuần | Đã làm | Vướng mắc | Cách xử lý |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

## Nguồn

- Repo: https://github.com/PrinceSinghhub/Ultimate-AI-Engineer-Roadmap-2026
- Khảo sát tin tuyển dụng: https://dev.to/gnana_6392e836fd500a957dc/ai-engineer-skills-companies-want-in-2026-3449-posting-analysis-5f9l
- Khóa Hugging Face: https://aiagentrank.io/learn/provider/huggingface
- So sánh khóa MCP: https://aiagentrank.io/learn/compare/deeplearning-ai-mcp-build-rich-context-agents-vs-huggingface-mcp-course
- NVIDIA API miễn phí: https://www.developersdigest.tech/models/free-api/nvidia
- Diễn đàn NVIDIA về giới hạn: https://forums.developer.nvidia.com/t/request-for-nvidia-nim-api-rate-limit-increase-40-200-rpm-agentic-development-workflow/378941
- Công cụ eval: https://developersdigest.tech/blog/ai-agent-evaluation-tools-compared-2026
- Công cụ observability: https://benchlm.ai/blog/posts/best-llm-observability-tools
- Xu hướng agent (blog nhà cung cấp): https://www.salesforce.com/blog/ai-agent-trends-2026
- Hugging Face Context Course: https://www.beri.net/learning/hf-context-course
