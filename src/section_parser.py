# =============================================================================
# section_parser.py — Report Section Segmentation
# =============================================================================
#
# LOGIC: Instead of treating the whole report as one blob, we split it into
# sections (CEO letter, Climate Strategy, Performance Data, Targets, etc.)
# This matters for two reasons:
#   1. We can say WHICH section contains a claim (precise pinpointing)
#   2. Different sections have different credibility norms:
#      - CEO letter: narrative, expect vague language
#      - Performance Data: should be specific, numbers-heavy
#      - If Performance Data section is also vague → strong greenwashing signal

import re
from src.config import SECTION_HEADER_PATTERNS


def parse_sections(pages: list) -> list:
    """
    Detect and group report sections from page-level text.

    Returns a list of section dicts:
      {name, pages, full_text, word_count, is_performance_section}
    """
    sections = []
    current_section = {
        "name": "Preamble / Table of Contents",
        "pages": [],
        "text_parts": [],
        "is_performance_section": False
    }

    for page_data in pages:
        page_num = page_data["page_num"]
        page_text = page_data["text"]
        lines = page_text.split('\n')

        for line in lines:
            # Check if this line is a section header
            detected_name = _detect_section_header(line)

            if detected_name:
                # Save the current section if it has content
                if current_section["text_parts"]:
                    section = _finalize_section(current_section)
                    if section["word_count"] > 50:  # skip tiny sections
                        sections.append(section)

                # Start a new section
                current_section = {
                    "name": detected_name,
                    "pages": [page_num],
                    "text_parts": [],
                    "is_performance_section": _is_performance_section(detected_name)
                }
            else:
                # Add content to current section
                if page_num not in current_section["pages"]:
                    current_section["pages"].append(page_num)
                current_section["text_parts"].append(line)

    # Don't forget the last section
    if current_section["text_parts"]:
        section = _finalize_section(current_section)
        if section["word_count"] > 50:
            sections.append(section)

    # If no sections detected, return the whole report as one section
    if len(sections) <= 1:
        all_text = " ".join([p["text"] for p in pages])
        sections = [{
            "name": "Full Report (sections not detected)",
            "pages": [p["page_num"] for p in pages],
            "full_text": all_text.lower(),
            "word_count": len(all_text.split()),
            "is_performance_section": False,
            "page_range": f"1-{pages[-1]['page_num'] if pages else 1}"
        }]

    return sections


def _detect_section_header(line: str) -> str:
    """
    Check if a line is a section header. Returns the cleaned header name or None.
    """
    line_stripped = line.strip()

    # Must be reasonably short to be a header (not a sentence)
    if len(line_stripped.split()) > 10:
        return None

    # Check against known patterns
    line_lower = line_stripped.lower()
    for pattern in SECTION_HEADER_PATTERNS:
        if re.match(pattern, line_lower):
            return line_stripped.title()

    # Also detect ALL-CAPS lines of 2-6 words as likely headers
    if (line_stripped.isupper() and
            2 <= len(line_stripped.split()) <= 6 and
            len(line_stripped) > 8):
        return line_stripped.title()

    return None


def _is_performance_section(section_name: str) -> bool:
    """
    Flag sections that SHOULD contain hard data.
    If these sections score high on vagueness, it's a stronger greenwashing signal.
    """
    performance_keywords = [
        "performance", "data", "metrics", "kpi",
        "targets", "results", "indicators", "figures",
        "emissions", "environmental data"
    ]
    name_lower = section_name.lower()
    return any(kw in name_lower for kw in performance_keywords)


def _finalize_section(current_section: dict) -> dict:
    """Convert text_parts list into a finalized section dict."""
    full_text = " ".join(current_section["text_parts"]).lower()
    pages = current_section["pages"]
    return {
        "name": current_section["name"],
        "pages": pages,
        "page_range": f"{min(pages)}-{max(pages)}" if pages else "?",
        "full_text": full_text,
        "word_count": len(full_text.split()),
        "is_performance_section": current_section["is_performance_section"]
    }


def score_section_vagueness(section: dict) -> dict:
    """
    Score a single section for vague vs specific language.
    Returns a risk score 0-10 for that section.

    LOGIC: Performance sections get penalized MORE for vagueness,
    because a section titled "Environmental Performance" should have numbers.
    """
    from src.config import VAGUE_ESG_WORDS, SPECIFIC_ESG_WORDS
    from src.matcher import match_terms
    text = section["full_text"]
    words = text.split()
    total_words = max(len(words), 1)

    vague_hits = match_terms(text, VAGUE_ESG_WORDS).total_asserted
    specific_hits = match_terms(text, SPECIFIC_ESG_WORDS).total_asserted

    # Normalized density per 1000 words
    vague_density = (vague_hits / total_words) * 1000
    specific_density = (specific_hits / total_words) * 1000

    # Base score: vague density minus specific density, scaled
    raw_score = min(10, max(0, (vague_density - specific_density) / 2))

    # Penalty: if this is a performance section and still vague, add 2 points
    if section.get("is_performance_section") and specific_density < 1:
        raw_score = min(10, raw_score + 2.0)

    return {
        "section_name": section["name"],
        "page_range": section["page_range"],
        "word_count": section["word_count"],
        "vague_hits": vague_hits,
        "specific_hits": specific_hits,
        "vague_density_per_1000": round(vague_density, 2),
        "specific_density_per_1000": round(specific_density, 2),
        "greenwashing_risk_score": round(raw_score, 2),
        "is_performance_section": section["is_performance_section"],
    }
