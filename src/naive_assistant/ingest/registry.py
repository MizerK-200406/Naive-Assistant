"""Registry các văn bản trong phần PDF 66-213 của Sổ tay.

Lưu ý dữ liệu:
- ``dao_tao_tin_chi`` và ``van_hoa_hoc_duong`` có cùng số quyết định đúng
  như Sổ tay in; số quyết định không được dùng làm khóa.
- Tiêu đề của ``qd_05_2022_ttg`` và ``qd_29_2025_ttg`` bị cắt dòng trong
  Sổ tay, nên ``short_name`` chỉ gồm loại văn bản và số hiệu.
- Các văn bản ``quy_dinh`` đều là bản trích, nên số Điều có thể không liên tục.
- PDF 7-65 chưa được đăng ký.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class DocSpec:
    doc_id: str
    short_name: str
    title: str
    decision: str | None
    kind: str
    he: str | None
    start_pdf_page: int
    end_pdf_page: int
    start_marker: str | None
    has_articles: bool
    parent_id: str | None
    verified: bool
    probe: str | None


REGISTRY: tuple[DocSpec, ...] = (
    DocSpec(
        "dao_tao_tin_chi",
        "Quy định đào tạo đại học theo tín chỉ",
        "QUY ĐỊNH ĐÀO TẠO ĐẠI HỌC THEO TÍN CHỈ CỦA HỌC VIỆN",
        "838/QĐ-HV ngày 11/10/2021",
        "quy_dinh",
        None,
        66,
        94,
        None,
        True,
        None,
        True,
        "QUY ĐỊNH ĐÀO TẠO ĐẠI HỌC THEO TÍN CHỈ",
    ),
    DocSpec(
        "to_chuc_thi",
        "Quy định tổ chức thi kết thúc học phần, thi học phần thay thế tốt nghiệp",
        "QUY ĐỊNH TỔ CHỨC THI KẾT THÚC HỌC PHẦN, THI HỌC PHẦN THAY THẾ TỐT NGHIỆP TRÌNH ĐỘ ĐẠI HỌC CỦA HỌC VIỆN",
        "1037/QĐ-HV ngày 12/11/2021",
        "quy_dinh",
        None,
        95,
        102,
        None,
        True,
        None,
        True,
        "QUY ĐỊNH TỔ CHỨC THI KẾT THÚC HỌC PHẦN",
    ),
    DocSpec(
        "chuan_dau_ra_ta_dai_tra",
        "Quy định tổ chức đào tạo và kiểm tra chuẩn đầu ra tiếng Anh (hệ đại trà)",
        "QUY ĐỊNH TỔ CHỨC ĐÀO TẠO VÀ KIỂM TRA CHUẨN ĐẦU RA TIẾNG ANH TRÌNH ĐỘ ĐẠI HỌC CHÍNH QUY TẠI HỌC VIỆN",
        "734/QĐ-HV ngày 05/10/2020",
        "quy_dinh",
        "dai_tra",
        103,
        111,
        None,
        True,
        None,
        True,
        "CHÍNH QUY TẠI HỌC VIỆN",
    ),
    DocSpec(
        "chuan_dau_ra_ta_clc",
        "Quy định tổ chức đào tạo và kiểm tra chuẩn đầu ra tiếng Anh (hệ chất lượng cao)",
        "QUY ĐỊNH TỔ CHỨC ĐÀO TẠO VÀ KIỂM TRA CHUẨN ĐẦU RA TIẾNG ANH TRÌNH ĐỘ ĐẠI HỌC CHÍNH QUY HỆ CHẤT LƯỢNG CAO TẠI HỌC VIỆN",
        "980/QĐ-HV ngày 29/10/2021",
        "quy_dinh",
        "chat_luong_cao",
        112,
        119,
        None,
        True,
        None,
        True,
        "HỆ CHẤT LƯỢNG CAO TẠI HỌC VIỆN",
    ),
    DocSpec(
        "dang_ky_mon_hoc",
        "Hướng dẫn đăng ký môn học và tra cứu thời khóa biểu, thông tin học tập của sinh viên",
        "HƯỚNG DẪN ĐĂNG KÝ MÔN HỌC VÀ TRA CỨU THỜI KHÓA BIỂU, THÔNG TIN HỌC TẬP CỦA SINH VIÊN",
        None,
        "huong_dan",
        None,
        120,
        126,
        None,
        False,
        None,
        True,
        "HƯỚNG DẪN ĐĂNG KÝ MÔN HỌC VÀ TRA CỨU THỜI KHÓA BIỂU",
    ),
    DocSpec(
        "cong_tac_sinh_vien",
        "Quy định công tác sinh viên trình độ đại học hình thức chính quy",
        "QUY ĐỊNH CÔNG TÁC SINH VIÊN TRÌNH ĐỘ ĐẠI HỌC HÌNH THỨC CHÍNH QUY CỦA HỌC VIỆN",
        "589/QĐ-HV ngày 28/04/2023",
        "quy_dinh",
        None,
        127,
        150,
        None,
        True,
        None,
        True,
        "QUY ĐỊNH CÔNG TÁC SINH VIÊN TRÌNH ĐỘ ĐẠI HỌC",
    ),
    DocSpec(
        "quy_hoc_bong",
        "Quy định về tạo lập, quản lý và sử dụng quỹ học bổng và hỗ trợ người học",
        "QUY ĐỊNH VỀ TẠO LẬP, QUẢN LÝ VÀ SỬ DỤNG QUỸ HỌC BỔNG VÀ HỖ TRỢ NGƯỜI HỌC TẠI HỌC VIÊN",
        "542/QĐ-HV ngày 13/03/2026",
        "quy_dinh",
        None,
        151,
        170,
        None,
        True,
        None,
        True,
        "QUY ĐỊNH VỀ TẠO LẬP, QUẢN LÝ VÀ SỬ DỤNG QUỸ HỌC BỔNG",
    ),
    DocSpec(
        "thu_nop_hoc_phi",
        "Quy định về thu nộp học phí và các khoản thu khác",
        "QUY ĐỊNH VỀ THU NỘP HỌC PHÍ VÀ CÁC KHOẢN THU KHÁC TẠI HỌC VIỆN",
        "1989/QĐ-HV ngày 28/12/2022",
        "quy_dinh",
        None,
        171,
        176,
        None,
        True,
        None,
        True,
        "QUY ĐỊNH VỀ THU NỘP HỌC PHÍ",
    ),
    DocSpec(
        "van_hoa_hoc_duong",
        "Quy định về văn hóa học đường và chuẩn mực ứng xử của người học",
        "QUY ĐỊNH VỀ VĂN HÓA HỌC ĐƯỜNG VÀ CHUẨN MỰC ỨNG XỬ CỦA NGƯỜI HỌC TẠI HỌC VIỆN",
        "838/QĐ-HV ngày 11/10/2021",
        "quy_dinh",
        None,
        177,
        182,
        None,
        True,
        None,
        True,
        "QUY ĐỊNH VỀ VĂN HÓA HỌC ĐƯỜNG",
    ),
    DocSpec(
        "nd_238_2025",
        "Nghị định 238/2025/NĐ-CP",
        "Nghị định 238/2025/NĐ-CP",
        "238/2025/NĐ-CP ngày 03/09/2025",
        "van_ban_nha_nuoc",
        None,
        183,
        191,
        None,
        True,
        None,
        True,
        "MỘT SỐ CHÍNH SÁCH CỦA NHÀ NƯỚC VỀ HỌC PHÍ VÀ TÍN DỤNG",
    ),
    DocSpec(
        "qd_05_2022_ttg",
        "Quyết định 05/2022/QĐ-TTg",
        "Quyết định 05/2022/QĐ-TTg",
        "05/2022/QĐ-TTg ngày 23/03/2022",
        "van_ban_nha_nuoc",
        None,
        191,
        193,
        r"^II/\s*Quyết định số 05/2022/QĐ-TTg",
        True,
        None,
        True,
        None,
    ),
    DocSpec(
        "qd_29_2025_ttg",
        "Quyết định 29/2025/QĐ-TTg",
        "Quyết định 29/2025/QĐ-TTg",
        "29/2025/QĐ-TTg ngày 28/08/2025",
        "van_ban_nha_nuoc",
        None,
        193,
        197,
        r"^III\.\s*Quyết định 29/2025/QĐ-TTg",
        True,
        None,
        True,
        None,
    ),
    DocSpec(
        "qd_29_2025_phu_luc_1",
        "Phụ lục I (kèm Quyết định 29/2025/QĐ-TTg): mẫu tờ khai tại thời điểm đề nghị Ngân hàng Chính sách xã hội cho vay vốn",
        "Phụ lục I (kèm Quyết định 29/2025/QĐ-TTg): mẫu tờ khai tại thời điểm đề nghị Ngân hàng Chính sách xã hội cho vay vốn",
        None,
        "phu_luc",
        None,
        197,
        199,
        r"^PHỤ LỤC I\s*$",
        False,
        "qd_29_2025_ttg",
        True,
        None,
    ),
    DocSpec(
        "phu_luc_2_to_khai_hang_nam",
        "Phụ lục II: mẫu tờ khai thông tin hằng năm của người học",
        "Phụ lục II: mẫu tờ khai thông tin hằng năm của người học",
        None,
        "phu_luc",
        None,
        200,
        201,
        None,
        False,
        None,
        False,
        "MẪU TỜ KHAI THÔNG TIN HẰNG NĂM",
    ),
    DocSpec(
        "thu_tuc_hanh_chinh",
        "Hướng dẫn thủ tục hành chính của Phòng Công tác sinh viên",
        "HƯỚNG DẪN THỦ TỤC HÀNH CHÍNH",
        None,
        "huong_dan",
        None,
        202,
        202,
        None,
        False,
        None,
        False,
        "HƯỚNG DẪN THỦ TỤC HÀNH CHÍNH",
    ),
    DocSpec(
        "cam_nang_sinh_vien",
        "Phần VI: Cẩm nang sinh viên",
        "PHẦN VI: CẨM NANG SINH VIÊN",
        None,
        "free_text",
        None,
        203,
        213,
        None,
        False,
        None,
        False,
        "CẨM NANG SINH VIÊN",
    ),
)


def get_doc(doc_id: str) -> DocSpec:
    """Trả về spec có ``doc_id`` tương ứng."""
    for spec in REGISTRY:
        if spec.doc_id == doc_id:
            return spec
    raise KeyError(doc_id)


def docs_on_page(pdf_page: int) -> list[DocSpec]:
    """Trả về các văn bản có phạm vi chứa trang PDF đã cho."""
    return [
        spec
        for spec in REGISTRY
        if spec.start_pdf_page <= pdf_page <= spec.end_pdf_page
    ]


def validate_registry() -> list[str]:
    """Kiểm tra các bất biến cấu trúc của registry."""
    issues: list[str] = []
    seen_ids: set[str] = set()
    all_ids = {spec.doc_id for spec in REGISTRY}

    for index, spec in enumerate(REGISTRY):
        if spec.doc_id in seen_ids:
            issues.append(f"doc_id trùng: {spec.doc_id}")
        seen_ids.add(spec.doc_id)

        if spec.start_pdf_page > spec.end_pdf_page:
            issues.append(f"phạm vi ngược: {spec.doc_id}")

        if spec.start_marker is not None:
            try:
                re.compile(spec.start_marker)
            except re.error as exc:
                issues.append(f"start_marker không hợp lệ: {spec.doc_id}: {exc}")

        if spec.parent_id is not None and spec.parent_id not in all_ids:
            issues.append(f"parent_id không tồn tại: {spec.doc_id}: {spec.parent_id}")

        if index == 0:
            continue

        previous = REGISTRY[index - 1]
        if spec.start_pdf_page < previous.start_pdf_page:
            issues.append(f"thứ tự start giảm: {spec.doc_id}")

        if spec.start_pdf_page <= previous.end_pdf_page:
            shared_pages = previous.end_pdf_page - spec.start_pdf_page + 1
            if shared_pages != 1:
                issues.append(f"chồng lấn quá một trang: {previous.doc_id}, {spec.doc_id}")
            if spec.start_marker is None:
                issues.append(f"chung trang nhưng thiếu marker: {spec.doc_id}")

    for required_id in (
        "qd_05_2022_ttg",
        "qd_29_2025_ttg",
        "qd_29_2025_phu_luc_1",
    ):
        try:
            spec = get_doc(required_id)
        except KeyError:
            issues.append(f"thiếu spec bắt buộc: {required_id}")
        else:
            if spec.start_marker is None:
                issues.append(f"spec bắt buộc thiếu marker: {required_id}")

    return issues
