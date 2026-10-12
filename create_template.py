# =============================================================================
# create_template.py — Generate the External Data Excel Template
# =============================================================================
# USAGE: python3 create_template.py
#
# This generates external_data.xlsx — the file your team fills in manually.
# One row per news article, management quote, NGO report, or regulatory action.
# The code then reads this file and cross-references it against the PDF scores.

import pandas as pd
from pathlib import Path

# Example rows showing the format. The banks and events are FICTIONAL on purpose:
# delete them and add only real items, each with a link to the original source.
EXAMPLE_ROWS = [
    {
        "bank_name":          "Example Bank A",
        "country":            "italy",
        "type":               "news",
        "headline":           "Example: bank reported to finance a new gas project",
        "source":             "Name of the newspaper",
        "url":                "https://link-to-the-original-article",
        "date":               "2025-01-31",
        "topic":              "fossil_fuel",
        "contradiction_level":"CONTRADICTS",
        "detail":             "Two or three sentences on what the source says and why it matters.",
        "report_claim":       "Paste the exact sentence from the bank's report here.",
    },
    {
        "bank_name":          "Example Bank B",
        "country":            "italy",
        "type":               "ngo",
        "headline":           "Example: NGO ranking places the bank's coal policy in the top tier",
        "source":             "Name of the NGO report",
        "url":                "https://link-to-the-report",
        "date":               "2025-06-30",
        "topic":              "fossil_fuel",
        "contradiction_level":"CONFIRMS",
        "detail":             "Two or three sentences on what the source says and why it matters.",
        "report_claim":       "Paste the exact sentence from the bank's report here.",
    },
]

# Column definitions with instructions for your team
COLUMNS = [
    "bank_name",          # Must match exactly: Intesa Sanpaolo, UniCredit, etc.
    "country",            # italy / germany / france
    "type",               # news / management / ngo / regulatory
    "headline",           # Short description: what was said or reported
    "source",             # Where it came from: Reuters, FT, CEO speech, etc.
    "url",                # Link to the original source, so every row can be checked
    "date",               # YYYY-MM-DD format
    "topic",              # fossil_fuel / netzero / financed_emissions / taxonomy / targets / general
    "contradiction_level",# STRONGLY_CONTRADICTS / CONTRADICTS / NEUTRAL / CONFIRMS
    "detail",             # Full explanation — what happened and why it matters
    "report_claim",       # Copy the relevant claim from the bank's report
]

# Instructions sheet content
INSTRUCTIONS = pd.DataFrame([
    ["FIELD", "WHAT TO PUT", "EXAMPLE"],
    ["bank_name", "Exact bank name as in config.py", "Banco BPM"],
    ["country", "lowercase country", "italy"],
    ["type", "news / management / ngo / regulatory", "news"],
    ["headline", "One sentence: what happened", "Bank finances new gas project"],
    ["source", "Where you found it", "Reuters / Bloomberg / FT"],
    ["url", "Link to the original article or report (required)", "https://..."],
    ["date", "Date of article/statement", "2024-03-15"],
    ["topic", "fossil_fuel / netzero / financed_emissions / taxonomy / targets / general", "fossil_fuel"],
    ["contradiction_level", "STRONGLY_CONTRADICTS / CONTRADICTS / NEUTRAL / CONFIRMS", "CONTRADICTS"],
    ["detail", "2-3 sentences explaining what the source says and why it matters", "The article reports that..."],
    ["report_claim", "Paste the relevant sentence from the bank PDF that this contradicts", "We are committed to..."],
    ["", "", ""],
    ["TOPIC GUIDE", "Use this to pick the right topic", ""],
    ["fossil_fuel", "Any news about fossil fuel financing, coal, oil, gas deals", ""],
    ["netzero", "CEO statements about net-zero, Paris alignment", ""],
    ["financed_emissions", "Reports on what the bank's loans actually emit", ""],
    ["taxonomy", "EU Taxonomy compliance, green asset ratio", ""],
    ["targets", "Whether the bank is meeting its climate targets", ""],
    ["general", "Anything else ESG related", ""],
], columns=["Field", "Instructions", "Example"])


def create_template():
    output_path = Path("external_data.xlsx")

    with pd.ExcelWriter(str(output_path), engine="openpyxl") as writer:
        # Sheet 1: Data entry sheet with examples
        df = pd.DataFrame(EXAMPLE_ROWS, columns=COLUMNS)
        df.to_excel(writer, sheet_name="External Data", index=False)

        # Sheet 2: Instructions
        INSTRUCTIONS.to_excel(writer, sheet_name="Instructions", index=False)

        # Format the data sheet
        ws = writer.sheets["External Data"]
        ws.column_dimensions["A"].width = 20  # bank_name
        ws.column_dimensions["B"].width = 10  # country
        ws.column_dimensions["C"].width = 12  # type
        ws.column_dimensions["D"].width = 45  # headline
        ws.column_dimensions["E"].width = 18  # source
        ws.column_dimensions["F"].width = 35  # url
        ws.column_dimensions["G"].width = 12  # date
        ws.column_dimensions["H"].width = 18  # topic
        ws.column_dimensions["I"].width = 22  # contradiction_level
        ws.column_dimensions["J"].width = 50  # detail
        ws.column_dimensions["K"].width = 50  # report_claim

        # Format the instructions sheet
        wi = writer.sheets["Instructions"]
        wi.column_dimensions["A"].width = 22
        wi.column_dimensions["B"].width = 55
        wi.column_dimensions["C"].width = 30

    print(f"\n✓ Template created: {output_path.absolute()}")
    print(f"\nNext steps:")
    print(f"  1. Open external_data.xlsx")
    print(f"  2. Read the Instructions sheet")
    print(f"  3. Fill in 3-5 rows per bank you have analyzed")
    print(f"  4. Save the file back in the greenwashing_detector folder")
    print(f"  5. Run: python3 analyze_single.py <pdf> --bank <name> --country <country>")
    print(f"     The code will automatically read external_data.xlsx and cross-reference\n")


if __name__ == "__main__":
    create_template()
