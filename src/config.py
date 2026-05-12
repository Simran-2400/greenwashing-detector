# =============================================================================
# config.py — Keyword Dictionaries & Bank Metadata
# Bank Greenwashing Detection Pipeline
# Course: Accounting — Prof. Andrea Cilloni, University of Parma
# =============================================================================
#
# DESIGN LOGIC:
# Every keyword list here is a deliberate research choice, not arbitrary.
# Each category maps to one of the 6 greenwashing signals we score.
# Rule: if a word could appear in ANY industry's ESG report without changing
# meaning — it is VAGUE. If it requires knowing the bank's actual data — SPECIFIC.

# -----------------------------------------------------------------------------
# SIGNAL 1: NET-ZERO CLAIM DENSITY
# Words that signal ambitious climate narrative.
# High count + low performance evidence = greenwashing flag.
# -----------------------------------------------------------------------------
NETZERO_KEYWORDS = [
    "net zero", "net-zero", "netzero",
    "carbon neutral", "carbon neutrality", "carbon-neutral",
    "climate neutral", "climate neutrality",
    "paris-aligned", "paris aligned", "paris agreement",
    "1.5 degrees", "1.5°c", "1.5 degree",
    "carbon negative", "climate positive",
    "zero emissions", "zero carbon",
    "net zero banking alliance", "nzba",
    "science-based target", "sbti", "science based target"
]

# -----------------------------------------------------------------------------
# SIGNAL 2: FINANCED EMISSIONS DISCLOSURE
# These are the SPECIFIC terms a bank must use if it actually measured
# what its loans and investments emit (Scope 3 Category 15).
# Absence of these terms while claiming net-zero = the core greenwashing signal.
# -----------------------------------------------------------------------------
FINANCED_EMISSIONS_KEYWORDS = [
    "financed emissions", "financed carbon",
    "scope 3 category 15", "category 15",
    "portfolio emissions", "portfolio carbon",
    "pcaf",                                  # Partnership for Carbon Accounting Financials
    "financed greenhouse", "financed ghg",
    "lending emissions", "investment emissions",
    "portfolio decarbonisation", "portfolio decarbonization",
    "weighted average carbon intensity", "waci",
    "portfolio carbon intensity",
    "absolute financed emissions",
    "financed scope 3"
]

# -----------------------------------------------------------------------------
# SIGNAL 3A: FOSSIL FUEL EXIT LANGUAGE (credible commitment signals)
# These phrases indicate a bank is ACTUALLY committing to exit fossil fuels.
# Presence of these = lower greenwashing risk on this signal.
# -----------------------------------------------------------------------------
FOSSIL_EXIT_KEYWORDS = [
    "phase out", "phase-out", "phasing out",
    "no new financing", "no new loans",
    "coal exclusion", "fossil fuel exclusion",
    "exclusion policy", "sector exclusion",
    "divest", "divestment", "divesting",
    "wind down", "winding down",
    "no new coal", "coal phase-out",
    "fossil fuel free", "exit coal",
    "thermal coal", "coal financing ban",
    "decommission", "stranded asset"
]

# -----------------------------------------------------------------------------
# SIGNAL 3B: FOSSIL FUEL CONTINUATION LANGUAGE (vague / enabling)
# These phrases let banks claim green credentials while still financing fossils.
# "Transition finance" is the most common loophole phrase in bank ESG reports.
# High count of these vs. exit language = greenwashing signal.
# -----------------------------------------------------------------------------
FOSSIL_CONTINUATION_KEYWORDS = [
    "transition finance", "energy transition finance",
    "bridge fuel", "bridging fuel",
    "continued support", "supporting the transition",
    "enabling clients", "accompanying clients",
    "orderly transition", "just transition",
    "natural gas transition", "gas as transition",
    "managed phase-down",  # COP26 language — intentionally weak
    "flexible approach", "case by case",
    "client engagement", "stewardship"  # can mask inaction
]

# -----------------------------------------------------------------------------
# SIGNAL 4: QUANTIFIED TARGETS (specificity)
# A SPECIFIC target has: a NUMBER + a BASELINE YEAR + a TARGET YEAR + a METRIC.
# These regex-detectable patterns identify quantified claims.
# We score the ratio: quantified claims / total climate claims.
# -----------------------------------------------------------------------------
import re

