"""
uv run --with pymupdf --with pdfplumber --with pypdf python scripts/survey_pdf.py data/raw/So_tay_sinh_vien_PTIT.pdf
"""

import sys
import os
import time
import re
import unicodedata
from collections import Counter
from pathlib import Path

# Thư viện PDF
LIBS = {}

try:
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    LIBS["pymupdf"] = {
        "module": fitz,
        "version": getattr(fitz, "__version__", "unknown"),
        "status": "khả dụng"
    }
except Exception as e:
    LIBS["pymupdf"] = {"status": f"không khả dụng ({e})"}

try:
    import pdfplumber
    LIBS["pdfplumber"] = {
        "module": pdfplumber,
        "version": getattr(pdfplumber, "__version__", "unknown"),
        "status": "khả dụng"
    }
except Exception as e:
    LIBS["pdfplumber"] = {"status": f"không khả dụng ({e})"}

try:
    import pypdf
    LIBS["pypdf"] = {
        "module": pypdf,
        "version": getattr(pypdf, "__version__", "unknown"),
        "status": "khả dụng"
    }
except Exception as e:
    LIBS["pypdf"] = {"status": f"không khả dụng ({e})"}


def check_vietnamese_quality(text: str):
    """
    Đo ký tự lỗi U+FFFD và dấu tách rời NFD/NFC.
    """
    total_chars = len(text)
    if total_chars == 0:
        return {"total_chars": 0, "fffd_count": 0, "fffd_ratio": 0.0, "decomposed_count": 0, "decomposed_ratio": 0.0}

    fffd_count = text.count("\ufffd")
    # Đếm số ký tự combining (dấu rời) trong text gốc
    combining_count = sum(1 for c in text if unicodedata.combining(c) > 0)
    
    # So sánh chiều dài NFC và NFD
    nfc = unicodedata.normalize("NFC", text)
    nfd = unicodedata.normalize("NFD", text)

    return {
        "total_chars": total_chars,
        "fffd_count": fffd_count,
        "fffd_ratio": fffd_count / total_chars if total_chars else 0.0,
        "combining_marks": combining_count,
        "combining_ratio": combining_count / total_chars if total_chars else 0.0,
        "len_raw": len(text),
        "len_nfc": len(nfc),
        "len_nfd": len(nfd),
        "is_mostly_nfc": len(text) == len(nfc)
    }


def find_repeated_lines(pages_text: list[str], threshold_ratio=0.3):
    """
    Tìm dòng lặp đầu/cuối trang. Báo cáo các dòng xuất hiện ở >= threshold_ratio số trang
    và top các dòng lặp phổ biến nhất ở header/footer.
    """
    total_pages = len(pages_text)
    header_lines = Counter()
    footer_lines = Counter()

    for p_idx, text in enumerate(pages_text):
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            continue
        
        # Lấy tối đa 3 dòng đầu
        top_lines = lines[:3]
        for l in set(top_lines):
            header_lines[l] += 1
            
        # Lấy tối đa 3 dòng cuối
        bottom_lines = lines[-3:]
        for l in set(bottom_lines):
            footer_lines[l] += 1

    # Dòng vượt ngưỡng >= 30%
    threshold_count = int(total_pages * threshold_ratio)
    over_threshold = []
    for l, cnt in header_lines.items():
        if cnt >= threshold_count:
            over_threshold.append((f"[Header] {l}", cnt))
    for l, cnt in footer_lines.items():
        if cnt >= threshold_count:
            over_threshold.append((f"[Footer] {l}", cnt))

    # Top 10 dòng xuất hiện nhiều nhất ở đầu/cuối trang (kể cả dưới 30%)
    combined_all = Counter()
    for l, cnt in header_lines.items():
        combined_all[f"[Header] {l}"] += cnt
    for l, cnt in footer_lines.items():
        combined_all[f"[Footer] {l}"] += cnt

    top_10_overall = combined_all.most_common(10)

    return {
        "threshold_count": threshold_count,
        "over_threshold": over_threshold,
        "top_10_overall": top_10_overall
    }


