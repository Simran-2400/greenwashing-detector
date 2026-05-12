# =============================================================================
# extractor.py — PDF to Clean Text
# =============================================================================
#
# LOGIC: A PDF sustainability report is not just text — it contains tables,
# headers, footers, page numbers, and images. We need to:
#   1. Extract raw text page by page
#   2. Remove noise (page numbers, repeated headers/footers)
#   3. Return both the full text AND a page-indexed version
#      (so we can later say "this claim is on page 12")

import pdfplumber
import re
from pathlib import Path


def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extract clean text from a bank sustainability report PDF.

    Returns a dict with:
      - full_text: entire report as one string (for keyword counting)
      - pages: list of {page_num, text} (for section detection)
      - word_count: total words in the report
      - page_count: number of pages processed
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages_data = []
    full_text_parts = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        for i, page in enumerate(pdf.pages):
            raw_text = page.extract_text()
            if not raw_text:
                continue  # skip empty pages (images, charts)

            cleaned = _clean_page_text(raw_text, i + 1)
            if len(cleaned.strip()) < 50:
                continue  # skip pages with almost no text (graphics pages)

            pages_data.append({
                "page_num": i + 1,
                "text": cleaned
            })
            full_text_parts.append(cleaned)

    full_text = "\n".join(full_text_parts).lower()  # lowercase for matching
    word_count = len(full_text.split())

    return {
        "full_text": full_text,
        "pages": pages_data,
        "word_count": word_count,
        "page_count": total_pages,
        "source_path": str(pdf_path)
    }


def _clean_page_text(text: str, page_num: int) -> str:
    """
    Remove noise from extracted page text.

    Noise types we filter:
      - Standalone page numbers (e.g. "12" or "Page 12 of 150")
      - Repeated short headers/footers (less than 5 words on a line)
      - Multiple blank lines
      - Special characters that break NLP
    """
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip standalone page numbers
        if re.match(r'^\d{1,3}$', line):
            continue

        # Skip "Page X of Y" patterns
        if re.match(r'^[Pp]age\s+\d+\s*(of\s+\d+)?$', line):
            continue

        # Skip very short lines that are likely headers/footers (< 4 words)
        # Exception: keep short lines that look like section headers (all caps)
        words = line.split()
        if len(words) < 4 and not line.isupper() and not line.endswith(':'):
            # Only skip if it looks like noise, not a heading
            if not any(char.isdigit() for char in line):
                continue

        # Remove special characters that break text matching
        line = re.sub(r'[^\w\s\.\,\!\?\:\;\-\%\€\$\(\)\/]', ' ', line)
        line = re.sub(r'\s+', ' ', line).strip()

        if line:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def extract_sentences(full_text: str) -> list:
    """
    Split full text into sentences.
    Used by signal_scorer.py to classify each sentence as
    forward-looking or backward-looking.
    """
    # Simple sentence splitter — handles most ESG report patterns
    # Split on period + space + capital letter, or newline
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', full_text)
    # Filter out very short fragments (likely headers or noise)
    sentences = [s.strip() for s in sentences if len(s.split()) >= 5]
    return sentences


def get_word_list(full_text: str) -> list:
    """
    Return a list of individual words, cleaned.
    Used by language_audit.py for frequency counting.
    """
    # Remove punctuation, split into words
    words = re.findall(r'\b[a-z][a-z\-]+[a-z]\b', full_text.lower())
    # Remove common English stop words that add no analytical value
    stop_words = {
        "the", "and", "of", "to", "in", "a", "is", "that", "for", "on",
        "are", "with", "as", "this", "our", "we", "its", "it", "be",
        "have", "has", "by", "an", "at", "or", "from", "was", "not",
        "which", "all", "their", "more", "also", "been", "will", "they",
        "than", "can", "into", "who", "year", "years", "new", "one",
        "these", "such", "other", "may", "been", "were", "had", "would",
        "through", "including", "based", "within", "over", "up",
        "your", "about", "per", "each", "both", "between", "further",
        "during", "however", "under", "while", "where", "when", "how"
    }
    return [w for w in words if w not in stop_words and len(w) > 3]
