# Quyết định Kỹ thuật 0001: Lựa chọn Thư viện Trích xuất PDF

- **Ngày:** 2026-11-14
- **Bối cảnh:** Sổ tay 213 trang PDF, có text layer số hoá hoàn chỉnh, tiếng Việt ở dạng NFC tương thích tốt, không phát sinh ký tự lỗi `U+FFFD` ở cả 3 thư viện khảo sát (PyMuPDF, pypdf, pdfplumber).
- **Các lựa chọn đã đo:**
  - `PyMuPDF`: 0,35s, 3,60 chữ đứng riêng/1000 token.
  - `pypdf`: 4,92s, 3,59 chữ đứng riêng/1000 token.
  - `pdfplumber`: 12,95s, 5,01 chữ đứng riêng/1000 token (thêm 2 trang gần rỗng: 21 và 203).
  - Tính năng `find_tables` của PyMuPDF làm vỡ chữ trong ô bảng, trong khi trích xuất text thông thường thì không bị.
- **Quyết định:** Sử dụng PyMuPDF làm thư viện trích xuất chính; pypdf chỉ dùng để đối chiếu dữ liệu; loại bỏ pdfplumber.
- **Lý do:**
  - Hỗ trợ lấy tọa độ từ (`get_text("words")`), phục vụ bóc tách cấu trúc bảng khung chương trình đào tạo.
  - Tốc độ xử lý vượt trội (0,35s cho toàn bộ 213 trang).
  - Chất lượng trích xuất văn bản tiếng Việt ngang pypdf sau khi tắt TEXT_MEDIABOX_CLIP; mặc định bit này làm mất 218 ký tự ở PDF 112, 116, 118 (bảng quy đổi điểm tiếng Anh, có chữ xoay).
- **Giới hạn đã biết:** PDF 10, 12, 13, 213 chứa ảnh chiếm 59-71% diện tích trang, nội dung trong ảnh không được trích xuất; không có OCR.
- **Rủi ro:** Giấy phép của PyMuPDF là `Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License`. Rủi ro này phải xử lý trước khi công khai repo; hướng giảm thiểu là đặt toàn bộ logic thư viện đằng sau hàm trừu tượng `extract_pages()` để dễ dàng thay thế backend khi cần thiết.
- **Phiên bản các gói (từ uv.lock thực tế):**
  - `pymupdf`: 2.1
  - `pyyaml`: 6.0.3
  - `pytest`: 9.2.0
