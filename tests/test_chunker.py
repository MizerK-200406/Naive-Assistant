import naive_assistant.ingest.chunker as chunker
from naive_assistant.ingest.chunker import MAX_CHARS, chunk_document
from naive_assistant.ingest.registry import DocSpec


def make_spec(
    doc_id: str = "test_doc",
    start: int = 10,
    end: int = 10,
    marker: str | None = None,
    he: str | None = None,
) -> DocSpec:
    return DocSpec(
        doc_id=doc_id,
        short_name=f"Văn bản {doc_id}",
        title=f"Văn bản {doc_id}",
        decision=None,
        kind="quy_dinh",
        he=he,
        start_pdf_page=start,
        end_pdf_page=end,
        start_marker=marker,
        has_articles=True,
        parent_id=None,
        verified=True,
        probe=None,
    )


def test_three_clean_articles_make_three_chunks():
    pages = {10: "4\nĐiều 1. Một\nNội dung 1\nĐiều 2: Hai\nNội dung 2\nĐiều 3. Ba\nNội dung 3"}
    chunks = chunk_document(make_spec(), pages)

    assert [item.chunk_id for item in chunks] == [
        "test_doc:d1",
        "test_doc:d2",
        "test_doc:d3",
    ]


def test_long_article_splits_by_khoan_and_keeps_title():
    long_text = "x" * 920
    pages = {10: f"Điều 1. Dài\nDòng dẫn nhập\n1. {long_text}\n2. {long_text}"}
    chunks = chunk_document(make_spec(), pages)

    assert [item.khoan for item in chunks] == ["1", "2"]
    assert [item.chunk_id for item in chunks] == ["test_doc:d1:k1", "test_doc:d1:k2"]
    assert all(item.text.startswith("Điều 1. Dài\n") for item in chunks)
    assert "Dòng dẫn nhập" in chunks[0].text
    assert all(len(item.text) <= MAX_CHARS for item in chunks)


def test_cross_reference_does_not_start_an_article():
    pages = {10: "Điều 1. Một\nÁp dụng Điều 8 của Quy chế này.\nNội dung"}
    chunks = chunk_document(make_spec(), pages)

    assert len(chunks) == 1
    assert "Điều 8 của Quy chế này." in chunks[0].text


def test_shared_page_is_cut_at_next_marker(monkeypatch):
    first = make_spec("first", start=20, end=20)
    second = make_spec("second", start=20, end=20, marker=r"^II/ VĂN BẢN HAI$")
    monkeypatch.setattr(chunker, "REGISTRY", (first, second))
    pages = {
        20: "14\nĐiều 1. Một\nNội dung một\nII/ VĂN BẢN HAI\nĐiều 1. Hai\nNội dung hai"
    }

    first_chunks = chunk_document(first, pages)
    second_chunks = chunk_document(second, pages)
    assert "Nội dung hai" not in first_chunks[0].text
    assert "Nội dung một" not in second_chunks[0].text
    assert "Nội dung một" in first_chunks[0].text
    assert "Nội dung hai" in second_chunks[0].text


def test_jump_and_duplicate_article_numbers_add_warnings():
    pages = {
        10: "Điều 1. Một\nA\nĐiều 3. Ba\nB\nĐiều 3. Ba lặp\nC"
    }
    chunks = chunk_document(make_spec(), pages)

    assert "NON_SEQUENTIAL 1->3" in chunks[1].warnings
    assert "NON_SEQUENTIAL 3->3" in chunks[2].warnings
    assert "DUPLICATE_DIEU 3" in chunks[2].warnings


def test_chapter_updates_for_following_articles():
    pages = {
        10: "Chương I: Chung\nĐiều 1. Một\nA\nChương II. Riêng\nĐiều 2. Hai\nB"
    }
    chunks = chunk_document(make_spec(), pages)

    assert [item.chuong for item in chunks] == ["I", "II"]
    assert "Chương II" not in chunks[0].text


def test_embed_prefix_distinguishes_he():
    pages = {10: "Điều 1. Một\nA"}
    dai_tra = chunk_document(make_spec("dai_tra", he="dai_tra"), pages)[0]
    clc = chunk_document(make_spec("clc", he="chat_luong_cao"), pages)[0]

    assert "hệ đại trà" in dai_tra.embed_text
    assert "hệ chất lượng cao" in clc.embed_text
    assert dai_tra.embed_text != clc.embed_text


def test_first_printed_page_line_is_removed():
    pages = {10: "- 4 -\nĐiều 1. Một\nA"}
    chunk = chunk_document(make_spec(), pages)[0]

    assert "- 4 -" not in chunk.text


def test_chunk_ids_are_unique_after_duplicate_and_line_split():
    long_line = "x" * 1900
    pages = {10: f"Điều 1. Một\n{long_line}\nĐiều 1. Lặp\n{long_line}"}
    chunks = chunk_document(make_spec(), pages)
    identifiers = [item.chunk_id for item in chunks]

    assert len(identifiers) == len(set(identifiers))
    assert all(":p" in identifier for identifier in identifiers)
