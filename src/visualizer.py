# =============================================================================
# visualizer.py — Charts for the Presentation
# =============================================================================
#
# LOGIC: Every chart here answers one specific research question.
# We don't make charts for decoration — each one is a finding.
#
# Chart 1: Greenwashing Index by bank (ranked bar chart) → WHO is worst?
# Chart 2: Narrative vs Performance scatter → WHERE is the gap?
# Chart 3: Country comparison heatmap → HOW do countries differ?
# Chart 4: Signal radar/spider chart → WHAT signals drive the score?
# Chart 5: Boilerplate ratio bar → HOW template-heavy is each report?

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path

# Color scheme: consistent with country groupings
COUNTRY_COLORS = {
    "italy":   "#009246",   # Italian green
    "germany": "#DD0000",   # German red
    "france":  "#0055A4",   # French blue
}

VERDICT_COLORS = {
    "LOW":      "#27500A",
    "MODERATE": "#BA7517",
    "HIGH":     "#E24B4A",
    "CRITICAL": "#501313",
}

OUTPUT_DIR = Path("data/output/charts")


def save_all_charts(df: pd.DataFrame, output_dir: str = None):
    """Run all 5 charts and save to output directory."""
    if output_dir:
        global OUTPUT_DIR
        OUTPUT_DIR = Path(output_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    paths = []
    paths.append(chart1_greenwashing_ranking(df))
    paths.append(chart2_narrative_vs_performance(df))
    paths.append(chart3_country_heatmap(df))
    paths.append(chart4_signal_breakdown(df))
    paths.append(chart5_boilerplate_ratio(df))

    print(f"\n✓ All charts saved to {OUTPUT_DIR}/")
    return paths


def chart1_greenwashing_ranking(df: pd.DataFrame) -> str:
    """
    Horizontal bar chart: all banks ranked by Greenwashing Index.
    Color = verdict. This is your headline chart.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    df_sorted = df.sort_values("Greenwashing Index", ascending=True)

    colors = [VERDICT_COLORS.get(v, "#888") for v in df_sorted["Verdict"]]
    bars = ax.barh(df_sorted["Bank"], df_sorted["Greenwashing Index"],
                   color=colors, edgecolor="white", linewidth=0.5)

    # Add value labels
    for bar, val in zip(bars, df_sorted["Greenwashing Index"]):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", fontsize=9)

    ax.set_xlim(0, 11)
    ax.set_xlabel("Greenwashing Index (0 = no risk, 10 = critical)", fontsize=10)
    ax.set_title("Bank Greenwashing Index — FY2024 Sustainability Reports", fontsize=12, pad=12)
    ax.axvline(x=3, color="#27500A", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.axvline(x=5.5, color="#BA7517", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.axvline(x=7.5, color="#E24B4A", linestyle="--", linewidth=0.8, alpha=0.5)

    # Country color coding on y-axis labels
    for label, bank in zip(ax.get_yticklabels(), df_sorted["Bank"]):
        country = df_sorted[df_sorted["Bank"] == bank]["Country"].values[0]
        label.set_color(COUNTRY_COLORS.get(country.lower(), "black"))

    legend = [mpatches.Patch(color=COUNTRY_COLORS[c], label=c.title())
              for c in COUNTRY_COLORS]
    ax.legend(handles=legend, title="Country", loc="lower right", fontsize=8)

    plt.tight_layout()
    path = str(OUTPUT_DIR / "chart1_greenwashing_ranking.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")
    return path


def chart2_narrative_vs_performance(df: pd.DataFrame) -> str:
    """
    Scatter plot: Narrative Score (x) vs Performance Score (y).
    Each point = one bank, colored by country.
    The diagonal line = perfect alignment.
    Points ABOVE the diagonal = under-reporters.
    Points BELOW the diagonal = greenwashers (high narrative, low performance).
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    for country, color in COUNTRY_COLORS.items():
        subset = df[df["Country"].str.lower() == country]
        ax.scatter(subset["Narrative Score"], subset["Performance Score"],
                   color=color, s=100, label=country.title(), zorder=3,
                   edgecolors="white", linewidth=0.8)
        for _, row in subset.iterrows():
            ax.annotate(row["Bank"].split()[0],
                        (row["Narrative Score"], row["Performance Score"]),
                        textcoords="offset points", xytext=(6, 4), fontsize=7)

    # Diagonal = perfect alignment
    ax.plot([0, 10], [0, 10], "k--", linewidth=0.8, alpha=0.4, label="Perfect alignment")

    # Quadrant labels
    ax.text(7.5, 2.0, "GREENWASHING\nZONE", fontsize=8, color="#E24B4A",
            alpha=0.7, ha="center", style="italic")
    ax.text(2.0, 7.5, "UNDER-\nREPORTING", fontsize=8, color="#27500A",
            alpha=0.7, ha="center", style="italic")

    ax.set_xlabel("Narrative Score (higher = more ambitious claims)", fontsize=10)
    ax.set_ylabel("Performance Score (higher = less disclosure)", fontsize=10)
    ax.set_title("Narrative vs Performance — The Talk-Walk Gap", fontsize=12, pad=12)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    path = str(OUTPUT_DIR / "chart2_narrative_vs_performance.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")
    return path


def chart3_country_heatmap(df: pd.DataFrame) -> str:
    """
    Heatmap: Banks (rows) × Signals (columns), colored by score.
    Grouped by country. This shows the full analytical picture at a glance.
    """
    signal_cols = [
        "S1: Net-Zero Density", "S2: Financed Emissions",
        "S3: Fossil Fuel", "S4: Target Quantif.",
        "S5: Fwd/Bwd Ratio", "S6: Taxonomy"
    ]

    df_sorted = df.sort_values(["Country", "Greenwashing Index"])
    heat_data = df_sorted[signal_cols].values
    y_labels = [f"{row['Bank']} ({row['Country'][:2].upper()})"
                for _, row in df_sorted.iterrows()]

    fig, ax = plt.subplots(figsize=(12, max(6, len(df) * 0.6)))
    sns.heatmap(heat_data, annot=True, fmt=".1f",
                xticklabels=[c.replace("S", "S").split(": ")[1] for c in signal_cols],
                yticklabels=y_labels,
                cmap="RdYlGn_r",   # red = high risk, green = low risk
                vmin=0, vmax=10,
                linewidths=0.5, linecolor="white",
                cbar_kws={"label": "Greenwashing Risk (0=low, 10=critical)"},
                ax=ax)

    ax.set_title("Greenwashing Signal Heatmap — All Banks × All Signals", fontsize=12, pad=12)
    ax.set_xlabel("")
    plt.xticks(rotation=30, ha="right", fontsize=9)
    plt.yticks(fontsize=9)
    plt.tight_layout()

    path = str(OUTPUT_DIR / "chart3_country_heatmap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")
    return path


def chart4_signal_breakdown(df: pd.DataFrame) -> str:
    """
    Grouped bar chart: average score per signal, grouped by country.
    This shows HOW each country's reporting culture differs.
    e.g. Italian banks may score high on S2 (financed emissions absent)
    while German banks score high on S4 (quantified targets).
    """
    signal_cols = [
        "S1: Net-Zero Density", "S2: Financed Emissions",
        "S3: Fossil Fuel", "S4: Target Quantif.",
        "S5: Fwd/Bwd Ratio", "S6: Taxonomy"
    ]
    short_labels = ["Net-Zero\nDensity", "Financed\nEmissions",
                    "Fossil\nFuel", "Target\nQuantif.",
                    "Fwd/Bwd\nRatio", "Taxonomy"]

    country_avgs = df.groupby("Country")[signal_cols].mean()
    x = np.arange(len(signal_cols))
    width = 0.25
    countries = list(country_avgs.index)

    fig, ax = plt.subplots(figsize=(12, 6))
    for i, country in enumerate(countries):
        vals = country_avgs.loc[country].values
        color = COUNTRY_COLORS.get(country.lower(), "#888")
        ax.bar(x + i * width, vals, width, label=country.title(),
               color=color, alpha=0.85, edgecolor="white")

    ax.set_xticks(x + width)
    ax.set_xticklabels(short_labels, fontsize=9)
    ax.set_ylabel("Average Score (0 = low risk, 10 = high risk)", fontsize=10)
    ax.set_title("Greenwashing Signal Profile by Country — Average Scores", fontsize=12, pad=12)
    ax.set_ylim(0, 10)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.2)
    ax.axhline(y=5.5, color="gray", linestyle="--", linewidth=0.6, alpha=0.5)

    plt.tight_layout()
    path = str(OUTPUT_DIR / "chart4_signal_breakdown_by_country.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")
    return path


