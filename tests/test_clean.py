from naive_assistant.ingest.clean import strip_page_number


def test_strip_hyphenated_page_number():
    assert strip_page_number("- 124 -\nĐiều 5. A", 124) == "Điều 5. A"


def test_strip_plain_page_number():
    assert strip_page_number("102\nPHỤ LỤC 1", 102) == "PHỤ LỤC 1"


def test_strip_first_nonempty_page_number_only():
    assert strip_page_number("15 \n\nPHẦN III", 15) == "\nPHẦN III"


def test_keep_different_page_number():
    text = "5\nabc"
    assert strip_page_number(text, 6) == text


def test_keep_page_number_at_end():
    text = "Điều 1\n- 6 -"
    assert strip_page_number(text, 6) == text


def test_keep_number_with_other_text():
    text = "102 Điều"
    assert strip_page_number(text, 102) == text


def test_keep_text_when_printed_page_is_none():
    text = "- 124 -\nĐiều 5. A"
    assert strip_page_number(text, None) == text
