# =============================================================================
# signal_scorer.py — The 6 Greenwashing Signals
# =============================================================================
#
# LOGIC: Each signal scores 0-10 where:
#   0  = no greenwashing risk on this dimension
#   10 = maximum greenwashing signal
#
# The signals map directly to the research framework:
#   Signals 1, 4, 5 → NARRATIVE side (what the bank SAYS)
#   Signals 2, 3, 6 → PERFORMANCE side (what the bank SHOWS)
#
# The gap between narrative scores and performance scores = Greenwashing Index.

import re
from src.matcher import match_terms
from src.config import (
    NETZERO_KEYWORDS, FINANCED_EMISSIONS_KEYWORDS,
    FOSSIL_EXIT_KEYWORDS, FOSSIL_CONTINUATION_KEYWORDS,
    SPECIFICITY_PATTERNS, VAGUE_CLAIM_PATTERNS,
    FORWARD_LOOKING_KEYWORDS, BACKWARD_LOOKING_KEYWORDS,
    TAXONOMY_KEYWORDS
)


def score_all_signals(full_text: str, word_count: int, sentences: list) -> dict:
    """
    Run all 6 greenwashing signal scorers on the report text.
    Returns a dict with each signal's score and evidence.
    """
    text = full_text.lower()
    words_1000 = max(word_count / 1000, 1)  # normalizer: per 1000 words

    results = {}
    results["netzero_density"]       = score_netzero_density(text, words_1000)
    results["financed_emissions"]    = score_financed_emissions(text, words_1000)
    results["fossil_fuel"]           = score_fossil_fuel(text)
    results["target_quantification"] = score_target_quantification(text, sentences)
    results["forward_backward"]      = score_forward_backward(text, sentences)
    results["taxonomy_disclosure"]   = score_taxonomy_disclosure(text, words_1000)

    return results


# =============================================================================
# SIGNAL 1: NET-ZERO CLAIM DENSITY
# =============================================================================
def score_netzero_density(text: str, words_1000: float) -> dict:
    """
    Counts how often net-zero / Paris-alignment language appears.
    High density without supporting performance data = greenwashing signal.

    Scoring logic:
    - Density < 1 per 1000 words → score 2 (low ambition claims)
    - Density 1-3 per 1000 words → score 5 (typical)
    - Density > 3 per 1000 words → score 8 (very high claim density)
    Note: this signal is NARRATIVE, so high score = high ambition (not bad alone).
    It becomes greenwashing when combined with low performance scores.
    """
    matches = match_terms(text, NETZERO_KEYWORDS)
    total_count = matches.total_asserted
    hits = [f"'{t}' appears {c}x" for t, c in matches.top_terms(10)]

    density = total_count / words_1000

    if density == 0:
        score = 1.0
        finding = "Bank makes almost no net-zero or Paris-alignment claims."
    elif density < 1:
        score = 3.0
        finding = f"Moderate climate ambition language ({total_count} occurrences)."
    elif density < 3:
        score = 6.0
        finding = f"High net-zero claim density ({total_count} occurrences, {density:.1f} per 1000 words)."
    else:
        score = 8.5
        finding = f"Very high net-zero claim density ({total_count} occurrences, {density:.1f} per 1000 words). Cross-check against performance data."

    return {
        "score": round(score, 2),
        "total_count": total_count,
        "negated_mentions": matches.total_negated,
        "density_per_1000_words": round(density, 2),
        "finding": finding,
        "evidence_summary": hits[:5],  # top 5 hits
        "signal_type": "NARRATIVE",
        "reasoning": "Net-zero density is a narrative signal. It only becomes a greenwashing flag when combined with absent performance disclosure."
    }