def chart5_boilerplate_ratio(df: pd.DataFrame) -> str:
    """
    Bar chart: boilerplate ratio per bank.
    Sorted by ratio. Red line at 65% threshold.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    df_sorted = df.sort_values("Boilerplate %", ascending=False)
    colors = [COUNTRY_COLORS.get(c.lower(), "#888") for c in df_sorted["Country"]]

    ax.bar(df_sorted["Bank"], df_sorted["Boilerplate %"],
           color=colors, edgecolor="white", linewidth=0.5)
    ax.axhline(y=65, color="#E24B4A", linestyle="--", linewidth=1.2,
               label="65% threshold (high boilerplate)")
    ax.axhline(y=45, color="#BA7517", linestyle="--", linewidth=1.0,
               label="45% threshold (moderate boilerplate)")

    ax.set_ylabel("Boilerplate Ratio (%)", fontsize=10)
    ax.set_title("Language Audit — Vague ESG Vocabulary as % of Total ESG Terms", fontsize=12, pad=12)
    ax.set_ylim(0, 100)
    plt.xticks(rotation=30, ha="right", fontsize=9)
    ax.legend(fontsize=9)

    legend = [mpatches.Patch(color=COUNTRY_COLORS[c], label=c.title())
              for c in COUNTRY_COLORS if c in df["Country"].str.lower().values]
    ax.legend(handles=legend + [
        mpatches.Patch(color="#E24B4A", label="High threshold (65%)"),
        mpatches.Patch(color="#BA7517", label="Moderate threshold (45%)")
    ], fontsize=8)

    plt.tight_layout()
    path = str(OUTPUT_DIR / "chart5_boilerplate_ratio.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")
    return path
