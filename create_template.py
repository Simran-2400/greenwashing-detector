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

# Pre-filled example rows so your team understands the format
EXAMPLE_ROWS = [
    {
        "bank_name":          "Intesa Sanpaolo",
        "country":            "italy",
        "type":               "news",
        "headline":           "Intesa Sanpaolo finances ENI gas expansion in Mediterranean",
        "source":             "Reuters",
        "date":               "2024-03-15",
        "topic":              "fossil_fuel",
        "contradiction_level":"CONTRADICTS",
        "detail":             "Reuters reported Intesa Sanpaolo provided €1.8bn syndicated loan to ENI for gas field development in North Africa, contradicting the bank's stated fossil fuel exit strategy.",
        "report_claim":       "We are committed to reducing our fossil fuel exposure and supporting the energy transition away from carbon-intensive sources.",
    },
    {
        "bank_name":          "Intesa Sanpaolo",
        "country":            "italy",
        "type":               "management",
        "headline":           "CEO Carlo Messina: natural gas is essential for energy security",
        "source":             "Bloomberg Interview",
        "date":               "2024-09-22",
        "topic":              "fossil_fuel",
        "contradiction_level":"CONTRADICTS",
        "detail":             "CEO Carlo Messina stated in a Bloomberg interview that natural gas financing will remain core to the bank's strategy for the foreseeable future, citing European energy security concerns.",
        "report_claim":       "Intesa Sanpaolo is aligned with the Paris Agreement and supports the transition to a low-carbon economy.",
    },
    {
        "bank_name":          "Intesa Sanpaolo",
        "country":            "italy",
        "type":               "ngo",
        "headline":           "Reclaim Finance ranks Intesa Sanpaolo in bottom tier for coal exit",
        "source":             "Reclaim Finance",
        "date":               "2024-06-10",
        "topic":              "fossil_fuel",
        "contradiction_level":"STRONGLY_CONTRADICTS",
        "detail":             "Reclaim Finance's 2024 Coal Policy Tracker ranked Intesa Sanpaolo in the bottom third of European banks for credible coal exit policies, despite the bank's net-zero commitments.",
        "report_claim":       "We have implemented sector-specific policies to reduce our coal exposure in line with our climate strategy.",
    },
    {
        "bank_name":          "UniCredit",
        "country":            "italy",
        "type":               "news",
        "headline":           "UniCredit green bond oversubscribed — investor confidence high",
        "source":             "Financial Times",
        "date":               "2024-05-20",
        "topic":              "netzero",
        "contradiction_level":"CONFIRMS",
        "detail":             "UniCredit's €1.5bn green bond was oversubscribed 4x, with institutional investors citing strong ESG credentials. Proceeds designated for renewable energy financing.",
        "report_claim":       "We are committed to sustainable finance and growing our green bond program to support clients' transition.",
    },
    {
        "bank_name":          "BNP Paribas",
        "country":            "france",
        "type":               "news",
        "headline":           "BNP Paribas among top 5 fossil fuel financiers in Europe — Rainforest Action Network",
        "source":             "Rainforest Action Network",
        "date":               "2024-04-02",
        "topic":              "financed_emissions",
        "contradiction_level":"STRONGLY_CONTRADICTS",
        "detail":             "The 2024 Banking on Climate Chaos report ranked BNP Paribas among the top 5 European banks financing fossil fuel expansion, with $24bn in fossil fuel financing in 2023.",
        "report_claim":       "BNP Paribas is committed to aligning its financing activities with a 1.5°C trajectory and the goals of the Paris Agreement.",
    },
    {
        "bank_name":          "Deutsche Bank",
        "country":            "germany",
        "type":               "regulatory",
        "headline":           "BaFin investigates Deutsche Bank subsidiary DWS for greenwashing",
        "source":             "BaFin / Wall Street Journal",
        "date":               "2024-01-18",
        "topic":              "taxonomy",
        "contradiction_level":"STRONGLY_CONTRADICTS",
        "detail":             "German financial regulator BaFin continued investigations into Deutsche Bank's asset management arm DWS for overstating ESG credentials in fund prospectuses, following a 2023 fine.",
        "report_claim":       "We are committed to transparent and credible ESG reporting across all our business lines.",
    },
]

# Column definitions with instructions for your team
COLUMNS = [
    "bank_name",          # Must match exactly: Intesa Sanpaolo, UniCredit, etc.
    "country",            # italy / germany / france
    "type",               # news / management / ngo / regulatory
    "headline",           # Short description: what was said or reported
    "source",             # Where it came from: Reuters, FT, CEO speech, etc.
    "date",               # YYYY-MM-DD format
    "topic",              # fossil_fuel / netzero / financed_emissions / taxonomy / targets / general
    "contradiction_level",# STRONGLY_CONTRADICTS / CONTRADICTS / NEUTRAL / CONFIRMS
    "detail",             # Full explanation — what happened and why it matters
    "report_claim",       # Copy the relevant claim from the bank's report
]

# Instructions sheet content
INSTRUCTIONS = pd.DataFrame([
    ["FIELD", "WHAT TO PUT", "EXAMPLE"],
    ["bank_name", "Exact bank name as in config.py", "Intesa Sanpaolo"],
    ["country", "lowercase country", "italy"],
    ["type", "news / management / ngo / regulatory", "news"],
    ["headline", "One sentence: what happened", "CEO says gas is essential"],
    ["source", "Where you found it", "Reuters / Bloomberg / FT"],
    ["date", "Date of article/statement", "2024-03-15"],
    ["topic", "fossil_fuel / netzero / financed_emissions / taxonomy / targets / general", "fossil_fuel"],
    ["contradiction_level", "STRONGLY_CONTRADICTS / CONTRADICTS / NEUTRAL / CONFIRMS", "CONTRADICTS"],
    ["detail", "2-3 sentences explaining what the source says and why it matters", "Reuters reported..."],
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
        ws.column_dimensions["F"].width = 12  # date
        ws.column_dimensions["G"].width = 18  # topic
        ws.column_dimensions["H"].width = 22  # contradiction_level
        ws.column_dimensions["I"].width = 50  # detail
        ws.column_dimensions["J"].width = 50  # report_claim

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
