# =============================================================================
# main.py — Full Pipeline: All Banks → All Charts
# =============================================================================
# USAGE:
#   python main.py --country italy          # run Italy only (start here)
#   python main.py --country all            # run all 15 banks
#   python main.py --country italy germany  # run two countries
#
# BEFORE RUNNING:
#   1. Download PDF reports from the links provided
#   2. Save them in data/reports/<country>/ with the filenames in config.py
#   3. pip install -r requirements.txt
#   4. python main.py --country italy

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from src.config import BANKS
from src.extractor import extract_text_from_pdf, extract_sentences, get_word_list
from src.language_audit import run_language_audit
from src.section_parser import parse_sections, score_section_vagueness
from src.signal_scorer import score_all_signals
from src.gap_calculator import calculate_greenwashing_index, build_summary_dataframe
from src.visualizer import save_all_charts

console = Console()

REPORTS_DIR = Path("data/reports")
OUTPUT_DIR  = Path("data/output")


def run_pipeline(countries: list) -> list:
    """
    Run the full pipeline for the specified countries.
    Returns list of result dicts (one per bank).
    """
    all_results = []

    for country in countries:
        if country not in BANKS:
            console.print(f"[yellow]Unknown country: {country}. Skipping.[/yellow]")
            continue

        console.print(f"\n[bold cyan]═══ {country.upper()} ═══[/bold cyan]")
        banks = BANKS[country]

        for bank_meta in banks:
            pdf_path = REPORTS_DIR / country / bank_meta["filename"]

            if not pdf_path.exists():
                console.print(
                    f"  [yellow]⚠ Missing:[/yellow] {pdf_path}\n"
                    f"  → Download from bank's sustainability page and save as: {bank_meta['filename']}"
                )
                continue

            console.print(f"\n  [bold]Analyzing {bank_meta['name']}...[/bold]")

            try:
                # Extract
                extracted  = extract_text_from_pdf(str(pdf_path))
                sentences  = extract_sentences(extracted["full_text"])
                word_list  = get_word_list(extracted["full_text"])

                # Analyze
                audit          = run_language_audit(extracted["full_text"], word_list)
                sections       = parse_sections(extracted["pages"])
                section_scores = [score_section_vagueness(s) for s in sections]
                signals        = score_all_signals(
                                     extracted["full_text"],
                                     extracted["word_count"],
                                     sentences)
                gap_calc       = calculate_greenwashing_index(
                                     signals, audit["boilerplate_ratio"])

                result = {
                    "bank_name":     bank_meta["name"],
                    "country":       country,
                    "ticker":        bank_meta["ticker"],
                    "word_count":    extracted["word_count"],
                    "language_audit": audit,
                    "sections":      section_scores,
                    "signals":       signals,
                    "gap_calc":      gap_calc,
                }
                all_results.append(result)

                # Mini summary line
                idx     = gap_calc["greenwashing_index"]
                verdict = gap_calc["verdict"]
                style   = "green" if verdict == "LOW" else \
                          "yellow" if verdict == "MODERATE" else "red"
                console.print(
                    f"  [green]✓[/green] {bank_meta['name']:25s} "
                    f"Index: [{style}]{idx:.1f}[/{style}]  "
                    f"Verdict: [{style}]{verdict}[/{style}]"
                )

            except Exception as e:
                console.print(f"  [red]✗ Error processing {bank_meta['name']}: {e}[/red]")
                continue

    return all_results


def print_summary_table(all_results: list):
    """Print a ranked summary table of all analyzed banks."""
    console.print("\n")
    console.rule("[bold]RESULTS SUMMARY[/bold]")

    sorted_results = sorted(all_results,
                            key=lambda x: x["gap_calc"]["greenwashing_index"],
                            reverse=True)

    t = Table(box=box.ROUNDED, show_header=True, header_style="bold",
              title="Bank Greenwashing Analysis — FY2024")
    t.add_column("Rank", justify="center", width=4)
    t.add_column("Bank",    min_width=20)
    t.add_column("Country", width=8)
    t.add_column("Index",   justify="center", width=6)
    t.add_column("Verdict", justify="center", width=10)
    t.add_column("Narr.",   justify="center", width=6)
    t.add_column("Perf.",   justify="center", width=6)
    t.add_column("Boilerplate", justify="center", width=10)

    styles = {"LOW": "green", "MODERATE": "yellow",
              "HIGH": "red", "CRITICAL": "bold red"}

    for rank, r in enumerate(sorted_results, 1):
        gc = r["gap_calc"]
        v  = gc["verdict"]
        s  = styles.get(v, "white")
        t.add_row(
            str(rank),
            r["bank_name"],
            r["country"].title(),
            f"[{s}]{gc['greenwashing_index']:.1f}[/{s}]",
            f"[{s}]{v}[/{s}]",
            f"{gc['narrative_score']:.1f}",
            f"{gc['performance_score']:.1f}",
            f"{r['language_audit']['boilerplate_ratio_pct']:.0f}%"
        )

    console.print(t)


def save_excel_output(df: pd.DataFrame):
    """Save the full results DataFrame to Excel for the written report."""
    out_path = OUTPUT_DIR / "scores" / "greenwashing_results.xlsx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(str(out_path), index=False)
    console.print(f"  [green]✓[/green] Excel output saved: {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Bank greenwashing detection pipeline."
    )
    parser.add_argument(
        "--country", nargs="+", default=["italy"],
        help="Countries to analyze: italy germany france all"
    )
    parser.add_argument(
        "--no-charts", action="store_true",
        help="Skip chart generation"
    )

    args = parser.parse_args()
    countries = args.country

    if "all" in countries:
        countries = ["italy", "germany", "france"]

    console.print("\n[bold]Bank Greenwashing Detection Pipeline[/bold]")
    console.print(f"Countries: {', '.join(c.title() for c in countries)}")
    console.print(f"Reports directory: {REPORTS_DIR.absolute()}\n")

    # Run pipeline
    all_results = run_pipeline(countries)

    if not all_results:
        console.print("\n[red]No reports were processed. "
                      "Check that PDFs are in the correct directory.[/red]")
        console.print(f"\nExpected structure:")
        for country in countries:
            for bank in BANKS.get(country, []):
                console.print(f"  {REPORTS_DIR}/{country}/{bank['filename']}")
        return

    # Print summary
    print_summary_table(all_results)

    # Build DataFrame
    df = build_summary_dataframe(all_results)
    save_excel_output(df)

    # Generate charts
    if not args.no_charts and len(all_results) >= 2:
        console.print("\n[bold]Generating charts...[/bold]")
        save_all_charts(df, str(OUTPUT_DIR / "charts"))
    elif len(all_results) < 2:
        console.print("\n[yellow]Need at least 2 banks to generate comparative charts.[/yellow]")

    console.print(f"\n[bold green]✓ Pipeline complete.[/bold green]")
    console.print(f"  Results: {OUTPUT_DIR / 'scores' / 'greenwashing_results.xlsx'}")
    console.print(f"  Charts:  {OUTPUT_DIR / 'charts'}/\n")


if __name__ == "__main__":
    main()
