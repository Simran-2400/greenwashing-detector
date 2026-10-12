# =============================================================================
# test_gap_calculator.py — Talk versus walk combination
# =============================================================================
# Greenwashing = big talk COMBINED with weak walk. The index must be highest
# when both scores are high, and the profile labels must match the quadrant.
# Run with:  python -m pytest tests/test_gap_calculator.py -v
# =============================================================================

from src.gap_calculator import calculate_greenwashing_index


def make_signals(talk: float, walk: float) -> dict:
    """All three talk signals get `talk`, all three walk signals get `walk`."""
    names_talk = ["netzero_density", "target_quantification", "forward_backward"]
    names_walk = ["financed_emissions", "fossil_fuel", "taxonomy_disclosure"]
    signals = {n: {"score": talk} for n in names_talk}
    signals.update({n: {"score": walk} for n in names_walk})
    return signals


def test_big_talk_weak_walk_scores_highest():
    risky = calculate_greenwashing_index(make_signals(8, 8), 0.0)
    backed = calculate_greenwashing_index(make_signals(8, 2), 0.0)
    modest = calculate_greenwashing_index(make_signals(2, 8), 0.0)
    assert risky["greenwashing_index"] > backed["greenwashing_index"]
    assert risky["greenwashing_index"] > modest["greenwashing_index"]


def test_big_talk_with_strong_disclosure_is_not_penalised_like_average():
    # A plain average would give both banks 5.0. The combination should not:
    # big talk backed by strong disclosure is lower risk than middling on both.
    backed = calculate_greenwashing_index(make_signals(8, 2), 0.0)
    middling = calculate_greenwashing_index(make_signals(5, 5), 0.0)
    assert backed["greenwashing_index"] < middling["greenwashing_index"]


def test_profile_labels_match_quadrants():
    assert calculate_greenwashing_index(make_signals(8, 8), 0.0)["profile"].startswith("GREENWASHING RISK")
    assert calculate_greenwashing_index(make_signals(8, 2), 0.0)["profile"].startswith("BACKED AMBITION")
    assert calculate_greenwashing_index(make_signals(2, 8), 0.0)["profile"].startswith("LOW TRANSPARENCY")
    assert calculate_greenwashing_index(make_signals(2, 2), 0.0)["profile"].startswith("UNDER-CLAIMER")


def test_boilerplate_penalty_is_capped_at_one_point():
    clean = calculate_greenwashing_index(make_signals(5, 5), 0.0)
    full = calculate_greenwashing_index(make_signals(5, 5), 1.0)
    assert round(full["greenwashing_index"] - clean["greenwashing_index"], 2) == 1.0
