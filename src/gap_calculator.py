# =============================================================================
# gap_calculator.py — Greenwashing Index
# =============================================================================
#
# Two scores, both on 0-10 where HIGH means MORE greenwashing risk:
#   NARRATIVE SCORE   (talk: what the bank SAYS  — signals 1, 4, 5)
#                     high = lots of ambitious, vague, future-heavy claims
#   PERFORMANCE SCORE (walk: what the bank SHOWS — signals 2, 3, 6)
#                     high = weak or missing hard disclosure
#
# Greenwashing is big talk COMBINED with weak walk, so the index uses the
# geometric mean sqrt(narrative x performance). It is only high when BOTH
# scores are high; a bank with big talk but strong disclosure stays moderate.
# A small boilerplate penalty (max 1 point) is added on top.

import math

from src.config import GREENWASHING_THRESHOLDS


def calculate_greenwashing_index(signals: dict, boilerplate_ratio: float) -> dict:
    """
    Calculate the Greenwashing Index from signal scores and boilerplate ratio.

    Returns the index, verdict, and component breakdown.
    """

    # --- Separate narrative vs performance signals ---
    narrative_signals = {
        "netzero_density": signals["netzero_density"]["score"],
        "target_quantification": signals["target_quantification"]["score"],
        "forward_backward": signals["forward_backward"]["score"],
    }

    performance_signals = {
        "financed_emissions": signals["financed_emissions"]["score"],
        "fossil_fuel": signals["fossil_fuel"]["score"],
        "taxonomy_disclosure": signals["taxonomy_disclosure"]["score"],
    }

    narrative_score = sum(narrative_signals.values()) / len(narrative_signals)
    performance_score = sum(performance_signals.values()) / len(performance_signals)

    # --- Boilerplate penalty (adds up to 1 point) ---
    boilerplate_penalty = min(1.0, boilerplate_ratio * 1.5)

    # --- Greenwashing Index: high only when talk AND walk risk are both high ---
    combined = math.sqrt(narrative_score * performance_score)
    greenwashing_index = min(10.0, combined + boilerplate_penalty)
    verdict = _get_verdict(greenwashing_index)

    # --- Profile: which talk/walk quadrant the bank falls in (midpoint 5) ---
    big_talk = narrative_score >= 5
    weak_walk = performance_score >= 5
    if big_talk and weak_walk:
        profile = "GREENWASHING RISK: big talk, weak disclosure."
    elif big_talk:
        profile = "BACKED AMBITION: big talk, supported by disclosure."
    elif weak_walk:
        profile = "LOW TRANSPARENCY: modest talk, weak disclosure."
    else:
        profile = "UNDER-CLAIMER: modest talk, strong disclosure."

    return {
        "greenwashing_index": round(greenwashing_index, 2),
        "verdict": verdict,
        "narrative_score": round(narrative_score, 2),
        "performance_score": round(performance_score, 2),
        "profile": profile,
        "boilerplate_penalty": round(boilerplate_penalty, 2),
        "signal_breakdown": {
            "narrative": {k: round(v, 2) for k, v in narrative_signals.items()},
            "performance": {k: round(v, 2) for k, v in performance_signals.items()}
        }
    }


def _get_verdict(index: float) -> str:
    for label, (low, high) in GREENWASHING_THRESHOLDS.items():
        if low <= index <= high:
            return label
    return "CRITICAL"


def build_summary_dataframe(all_results: list) -> object:
    """
    Combine results from multiple banks into a single pandas DataFrame.
    Used by visualizer.py to generate comparative charts.

    all_results: list of dicts, one per bank, each containing:
      {bank_name, country, greenwashing_index, verdict, narrative_score,
       performance_score, boilerplate_ratio_pct, ...signal scores}
    """
    import pandas as pd

    rows = []
    for r in all_results:
        row = {
            "Bank": r["bank_name"],
            "Country": r["country"],
            "Greenwashing Index": r["gap_calc"]["greenwashing_index"],
            "Narrative Score": r["gap_calc"]["narrative_score"],
            "Performance Score": r["gap_calc"]["performance_score"],
            "Profile": r["gap_calc"]["profile"],
            "Verdict": r["gap_calc"]["verdict"],
            "Boilerplate %": r["language_audit"]["boilerplate_ratio_pct"],
            # Individual signals
            "S1: Net-Zero Density": r["signals"]["netzero_density"]["score"],
            "S2: Financed Emissions": r["signals"]["financed_emissions"]["score"],
            "S3: Fossil Fuel": r["signals"]["fossil_fuel"]["score"],
            "S4: Target Quantif.": r["signals"]["target_quantification"]["score"],
            "S5: Fwd/Bwd Ratio": r["signals"]["forward_backward"]["score"],
            "S6: Taxonomy": r["signals"]["taxonomy_disclosure"]["score"],
        }
        rows.append(row)

    return pd.DataFrame(rows)
