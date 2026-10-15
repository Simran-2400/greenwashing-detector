"""
find_pages.py — Locate the Sustainability Statement inside a bank annual report.

Big annual reports bury the CSRD Sustainability Statement in the middle. Its
pages carry a running header such as "Consolidated Sustainability Statement",
so we mark every page that names the statement, plus the sideways (landscape)
table pages, whose rotated header is hard to read. The longest block of marked
pages is the statement.

Small gaps are allowed (blank pages, reports that print the header on odd
pages only). The auditor's assurance report is left out: it names the
statement but is not the bank's own text.

Checked on the FY2025 reports of Intesa Sanpaolo, UniCredit, Banco BPM, BPER
and MPS: all five ranges match the ones verified by hand.

The output is a SUGGESTION. Always check the start and end pages in the PDF
before writing them into config.py.

    python3 find_pages.py data/reports/italy_2025
"""

import re
import sys
from pathlib import Path

import pdfplumber

from src.extractor import _page_text   # also reads sideways table pages

HEADER = re.compile(r"sustainability (statement|reporting)", re.I)
AUDITOR = re.compile(r"independent auditor|auditor['’]s responsibilit|assurance engagement|certification of", re.I)
MAX_GAP = 3   # unmarked pages allowed inside one block


def is_statement_page(text: str, sideways: bool) -> bool:
    """True if the page names the statement (or is a sideways table) and is not the auditor's report."""
    text = " ".join(text.split())
    return (bool(HEADER.search(text)) or sideways) and not AUDITOR.search(text)


def find_block(marked: list) -> tuple:
    """Longest block of marked pages (1-indexed), allowing gaps of MAX_GAP pages."""
    best = None
    start = last = None
    for page, ok in enumerate(marked, start=1):
        if not ok:
            continue
        if last is not None and page - last <= MAX_GAP + 1:
            last = page
        else:
            start = last = page
        if best is None or last - start > best[1] - best[0]:
            best = (start, last)
    return best


def scan(pdf_path: Path) -> None:
    marked = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            chars = page.chars
            sideways = bool(chars) and sum(not c["upright"] for c in chars) > len(chars) / 2
            marked.append(is_statement_page(_page_text(page) or "", sideways))
            page.close()   # free memory: annual reports run to 1,000+ pages
    block = find_block(marked)
    print(f"\n{pdf_path.name}  ({len(marked)} pages)")
    if block is None:
        print("  statement not found: check the table of contents by hand")
        return
    start, end = block
    print(f"  sustainability statement : pages {start}-{end}  ({end - start + 1} pages)")
    print(f"  config entry             : ({start}, {end})")


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "data/reports/italy_2025")
    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs found in {folder}")
    print(f"Scanning {len(pdfs)} reports in {folder}. This takes a few minutes.")
    for pdf in pdfs:
        scan(pdf)
    print("\nCheck each range in the PDF, then add it to BANKS in src/config.py")
