# =============================================================================
# external_validator.py — External Reality Cross-Reference
# =============================================================================
#
# LOGIC: The team manually fills in an Excel/CSV file with:
#   - News articles about each bank's actual ESG actions
#   - CEO/management public statements
#   - NGO reports, regulatory actions
#
# This module reads that file and cross-references each item
# against the bank's report signal scores — flagging contradictions.
#
# HOW IT WORKS:
#   1. Team researches 3-5 items per bank (takes ~30 min per bank)
#   2. Fills in the template Excel file (external_data.xlsx)
#   3. Code reads it, matches by bank name, compares topics to signal scores
#   4. Outputs a contradiction report + adjusted reality score

import pandas as pd
from pathlib import Path


# How contradiction levels affect the external reality score
CONTRADICTION_WEIGHTS = {
    "STRONGLY_CONTRADICTS": 9.0,
    "CONTRADICTS":          6.5,
    "NEUTRAL":              5.0,
    "CONFIRMS":             1.5,
}

# Which external topic maps to which signal
TOPIC_TO_SIGNAL = {
    "fossil_fuel":        "fossil_fuel",
    "netzero":            "netzero_density",
    "financed_emissions": "financed_emissions",
    "taxonomy":           "taxonomy_disclosure",
    "targets":            "target_quantification",
    "general":            None,
}


def load_external_data(filepath: str) -> pd.DataFrame:
    """
    Load the external reality Excel or CSV file.
    Returns empty DataFrame if file doesn't exist yet.
    """
    path = Path(filepath)
    if not path.exists():
        print(f"  [!] No external data file found at {filepath}")
        print(f"      Run: python3 create_template.py to generate the template")
        return pd.DataFrame()

    if path.suffix == ".csv":
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    # Normalize bank names for matching
    df["bank_name_clean"] = df["bank_name"].str.strip().str.lower()
    return df


def validate_bank(bank_name: str, signals: dict, external_df: pd.DataFrame) -> dict:
    """
    Cross-reference a bank's signal scores against external reality items.

    Returns:
      - items: list of external items for this bank with analysis
      - external_reality_score: 0-10 (how much reality contradicts the report)
      - contradiction_count: number of direct contradictions found
      - confirmation_count: number of confirming items found
      - summary: one-paragraph finding
    """
    if external_df.empty:
        return _empty_result()

    # Match rows for this bank
    bank_clean = bank_name.strip().lower()
    bank_rows = external_df[external_df["bank_name_clean"] == bank_clean]

    if bank_rows.empty:
        return _empty_result(
            f"No external data found for '{bank_name}'. "
            f"Add entries to external_data.xlsx to enable reality check."
        )

    items = []
    contradiction_scores = []
    contradiction_count = 0
    confirmation_count = 0

    for _, row in bank_rows.iterrows():
        contradiction = str(row.get("contradiction_level", "NEUTRAL")).upper().strip()
        topic = str(row.get("topic", "general")).lower().strip()
        signal_key = TOPIC_TO_SIGNAL.get(topic)

        # Get the report's score on this topic for comparison
        report_score = None
        signal_finding = None
        if signal_key and signal_key in signals:
            report_score = signals[signal_key]["score"]
            signal_finding = signals[signal_key]["finding"]

        # Build the analysis sentence
        analysis = _build_analysis(
            contradiction, topic, row, report_score, signal_finding
        )

        item = {
            "type":              str(row.get("type", "news")),
            "headline":          str(row.get("headline", "")),
            "source":            str(row.get("source", "")),
            "date":              str(row.get("date", "")),
            "topic":             topic,
            "contradiction":     contradiction,
            "detail":            str(row.get("detail", "")),
            "report_claim":      str(row.get("report_claim", "")),
            "related_signal":    signal_key,
            "report_score":      report_score,
            "analysis":          analysis,
        }
        items.append(item)

        # Track score
        weight = CONTRADICTION_WEIGHTS.get(contradiction, 5.0)
        contradiction_scores.append(weight)

        if contradiction in ("CONTRADICTS", "STRONGLY_CONTRADICTS"):
            contradiction_count += 1
        elif contradiction == "CONFIRMS":
            confirmation_count += 1

    # External reality score = average of contradiction weights
    external_reality_score = (
        sum(contradiction_scores) / len(contradiction_scores)
        if contradiction_scores else 5.0
    )

    # Build summary
    total = len(items)
    summary = (
        f"Found {total} external item(s) for {bank_name}. "
        f"{contradiction_count} contradict the report, "
        f"{confirmation_count} confirm it. "
    )
    if contradiction_count > total / 2:
        summary += (
            "External evidence raises significant concerns about the "
            "credibility of the bank's sustainability report."
        )
    elif confirmation_count > total / 2:
        summary += (
            "External evidence broadly supports the bank's "
            "sustainability disclosures."
        )
    else:
        summary += "External evidence presents a mixed picture."

    return {
        "items":                   items,
        "external_reality_score":  round(external_reality_score, 2),
        "contradiction_count":     contradiction_count,
        "confirmation_count":      confirmation_count,
        "total_items":             total,
        "summary":                 summary,
    }


