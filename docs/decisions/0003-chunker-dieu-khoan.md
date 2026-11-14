# ADR 0003: Chunker theo Điều và Khoản

- Ngày: 2026-11-14
- Trạng thái: Chấp nhận

## Bối cảnh

Các văn bản có cấu trúc Điều nhưng số Điều có thể nhảy do Sổ tay chỉ in bản
trích. Một số văn bản bắt đầu trên cùng trang với phần cuối văn bản trước. Hai
quy định chuẩn đầu ra tiếng Anh cần phân biệt hệ trong dữ liệu embedding.

## Quyết định

Mỗi Điều tạo một chunk. Điều dài hơn 1800 ký tự được ưu tiên tách và gom theo
Khoản; nếu không thể thì tách theo dòng. Trang chung được cắt bằng marker đã
đăng ký. Tiền tố `embed_text` gồm tên văn bản và tên hệ khi có.

## Hệ quả

Số Điều nhảy chỉ sinh cảnh báo, không sửa nội dung. Ngưỡng 1800 là điểm xuất
phát và sẽ được điều chỉnh theo số đo ở GĐ4.

## Chưa làm

Chưa chunk bảng, PDF 7-65, văn bản hướng dẫn, phụ lục và cẩm nang.