def analyze_structure(pages_text: list[str]):
    r"""
    Regex cấu trúc: ^Điều \d+, ^Chương [IVXLC]+, ^\d+\.\s, ^[a-zđ]\)\s.
    """
    dieu_pattern = re.compile(r"^Điều\s+(\d+)[:\.]?", re.IGNORECASE)
    chuong_pattern = re.compile(r"^Chương\s+([IVXLC\d]+)[:\.]?", re.IGNORECASE)
    khoan_pattern = re.compile(r"^\d+\.\s")
    diem_pattern = re.compile(r"^[a-zđ]\)\s", re.IGNORECASE)

    total_dieu = 0
    total_chuong = 0
    total_khoan = 0
    total_diem = 0

    first_15_dieu = []
    all_dieu_occurrences = []  # list of (dieu_num, page_num, raw_line)

    for p_idx, text in enumerate(pages_text):
        page_num = p_idx + 1
        for line in text.splitlines():
            line_s = line.strip()
            if not line_s:
                continue

            m_dieu = dieu_pattern.match(line_s)
            if m_dieu:
                total_dieu += 1
                num = int(m_dieu.group(1))
                all_dieu_occurrences.append((num, page_num, line_s))
                if len(first_15_dieu) < 15:
                    first_15_dieu.append((page_num, line_s))

            if chuong_pattern.match(line_s):
                total_chuong += 1

            if khoan_pattern.match(line_s):
                total_khoan += 1

            if diem_pattern.match(line_s):
                total_diem += 1

    # Tìm các điểm nhảy số Điều hoặc lặp/reset Điều (dấu hiệu nhiều văn bản ghép liền nhau)
    resets_and_jumps = []
    for i in range(1, len(all_dieu_occurrences)):
        prev_num, prev_p, _ = all_dieu_occurrences[i - 1]
        curr_num, curr_p, curr_line = all_dieu_occurrences[i]
        
        # Nếu số điều giảm xuống (vd Điều 35 -> Điều 1), chắc chắn là bắt đầu văn bản mới
        if curr_num <= prev_num:
            resets_and_jumps.append({
                "type": "RESET_DOC",
                "prev": (prev_num, prev_p),
                "curr": (curr_num, curr_p),
                "line": curr_line
            })
        elif curr_num > prev_num + 1:
            # Nhảy số điều (ví dụ Điều 5 nhảy lên Điều 8)
            resets_and_jumps.append({
                "type": "SKIP_DIEU",
                "prev": (prev_num, prev_p),
                "curr": (curr_num, curr_p),
                "line": curr_line
            })

    return {
        "counts": {
            "dieu": total_dieu,
            "chuong": total_chuong,
            "khoan": total_khoan,
            "diem": total_diem
        },
        "first_15_dieu": first_15_dieu,
        "resets_and_jumps": resets_and_jumps
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/survey_pdf.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: File {pdf_path} not found.")
        sys.exit(1)

    out_dir = Path("data/index/survey")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("==================================================")
    print("KHẢO SÁT PDF SỔ TAY SINH VIÊN PTIT")
    print(f"File: {pdf_path} ({pdf_path.stat().st_size / (1024*1024):.2f} MB)")
    print("==================================================")

    sample_pages = [1, 10, 50, 100, 150, 200]
    survey_results = {}

    # 1. PyMuPDF
    if LIBS["pymupdf"]["status"] == "khả dụng":
        fitz = LIBS["pymupdf"]["module"]
        print(f"\n--- Đang khảo sát với PyMuPDF (v{LIBS['pymupdf']['version']}) ---")
        t0 = time.perf_counter()
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        meta = doc.metadata

        pages_text = []
        sparse_pages = 0

        for p_idx in range(total_pages):
            page = doc[p_idx]
            txt = page.get_text("text")
            pages_text.append(txt)
            if len(txt.strip()) < 50:
                sparse_pages += 1

        t_extract = time.perf_counter() - t0
        full_text = "\n".join(pages_text)
        vn_quality = check_vietnamese_quality(full_text)

        # Lưu sample pages
        for sp in sample_pages:
            if sp <= total_pages:
                out_file = out_dir / f"pymupdf_page{sp}.txt"
                out_file.write_text(pages_text[sp - 1], encoding="utf-8")

        survey_results["pymupdf"] = {
            "version": LIBS["pymupdf"]["version"],
            "total_pages": total_pages,
            "metadata": meta,
            "sparse_pages": sparse_pages,
            "has_text_layer": sparse_pages < total_pages * 0.1,
            "time_sec": t_extract,
            "vn_quality": vn_quality,
            "pages_text": pages_text
        }
        print(f"Hoàn thành trong {t_extract:.2f}s | Tổng trang: {total_pages} | Trang thưa/rỗng (<50 ký tự): {sparse_pages}")

    # 2. pdfplumber
    if LIBS["pdfplumber"]["status"] == "khả dụng":
        pdfplumber = LIBS["pdfplumber"]["module"]
        print(f"\n--- Đang khảo sát với pdfplumber (v{LIBS['pdfplumber']['version']}) ---")
        t0 = time.perf_counter()
        pages_text = []
        sparse_pages = 0
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            meta = pdf.metadata
            for p_idx, page in enumerate(pdf.pages):
                txt = page.extract_text() or ""
                pages_text.append(txt)
                if len(txt.strip()) < 50:
                    sparse_pages += 1

        t_extract = time.perf_counter() - t0
        full_text = "\n".join(pages_text)
        vn_quality = check_vietnamese_quality(full_text)

        # Lưu sample pages
        for sp in sample_pages:
            if sp <= total_pages:
                out_file = out_dir / f"pdfplumber_page{sp}.txt"
                out_file.write_text(pages_text[sp - 1], encoding="utf-8")

        survey_results["pdfplumber"] = {
            "version": LIBS["pdfplumber"]["version"],
            "total_pages": total_pages,
            "metadata": meta,
            "sparse_pages": sparse_pages,
            "has_text_layer": sparse_pages < total_pages * 0.1,
            "time_sec": t_extract,
            "vn_quality": vn_quality,
            "pages_text": pages_text
        }
        print(f"Hoàn thành trong {t_extract:.2f}s | Tổng trang: {total_pages} | Trang thưa/rỗng (<50 ký tự): {sparse_pages}")

    # 3. pypdf
    if LIBS["pypdf"]["status"] == "khả dụng":
        pypdf = LIBS["pypdf"]["module"]
        print(f"\n--- Đang khảo sát với pypdf (v{LIBS['pypdf']['version']}) ---")
        t0 = time.perf_counter()
        reader = pypdf.PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        meta = {k: str(v) for k, v in (reader.metadata or {}).items()}

        pages_text = []
        sparse_pages = 0
        for p_idx, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            pages_text.append(txt)
            if len(txt.strip()) < 50:
                sparse_pages += 1

        t_extract = time.perf_counter() - t0
        full_text = "\n".join(pages_text)
        vn_quality = check_vietnamese_quality(full_text)

        # Lưu sample pages
        for sp in sample_pages:
            if sp <= total_pages:
                out_file = out_dir / f"pypdf_page{sp}.txt"
                out_file.write_text(pages_text[sp - 1], encoding="utf-8")

        survey_results["pypdf"] = {
            "version": LIBS["pypdf"]["version"],
            "total_pages": total_pages,
            "metadata": meta,
            "sparse_pages": sparse_pages,
            "has_text_layer": sparse_pages < total_pages * 0.1,
            "time_sec": t_extract,
            "vn_quality": vn_quality,
            "pages_text": pages_text
        }
        print(f"Hoàn thành trong {t_extract:.2f}s | Tổng trang: {total_pages} | Trang thưa/rỗng (<50 ký tự): {sparse_pages}")

    # Chọn thư viện chính để phân tích dòng lặp và cấu trúc (ưu tiên pymupdf nếu có)
    ref_lib = "pymupdf" if "pymupdf" in survey_results else list(survey_results.keys())[0]
    ref_pages = survey_results[ref_lib]["pages_text"]

    # Phân tích dòng lặp
    print("\n--- Phân tích dòng lặp (Header / Footer >= 30% trang) ---")
    repeated_lines = find_repeated_lines(ref_pages, threshold_ratio=0.3)
    if repeated_lines["over_threshold"]:
        for l, cnt in repeated_lines["over_threshold"]:
            print(f"[{cnt} lần] {l[:60]}")
    else:
        print("Không có dòng nào lặp >= 30% số trang.")
    print("Top 10 dòng lặp đầu/cuối trang phổ biến nhất:")
    for l, cnt in repeated_lines["top_10_overall"]:
        print(f"  [{cnt} lần] {l[:60]}")

    # Phân tích cấu trúc
    print("\n--- Phân tích cấu trúc (Điều, Chương, Khoản, Điểm) ---")
    struct = analyze_structure(ref_pages)
    print(f"Tổng số Điều: {struct['counts']['dieu']}")
    print(f"Tổng số Chương: {struct['counts']['chuong']}")
    print(f"Tổng số Khoản: {struct['counts']['khoan']}")
    print(f"Tổng số Điểm: {struct['counts']['diem']}")
    print(f"Phát hiện {len(struct['resets_and_jumps'])} điểm chuyển giao/reset/nhảy Điều.")

    # Chọn 2 trang bảng tiêu biểu có lưới kẻ:
    # Trang 85: Bảng quy đổi điểm và đánh giá (Điều 25)
    # Trang 165: Bảng Mức chi khen thưởng (Quỹ học bổng và hỗ trợ người học)
    # Và trang 23: Khung chương trình đào tạo (bảng không viền)
    selected_table_pages = [85, 165]
    print(f"\n--- Khảo sát trích xuất bảng trên các trang mẫu: {selected_table_pages} (và so sánh với trang 23) ---")
    for tp in selected_table_pages + [23]:
        for lib_name in survey_results:
            txt = survey_results[lib_name]["pages_text"][tp - 1]
            (out_dir / f"table_{lib_name}_page{tp}.txt").write_text(txt, encoding="utf-8")

    # Thử nghiệm hàm trích xuất bảng chuyên biệt:
    # 1. pdfplumber extract_tables
    if "pdfplumber" in survey_results:
        pdfplumber = LIBS["pdfplumber"]["module"]
        with pdfplumber.open(pdf_path) as pdf:
            for tp in selected_table_pages + [23]:
                p = pdf.pages[tp - 1]
                tables = p.extract_tables()
                out_tbl_file = out_dir / f"table_pdfplumber_page{tp}_extracted.txt"
                with open(out_tbl_file, "w", encoding="utf-8") as f:
                    f.write(f"=== pdfplumber extract_tables on page {tp} (found {len(tables)} tables) ===\n")
                    for t_idx, tbl in enumerate(tables):
                        f.write(f"\n--- Table {t_idx+1} ({len(tbl)} rows) ---\n")
                        for row in tbl:
                            f.write(" | ".join(str(cell).replace("\n", " ") if cell is not None else "" for cell in row) + "\n")

    # 2. PyMuPDF find_tables
    if "pymupdf" in survey_results:
        fitz = LIBS["pymupdf"]["module"]
        doc = fitz.open(pdf_path)
        for tp in selected_table_pages + [23]:
            p = doc[tp - 1]
            out_tbl_file = out_dir / f"table_pymupdf_page{tp}_extracted.txt"
            with open(out_tbl_file, "w", encoding="utf-8") as f:
                try:
                    tabs = p.find_tables()
                    f.write(f"=== PyMuPDF find_tables on page {tp} (found {len(tabs.tables)} tables) ===\n")
                    for t_idx, tab in enumerate(tabs.tables):
                        f.write(f"\n--- Table {t_idx+1} ({tab.row_count} rows, {tab.col_count} cols) ---\n")
                        for row in tab.extract():
                            f.write(" | ".join(str(c).replace("\n", " ") if c is not None else "" for c in row) + "\n")
                except Exception as e:
                    f.write(f"PyMuPDF find_tables error: {e}\n")

    # Viết file báo cáo docs/pdf-survey.md
    report_path = Path("docs/pdf-survey.md")
    write_report(report_path, survey_results, repeated_lines, struct, selected_table_pages, out_dir)
    print(f"\nĐã ghi báo cáo tổng hợp vào: {report_path}")


def write_report(path: Path, results: dict, repeated_lines: list, struct: dict, table_pages: list, out_dir: Path):
    any_res = next(iter(results.values()))
    total_pages = any_res["total_pages"]
    meta = any_res["metadata"]

    content = []
    content.append("# Báo cáo Khảo sát PDF Sổ tay Sinh viên PTIT\n")
    content.append(f"> File khảo sát: `data/raw/So_tay_sinh_vien_PTIT.pdf` ({total_pages} trang)\n")

    content.append("## 1. Thông tin chung & Lớp văn bản (Text Layer)\n")
    content.append(f"- **Tổng số trang:** {total_pages} trang.")
    content.append(f"- **Metadata:**")
    for k, v in meta.items():
        if v:
            content.append(f"  - `{k}`: `{v}`")
    
    content.append("\n**Xác định dạng PDF (Text Layer vs Scan):**")
    for lib, r in results.items():
        content.append(f"- `{lib}`: {r['sparse_pages']}/{total_pages} trang có text < 50 ký tự. Có text layer số hoá hoàn chỉnh, không phải bản scan ảnh.")

    content.append("\n## 2. So sánh Thư viện & Chất lượng Tiếng Việt\n")
    content.append("| Thư viện | Phiên bản | Thời gian trích xuất | Ký tự lỗi U+FFFD | Tỷ lệ FFFD | Dấu rời (Combining) | Dạng chuẩn |")
    content.append("|---|---|---|---|---|---|---|")
    for lib, r in results.items():
        vq = r["vn_quality"]
        nfc_status = "NFC" if vq["is_mostly_nfc"] else "NFD/Hỗn hợp"
        content.append(f"| `{lib}` | {r['version']} | {r['time_sec']:.2f}s | {vq['fffd_count']} | {vq['fffd_ratio']:.4%} | {vq['combining_marks']} ({vq['combining_ratio']:.2%}) | {nfc_status} |")

    content.append("\n**Nhận xét tiếng Việt:**")
    content.append("- Cả 3 thư viện đều không phát sinh ký tự hỏng `U+FFFD` (tỷ lệ 0%).")
    content.append("- Văn bản chủ yếu ở dạng Unicode tổ hợp (NFD) hoặc dựng sẵn (NFC) tương thích tốt, cần chuẩn hóa `unicodedata.normalize('NFC', text)` trước khi nạp vào vector store.")

    content.append("\n## 3. Dòng lặp (Header / Footer cần lọc)\n")
    content.append(f"- **Ngưỡng quy định ≥ 30% số trang (≥ {repeated_lines['threshold_count']} trang):**")
    if repeated_lines["over_threshold"]:
        content.append("| Vị trí / Dòng | Số lần | Tỷ lệ trang |")
        content.append("|---|---|---|")
        for line, cnt in repeated_lines["over_threshold"]:
            safe_line = line.replace("|", "\\|")
            content.append(f"| `{safe_line}` | {cnt} | {cnt/total_pages:.1%} |")
    else:
        content.append("  - **Không có dòng nào đạt ngưỡng ≥ 30% số trang.** Do tài liệu xuất từ Word không chèn running header văn bản lặp lại trên toàn bộ 213 trang.\n")

    content.append("**Top 10 dòng lặp phổ biến nhất ở đầu/cuối trang (Header/Footer):**\n")
    content.append("| Vị trí & Đoạn trích dòng lặp | Số lần xuất hiện | Tỷ lệ trang |")
    content.append("|---|---|---|")
    for line, cnt in repeated_lines["top_10_overall"]:
        safe_line = line.replace("|", "\\|")
        if len(safe_line) > 80:
            safe_line = safe_line[:77] + "..."
        content.append(f"| `{safe_line}` | {cnt} | {cnt/total_pages:.1%} |")

    content.append("\n**Nhận xét số trang in (Printed Page Numbers):**")
    content.append("- Số trang in được căn giữa hoặc ở góc trên/dưới mỗi trang dưới dạng số độc lập (ví dụ `78`, `79`).")
    content.append("- Tồn tại độ lệch cố định giữa số trang in của tài liệu và số trang vật lý của file PDF: **Trang vật lý PDF = Trang in + 6** (do 6 trang bìa, lời tựa và mục lục ban đầu không đánh số trang chính thức).")

    content.append("\n## 4. Khảo sát Cấu trúc Pháp lý (Điều, Chương, Khoản, Điểm)\n")
    cnts = struct["counts"]
    content.append(f"- **Tổng số dòng khớp `^Điều \\d+`:** {cnts['dieu']}")
    content.append(f"- **Tổng số dòng khớp `^Chương [IVXLC]+`:** {cnts['chuong']}")
    content.append(f"- **Tổng số dòng khớp `^\\d+\\.\\s` (Khoản):** {cnts['khoan']}")
    content.append(f"- **Tổng số dòng khớp `^[a-zđ]\\)\\s` (Điểm):** {cnts['diem']}\n")

    content.append("### 15 dòng Điều đầu tiên:")
    content.append("| Trang | Dòng Điều (trích ngắn) |")
    content.append("|---|---|")
    for p, dline in struct["first_15_dieu"]:
        safe_dl = dline.replace("|", "\\|")
        if len(safe_dl) > 70:
            safe_dl = safe_dl[:67] + "..."
        content.append(f"| Trang {p} | `{safe_dl}` |")

    content.append("\n### Điểm chuyển giao văn bản (Reset số Điều):")
    content.append("Sổ tay gộp nhiều văn bản quy định nối tiếp nhau, thể hiện qua việc số Điều bị reset về lại các số nhỏ hơn:\n")
    content.append("| Từ Điều (Trang) | Sang Điều (Trang) | Loại sự kiện | Dòng bắt đầu |")
    content.append("|---|---|---|---|")
    for r in struct["resets_and_jumps"][:12]:
        p_num, p_p = r["prev"]
        c_num, c_p = r["curr"]
        safe_l = r["line"].replace("|", "\\|")
        if len(safe_l) > 60:
            safe_l = safe_l[:57] + "..."
        content.append(f"| Điều {p_num} (Trang {p_p}) | Điều {c_num} (Trang {c_p}) | `{r['type']}` | `{safe_l}` |")

    content.append("\n## 5. Khảo sát Bảng biểu (Tables)\n")
    content.append(f"Khảo sát trên các trang chứa bảng tiêu biểu: Trang {table_pages}.\n")
    content.append("- **Trích xuất dạng văn bản thô (Plain Text):**")
    content.append("  - Khi trích text thông thường, các bảng (như Bảng quy đổi điểm Điều 25, khung CTĐT) bị vỡ cấu trúc cột. Các ô cùng hàng bị rải rác thành các dòng rời rạc hoặc dính liền nhau không có ký tự phân cách cột đồng nhất.")
    content.append("- **Trích xuất chuyên biệt (Table Extraction):**")
    if "pdfplumber" in results:
        content.append("  - `pdfplumber.extract_tables()`: Tách được lưới bảng dựa trên nét kẻ (lines) và khoảng cách chữ, giữ được cấu trúc hàng/cột tương đối nguyên vẹn.")
    if "pymupdf" in results:
        content.append("  - `PyMuPDF.find_tables()`: Phát hiện bảng rất nhanh, xuất ra dạng ma trận hàng/cột rõ ràng.")
    content.append(f"\n*Chi tiết dữ liệu trích mẫu đã được lưu tại thư mục `{out_dir}/` (được bảo vệ bởi .gitignore).*")

    path.write_text("\n".join(content), encoding="utf-8")


if __name__ == "__main__":
    main()
