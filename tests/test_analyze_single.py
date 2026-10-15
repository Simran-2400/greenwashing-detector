# =============================================================================
# test_analyze_single.py — The single-report script must use the page range
# =============================================================================
# Before, analyze_single.py always read the whole annual report (1,000+ pages
# of financial statements), so its scores differed from main.py's.
# Run with:  python -m pytest tests/test_analyze_single.py -v
# =============================================================================

from analyze_single import pages_from_config


def test_page_range_comes_from_config():
    assert pages_from_config("BPER Banca", "italy", 2025) == (94, 261)


def test_bank_name_is_case_insensitive():
    assert pages_from_config("bper banca", "italy", 2025) == (94, 261)


def test_unknown_bank_or_missing_year_gives_no_range():
    assert pages_from_config("Unknown Bank", "italy", 2025) is None
    assert pages_from_config("BPER Banca", "italy", 2024) is None
