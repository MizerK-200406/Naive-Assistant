# Spec — Naive-Assistant

## 1. Vấn đề

Sổ tay sinh viên PTIT cơ sở TP.HCM (khóa 2026) dài hơn 200 trang, gộp nhiều quy chế khác nhau: quy định đào tạo, thi cử, công tác sinh viên, học bổng, học phí, văn hóa học đường, chính sách nhà nước. Sinh viên khó tìm đúng quy định và dễ hiểu sai, nhất là khi một câu hỏi cần ghép thông tin từ nhiều điều khoản.

## 2. Người dùng

- **Chính:** sinh viên PTIT (đặc biệt tân sinh viên).
- **Phụ:** nhà tuyển dụng/người review portfolio, xem dự án như một bản demo kỹ thuật AI Engineering hoàn chỉnh.

## 3. Quyết định đã chốt

| Mục | Quyết định |
|---|---|
| Tên dự án | Naive-Assistant (repo: `naive-assistant`) |
| Bộ tài liệu | Sổ tay sinh viên PTIT khóa 2026, cơ sở TP.HCM (1 file PDF, ~207 trang) |
| LLM | API miễn phí của NVIDIA, cần kiểm tra danh sách model và hạn mức hiện tại trước khi chọn |
| Chi phí | Toàn bộ free |
| Thời gian | 3 giờ/ngày |
| Mục tiêu | Portfolio xin thực tập AI Engineer |

## 4. User stories

1. Là sinh viên, tôi hỏi bằng tiếng Việt tự nhiên ("rớt môn bắt buộc thì phải làm gì?") và nhận câu trả lời ngắn gọn kèm điều khoản để tự kiểm tra.
2. Là sinh viên, tôi hỏi câu nhiều bước ("tôi nợ 25 tín chỉ, có bị cảnh báo học tập không?") và hệ thống tự tra nhiều chỗ rồi tổng hợp.
3. Là sinh viên, khi hỏi điều Sổ tay không nói (ví dụ lịch thi cụ thể), tôi được báo rõ là không có thông tin, kèm gợi ý phòng/đơn vị nên liên hệ nếu Sổ tay có nêu.
4. Là người dùng công cụ AI, tôi gắn Naive-Assistant vào Claude/Codex qua MCP để tra cứu ngay trong lúc làm việc.
5. Là người phát triển, tôi xem được điểm chất lượng, chi phí (nếu có) và độ trễ của từng câu hỏi.

## 5. Phạm vi

**Trong phạm vi (v1):** hỏi đáp trên một PDF tiếng Việt, trích dẫn điều/khoản/trang, agent nhiều bước, MCP server, bộ đánh giá, quan sát (log/trace), API có thể deploy, chạy được bằng model local.

**Ngoài phạm vi (v1):** đăng nhập, dữ liệu cá nhân của sinh viên (điểm, học phí), tài liệu của các trường khác, app di động, đa ngôn ngữ, thay thế tư vấn chính thức của phòng ban.

## 6. Đặc điểm của dữ liệu (ảnh hưởng thiết kế)

- Cấu trúc phân cấp rõ: Phần → Quy định → Chương → Điều → Khoản → Điểm. Chunk nên theo cấu trúc này, không cắt theo số ký tự.
- Có **bảng**: bảng quy đổi điểm, khung chương trình theo ngành/học kỳ, mức học bổng. Khi trích từ PDF, bảng bị vỡ cột. Cần cách xử lý riêng và cần câu hỏi test cho nhóm này.
- Có **mâu thuẫn nội bộ** giữa các văn bản. Ví dụ: thời hạn khiếu nại điểm thi là 10 ngày (Quy định đào tạo, Điều 30) nhưng 7 ngày (Quy định tổ chức thi, Điều 10); thời hạn trả kết quả phúc tra cũng khác nhau (7 ngày làm việc và 15 ngày làm việc). Cần xử lý theo nguyên tắc số 3 của Constitution.
- Có tham chiếu chéo ("theo khoản 3 Điều 12 của Quy chế này"), cần agent biết tra tiếp.
- Có số trang và dòng tiêu đề lặp, cần làm sạch khi nạp.
- Nhiều thông tin chỉ đúng với khóa/hệ nhất định (đại trà và chất lượng cao có chuẩn tiếng Anh khác nhau). Câu trả lời phải nêu điều kiện áp dụng.

## 7. Tiêu chí thành công (đo được)

Các ngưỡng là mục tiêu ban đầu, được chỉnh lại sau khi có đo thực tế ở Giai đoạn 4.

- Trả lời đúng ≥ 80% trên bộ 40 câu hỏi test tự xây.
- 100% câu trả lời có trích dẫn; các câu "không có trong tài liệu" được từ chối đúng ≥ 90%.
- Có bảng so sánh trước và sau khi cải thiện (ít nhất 2 vòng).
- Có bảng so sánh API NVIDIA và model local (chất lượng, tốc độ).
- Chạy hoàn toàn free; có link demo, README đầy đủ, video demo dưới 3 phút.

## 8. Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| API free có giới hạn tốc độ/số lượt, hoặc thay đổi | Cache kết quả, giới hạn tần suất gọi, có phương án local |
| Sổ tay ghi "Lưu hành nội bộ", đăng công khai có thể không phù hợp | Không đưa PDF vào repo, kiểm tra với phòng Công tác sinh viên nếu muốn demo công khai |
| Bảng trong PDF vỡ cấu trúc | Thử nhiều cách trích xuất, đo bằng nhóm câu hỏi bảng |
| Câu trả lời sai về quy chế có thể gây hại thực tế cho sinh viên | Luôn kèm trích dẫn và dòng nhắc xác nhận lại với phòng chức năng |
| Quá phạm vi so với 3 giờ/ngày | Làm từng giai đoạn, cắt Fine-tuning nếu trễ tiến độ |
