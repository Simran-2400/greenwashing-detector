# =============================================================================
# test_find_pages.py — Locating the sustainability statement in a report
# =============================================================================
# The old version counted keywords per page and cut statements short when
# they contained table-heavy pages. The new version follows the statement's
# running header. Run with:  python -m pytest tests/test_find_pages.py -v
# =============================================================================

from find_pages import find_block, is_statement_page


def test_page_with_running_header_is_marked():
    text = "Report on operations – Consolidated Sustainability Statement\nExecutive summary"
    assert is_statement_page(text, sideways=False)


def test_sideways_table_page_is_marked_even_without_readable_header():
    assert is_statement_page("a b c d 31.12.2025 15.609 967", sideways=True)


def test_auditor_report_is_not_marked():
    text = "Independent auditor's limited assurance report on the consolidated sustainability statement"
    assert not is_statement_page(text, sideways=False)


def test_statutory_auditors_inside_the_statement_still_count():
    # MPS: the governance section mentions the "Board of Statutory Auditors"
    text = "2025 Financial Statement - Sustainability Statement\nThe Board of Statutory Auditors ascertains..."
    assert is_statement_page(text, sideways=False)


def test_small_gaps_are_bridged_and_the_longest_block_wins():
    #         pages: 1  2  3  4  5  6  7  8  9  10 11 12 13 14
    marked = [1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1]
    assert find_block([bool(m) for m in marked]) == (7, 14)


def test_a_long_gap_splits_blocks():
    marked = [1, 1, 1, 0, 0, 0, 0, 1, 1]
    assert find_block([bool(m) for m in marked]) == (1, 3)


def test_nothing_marked_gives_none():
    assert find_block([False, False]) is None
