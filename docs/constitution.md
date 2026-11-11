# Constitution — Naive-Assistant

Những nguyên tắc không đổi. Mọi quyết định thiết kế và code sau này phải tuân theo. Muốn đổi nguyên tắc thì phải sửa file này và ghi lý do.

1. **Không bịa.** Nếu tài liệu không có thông tin thì trả lời "không tìm thấy trong Sổ tay", không đoán, không dùng kiến thức bên ngoài để lấp chỗ trống.
2. **Mọi câu trả lời phải có trích dẫn.** Ghi rõ văn bản/quy định, điều khoản và số trang để người dùng tự kiểm tra.
3. **Mâu thuẫn thì nói ra.** Khi hai văn bản trong Sổ tay nói khác nhau về cùng một việc (ví dụ thời hạn khiếu nại điểm), nêu cả hai nguồn và không tự chọn một bên.
4. **Đo được thì mới cải thiện được.** Không sửa hệ thống nếu chưa có số liệu trước và sau trên bộ câu hỏi test.
5. **Tiếng Việt là ưu tiên số một.** Chunk, truy vấn, câu trả lời và đánh giá đều kiểm tra bằng tiếng Việt thật.
6. **Miễn phí.** Toàn bộ dự án chạy được mà không tốn tiền: API free, model/embedding local, hạ tầng free. Mọi chi phí phát sinh phải bị chặn bằng hạn mức.
7. **Đổi được nhà cung cấp LLM.** Tầng LLM phải tách riêng để đổi giữa API NVIDIA và model local mà không viết lại hệ thống.
8. **Bí mật và dữ liệu không lên Git.** API key chỉ nằm trong `.env`. File PDF gốc không đưa vào repo công khai (Sổ tay ghi "Lưu hành nội bộ").
9. **Tự giải thích được.** Mọi phần của code đều phải giải thích được khi phỏng vấn, kể cả phần AI viết giúp.
10. **Xong từng giai đoạn mới sang giai đoạn sau.** Mỗi giai đoạn có điều kiện "xong" cụ thể và phải commit/tag.