# =============================================================================
# SIGNAL 2: FINANCED EMISSIONS DISCLOSURE
# =============================================================================
def score_financed_emissions(text: str, words_1000: float) -> dict:
    """
    Checks whether the bank actually discloses what its loans emit.
    This is the most critical signal for banks specifically.

    Key: a bank can decarbonize its offices to zero and still finance
    billions in coal extraction. Only financed emissions data reveals this.

    Scoring:
    - PCAF + Category 15 + specific data → score 1 (credible)
    - Some mentions, no data → score 5
    - Net-zero claims exist but zero financed emissions terms → score 9
    """
    matches = match_terms(text, FINANCED_EMISSIONS_KEYWORDS)
    hits = dict(matches.asserted)

    total_hits = sum(hits.values())
    unique_terms = len(hits)

    # Check quality: does PCAF appear? Does "category 15" appear?
    has_pcaf = "pcaf" in hits
    has_category15 = any("category 15" in k or "cat 15" in k for k in hits)
    has_waci = "waci" in hits or "weighted average carbon intensity" in hits

    if unique_terms == 0:
        score = 9.5
        finding = "No financed emissions disclosure found. The bank does not report what its loan portfolio emits."
    elif unique_terms <= 2 and not has_pcaf:
        score = 6.5
        finding = f"Minimal financed emissions disclosure ({unique_terms} unique terms). No PCAF methodology referenced."
    elif has_pcaf and not has_category15:
        score = 4.0
        finding = f"PCAF referenced but Scope 3 Category 15 not explicitly named. Partial disclosure."
    elif has_pcaf and has_category15:
        score = 1.5
        finding = f"Credible financed emissions disclosure: PCAF methodology + Scope 3 Category 15 referenced ({total_hits} total mentions)."
    else:
        score = 5.0
        finding = f"Partial financed emissions disclosure ({unique_terms} terms, {total_hits} mentions)."

    return {
        "score": round(score, 2),
        "unique_terms_found": unique_terms,
        "total_mentions": total_hits,
        "has_pcaf": has_pcaf,
        "has_category15": has_category15,
        "has_waci": has_waci,
        "terms_found": dict(sorted(hits.items(), key=lambda x: x[1], reverse=True)),
        "finding": finding,
        "signal_type": "PERFORMANCE",
        "reasoning": "Financed emissions (Scope 3 Cat.15) is the only metric that captures a bank's real climate impact. Non-disclosure while claiming net-zero is the clearest greenwashing signal."
    }


# =============================================================================
# SIGNAL 3: FOSSIL FUEL SPECIFICITY
# =============================================================================
def score_fossil_fuel(text: str) -> dict:
    """
    Measures the ratio of credible EXIT language to enabling CONTINUATION language.

    Exit language (good): "no new financing", "coal exclusion", "phase-out"
    Continuation language (bad): "transition finance", "bridge fuel", "case by case"

    Scoring:
    - Exit >> Continuation → score 2 (credible commitment)
    - Balanced → score 5
    - Continuation >> Exit → score 8 (greenwashing via loophole language)
    - No fossil fuel mention at all → score 7 (avoidance is also a signal)
    """
    exit_hits = dict(match_terms(text, FOSSIL_EXIT_KEYWORDS).asserted)
    continuation_hits = dict(match_terms(text, FOSSIL_CONTINUATION_KEYWORDS).asserted)

    total_exit = sum(exit_hits.values())
    total_continuation = sum(continuation_hits.values())

    if total_exit == 0 and total_continuation == 0:
        score = 6.5
        finding = "No fossil fuel language detected. The bank avoids discussing its fossil fuel exposure entirely."
    elif total_continuation > total_exit * 2:
        score = 8.0
        finding = f"Continuation language ({total_continuation} hits) dominates exit language ({total_exit} hits). 'Transition finance' framing enables continued fossil fuel support."
    elif total_exit > total_continuation * 2:
        score = 2.0
        finding = f"Exit language ({total_exit} hits) strongly dominates. Policy commitments appear credible."
    else:
        score = 5.0
        finding = f"Mixed fossil fuel language: {total_exit} exit signals vs {total_continuation} continuation signals."

    return {
        "score": round(score, 2),
        "exit_hits": dict(sorted(exit_hits.items(), key=lambda x: x[1], reverse=True)),
        "continuation_hits": dict(sorted(continuation_hits.items(), key=lambda x: x[1], reverse=True)),
        "total_exit": total_exit,
        "total_continuation": total_continuation,
        "finding": finding,
        "signal_type": "PERFORMANCE",
        "reasoning": "Banks often use 'transition finance' language to claim green credentials while continuing to fund fossil fuel projects."
    }


