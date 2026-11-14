"""
uv run --with pymupdf --with pdfplumber --with pypdf python scripts/survey_pdf_v2.py data/raw/So_tay_sinh_vien_PTIT.pdf
"""

import sys
import re
import unicodedata
from collections import Counter
from pathlib import Path


def safe_trunc(s, n=110):
    s = str(s).replace("\n", " ").strip()
    return s[:n] if len(s) > n else s


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/survey_pdf_v2.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: File {pdf_path} not found.")
        sys.exit(1)

    # Khởi tạo các thư viện
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    import pdfplumber
    import pypdf

    # =========================================================================
    # MỤC 1: Tách từ tiếng Việt
    # =========================================================================
    print("== Mục 1 ==")
    try:
        single_re = re.compile(r"(?<!\S)[^\W\d_](?!\S)")
        # Regex tìm dòng có chữ cái đứng riêng giữa 2 từ (ví dụ phân mảnh từ)
        fragment_re = re.compile(r"\b\w{2,}\s+[^\W\d_]\s+\w{2,}\b")

        doc_fitz = fitz.open(pdf_path)
        pdf_plumber = pdfplumber.open(pdf_path)
        reader_pypdf = pypdf.PdfReader(str(pdf_path))

        extractors = [
            ("pymupdf", [p.get_text("text") for p in doc_fitz]),
            ("pdfplumber", [p.extract_text() or "" for p in pdf_plumber.pages]),
            ("pypdf", [p.extract_text() or "" for p in reader_pypdf.pages])
        ]

        for lib_name, raw_pages in extractors:
            pages_nfc = [unicodedata.normalize("NFC", t) for t in raw_pages]
            full_text = "\n".join(pages_nfc)
            tokens = full_text.split()
            total_tokens = len(tokens)
            singles = [t for t in tokens if single_re.match(t)]
            single_cnt = len(singles)
            ratio_1000 = (single_cnt / total_tokens * 1000) if total_tokens else 0.0
            top8 = Counter(singles).most_common(8)
            non_space_chars = len(re.sub(r"\s+", "", full_text))

            # Tìm 3 dòng ví dụ có chữ cái đứng riêng giữa các từ
            examples = []
            for line in full_text.splitlines():
                ls = line.strip()
                if fragment_re.search(ls):
                    examples.append(safe_trunc(ls, 100))
                    if len(examples) == 3:
                        break

            print(f"[{lib_name}] Tổng tokens: {total_tokens} | Ký tự không khoảng trắng: {non_space_chars}")
            print(f"[{lib_name}] Chữ cái đứng riêng: {single_cnt} ({ratio_1000:.2f} / 1000 tokens)")
            print(f"[{lib_name}] Top 8 chữ cái đứng riêng: {top8}")
            print(f"[{lib_name}] 3 dòng ví dụ chứa chữ cái đứng riêng:")
            for ex in examples:
                print(f"  - {ex}")
    except Exception as e:
        print(f"LỖI mục 1: {e}")

    # =========================================================================
    # MỤC 2: Trang có text < 50 ký tự
    # =========================================================================
    print("\n== Mục 2 ==")
    try:
        for lib_name, raw_pages in extractors:
            sparse_pages = [p_idx + 1 for p_idx, t in enumerate(raw_pages) if len(t.strip()) < 50]
            print(f"[{lib_name}] Các trang có text < 50 ký tự ({len(sparse_pages)} trang): {sparse_pages}")
    except Exception as e:
        print(f"LỖI mục 2: {e}")

    # =========================================================================
    # MỤC 3: Số trang in (dùng pymupdf)
    # =========================================================================
    print("\n== Mục 3 ==")
    try:
        fitz_pages = [unicodedata.normalize("NFC", p.get_text("text")) for p in doc_fitz]
        total_p = len(fitz_pages)

        offsets_counter = Counter()
        no_printed_num = []
        deviant_pages = []
        multi_cand_pages = []

        num_re = re.compile(r"^\d{1,3}$")

        for p_idx, text in enumerate(fitz_pages):
            pdf_p = p_idx + 1
            non_empty = [l.strip() for l in text.splitlines() if l.strip()]
            if not non_empty:
                no_printed_num.append(pdf_p)
                continue

            candidates = non_empty[:2] + non_empty[-2:]
            nums = [int(c) for c in candidates if num_re.match(c)]

            if len(nums) >= 2:
                multi_cand_pages.append((pdf_p, nums))

            if nums:
                printed = nums[0]
                offset = pdf_p - printed
                offsets_counter[offset] += 1
                if offset != 6:
                    deviant_pages.append((pdf_p, offset))
            else:
                no_printed_num.append(pdf_p)

        print(f"Histogram offset: {dict(sorted(offsets_counter.items()))}")
        print(f"Trang không thấy số in ({len(no_printed_num)} trang): {no_printed_num[:40]}")
        print(f"Trang có offset ≠ 6 ({len(deviant_pages)} trang): {deviant_pages[:40]}")
        print(f"Trang có ≥ 2 ứng viên số ({len(multi_cand_pages)} trang, in tối đa 20): {multi_cand_pages[:20]}")
    except Exception as e:
        print(f"LỖI mục 3: {e}")

    # =========================================================================
    # MỤC 4: Mục lục (Trang PDF 1 đến 6)
    # =========================================================================
    print("\n== Mục 4 ==")
    try:
        toc_lines = []
        for p_idx in range(min(6, total_p)):
            for l in fitz_pages[p_idx].splitlines():
                ls = l.strip()
                if ls:
                    toc_lines.append(safe_trunc(ls, 110))
                    if len(toc_lines) >= 60:
                        break
            if len(toc_lines) >= 60:
                break

        print(f"Mục lục trang 1-6 (in {len(toc_lines)} dòng đầu không rỗng):")
        for idx, line in enumerate(toc_lines):
            print(f"{idx+1:2d}: {line}")
    except Exception as e:
        print(f"LỖI mục 4: {e}")

    # =========================================================================
    # MỤC 5: Cấu trúc, regex chặt (dùng pymupdf)
    # =========================================================================
    print("\n== Mục 5 ==")
    try:
        dieu_loose_re = re.compile(r"^Điều\s+\d+")
        dieu_strict_re = re.compile(r"^Điều\s+(\d+)\.(\s|$)")
        chuong_re = re.compile(r"^Chương\s+([IVXLC]+)\b")

        non_strict_dieu = []
        total_chuong = 0
        all_strict_dieu = []

        for p_idx, text in enumerate(fitz_pages):
            pdf_p = p_idx + 1
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            for idx, l in enumerate(lines):
                if chuong_re.match(l):
                    total_chuong += 1

                if dieu_loose_re.match(l) and not dieu_strict_re.match(l):
                    non_strict_dieu.append((pdf_p, safe_trunc(l, 80)))

                m = dieu_strict_re.match(l)
                if m:
                    d_num = int(m.group(1))
                    prev_lines = lines[max(0, idx - 2):idx]
                    all_strict_dieu.append((pdf_p, d_num, safe_trunc(l, 80), prev_lines))

        print(f"5a. Số dòng khớp loose (^Điều \\d+) nhưng KHÔNG khớp strict: {len(non_strict_dieu)}")
        print("12 ví dụ đầu (trang PDF, dòng):")
        for p, l in non_strict_dieu[:12]:
            print(f"  Trang {p:3d}: {l}")

        print(f"\n5b. Tổng số dòng khớp ^Chương ([IVXLC]+)\\b: {total_chuong}")

        # 5c. Phân chia văn bản khi gặp Điều 1
        documents = []
        curr_doc = None
        for pdf_p, d_num, l_str, prev_lines in all_strict_dieu:
            if d_num == 1:
                if curr_doc is not None:
                    documents.append(curr_doc)
                curr_doc = {
                    "start_pdf_p": pdf_p,
                    "title_candidates": prev_lines,
                    "dieu_1_line": l_str,
                    "dieu_list": [(d_num, pdf_p)],
                }
            else:
                if curr_doc is not None:
                    curr_doc["dieu_list"].append((d_num, pdf_p))
        if curr_doc is not None:
            documents.append(curr_doc)

        print(f"\n5c. Phân chia văn bản theo Điều 1 ({len(documents)} văn bản):")
        for idx, doc_info in enumerate(documents):
            stt = idx + 1
            p_start = doc_info["start_pdf_p"]
            p_in = p_start - 6
            title = " // ".join(doc_info["title_candidates"]) if doc_info["title_candidates"] else "N/A"
            d1_name = doc_info["dieu_1_line"]
            d_nums = [d for d, p in doc_info["dieu_list"]]
            total_d = len(d_nums)
            max_d = max(d_nums) if d_nums else 0
            p_last = doc_info["dieu_list"][-1][1] if doc_info["dieu_list"] else p_start
            out_str = f"VB {stt} | PDF {p_start} (In {p_in}) -> PDF {p_last} | {total_d} Điều (Max: {max_d}) | {safe_trunc(title, 40)} | {safe_trunc(d1_name, 35)}"
            print(safe_trunc(out_str, 110))

        # 5d. Bất thường trong từng văn bản
        print("\n5d. Bất thường thứ tự Điều trong văn bản (b ≠ a + 1):")
        anomalies = []
        for idx, doc_info in enumerate(documents):
            d_list = doc_info["dieu_list"]
            for i in range(1, len(d_list)):
                a, p_a = d_list[i - 1]
                b, p_b = d_list[i]
                if b != a + 1:
                    anomalies.append((idx + 1, a, b, p_b))

        for vb_idx, a, b, p in anomalies[:30]:
            print(f"  VB {vb_idx}: Điều {a} → Điều {b} (Trang PDF {p})")

        # 5e. Dòng IN HOA bắt đầu bằng từ khóa
        print("\n5e. Dòng IN HOA bắt đầu bằng từ khóa pháp lý (tối đa 40):")
        kw_re = re.compile(r"^(QUY ĐỊNH|QUY CHẾ|QUY TRÌNH|HƯỚNG DẪN|CHÍNH SÁCH|QUYẾT ĐỊNH)\b")
        caps_lines = []
        last_l = None
        for p_idx, text in enumerate(fitz_pages):
            pdf_p = p_idx + 1
            for l in text.splitlines():
                ls = l.strip()
                if kw_re.match(ls) and ls == ls.upper() and len(ls) > 5:
                    if ls != last_l:
                        caps_lines.append((pdf_p, safe_trunc(ls, 85)))
                        last_l = ls

        for p, l in caps_lines[:40]:
            print(f"  (Trang {p:3d}) {l}")
    except Exception as e:
        print(f"LỖI mục 5: {e}")

    # =========================================================================
    # MỤC 6: Bảng khung chương trình không viền
    # =========================================================================
    print("\n== Mục 6 ==")
    try:
        # 6a. Trang chứa "Chi tiết về chương trình đào tạo"
        detail_pages = []
        for p_idx, text in enumerate(fitz_pages):
            if "Chi tiết về chương trình đào tạo" in text:
                detail_pages.append(p_idx + 1)
        print(f"6a. Trang chứa 'Chi tiết về chương trình đào tạo' ({len(detail_pages)} trang): {detail_pages}")

        # 6b. Trang đầu tiên chứa "Nhập môn học sâu"
        deep_p = None
        for p_idx, text in enumerate(fitz_pages):
            if "Nhập môn học sâu" in text:
                deep_p = p_idx + 1
                break

        print(f"\n6b. Trang đầu tiên chứa 'Nhập môn học sâu': Trang PDF {deep_p}")
        if deep_p:
            p_obj_fitz = doc_fitz[deep_p - 1]
            p_text = fitz_pages[deep_p - 1]
            lines_20 = [l.strip() for l in p_text.splitlines() if l.strip()][:20]
            print("20 dòng đầu text pymupdf:")
            for l in lines_20:
                print(f"  {safe_trunc(l, 100)}")

            # PyMuPDF find_tables(strategy="text")
            print("\n[PyMuPDF find_tables(strategy='text')]")
            tabs_mu = p_obj_fitz.find_tables(strategy="text")
            num_mu = len(tabs_mu.tables)
            print(f"Số bảng: {num_mu}")
            if num_mu > 0:
                t0_mu = tabs_mu.tables[0]
                print(f"Kích thước bảng 1: {t0_mu.row_count} hàng x {t0_mu.col_count} cột")
                rows_mu = t0_mu.extract()
                single_mu = sum(
                    len(single_re.findall(str(c)))
                    for r in rows_mu for c in r if c
                )
                print("3 hàng đầu tiên:")
                for r in rows_mu[:3]:
                    row_str = " | ".join(safe_trunc(c, 25) if c is not None else "" for c in r)
                    print(f"  {safe_trunc(row_str, 105)}")
                print(f"Số chữ cái đứng riêng trong bảng 1: {single_mu}")

            # pdfplumber extract_tables
            print("\n[pdfplumber extract_tables (vertical/horizontal strategy='text')]")
            p_obj_pl = pdf_plumber.pages[deep_p - 1]
            tabs_pl = p_obj_pl.extract_tables({"vertical_strategy": "text", "horizontal_strategy": "text"})
            num_pl = len(tabs_pl)
            print(f"Số bảng: {num_pl}")
            if num_pl > 0:
                t0_pl = tabs_pl[0]
                rows_cnt = len(t0_pl)
                cols_cnt = len(t0_pl[0]) if rows_cnt > 0 else 0
                print(f"Kích thước bảng 1: {rows_cnt} hàng x {cols_cnt} cột")
                single_pl = sum(
                    len(single_re.findall(str(c)))
                    for r in t0_pl for c in r if c
                )
                print("3 hàng đầu tiên:")
                for r in t0_pl[:3]:
                    row_str = " | ".join(safe_trunc(c, 25) if c is not None else "" for c in r)
                    print(f"  {safe_trunc(row_str, 105)}")
                print(f"Số chữ cái đứng riêng trong bảng 1: {single_pl}")
    except Exception as e:
        print(f"LỖI mục 6: {e}")


if __name__ == "__main__":
    main()
