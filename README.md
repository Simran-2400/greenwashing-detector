# Talk versus Walk: Greenwashing Detection in EU Bank Sustainability Reports

A Python pipeline that reads bank sustainability statements published under the EU Corporate Sustainability Reporting Directive (CSRD) and measures the gap between what a bank **says** about climate (its narrative) and what its reported figures **show** (its disclosures).

Master's thesis project, MSc Data Science for Management, University of Parma.

---

## The idea in one paragraph

Since FY2024, large EU banks publish a Consolidated Sustainability Statement inside their annual report. It contains two things side by side: a long narrative about climate ambition, and quantitative disclosures such as the Green Asset Ratio and financed emissions. Usually these tell the same story. Sometimes they don't. A bank can write confidently about net zero while only a small share of its lending is green. This project scores the narrative with theory-grounded language signals and treats a large talk versus walk gap as a statistical outlier among peer banks.

It is a **screening tool**, not a verdict. It flags which reports deserve a closer look and shows the exact sentences behind every score.

## How it works

```
PDF annual report
   │
   ├─ 1. Extract       pdfplumber reads only the sustainability statement pages
   ├─ 2. Section       headers are detected (strategy, targets, metrics, ...)
   ├─ 3. Match         validated keyword engine (word boundaries, negation, evidence)
   ├─ 4. Score         six signals, each tied to an impression management tactic
   ├─ 5. Audit         boilerplate ratio: vague vs specific ESG vocabulary
   └─ 6. Output        Excel results + charts  →  statistical layer (outlier detection)
```

## The six signals

Each signal measures one impression management tactic from the accounting literature on narrative disclosure (Merkl-Davies and Brennan, 2007).

| # | Signal | What it captures | Side |
|---|---|---|---|
| 1 | Net-zero claim density | Aspirational climate claims per 1,000 words | Talk |
| 2 | Financed emissions disclosure | Whether Scope 3 Category 15 / PCAF figures are reported | Walk |
| 3 | Fossil exit vs continuation | Binding exit language vs hedged, loophole wording | Talk |
| 4 | Target quantification | Share of targets with a number, baseline and deadline | Talk |
| 5 | Forward vs backward orientation | Promises vs reported results | Talk |
| 6 | EU Taxonomy / GAR disclosure | Whether the mandated alignment metrics are disclosed | Walk |

The full reasoning for every keyword list, and every term removed, is in [`docs/DICTIONARY_JUSTIFICATION.md`](docs/DICTIONARY_JUSTIFICATION.md).

## Measurement validity

The first version of the pipeline used plain substring counting, which inflated scores. For example, `"gar"` matched inside `"regarding"`, and `"we have not set a net-zero target"` counted as a net-zero claim. The matching engine in [`src/matcher.py`](src/matcher.py) fixes this:

- **Whole-word matching** so terms only match as complete words or phrases
- **Longest match first** so `"Net Zero Banking Alliance"` counts once, not twice
- **Negation handling** so negated mentions are reported separately and excluded from scores
- **Evidence trail** so every count links back to the sentence that produced it

Each fix is locked in by a regression test.

## Quick start

Requires Python 3.10 or newer.

```bash
git clone https://github.com/Simran-2400/greenwashing-detector.git
cd greenwashing-detector
pip install -r requirements.txt
```

Place the bank PDFs in `data/reports/<country>/` using the filenames listed in [`src/config.py`](src/config.py), then run:

```bash
python main.py --country italy            # all banks for one country
python analyze_single.py report.pdf --bank "Banco BPM" --country italy   # one report
python -m pytest tests/ -v                # run the test suite
```

Results are written to `data/output/scores/greenwashing_results.xlsx` and charts to `data/output/charts/`.

### Annual reports with an embedded statement

Most banks publish the sustainability statement as a chapter of a 1,000-page annual report. Analysing the whole PDF would bury the signal under financial statements, so each bank in `config.py` can carry a page range:

```python
{"name": "BPER Banca", "filename": "bper_2025.pdf", "pages": (94, 229)}
```

`pages: None` analyses the whole file, which is correct when the bank publishes a standalone statement.

## Project structure

```
greenwashing-detector/
├── main.py                  Run the full pipeline for one or more countries
├── analyze_single.py        Detailed analysis of a single report
├── create_template.py       Template for external evidence (news, NGO reports)
├── src/
│   ├── config.py            Keyword dictionaries, bank list, page ranges
│   ├── extractor.py         PDF text extraction with page-range selection
│   ├── matcher.py           Validated keyword matching engine
│   ├── section_parser.py    Section detection
│   ├── signal_scorer.py     The six greenwashing signals
│   ├── language_audit.py    Boilerplate ratio
│   ├── gap_calculator.py    Talk versus walk gap
│   ├── external_validator.py  Cross-check against external evidence
│   └── visualizer.py        Charts
├── tests/                   Regression tests (pytest)
└── docs/
    └── DICTIONARY_JUSTIFICATION.md
```

## Data

- **Sample:** FY2025 Consolidated Sustainability Statements, the second CSRD reporting year. Pilot on five Italian banks (Intesa Sanpaolo, UniCredit, Banco BPM, BPER Banca, Monte dei Paschi), extending to roughly 30 to 40 EU banks reporting in English. FY2024 is used as a robustness check.
- **Sources:** public documents only, downloaded from each bank's investor relations website.
- **Not in this repository:** bank PDFs are copyrighted, so `data/reports/` and `data/output/` are excluded by `.gitignore`.

## Status

| Component | Status |
|---|---|
| Validated matching engine | Done |
| Theory-grounded dictionaries | Done |
| Page-range extraction | Done |
| FY2025 Italian pilot corpus | Collected |
| First full pipeline run | Next |
| EU sample frame (30 to 40 banks) | Planned |
| Statistical layer: Forward Search and robust regression (FSDA) | Planned |

## Known limitations

- Dictionary methods capture recognised wording, not every possible phrasing.
- There is no ground truth for greenwashing, so the index supports construct validity arguments rather than a proven accuracy figure.
- English-language reports only.
- Score labels (LOW to CRITICAL) are for readability. Inference is done on the continuous scores.

## Author

**Simran Vishnoi**, MSc Data Science for Management, University of Parma.
