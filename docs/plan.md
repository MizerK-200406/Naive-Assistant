# Plan — Naive-Assistant

## 1. Kiến trúc (mức khái niệm)

```
PDF Sổ tay → [Nạp: làm sạch + chunk theo Điều/Khoản + metadata] → Kho tìm kiếm (vector + từ khóa)
                                                                        ↓
Người dùng → API → Agent (tool calling) ⇄ Tầng LLM (NVIDIA API | local)
                       ↓                        
               MCP server (cùng bộ tool)     Log / Trace / Eval
```

| Khối | Nhiệm vụ |
|---|---|
| Nạp tài liệu | Đọc PDF, làm sạch, chia đoạn theo cấu trúc Điều/Khoản, giữ metadata (văn bản, điều, khoản, trang) |
| Kho tìm kiếm | Lưu và tìm đoạn theo ngữ nghĩa, có thể kết hợp từ khóa (BM25) vì quy chế nhiều thuật ngữ cố định |
| Agent | Quyết định tìm gì, tìm mấy lần, theo tham chiếu chéo, tổng hợp và trích dẫn |
| Tầng LLM | Một giao diện chung, đổi được giữa API NVIDIA và model local |
| MCP server | Đưa các tool tìm kiếm ra cho Claude/Codex |
| Đánh giá | Chạy bộ 40 câu hỏi và chấm điểm |
| Quan sát | Ghi log, trace từng bước, độ trễ, số lượt gọi API |
| Triển khai | Đóng gói, API, CI, deploy free |

## 2. Ràng buộc "toàn bộ free"

Ứng viên công cụ (chỉ là ứng viên, chọn thật ở Giai đoạn 1 và ghi lý do vào `docs/decisions/`):

- **LLM:** API của NVIDIA (kiểm tra model và hạn mức trên trang chính thức trước khi dùng). Dự phòng: model nhỏ chạy local trên GPU của LOQ.
- **Embedding:** model embedding của NVIDIA qua API, hoặc model đa ngôn ngữ chạy local.
- **Kho tìm kiếm:** loại chạy file/local, không cần server riêng.
- **Quan sát:** log tự viết vào SQLite trước, thêm công cụ tự host khi cần.
- **Deploy:** gói free của một nền tảng hosting. Kiểm tra giới hạn hiện tại trước khi chọn.

Nguyên tắc: mọi lời gọi API đi qua một chỗ duy nhất, có cache và giới hạn tần suất.

## 3. Lộ trình (3 giờ/ngày ≈ 21 giờ/tuần)

| GĐ | Nội dung | Xong khi | Ước lượng |
|---|---|---|---|
| -1 | Đặc tả và bộ câu hỏi test | 4 file spec + 40 câu hỏi có đáp án và nguồn | 3–4 ngày |
| 0 | Khởi tạo repo, môi trường, `.env`, `.gitignore`, CI rỗng | `uv run` chạy được, đã push GitHub | 1 ngày |
| 1 | Nạp tài liệu và RAG cơ bản | Hỏi 1 câu ra đáp án kèm điều khoản và trang | 1 tuần |
| 2 | Agent + tool calling | Câu hỏi nhiều bước được xử lý đúng | 1 tuần |
| 3 | MCP server | Claude/Codex gọi được tool của bạn | 2–3 ngày |
| 4 | Evaluation | Bảng điểm trước/sau ít nhất 2 vòng cải thiện | 1 tuần |
| 5 | Observability | Xem được độ trễ và số lượt gọi từng câu hỏi | 3–4 ngày |
| 6 | Production | API, Docker, CI, có link chạy thật | 1 tuần |
| 7 | Local LLM | Bảng so sánh API và local | 3–4 ngày |
| 8 | Fine-tuning (tùy chọn) | Chỉ làm nếu còn thời gian: fine-tune embedding/reranker tiếng Việt | 1–2 tuần |
| 9 | System design | README, design doc, video demo | 3–4 ngày |

Tổng khoảng 7–9 tuần nếu giữ được 3 giờ/ngày. Giai đoạn 8 là phần cắt đầu tiên nếu trễ.

## 4. Nhật ký quyết định

Mỗi quyết định kỹ thuật lớn tạo một file ngắn trong `docs/decisions/` gồm: bối cảnh, các lựa chọn đã cân nhắc, quyết định, lý do. Đây cũng là tài liệu tốt để trả lời phỏng vấn.

## 5. Tasks của Giai đoạn -1

- [x] Chốt tên dự án và các câu hỏi Clarify
- [ ] Đọc lướt Sổ tay một lượt, ghi lại các phần quan trọng và chỗ nghi mâu thuẫn
- [ ] Viết 40 câu hỏi test theo `eval-guide.md` (việc quan trọng nhất, làm bằng tay)
- [ ] Kiểm tra từng đáp án chuẩn bằng cách đối chiếu trực tiếp với PDF
- [ ] Vẽ sơ đồ kiến trúc 1 trang
- [ ] Đặt 4 file spec vào `docs/` của repo ở Giai đoạn 0
