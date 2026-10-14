# =============================================================================
# test_signal_scorer.py — Signal 4 (target quantification)
# =============================================================================
# The original code counted every non-specific climate sentence as vague,
# so the VAGUE_CLAIM_PATTERNS list never changed the result. These tests
# check that only sentences with vague wording are counted as vague.
# Run with:  python -m pytest tests/test_signal_scorer.py -v
# =============================================================================

from src.signal_scorer import (score_target_quantification, score_forward_backward,
                                score_netzero_density, score_fossil_fuel)


def test_plain_description_is_not_counted_as_vague():
    sentences = ["our climate team reports to the board every quarter."]
    res = score_target_quantification("", sentences)
    assert res["vague_count"] == 0


def test_vague_wording_is_counted_as_vague():
    sentences = ["we aim to significantly reduce our carbon footprint over time."]
    res = score_target_quantification("", sentences)
    assert res["vague_count"] == 1
    assert res["specific_count"] == 0


def test_specific_target_is_counted_as_specific():
    sentences = ["we will reduce financed emissions by 43% by 2030 from a 2019 baseline."]
    res = score_target_quantification("", sentences)
    assert res["specific_count"] == 1


def test_only_plain_descriptions_give_neutral_score():
    sentences = ["our climate team reports to the board every quarter.",
                 "the carbon committee met four times in the year."]
    res = score_target_quantification("", sentences)
    assert res["score"] == 5.0


# ---------------------------------------------------------------------------
# Signal 5: year phrases follow the report year (no hardcoded 2024)
# ---------------------------------------------------------------------------
def test_backward_years_follow_the_report_year():
    text = "emissions fell in 2025. the portfolio was rebalanced during 2024."
    assert score_forward_backward(text, 2025)["backward_count"] == 2
    # For an FY2024 report, "in 2025" is not a past result and is not counted
    assert score_forward_backward(text, 2024)["backward_count"] == 1


# ---------------------------------------------------------------------------
# Continuous scores: banks with different ratios must get different scores
# (the old step scoring put e.g. densities 1.1 and 2.9 in the same bucket)
# ---------------------------------------------------------------------------
def test_netzero_density_is_continuous():
    low = score_netzero_density("net zero " * 11, 10)    # 1.1 per 1,000 words
    high = score_netzero_density("net zero " * 29, 10)   # 2.9 per 1,000 words
    assert low["score"] == 3.75
    assert high["score"] == 8.25
    assert score_netzero_density("", 10)["score"] == 1.0


def test_fossil_fuel_score_is_share_of_continuation_language():
    text = "phase out. phase out. phase out. transition finance."
    assert score_fossil_fuel(text)["score"] == 2.5          # 1 of 4 is continuation
    assert score_fossil_fuel("no relevant words")["score"] == 6.5


def test_forward_score_is_share_of_forward_language():
    text = "we aim to grow. we plan to expand. we achieved results. we reduced costs."
    assert score_forward_backward(text, 2025)["score"] == 5.0   # 2 of 4 forward


def test_vague_share_drives_target_score():
    sentences = ["we will cut financed emissions by 43% by 2030.",
                 "we aim to significantly reduce our carbon footprint over time.",
                 "we strive to cut carbon where possible."]
    assert score_target_quantification("", sentences)["score"] == 6.67   # 2 of 3 vague
