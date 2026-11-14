import pytest

from naive_assistant.ingest.registry import (
    REGISTRY,
    docs_on_page,
    get_doc,
    validate_registry,
)


def doc_ids(pdf_page: int) -> list[str]:
    return [spec.doc_id for spec in docs_on_page(pdf_page)]


def test_registry_is_valid_and_complete():
    assert validate_registry() == []
    assert len(REGISTRY) == 16


def test_docs_on_shared_pages_keep_registry_order():
    assert doc_ids(191) == ["nd_238_2025", "qd_05_2022_ttg"]
    assert doc_ids(193) == ["qd_05_2022_ttg", "qd_29_2025_ttg"]
    assert doc_ids(197) == ["qd_29_2025_ttg", "qd_29_2025_phu_luc_1"]


def test_docs_on_boundary_and_unregistered_pages():
    assert doc_ids(111) == ["chuan_dau_ra_ta_dai_tra"]
    assert doc_ids(112) == ["chuan_dau_ra_ta_clc"]
    assert docs_on_page(50) == []


def test_get_doc_rejects_unknown_id():
    with pytest.raises(KeyError):
        get_doc("khong_ton_tai")


def test_english_output_specs_have_distinct_he():
    assert get_doc("chuan_dau_ra_ta_dai_tra").he != get_doc(
        "chuan_dau_ra_ta_clc"
    ).he


def test_duplicate_decision_is_preserved_from_printed_handbook():
    assert get_doc("dao_tao_tin_chi").decision == get_doc(
        "van_hoa_hoc_duong"
    ).decision
