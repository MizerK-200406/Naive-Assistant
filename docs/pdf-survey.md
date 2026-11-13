# Báo cáo Khảo sát PDF Sổ tay Sinh viên PTIT

> File khảo sát: `data/raw/So_tay_sinh_vien_PTIT.pdf` (213 trang)

## 1. Thông tin chung & Lớp văn bản (Text Layer)

- **Tổng số trang:** 213 trang.
- **Metadata:**
  - `format`: `PDF 1.5`
  - `author`: `ACER`
  - `creator`: `Microsoft® Word 2016`
  - `producer`: `Microsoft® Word 2016`
  - `creationDate`: `D:20260824081036+07'00'`
  - `modDate`: `D:20260824081036+07'00'`

**Xác định dạng PDF (Text Layer vs Scan):**
- `pymupdf`: 5/213 trang có text < 50 ký tự. Có text layer số hoá hoàn chỉnh, không phải bản scan ảnh.
- `pdfplumber`: 7/213 trang có text < 50 ký tự. Có text layer số hoá hoàn chỉnh, không phải bản scan ảnh.
- `pypdf`: 5/213 trang có text < 50 ký tự. Có text layer số hoá hoàn chỉnh, không phải bản scan ảnh.

## 2. So sánh Thư viện & Chất lượng Tiếng Việt

| Thư viện | Phiên bản | Thời gian trích xuất | Ký tự lỗi U+FFFD | Tỷ lệ FFFD | Dấu rời (Combining) | Dạng chuẩn |
|---|---|---|---|---|---|---|
| `pymupdf` | 2.1 | 0.35s | 0 | 0.0000% | 0 (0.00%) | NFC |
| `pdfplumber` | 0.11.10 | 12.95s | 0 | 0.0000% | 0 (0.00%) | NFC |
| `pypdf` | 7.1.0 | 4.92s | 0 | 0.0000% | 0 (0.00%) | NFC |

**Nhận xét tiếng Việt:**
- Cả 3 thư viện đều không phát sinh ký tự hỏng `U+FFFD` (tỷ lệ 0%).
- Văn bản chủ yếu ở dạng Unicode tổ hợp (NFD) hoặc dựng sẵn (NFC) tương thích tốt, cần chuẩn hóa `unicodedata.normalize('NFC', text)` trước khi nạp vào vector store.

## 3. Dòng lặp (Header / Footer cần lọc)

- **Ngưỡng quy định ≥ 30% số trang (≥ 63 trang):**
  - **Không có dòng nào đạt ngưỡng ≥ 30% số trang.** Do tài liệu xuất từ Word không chèn running header văn bản lặp lại trên toàn bộ 213 trang.

**Top 10 dòng lặp phổ biến nhất ở đầu/cuối trang (Header/Footer):**

| Vị trí & Đoạn trích dòng lặp | Số lần xuất hiện | Tỷ lệ trang |
|---|---|---|
| `[Footer] 3` | 22 | 10.3% |
| `[Footer] Chi tiết về chương trình đào tạo sinh viên xem tại: https://daotao.p...` | 12 | 5.6% |
| `[Footer] 2` | 11 | 5.2% |
| `[Header] 5` | 8 | 3.8% |
| `[Header] TT` | 8 | 3.8% |
| `[Footer] HK7` | 6 | 2.8% |
| `[Footer] HK8` | 6 | 2.8% |
| `[Header] 19` | 4 | 1.9% |
| `[Header] Nội dung đánh giá` | 4 | 1.9% |
| `[Footer] 18` | 4 | 1.9% |

**Nhận xét số trang in (Printed Page Numbers):**
- Số trang in được căn giữa hoặc ở góc trên/dưới mỗi trang dưới dạng số độc lập (ví dụ `78`, `79`).
- Tồn tại độ lệch cố định giữa số trang in của tài liệu và số trang vật lý của file PDF: **Trang vật lý PDF = Trang in + 6** (do 6 trang bìa, lời tựa và mục lục ban đầu không đánh số trang chính thức).

## 4. Khảo sát Cấu trúc Pháp lý (Điều, Chương, Khoản, Điểm)

- **Tổng số dòng khớp `^Điều \d+`:** 167
- **Tổng số dòng khớp `^Chương [IVXLC]+`:** 56
- **Tổng số dòng khớp `^\d+\.\s` (Khoản):** 750
- **Tổng số dòng khớp `^[a-zđ]\)\s` (Điểm):** 497

