# Hướng dẫn viết 40 câu hỏi test

Bộ câu hỏi này là tài sản quan trọng nhất của dự án. Viết bằng tay, đáp án phải đối chiếu trực tiếp với PDF, không nhờ AI viết rồi tin luôn.

## 1. Cơ cấu 40 câu

| Nhóm | Số câu | Mục đích |
|---|---|---|
| A. Tra cứu đơn giản | 14 | Một điều khoản là đủ trả lời |
| B. Nhiều bước / ghép nhiều chỗ | 10 | Cần tìm nhiều đoạn hoặc tính toán |
| C. Bảng và chương trình đào tạo | 5 | Kiểm tra khả năng xử lý bảng bị vỡ |
| D. Mâu thuẫn / phụ thuộc điều kiện | 5 | Hai văn bản nói khác nhau, hoặc đáp án khác nhau theo hệ (đại trà/CLC) |
| E. Không có trong tài liệu | 6 | Kiểm tra từ chối đúng, không bịa |

## 2. Định dạng mỗi câu

```yaml
id: A01
nhom: A
cau_hoi: "Điều kiện để được dự thi kết thúc học phần là gì?"
dap_an_chuan: "Tham gia học tối thiểu 80% số giờ lên lớp; đáp ứng điều kiện trong đề cương; đã hoàn thành học phí; không vi phạm kỷ luật."
nguon: "Quy định đào tạo, Điều 29 khoản 1 (cũng nêu ở Quy định tổ chức thi, Điều 7)"
trang: "<điền số trang trong PDF>"
tu_khoa_bat_buoc: ["80%", "học phí"]
```

Với nhóm E, `dap_an_chuan` là "Không có thông tin trong Sổ tay" và ghi thêm lý do.

## 3. Ví dụ đã đối chiếu với nội dung Sổ tay

**Nhóm A (tra cứu)**
- Số tín chỉ tối thiểu và tối đa được đăng ký mỗi học kỳ chính? → Chương trình cử nhân 15–25; chương trình kỹ sư 16–25 (Quy định đào tạo, Điều 12 khoản 3).
- Điểm thi 8,7 được xếp điểm chữ và thang 4 là bao nhiêu? → A, 3,7 (Điều 25, Bảng 1).
- Sinh viên chương trình đại trà phải đạt chuẩn đầu ra tiếng Anh bao nhiêu? → 450 điểm TOEIC trở lên (Quy định tiếng Anh, Điều 9). Hệ chất lượng cao: TOEFL iBT từ 70.

**Nhóm B (nhiều bước)**
- "Tôi đang nợ 25 tín chỉ từ đầu khóa, có bị cảnh báo học tập không?" → Có, mức 1, vì tổng tín chỉ nợ đọng từ đầu khóa vượt 24 (Điều 33 khoản 3 điểm a). Câu này kiểm tra cả việc tìm điều khoản lẫn so sánh số.
- "Học phí học kỳ này chưa đóng thì ảnh hưởng gì?" → Không được dự thi kết thúc học phần và không đăng ký môn kỳ sau; nợ học phí còn bị trừ điểm rèn luyện và có thể bị xem xét xử lý (ghép Quy định thu nộp học phí Điều 6–7, Điều 29 quy chế đào tạo, phiếu đánh giá rèn luyện tiêu chí 2.1).

**Nhóm C (bảng)**
- "Ngành CNTT chất lượng cao, chuyên ngành Trí tuệ nhân tạo, học Nhập môn học sâu ở học kỳ nào và mấy tín chỉ?" → HK8, 3 tín chỉ (bảng chuyên ngành Trí tuệ nhân tạo, năm 4).

**Nhóm D (mâu thuẫn / điều kiện)**
- "Thời hạn khiếu nại điểm thi kết thúc học phần là bao lâu?" → Sổ tay có hai con số khác nhau: 10 ngày (Quy định đào tạo, Điều 30 và Quy định tổ chức thi, Điều 21) và 7 ngày kể từ ngày công bố điểm (Quy định tổ chức thi, Điều 10). Câu trả lời tốt phải nêu cả hai nguồn và khuyên xác nhận lại với Trung tâm Khảo thí.
- "Chuẩn đầu ra tiếng Anh là gì?" → Phụ thuộc hệ: đại trà TOEIC 450, chất lượng cao TOEFL iBT 70. Câu trả lời tốt phải hỏi lại hoặc nêu cả hai.

**Nhóm E (không có trong tài liệu)**
- "Học phí một tín chỉ ngành AI năm học 2026–2027 là bao nhiêu?" → Sổ tay chỉ nêu mức trần học phí theo khối ngành của Nhà nước (tính theo tháng), không nêu học phí thực tế từng ngành của PTIT.
- "Lịch thi học kỳ 1 năm 2026 là khi nào?" → Không có; lịch thi xem trên hệ thống UIS.
- Hai câu nữa bạn tự nghĩ: điểm chuẩn tuyển sinh, tên giảng viên một môn cụ thể, v.v.

Lưu ý: các đáp án trên mình lấy từ nội dung bạn gửi. Vẫn cần bạn đối chiếu lại với PDF gốc và điền số trang trước khi dùng làm đáp án chuẩn.

## 4. Quy tắc viết

1. Viết câu hỏi như sinh viên thật hỏi (ngắn, không đúng thuật ngữ), không chép lại câu chữ của quy chế. Ít nhất 10 câu dùng cách nói đời thường ("rớt môn", "bị đuổi học", "xin nghỉ một kỳ").
2. Mỗi câu chỉ có một đáp án chuẩn rõ ràng và có nguồn.
3. Không để câu hỏi chứa sẵn đáp án.
4. Trộn các phần của Sổ tay: đào tạo, thi cử, rèn luyện/kỷ luật, học bổng, học phí, ký túc xá, thủ tục.
5. Chia 30 câu để tối ưu hóa và **giữ riêng 10 câu làm tập kiểm tra cuối** (không xem khi chỉnh hệ thống). Cách này tránh việc hệ thống chỉ "học thuộc" bộ test.
6. Khi hệ thống trả lời sai, đừng sửa đáp án để cho khớp. Chỉ sửa đáp án nếu phát hiện chính đáp án chuẩn của bạn sai so với PDF.

## 5. Cách chấm (sẽ dùng ở Giai đoạn 4)

- Đúng/sai theo từ khóa bắt buộc và nguồn trích dẫn có khớp không.
- Có trích dẫn hay không.
- Với nhóm E: có từ chối đúng không.
- Với nhóm D: có nêu đủ cả hai nguồn/điều kiện không.