# =============================================================================
# SIGNAL 4: TARGET QUANTIFICATION (SPECIFICITY)
# =============================================================================
def score_target_quantification(text: str, sentences: list) -> dict:
    """
    Checks whether climate targets are backed by numbers, years, and baselines.

    Method: scan sentences containing climate keywords for
    quantification patterns (%, years, tonnes CO2, euros).

    "We will reduce financed emissions by 43% by 2030 from a 2019 baseline" → specific ✓
    "We are committed to reducing our climate impact" → vague ✗
    """
    # Find sentences that contain climate claims
    climate_trigger_words = [
        "target", "goal", "aim", "commit", "reduce", "cut",
        "emission", "carbon", "climate", "net zero", "decarboni"
    ]

    climate_sentences = []
    for sent in sentences:
        sent_lower = sent.lower()
        if any(trigger in sent_lower for trigger in climate_trigger_words):
            climate_sentences.append(sent_lower)

    if not climate_sentences:
        return {
            "score": 5.0,
            "finding": "Insufficient climate claim sentences detected for quantification analysis.",
            "signal_type": "NARRATIVE",
            "reasoning": "Could not locate target claims in text.",
            "specific_count": 0,
            "vague_count": 0,
            "specificity_ratio": 0
        }

    specific_count = 0
    vague_count = 0
    specific_examples = []
    vague_examples = []

    for sent in climate_sentences[:100]:  # analyze first 100 climate sentences
        is_specific = any(re.search(p, sent) for p in SPECIFICITY_PATTERNS)
        is_vague = any(re.search(p, sent) for p in VAGUE_CLAIM_PATTERNS)

        if is_specific:
            specific_count += 1
            if len(specific_examples) < 3:
                specific_examples.append(sent[:120])
        elif is_vague or not is_specific:
            vague_count += 1
            if len(vague_examples) < 3:
                vague_examples.append(sent[:120])

    total = specific_count + vague_count
    specificity_ratio = (specific_count / total) if total > 0 else 0

    if specificity_ratio > 0.6:
        score = 2.0
        finding = f"Strong target quantification: {specific_count}/{total} climate claims include specific numbers, years, or metrics."
    elif specificity_ratio > 0.35:
        score = 5.0
        finding = f"Moderate quantification: {specific_count}/{total} climate claims are specific. Many remain vague."
    else:
        score = 8.0
        finding = f"Weak quantification: only {specific_count}/{total} climate claims include hard numbers. Most targets are vague."

    return {
        "score": round(score, 2),
        "specific_count": specific_count,
        "vague_count": vague_count,
        "specificity_ratio": round(specificity_ratio, 3),
        "specific_examples": specific_examples,
        "vague_examples": vague_examples,
        "finding": finding,
        "signal_type": "NARRATIVE",
        "reasoning": "Specific targets (number + baseline year + target year) are accountable. Vague aspirations are not."
    }


