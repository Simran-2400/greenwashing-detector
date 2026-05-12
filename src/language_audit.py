# =============================================================================
# language_audit.py — Word Frequency Analysis & Boilerplate Ratio
# =============================================================================
#
# LOGIC: Before scoring any specific signal, we audit the report's language.
# The key insight: a report heavy on vague ESG vocabulary and light on
# specific technical terms is likely using template language — not genuine
# disclosure. We measure this with the BOILERPLATE RATIO.
#
# Boilerplate Ratio = vague_count / (vague_count + specific_count)
# Range: 0.0 (fully specific) to 1.0 (fully vague/template)
# Threshold: above 0.65 = high boilerplate = greenwashing signal

from collections import Counter
from src.config import VAGUE_ESG_WORDS, SPECIFIC_ESG_WORDS, BOILERPLATE_THRESHOLDS


def run_language_audit(full_text: str, word_list: list) -> dict:
    """
    Run the full language audit on a bank's report text.

    Returns:
      - boilerplate_ratio: float 0-1
      - vague_count: how many vague ESG words found
      - specific_count: how many specific ESG words found
      - top_vague_words: list of (word, count) for most repeated vague terms
      - top_specific_words: list of (word, count) for specific terms found
      - top_all_words: overall most frequent non-stop words
      - boilerplate_label: LOW / MODERATE / HIGH
      - interpretation: one-sentence finding
    """

    # --- Count vague vocabulary ---
    vague_counts = {}
    for term in VAGUE_ESG_WORDS:
        count = full_text.count(term.lower())
        if count > 0:
            vague_counts[term] = count

    total_vague = sum(vague_counts.values())

    # --- Count specific vocabulary ---
    specific_counts = {}
    for term in SPECIFIC_ESG_WORDS:
        count = full_text.count(term.lower())
        if count > 0:
            specific_counts[term] = count

    total_specific = sum(specific_counts.values())

    # --- Calculate boilerplate ratio ---
    denominator = total_vague + total_specific
    boilerplate_ratio = (total_vague / denominator) if denominator > 0 else 0.5

    # --- Label the ratio ---
    if boilerplate_ratio < BOILERPLATE_THRESHOLDS["LOW"]:
        label = "LOW"
        interpretation = (
            f"The report uses relatively specific technical language "
            f"({total_specific} specific terms vs {total_vague} vague terms). "
            f"This suggests substantive disclosure rather than template reporting."
        )
    elif boilerplate_ratio < BOILERPLATE_THRESHOLDS["MODERATE"]:
        label = "MODERATE"
        interpretation = (
            f"The report mixes specific and vague ESG language "
            f"({total_specific} specific vs {total_vague} vague terms). "
            f"Some sections may rely on template language."
        )
    else:
        label = "HIGH"
        interpretation = (
            f"The report is dominated by vague ESG vocabulary "
            f"({total_vague} vague terms vs only {total_specific} specific terms). "
            f"A boilerplate ratio of {boilerplate_ratio:.0%} indicates template-heavy reporting."
        )

    # --- Top repeated terms across all categories ---
    word_counter = Counter(word_list)
    top_all = word_counter.most_common(20)

    # Sort vague and specific by count
    top_vague = sorted(vague_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_specific = sorted(specific_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # --- Repetition flag: identify suspiciously repeated vague terms ---
    # A single vague term appearing 30+ times in a report is a red flag
    repetition_flags = [
        (term, count) for term, count in vague_counts.items()
        if count >= 20
    ]

    return {
        "boilerplate_ratio": round(boilerplate_ratio, 4),
        "boilerplate_ratio_pct": round(boilerplate_ratio * 100, 1),
        "boilerplate_label": label,
        "vague_count": total_vague,
        "specific_count": total_specific,
        "top_vague_words": top_vague,
        "top_specific_words": top_specific,
        "top_all_words": top_all,
        "repetition_flags": repetition_flags,
        "interpretation": interpretation,
    }