### 15 dòng Điều đầu tiên:
| Trang | Dòng Điều (trích ngắn) |
|---|---|
| Trang 66 | `Điều 1. Phạm vi điều chỉnh và đối tượng áp dụng` |
| Trang 66 | `Điều 2. Mục tiêu đào tạo` |
| Trang 66 | `Điều 3. Học chế tín chỉ` |
| Trang 67 | `Điều 4. Học phần và tín chỉ` |
| Trang 68 | `Điều 5. Ngành đào tạo` |
| Trang 68 | `Điều 6. Chương trình đào tạo` |
| Trang 70 | `Điều 7. Chuẩn đầu ra của chương trình đào tạo` |
| Trang 71 | `Điều 8. Thời gian và kế hoạch đào tạo` |
| Trang 73 | `Điều 9. Đăng ký nhập học` |
| Trang 73 | `Điều 10. Tổ chức lớp học` |
| Trang 74 | `Điều 11. Lập và thông báo kế hoạch đào tạo` |
| Trang 74 | `Điều 12. Đăng ký học tập` |
| Trang 76 | `Điều 13. Đăng ký bổ sung hoặc rút bớt học phần` |
| Trang 76 | `Điều 14. Học lại và học cải thiện điểm` |
| Trang 77 | `Điều 15. Nghỉ học tạm thời` |

### Điểm chuyển giao văn bản (Reset số Điều):
Sổ tay gộp nhiều văn bản quy định nối tiếp nhau, thể hiện qua việc số Điều bị reset về lại các số nhỏ hơn:

| Từ Điều (Trang) | Sang Điều (Trang) | Loại sự kiện | Dòng bắt đầu |
|---|---|---|---|
| Điều 15 (Trang 77) | Điều 8 (Trang 77) | `RESET_DOC` | `Điều 8 của Quy chế này.` |
| Điều 8 (Trang 77) | Điều 16 (Trang 78) | `SKIP_DIEU` | `Điều 16. Chuyển trường, chuyển cơ sở đào tạo, chuyển hình...` |
| Điều 40 (Trang 93) | Điều 1 (Trang 95) | `RESET_DOC` | `Điều 1. Phạm vi điều chỉnh và đối tượng áp dụng` |
| Điều 10 (Trang 99) | Điều 21 (Trang 99) | `SKIP_DIEU` | `Điều 21. Trách nhiệm của sinh viên dự thi` |
| Điều 21 (Trang 99) | Điều 27 (Trang 101) | `SKIP_DIEU` | `Điều 27. Xử lý đối với sinh viên vi phạm quy chế thi` |
| Điều 27 (Trang 101) | Điều 1 (Trang 103) | `RESET_DOC` | `Điều 1. Phạm vi và đối tượng áp dụng` |
| Điều 10 (Trang 106) | Điều 1 (Trang 112) | `RESET_DOC` | `Điều 1. Phạm vi và đối tượng áp dụng/` |
| Điều 10 (Trang 115) | Điều 1 (Trang 127) | `RESET_DOC` | `Điều 1. Phạm vi Điều chỉnh và đối tượng áp dụng` |
| Điều 6 (Trang 129) | Điều 10 (Trang 130) | `SKIP_DIEU` | `Điều 10. Nguyên tắc đánh giá kết quả rèn luyện của sinh v...` |
| Điều 25 (Trang 140) | Điều 1 (Trang 151) | `RESET_DOC` | `Điều 1. Phạm vi và đối tượng áp dụng` |
| Điều 18 (Trang 162) | Điều 1 (Trang 171) | `RESET_DOC` | `Điều 1. Phạm vi điều chỉnh` |
| Điều 11 (Trang 176) | Điều 1 (Trang 177) | `RESET_DOC` | `Điều 1. Đối tượng áp dụng` |

## 5. Khảo sát Bảng biểu (Tables)

Khảo sát trên các trang chứa bảng tiêu biểu: Trang [85, 165].

- **Trích xuất dạng văn bản thô (Plain Text):**
  - Khi trích text thông thường, các bảng (như Bảng quy đổi điểm Điều 25, khung CTĐT) bị vỡ cấu trúc cột. Các ô cùng hàng bị rải rác thành các dòng rời rạc hoặc dính liền nhau không có ký tự phân cách cột đồng nhất.
- **Trích xuất chuyên biệt (Table Extraction):**
  - `pdfplumber.extract_tables()`: Tách được lưới bảng dựa trên nét kẻ (lines) và khoảng cách chữ, giữ được cấu trúc hàng/cột tương đối nguyên vẹn.
  - `PyMuPDF.find_tables()`: Phát hiện bảng rất nhanh, xuất ra dạng ma trận hàng/cột rõ ràng.

*Chi tiết dữ liệu trích mẫu đã được lưu tại thư mục `data/index/survey/` (được bảo vệ bởi .gitignore).*