def _build_analysis(contradiction, topic, row, report_score, signal_finding):
    """Generate a one-sentence analysis of why this item confirms or contradicts."""
    headline = str(row.get("headline", ""))
    report_claim = str(row.get("report_claim", ""))

    if contradiction == "STRONGLY_CONTRADICTS":
        return (
            f"This directly contradicts the report's {topic} claims. "
            f"The report states: '{report_claim[:80]}' "
            f"but external evidence shows the opposite."
        )
    elif contradiction == "CONTRADICTS":
        return (
            f"This conflicts with the report's {topic} narrative. "
            f"The report score on this signal is {report_score}/10."
        )
    elif contradiction == "CONFIRMS":
        return (
            f"This supports the report's {topic} disclosure. "
            f"External evidence is consistent with reported commitments."
        )
    else:
        return f"This item provides additional context on the bank's {topic} position."


def _empty_result(message=None):
    return {
        "items":                  [],
        "external_reality_score": None,
        "contradiction_count":    0,
        "confirmation_count":     0,
        "total_items":            0,
        "summary":                message or "No external data available.",
    }


def print_external_report(bank_name: str, result: dict, console):
    """Pretty-print the external reality section to terminal."""
    from rich.table import Table
    from rich import box

    console.print("\n[bold underline]LAYER 2 — External Reality Check[/bold underline]")

    if not result["items"]:
        console.print(f"  [dim]{result['summary']}[/dim]")
        return

    score = result["external_reality_score"]
    score_style = "green" if score <= 3 else "yellow" if score <= 6 else "red"

    console.print(f"  External reality score: [{score_style}]{score}/10[/{score_style}]")
    console.print(f"  {result['summary']}")

    t = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    t.add_column("Type",          width=10)
    t.add_column("Headline",      min_width=30, max_width=45)
    t.add_column("Source",        width=14)
    t.add_column("Date",          width=10)
    t.add_column("Topic",         width=12)
    t.add_column("Verdict",       width=20)

    verdict_styles = {
        "STRONGLY_CONTRADICTS": "bold red",
        "CONTRADICTS":          "red",
        "NEUTRAL":              "dim",
        "CONFIRMS":             "green",
    }

    for item in result["items"]:
        v = item["contradiction"]
        style = verdict_styles.get(v, "white")
        t.add_row(
            item["type"].upper(),
            item["headline"][:45],
            item["source"][:14],
            item["date"][:10],
            item["topic"],
            f"[{style}]{v.replace('_', ' ')}[/{style}]",
        )
    console.print(t)

    # Show details for contradictions only
    contradictions = [i for i in result["items"]
                      if i["contradiction"] in ("CONTRADICTS", "STRONGLY_CONTRADICTS")]
    if contradictions:
        console.print(f"\n  [red]Contradiction details:[/red]")
        for item in contradictions:
            console.print(f"    • [bold]{item['headline'][:70]}[/bold]")
            console.print(f"      {item['analysis']}")
            if item["report_claim"]:
                console.print(f"      Report claimed: [dim italic]\"{item['report_claim'][:80]}\"[/dim italic]")
            console.print()
