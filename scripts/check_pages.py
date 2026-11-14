import json
from pathlib import Path


def main():
    pages_path = Path("data/index/pages.jsonl")
    if not pages_path.exists():
        print(f"Error: Không tìm thấy file {pages_path}")
        return

    with pages_path.open("r", encoding="utf-8") as f:
        pages = [json.loads(line) for line in f if line.strip()]

    # a. Tổng số trang và danh sách trang có n_chars < 50
    under_50 = [p["pdf_page"] for p in pages if p["n_chars"] < 50]
    print(f"Tổng số trang: {len(pages)}")
    print(f"Trang có n_chars < 50 ({len(under_50)} trang): {under_50}")

    # b. Đánh giá hai đoạn PDF 7-111 và 112-213
    def evaluate_segment(start_pdf: int, end_pdf: int):
        seg = [p for p in pages if start_pdf <= p["pdf_page"] <= end_pdf]
        match = [p for p in seg if p["printed_page"] in p["margin_numbers"]]
        empty = [p for p in seg if len(p["margin_numbers"]) == 0]
        mismatch = [
            p
            for p in seg
            if len(p["margin_numbers"]) > 0 and p["printed_page"] not in p["margin_numbers"]
        ]
        return len(match), len(empty), mismatch

    m1, e1, mis1 = evaluate_segment(7, 111)
    print(f"Đoạn PDF 7-111: Khớp={m1}, Rỗng={e1}, Lệch={len(mis1)}")
    if mis1:
        mis_list = [(p["pdf_page"], p["margin_numbers"]) for p in mis1[:30]]
        print(f"  Trang lệch PDF 7-111: {mis_list}")

    m2, e2, mis2 = evaluate_segment(112, 213)
    print(f"Đoạn PDF 112-213: Khớp={m2}, Rỗng={e2}, Lệch={len(mis2)}")
    if mis2:
        mis_list = [(p["pdf_page"], p["margin_numbers"]) for p in mis2[:30]]
        print(f"  Trang lệch PDF 112-213: {mis_list}")

    # c. 6 trang mẫu PDF 112, 130, 150, 170, 190, 210
    sample_pages = [112, 130, 150, 170, 190, 210]
    for sp in sample_pages:
        p = pages[sp - 1]
        lines = [line.strip() for line in p["text"].splitlines() if line.strip()]
        f2 = lines[:2]
        l2 = lines[-2:] if len(lines) >= 2 else lines
        print(f"PDF {p['pdf_page']} | In: {p['printed_page']} | Margin: {p['margin_numbers']}")
        for l in f2:
            print(f"  Đầu: {l[:70]}")
        for l in l2:
            print(f"  Cuối: {l[:70]}")


if __name__ == "__main__":
    main()
