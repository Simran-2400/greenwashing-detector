# =============================================================================
# analyze_single.py — Analyze One Bank PDF
# =============================================================================
# USAGE:
#   python analyze_single.py path/to/bank_report.pdf --bank "BNP Paribas" --country france
#
# This is the script you demo in the presentation.
# Upload any bank PDF → get full in-depth scored analysis printed to terminal.

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractor import extract_text_from_pdf, extract_sentences, get_word_list
from src.language_audit import run_language_audit
from src.section_parser import parse_sections, score_section_vagueness
from src.signal_scorer import score_all_signals
from src.gap_calculator import calculate_greenwashing_index
from src.external_validator import load_external_data, validate_bank, print_external_report

EXTERNAL_DATA_PATH = "external_data.xlsx"

console = Console()

VERDICT_STYLES = {
    "LOW":      "bold green",
    "MODERATE": "bold yellow",
    "HIGH":     "bold red",
    "CRITICAL": "bold white on red",
}

SCORE_STYLE = lambda s: "green" if s <= 3 else "yellow" if s <= 5.5 else "red"


def analyze_bank(pdf_path: str, bank_name: str, country: str) -> dict:
    """Full pipeline: PDF → scores → report."""

    console.print(f"\n[bold]Analyzing:[/bold] {bank_name} ({country.title()})")
    console.print(f"[dim]File: {pdf_path}[/dim]\n")

    # ── LAYER 1A: Extract text ────────────────────────────────────────────────
    with console.status("[cyan]Extracting text from PDF..."):
        extracted = extract_text_from_pdf(pdf_path)
        sentences = extract_sentences(extracted["full_text"])
        word_list = get_word_list(extracted["full_text"])

    console.print(f"  [green]✓[/green] Extracted {extracted['word_count']:,} words from {extracted['page_count']} pages")

    # ── LAYER 1B: Language audit ──────────────────────────────────────────────
    with console.status("[cyan]Running language audit..."):
        audit = run_language_audit(extracted["full_text"], word_list)

    boilerplate_style = "green" if audit["boilerplate_label"] == "LOW" else \
                        "yellow" if audit["boilerplate_label"] == "MODERATE" else "red"
    console.print(f"  [green]✓[/green] Boilerplate ratio: [{boilerplate_style}]{audit['boilerplate_ratio_pct']}%[/{boilerplate_style}] ({audit['boilerplate_label']})")

    # ── LAYER 1C: Section segmentation ───────────────────────────────────────
    with console.status("[cyan]Segmenting report sections..."):
        sections = parse_sections(extracted["pages"])
        section_scores = [score_section_vagueness(s) for s in sections]

    console.print(f"  [green]✓[/green] Detected {len(sections)} report sections")

    # ── LAYER 1D: Signal scoring ──────────────────────────────────────────────
    with console.status("[cyan]Scoring 6 greenwashing signals..."):
        signals = score_all_signals(
            extracted["full_text"],
            extracted["word_count"],
            sentences
        )

    console.print(f"  [green]✓[/green] Scored all 6 signals")

    # ── Gap calculation ───────────────────────────────────────────────────────
    gap_calc = calculate_greenwashing_index(signals, audit["boilerplate_ratio"])

    # ── External reality check ────────────────────────────────────────────────
    with console.status("[cyan]Loading external reality data..."):
        external_df = load_external_data(EXTERNAL_DATA_PATH)
        external = validate_bank(bank_name, signals, external_df)

    # ── Print full report ─────────────────────────────────────────────────────
    _print_report(bank_name, country, extracted, audit, sections,
                  section_scores, signals, gap_calc, external)

    # Return structured result for batch processing
    return {
        "bank_name": bank_name,
        "country": country,
        "word_count": extracted["word_count"],
        "language_audit": audit,
        "sections": section_scores,
        "signals": signals,
        "gap_calc": gap_calc,
    }


