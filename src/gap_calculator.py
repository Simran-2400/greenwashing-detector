# =============================================================================
# gap_calculator.py — Greenwashing Index
# =============================================================================
#
# LOGIC: The greenwashing index is not just an average of 6 scores.
# It specifically measures the GAP between:
#   NARRATIVE SCORE  (what the bank SAYS  — signals 1, 4, 5)
#   PERFORMANCE SCORE (what the bank SHOWS — signals 2, 3, 6)
#
# A bank that scores high on narrative AND high on performance is greenwashing.
# A bank that scores low on both is under-claiming.
# A bank that scores high on performance but low on narrative is conservative.
#
# GREENWASHING INDEX = Narrative Score (amplified by Performance Gap)

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

    # --- Boilerplate penalty ---
    # A high boilerplate ratio adds up to 1.0 point to the final index
    boilerplate_penalty = min(1.0, boilerplate_ratio * 1.5)

    # --- Greenwashing Index ---
    # Simple average of all 6 signals + boilerplate penalty
    raw_index = (narrative_score + performance_score) / 2
    greenwashing_index = min(10.0, raw_index + boilerplate_penalty)

    # --- Verdict ---
    verdict = _get_verdict(greenwashing_index)

    # --- Gap analysis ---
    gap = performance_score - narrative_score
    if gap > 2:
        gap_interpretation = "UNDER-REPORTER: Performance evidence exceeds narrative claims. Bank is conservative in its ESG communication."
    elif gap < -2:
        gap_interpretation = "GREENWASHING RISK: Narrative ambition significantly exceeds performance evidence. Classic talk-walk gap."
    else:
        gap_interpretation = "ALIGNED: Narrative and performance scores are broadly consistent."

    return {
        "greenwashing_index": round(greenwashing_index, 2),
        "verdict": verdict,
        "narrative_score": round(narrative_score, 2),
        "performance_score": round(performance_score, 2),
        "gap": round(performance_score - narrative_score, 2),
        "gap_interpretation": gap_interpretation,
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
            "Gap (Perf - Narr)": r["gap_calc"]["gap"],
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