# Patterns that indicate SPECIFIC, quantified claims
SPECIFICITY_PATTERNS = [
    r'\d+\.?\d*\s*%',                        # any percentage: "43%", "12.5%"
    r'by\s+20[23456789]\d',                  # target year: "by 2030", "by 2050"
    r'\d+\.?\d*\s*(mt|kt|gt)co2',           # emissions in megatons/gigatons
    r'\d+\.?\d*\s*tco2e?',                   # tCO2e: tonnes of CO2 equivalent
    r'€\s*\d+\.?\d*\s*(billion|million|bn|m)', # monetary target: "€50 billion"
    r'\$\s*\d+\.?\d*\s*(billion|million|bn|m)',
    r'\d{4}\s*baseline',                     # baseline year: "2019 baseline"
    r'from\s+\d{4}\s+to\s+\d{4}',          # period: "from 2019 to 2030"
    r'reduce[sd]?\s+by\s+\d+',             # "reduced by 43"
    r'\d+\.?\d*\s*gwh',                     # energy in GWh
    r'\d+\.?\d*\s*mwh',                     # energy in MWh
]

# Vague claim indicators — the opposite of specificity
VAGUE_CLAIM_PATTERNS = [
    r'\bsignificantly\b',
    r'\bsubstantially\b',
    r'\bgradually\b',
    r'\bprogressively\b',
    r'\bover time\b',
    r'\bin due course\b',
    r'\bwhere possible\b',
    r'\bwhen appropriate\b',
    r'\bas soon as\b',
    r'\bwe aim\b(?!\s+to\s+\d)',  # "we aim" without a number following
    r'\bwe aspire\b',
    r'\bwe strive\b',
    r'\bwe endeavour\b',
]

# -----------------------------------------------------------------------------
# SIGNAL 5: FORWARD-LOOKING vs BACKWARD-LOOKING RATIO
# Heavy future-tense language = promises not yet delivered.
# Heavy past-tense language = accountability for actual results.
# A credible report balances both. A greenwashing report is future-heavy.
# -----------------------------------------------------------------------------
FORWARD_LOOKING_KEYWORDS = [
    "will", "aim to", "plan to", "intend to",
    "we commit", "we are committed to",
    "target to", "goal to", "objective to",
    "by 2025", "by 2030", "by 2035", "by 2040", "by 2050",
    "we aspire", "we strive", "we endeavour",
    "going forward", "in the future", "over the coming",
    "next year", "next years", "upcoming",
    "roadmap", "pathway", "trajectory"
]

BACKWARD_LOOKING_KEYWORDS = [
    "achieved", "delivered", "completed", "accomplished",
    "reduced", "decreased", "cut", "lowered",
    "increased", "grew", "expanded",
    "reported", "measured", "disclosed", "published",
    "in 2024", "during 2024", "as of 2024",
    "in 2023", "during 2023", "as of 2023",
    "last year", "this year",
    "we have", "we reduced", "we achieved",
    "year-on-year", "year on year", "compared to previous"
]

# -----------------------------------------------------------------------------
# SIGNAL 6: TAXONOMY ALIGNMENT DISCLOSURE
# EU Taxonomy requires banks to report what % of their assets are "green".
# If a bank claims climate leadership but never reports their Green Asset Ratio
# or Taxonomy-aligned %, that gap is a concrete greenwashing signal.
# -----------------------------------------------------------------------------
TAXONOMY_KEYWORDS = [
    "taxonomy-aligned", "taxonomy aligned",
    "taxonomy-eligible", "taxonomy eligible",
    "green asset ratio", "gar",
    "btar",                                  # Banking Book Taxonomy Alignment Ratio
    "taxonomy regulation",
    "article 8", "article 9",               # SFDR fund classifications
    "eu taxonomy",
    "taxonomy substantial contribution",
    "do no significant harm", "dnsh",
    "minimum social safeguards",
    "taxonomy kpi", "taxonomy disclosure"
]

# -----------------------------------------------------------------------------
# LANGUAGE AUDIT: VAGUE vs SPECIFIC ESG VOCABULARY
# Used to calculate the boilerplate ratio:
#   boilerplate_ratio = vague_count / (vague_count + specific_count)
# A ratio above 0.70 means the report is mostly template language.
# -----------------------------------------------------------------------------
VAGUE_ESG_WORDS = [
    "sustainable", "sustainability",
    "responsible", "responsibility",
    "commitment", "committed",
    "dedicated", "dedication",
    "holistic", "integrated",
    "mindful", "conscious",
    "eco-friendly", "eco friendly",
    "green", "greener",
    "positive impact",
    "long-term value",
    "stakeholder", "stakeholders",
    "purpose-led", "purpose driven",
    "journey", "transformation journey",
    "ambition", "ambitious",
    "aspiration", "aspirational",
    "embedding", "embed",
    "culture of sustainability",
    "at the heart",
    "fully committed",
    "proud to",
    "we believe",
]

