# ADR 0002: Registry văn bản trong Sổ tay

- Ngày: 2026-11-14
- Trạng thái: Chấp nhận

## Bối cảnh

Sổ tay chứa nhiều văn bản nối tiếp nhau; số Điều được đặt lại theo từng văn
bản. Một số trang biên chứa đồng thời phần cuối văn bản trước và phần đầu văn
bản sau. Các bản quy định là bản trích nên chuỗi số Điều có thể không liên tục.

## Quyết định

Đăng ký mỗi văn bản bằng `DocSpec` với phạm vi trang PDF, marker bắt đầu khi
chung trang biên, metadata nhận dạng và trạng thái kiểm chứng. `doc_id` là khóa;
số quyết định chỉ là metadata vì có thể trùng đúng như bản in. PDF 7-65 chưa
thuộc registry này.

Việc loại số trang in được tách thành hàm thuần, chỉ bỏ dòng không rỗng đầu tiên
khi dòng đó khớp chính xác số trang dự kiến.

## Hệ quả

Chunker có thể xác định văn bản theo registry và tách đúng tại marker mà không
suy diễn từ chuỗi số Điều. Script kiểm tra đối chiếu registry với `pages.jsonl`
nhưng không thay đổi dữ liệu nguồn.