def _print_report(bank_name, country, extracted, audit, sections,
                  section_scores, signals, gap_calc, external):
    """Pretty-print the full analysis to terminal."""

    verdict = gap_calc["verdict"]
    index = gap_calc["greenwashing_index"]
    style = VERDICT_STYLES.get(verdict, "bold")

    # ── Header ────────────────────────────────────────────────────────────────
    console.print()
    console.rule(f"[bold]{bank_name}[/bold] — Greenwashing Analysis")

    console.print(Panel(
        f"[{style}]VERDICT: {verdict}[/{style}]\n"
        f"Greenwashing Index: [{style}]{index}/10[/{style}]\n"
        f"Narrative Score: {gap_calc['narrative_score']}/10  |  "
        f"Performance Score: {gap_calc['performance_score']}/10\n"
        f"Gap interpretation: {gap_calc['gap_interpretation']}",
        title="Overall Result",
        border_style="dim"
    ))

    # ── Language Audit ────────────────────────────────────────────────────────
    console.print("\n[bold underline]LAYER 1A — Language Audit[/bold underline]")
    boilerplate_style = "green" if audit["boilerplate_label"] == "LOW" else \
                        "yellow" if audit["boilerplate_label"] == "MODERATE" else "red"

    console.print(f"  Boilerplate ratio: [{boilerplate_style}]{audit['boilerplate_ratio_pct']}% ({audit['boilerplate_label']})[/{boilerplate_style}]")
    console.print(f"  Vague ESG terms: {audit['vague_count']} occurrences")
    console.print(f"  Specific ESG terms: {audit['specific_count']} occurrences")
    console.print(f"  Interpretation: [dim]{audit['interpretation']}[/dim]")

    if audit["repetition_flags"]:
        console.print(f"\n  [yellow]⚠ Repetition flags:[/yellow]")
        for term, count in audit["repetition_flags"][:5]:
            console.print(f"    '{term}' appears [yellow]{count}×[/yellow]")

    if audit["top_vague_words"]:
        console.print(f"\n  Most repeated vague terms:")
        for term, count in audit["top_vague_words"][:5]:
            console.print(f"    [dim]'{term}'[/dim] — {count}×")

    # ── Section Scores ────────────────────────────────────────────────────────
    console.print("\n[bold underline]LAYER 1B — Report Section Breakdown[/bold underline]")
    t = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    t.add_column("Section", style="dim", min_width=25)
    t.add_column("Pages", justify="center")
    t.add_column("Words", justify="right")
    t.add_column("Risk Score", justify="center")
    t.add_column("Perf. Section?", justify="center")

    for s in sorted(section_scores, key=lambda x: x["greenwashing_risk_score"], reverse=True)[:8]:
        risk = s["greenwashing_risk_score"]
        risk_style = SCORE_STYLE(risk)
        t.add_row(
            s["section_name"][:35],
            s["page_range"],
            str(s["word_count"]),
            f"[{risk_style}]{risk:.1f}[/{risk_style}]",
            "⚠ YES" if s["is_performance_section"] else "no"
        )
    console.print(t)

    # ── Signal Scores ─────────────────────────────────────────────────────────
    console.print("\n[bold underline]LAYER 1C — Greenwashing Signal Scores[/bold underline]")
    t2 = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    t2.add_column("Signal", min_width=28)
    t2.add_column("Type", justify="center")
    t2.add_column("Score", justify="center")
    t2.add_column("Finding", max_width=55)

    signal_labels = {
        "netzero_density":       "S1: Net-Zero Claim Density",
        "financed_emissions":    "S2: Financed Emissions",
        "fossil_fuel":           "S3: Fossil Fuel Specificity",
        "target_quantification": "S4: Target Quantification",
        "forward_backward":      "S5: Fwd vs Bwd Ratio",
        "taxonomy_disclosure":   "S6: Taxonomy Disclosure",
    }

    for key, label in signal_labels.items():
        sig = signals[key]
        score = sig["score"]
        score_style = SCORE_STYLE(score)
        t2.add_row(
            label,
            sig["signal_type"],
            f"[{score_style}]{score:.1f}[/{score_style}]",
            sig["finding"][:80]
        )

    console.print(t2)

    # ── Key Findings ──────────────────────────────────────────────────────────
    console.print("\n[bold underline]Key Findings[/bold underline]")

    # Sort signals by severity
    sorted_signals = sorted(
        [(k, v) for k, v in signals.items()],
        key=lambda x: x[1]["score"], reverse=True
    )

    for i, (key, sig) in enumerate(sorted_signals[:3], 1):
        score_style = SCORE_STYLE(sig["score"])
        label = signal_labels[key]
        console.print(f"  [{i}] [{score_style}]{label} (score: {sig['score']:.1f})[/{score_style}]")
        console.print(f"      {sig['finding']}")
        console.print(f"      [dim]{sig['reasoning']}[/dim]\n")

    # ── External Reality ──────────────────────────────────────────────────────
    print_external_report(bank_name, external, console)

    console.rule()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a bank sustainability report for greenwashing signals."
    )
    parser.add_argument("pdf_path", help="Path to the PDF sustainability report")
    parser.add_argument("--bank", default="Unknown Bank", help="Bank name")
    parser.add_argument("--country", default="unknown", help="Country (italy/germany/france)")
    parser.add_argument("--save-json", action="store_true", help="Save results to JSON file")

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        console.print(f"[red]Error: File not found: {args.pdf_path}[/red]")
        sys.exit(1)

    result = analyze_bank(args.pdf_path, args.bank, args.country)

    if args.save_json:
        out_path = f"data/output/scores/{args.bank.lower().replace(' ', '_')}_result.json"
        Path("data/output/scores").mkdir(parents=True, exist_ok=True)
        # Convert to serializable format
        serializable = {k: v for k, v in result.items()
                        if k not in ["signals"]}
        serializable["signals"] = {
            k: {sk: sv for sk, sv in v.items() if not isinstance(sv, dict)}
            for k, v in result["signals"].items()
        }
        with open(out_path, "w") as f:
            json.dump(serializable, f, indent=2)
        console.print(f"\n[green]Results saved to {out_path}[/green]")


if __name__ == "__main__":
    main()
