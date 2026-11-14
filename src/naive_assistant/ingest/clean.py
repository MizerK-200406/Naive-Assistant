"""Các phép làm sạch text trang không phụ thuộc bộ trích xuất PDF."""

from __future__ import annotations

import re


def strip_page_number(text: str, printed_page: int | None) -> str:
    """Bỏ đúng dòng số trang in nếu đó là dòng không rỗng đầu tiên."""
    if printed_page is None:
        return text

    lines = text.splitlines(keepends=True)
    pattern = re.compile(rf"-?\s*{re.escape(str(printed_page))}\s*-?")

    for index, line in enumerate(lines):
        candidate = line.strip()
        if not candidate:
            continue
        if pattern.fullmatch(candidate):
            return "".join(lines[:index] + lines[index + 1 :])
        return text

    return text
