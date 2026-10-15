# =============================================================================
# test_extractor.py — Sentence splitting on lowercased report text
# =============================================================================
# The pipeline lowercases the report before splitting it into sentences.
# The original splitter waited for a capital letter after each full stop,
# so it never split at all. These tests lock in the fix.
# Run with:  python -m pytest tests/test_extractor.py -v
# =============================================================================

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pdfplumber

from src.extractor import extract_sentences, _page_text


def test_lowercase_text_is_split_into_sentences():
    text = ("we reduced financed emissions by 20% in 2024. "
            "we aim to reach net zero by 2050 across the portfolio. "
            "our methodology follows the pcaf standard for all sectors.")
    assert len(extract_sentences(text)) == 3


def test_decimals_do_not_split_a_sentence():
    text = "the green asset ratio rose to 1.5% in 2024 from 1.2% a year earlier."
    assert len(extract_sentences(text)) == 1


def test_abbreviations_do_not_split_a_sentence():
    text = ("we finance renewable projects, e.g. wind and solar parks, across italy. "
            "we exclude thermal coal, i.e. mining and power generation, from new lending.")
    assert len(extract_sentences(text)) == 2


def test_line_breaks_inside_a_sentence_are_kept_together():
    text = "we will reduce the carbon intensity of\nour power portfolio by 2030. next sentence has five words."
    sentences = extract_sentences(text)
    assert len(sentences) == 2
    assert "carbon intensity of\nour power portfolio" in sentences[0]


# ---------------------------------------------------------------------------
# Sideways (landscape) pages: banks print EU Taxonomy tables rotated by 90
# degrees, and pdfplumber's default reads that text backwards ("gar" -> "rag")
# ---------------------------------------------------------------------------
def test_sideways_table_row_is_read_forwards(tmp_path):
    pdf_path = tmp_path / "rotated.pdf"
    fig = plt.figure(figsize=(4, 6))
    fig.text(0.5, 0.1, "Green asset ratio (GAR) stock 3,872.4 4,443.0 9.2 10.5",
             rotation=90, fontsize=9)
    fig.savefig(pdf_path)
    plt.close(fig)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        assert ")RAG(" in page.extract_text()          # the bug: read backwards
        assert _page_text(page) == "Green asset ratio (GAR) stock 3,872.4 4,443.0 9.2 10.5"
