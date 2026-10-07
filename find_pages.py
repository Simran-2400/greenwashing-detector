"""
find_pages.py — Locate the Sustainability Statement inside a bank annual report.

Big annual reports bury the CSRD Sustainability Statement in the middle. This
scans each PDF, scores every page for ESRS/sustainability vocabulary, and
reports the longest dense run of such pages: the likely statement.

The output is a SUGGESTION. Always eyeball the reported start/end pages in the
PDF before writing them into config.py.

    python3 find_pages.py                      # all PDFs in a folder
    python3 find_pages.py data/reports/italy_2025
"""

import sys
from pathlib import Path
import pdfplumber

# Vocabulary that appears densely inside a sustainability statement and
# almost nowhere else in an annual report.
MARKERS = [
    "esrs", "sustainability statement", "double materiality", "csrd",
    "scope 1", "scope 2", "scope 3", "ghg emissions", "financed emissions",
    "taxonomy", "green asset ratio", "climate change mitigation",
    "value chain", "own workforce", "ipcc", "net zero", "decarbonisation",
]

MIN_HITS = 3        # a page needs this many marker hits to count as "in-scope"
MAX_GAP = 10        # pages of quiet allowed inside one run before it breaks


def page_score(text: str) -> int:
    t = (text or "").lower()
    return sum(t.count(m) for m in MARKERS)


def find_run(scores: list) -> tuple:
    """Longest run of in-scope pages, tolerating small gaps. Returns (start, end)."""
    best = current = None
    gap = 0
    for i, s in enumerate(scores, start=1):
        if s >= MIN_HITS:
            current = current or [i, i]
            current[1], gap = i, 0
        elif current:
            gap += 1
            if gap > MAX_GAP:
                best = max(best or current, current, key=lambda r: r[1] - r[0])
                current = None
    best = max(best or current, current or best, key=lambda r: r[1] - r[0])
    return tuple(best)


def scan(pdf_path: Path) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        scores = [page_score(p.extract_text()) for p in pdf.pages]
    start, end = find_run(scores)
    dense = sum(1 for s in scores if s >= MIN_HITS)
    print(f"\n{pdf_path.name}")
    print(f"  total pages     : {len(scores)}")
    print(f"  sustainability  : pages {start}–{end}  ({end - start + 1} pages)")
    print(f"  in-scope pages  : {dense}")
    print(f"  config entry    : \"pages\": ({start}, {end})")


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "data/reports/italy_2025")
    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs found in {folder}")
    print(f"Scanning {len(pdfs)} reports in {folder} — this takes a few minutes.")
    for pdf in pdfs:
        scan(pdf)
    print("\nVerify each range in the PDF, then paste into BANKS in src/config.py")
