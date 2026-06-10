# =============================================================================
# test_matcher.py — Validity tests for the keyword matching engine
# =============================================================================
# Each test documents a measurement-validity failure of the original
# str.count() approach and proves the new matcher fixes it.
# Run with:  python -m pytest tests/test_matcher.py -v
# =============================================================================

from src.matcher import match_terms, KeywordMatcher
from src.config import (NETZERO_KEYWORDS, TAXONOMY_KEYWORDS,
                        FORWARD_LOOKING_KEYWORDS, VAGUE_ESG_WORDS)


# ---------------------------------------------------------------------------
# 1. SUBSTRING FALSE POSITIVES
# ---------------------------------------------------------------------------
def test_gar_does_not_match_regarding():
    text = "Further information regarding our garden party and Garanti Bank."
    res = match_terms(text, TAXONOMY_KEYWORDS)
    assert res.total_asserted == 0, f"False positives: {res.asserted}"
    # old behaviour for reference: text.count('gar') == 3


def test_gar_matches_real_gar():
    text = "The bank discloses a GAR of 3.1% for 2024. The GAR improved year on year."
    res = match_terms(text, TAXONOMY_KEYWORDS)
    assert res.asserted.get("gar") == 2


def test_will_does_not_match_goodwill():
    text = "Goodwill impairment and the willingness of stakeholders were discussed."
    res = match_terms(text, FORWARD_LOOKING_KEYWORDS)
    assert "will" not in res.asserted
    # old behaviour: text.count('will') == 2


def test_green_does_not_match_greenhouse():
    text = "Greenhouse gas emissions and evergreen funding structures."
    res = match_terms(text, VAGUE_ESG_WORDS)
    assert "green" not in res.asserted
    # old behaviour: text.count('green') == 2


# ---------------------------------------------------------------------------
# 2. DOUBLE COUNTING / OVERLAPPING TERMS
# ---------------------------------------------------------------------------
def test_longest_match_wins_no_double_count():
    text = "We joined the Net Zero Banking Alliance in 2021."
    res = match_terms(text, NETZERO_KEYWORDS)
    assert res.asserted.get("net zero banking alliance") == 1
    assert "net zero" not in res.asserted, "inner phrase double-counted"
    assert res.total_asserted == 1
    # old behaviour: 'net zero banking alliance' AND 'net zero' both counted = 2


def test_hyphen_variants_collapse_to_one_canonical_term():
    text = "Our net-zero strategy. Our net zero strategy. Our net  zero strategy."
    res = match_terms(text, NETZERO_KEYWORDS)
    assert res.asserted == {"net zero": 3}


# ---------------------------------------------------------------------------
# 3. NEGATION HANDLING
# ---------------------------------------------------------------------------
def test_simple_negation_excluded_from_asserted():
    text = "The bank has not set a net zero target."
    res = match_terms(text, NETZERO_KEYWORDS)
    assert res.total_asserted == 0
    assert res.negated.get("net zero") == 1


def test_negation_does_not_cross_sentence_boundary():
    text = "We do not finance coal. Our net zero target covers all portfolios."
    res = match_terms(text, NETZERO_KEYWORDS)
    assert res.asserted.get("net zero") == 1
    assert res.total_negated == 0


def test_no_negation_counts_normally():
    text = "We are committed to net zero by 2050 and carbon neutrality by 2030."
    res = match_terms(text, NETZERO_KEYWORDS)
    assert res.asserted.get("net zero") == 1
    assert res.asserted.get("carbon neutrality") == 1


# ---------------------------------------------------------------------------
# 4. EVIDENCE TRAIL (auditability)
# ---------------------------------------------------------------------------
def test_evidence_snippets_recorded():
    text = "In 2024 the bank reaffirmed its net zero commitment in the annual report."
    res = match_terms(text, NETZERO_KEYWORDS)
    assert len(res.evidence) == 1
    ev = res.evidence[0]
    assert ev["term"] == "net zero"
    assert ev["negated"] is False
    assert "reaffirmed" in ev["snippet"]


# ---------------------------------------------------------------------------
# 5. EDGE CASES
# ---------------------------------------------------------------------------
def test_empty_text_and_empty_dictionary():
    assert match_terms("", NETZERO_KEYWORDS).total_asserted == 0
    assert KeywordMatcher([]).match("net zero everywhere").total_asserted == 0


def test_term_at_start_and_end_of_text():
    text = "net zero is the goal and the goal is net zero"
    res = match_terms(text, NETZERO_KEYWORDS)
    assert res.asserted.get("net zero") == 2
