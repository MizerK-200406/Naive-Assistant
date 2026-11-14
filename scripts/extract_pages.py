import sys
from pathlib import Path

from naive_assistant.ingest.extract import extract_pages, write_jsonl


def main():
    if len(sys.argv) < 2:
        pdf_path = Path("data/raw/So_tay_sinh_vien_PTIT.pdf")
    else:
        pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"Error: Không tìm thấy file {pdf_path}")
        sys.exit(1)

    out_path = Path("data/index/pages.jsonl")
    records = extract_pages(pdf_path)
    write_jsonl(records, out_path)
    print(f"Đã ghi {len(records)} trang vào {out_path}")


if __name__ == "__main__":
    main()