SPECIFIC_ESG_WORDS = [
    "pcaf", "tcfd", "tnfd",
    "scope 1", "scope 2", "scope 3",
    "tco2e", "mtco2e", "gtco2e",
    "ghg protocol",
    "taxonomy-aligned", "taxonomy aligned",
    "green asset ratio",
    "financed emissions",
    "science-based target", "sbti",
    "sfdr", "article 8", "article 9",
    "double materiality",
    "esrs",                                  # European Sustainability Reporting Standards
    "csrd",
    "basis points",
    "waci",
    "category 15",
    "limited assurance", "reasonable assurance",  # third-party verification
    "absolute emissions",
    "intensity metric",
    "decarbonisation pathway",
    "net zero banking alliance",
]

# -----------------------------------------------------------------------------
# SECTION HEADER DETECTION
# Used by section_parser.py to split the report into logical parts.
# We look for lines that match these patterns (case-insensitive).
# -----------------------------------------------------------------------------
SECTION_HEADER_PATTERNS = [
    r'^(executive|ceo|chairman|chief executive)[\s\w]*message',
    r'^(ceo|chairman|managing director)[\s\'s]*letter',
    r'^(climate|environmental)[\s\w]*(strategy|approach|framework)',
    r'^(environmental|climate)[\s\w]*(performance|data|metrics)',
    r'^(social|community)[\s\w]*(responsibility|impact|performance)',
    r'^(governance|esg governance)',
    r'^(targets?|goals?|objectives?)[\s\w]*(and|&)?[\s\w]*(commitments?|milestones?)?',
    r'^(sustainable finance|green finance)',
    r'^(risk|climate risk)[\s\w]*management',
    r'^(methodology|approach|reporting)',
    r'^(about this report|reporting framework)',
    r'^(our (approach|commitment|strategy|performance))',
    r'^(highlights?|key (figures?|data|results?))',
]

# -----------------------------------------------------------------------------
# BANK METADATA
# Used to organize output files and label charts.
# Add more banks here as you scale from Italy → Italy+Germany+France.
# -----------------------------------------------------------------------------
BANKS = {
    "italy": [
        {"name": "Intesa Sanpaolo",    "ticker": "ISP",  "filename": "intesa_sanpaolo_2024.pdf"},
        {"name": "UniCredit",          "ticker": "UCG",  "filename": "unicredit_2024.pdf"},
        {"name": "Banco BPM",          "ticker": "BAMI", "filename": "banco_bpm_2024.pdf"},
        {"name": "BPER Banca",         "ticker": "BPE",  "filename": "bper_2024.pdf"},
        {"name": "Monte dei Paschi",   "ticker": "BMPS", "filename": "mps_2024.pdf"},
    ],
    "germany": [
        {"name": "Deutsche Bank",      "ticker": "DBK",  "filename": "deutsche_bank_2024.pdf"},
        {"name": "Commerzbank",        "ticker": "CBK",  "filename": "commerzbank_2024.pdf"},
        {"name": "LBBW",               "ticker": "LBBW", "filename": "lbbw_2024.pdf"},
        {"name": "Aareal Bank",        "ticker": "ARL",  "filename": "aareal_2024.pdf"},
        {"name": "Helaba",             "ticker": "HLB",  "filename": "helaba_2024.pdf"},
    ],
    "france": [
        {"name": "BNP Paribas",        "ticker": "BNP",  "filename": "bnp_paribas_2024.pdf"},
        {"name": "Societe Generale",   "ticker": "GLE",  "filename": "societe_generale_2024.pdf"},
        {"name": "Credit Agricole",    "ticker": "ACA",  "filename": "credit_agricole_2024.pdf"},
        {"name": "Natixis / BPCE",     "ticker": "BPCE", "filename": "bpce_2024.pdf"},
        {"name": "Credit Mutuel",      "ticker": "CMA",  "filename": "credit_mutuel_2024.pdf"},
    ]
}

# Scoring thresholds — used by gap_calculator.py
GREENWASHING_THRESHOLDS = {
    "LOW":      (0.0, 3.0),
    "MODERATE": (3.0, 5.5),
    "HIGH":     (5.5, 7.5),
    "CRITICAL": (7.5, 10.0),
}

BOILERPLATE_THRESHOLDS = {
    "LOW":      0.45,   # below 45% vague = specific, credible reporting
    "MODERATE": 0.65,   # 45-65% vague = mixed
    "HIGH":     0.80,   # above 65% vague = mostly template language
}