# =============================================================================
# SIGNAL 5: FORWARD-LOOKING vs BACKWARD-LOOKING RATIO
# =============================================================================
def score_forward_backward(text: str, sentences: list) -> dict:
    """
    Measures how much of the report is future promises vs. past results.

    A credible report balances both:
    - "We reduced financed emissions by 12% in 2024" (backward = accountability)
    - "We target 43% reduction by 2030" (forward = ambition)

    A greenwashing report is future-heavy:
    - "We will commit to... we aim to... by 2030 we plan..."
    - With little evidence of what was actually achieved.
    """
    forward_count = match_terms(text, FORWARD_LOOKING_KEYWORDS).total_asserted
    backward_count = match_terms(text, BACKWARD_LOOKING_KEYWORDS).total_asserted

    total = forward_count + backward_count
    forward_ratio = (forward_count / total) if total > 0 else 0.5

    if forward_ratio > 0.70:
        score = 8.0
        finding = f"Report is heavily future-oriented ({forward_ratio:.0%} forward-looking). Few past achievements documented."
    elif forward_ratio > 0.55:
        score = 5.5
        finding = f"Moderately future-heavy ({forward_ratio:.0%} forward-looking). Balance between promises and results could improve."
    elif forward_ratio > 0.40:
        score = 3.0
        finding = f"Good balance between forward targets ({forward_ratio:.0%}) and past results. Accountability is evident."
    else:
        score = 1.5
        finding = f"Report is primarily backward-looking ({1-forward_ratio:.0%} past results). Strong accountability posture."

    return {
        "score": round(score, 2),
        "forward_count": forward_count,
        "backward_count": backward_count,
        "forward_ratio": round(forward_ratio, 3),
        "finding": finding,
        "signal_type": "NARRATIVE",
        "reasoning": "A report full of 'we will' and 'by 2050' without 'we achieved' is making promises, not accounting for results."
    }


# =============================================================================
# SIGNAL 6: TAXONOMY ALIGNMENT DISCLOSURE
# =============================================================================
def score_taxonomy_disclosure(text: str, words_1000: float) -> dict:
    """
    Checks whether the bank reports its EU Taxonomy alignment.

    Under CSRD, large banks must disclose their Green Asset Ratio (GAR)
    and Banking Book Taxonomy Alignment Ratio (BTAR).
    Claiming "green leadership" without disclosing these ratios is a
    clear accountability gap.
    """
    matches = match_terms(text, TAXONOMY_KEYWORDS)
    hits = dict(matches.asserted)

    total_hits = sum(hits.values())
    unique_terms = len(hits)

    has_gar = "green asset ratio" in hits or "gar" in hits
    has_btar = "btar" in hits or "banking book taxonomy" in hits
    has_percentage = bool(re.search(
        r'taxonomy[- ]aligned.*?\d+\.?\d*\s*%|\d+\.?\d*\s*%.*?taxonomy[- ]aligned',
        text
    ))

    if unique_terms == 0:
        score = 9.0
        finding = "No EU Taxonomy alignment disclosure found. The bank reports no Green Asset Ratio or Taxonomy-eligible assets."
    elif has_gar and has_percentage:
        score = 1.5
        finding = f"Strong Taxonomy disclosure: Green Asset Ratio referenced with specific percentage ({total_hits} total mentions)."
    elif has_gar or has_btar:
        score = 3.5
        finding = f"Taxonomy disclosure present (GAR/BTAR referenced) but no specific alignment percentage found."
    elif unique_terms >= 2:
        score = 5.5
        finding = f"Partial Taxonomy disclosure ({unique_terms} terms, {total_hits} mentions). Key ratios (GAR/BTAR) not clearly stated."
    else:
        score = 7.0
        finding = f"Minimal Taxonomy disclosure ({unique_terms} term). Insufficient for CSRD compliance verification."

    return {
        "score": round(score, 2),
        "unique_terms_found": unique_terms,
        "total_mentions": total_hits,
        "has_gar": has_gar,
        "has_btar": has_btar,
        "has_percentage": has_percentage,
        "terms_found": dict(sorted(hits.items(), key=lambda x: x[1], reverse=True)),
        "finding": finding,
        "signal_type": "PERFORMANCE",
        "reasoning": "EU Taxonomy alignment is the most standardized measure of whether a bank's assets are genuinely 'green'. Non-disclosure contradicts green leadership claims."
    }
