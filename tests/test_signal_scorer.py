# =============================================================================
# test_signal_scorer.py — Signal 4 (target quantification)
# =============================================================================
# The original code counted every non-specific climate sentence as vague,
# so the VAGUE_CLAIM_PATTERNS list never changed the result. These tests
# check that only sentences with vague wording are counted as vague.
# Run with:  python -m pytest tests/test_signal_scorer.py -v
# =============================================================================

from src.signal_scorer import score_target_quantification


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
