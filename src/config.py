# =============================================================================
# config.py — Theory-Grounded Keyword Dictionaries & Bank Metadata
# Bank Greenwashing Detection Pipeline
# Supervisors: Prof. Andrea Cilloni (Accounting), Prof. Marco Riani (Statistics)
# =============================================================================
#
# DESIGN LOGIC (v2 — theory-grounded):
# Every dictionary below operationalizes a recognized IMPRESSION MANAGEMENT
# (IM) tactic from the accounting narrative-disclosure literature, primarily
# the framework of Merkl-Davies & Brennan (2007). Each list header states:
#   [IM TACTIC]  the tactic the dictionary measures
#   [DIRECTION]  whether high counts raise or lower the greenwashing signal
#   [PRUNED]     terms removed in v2 because they were noisy or neutral
# Full per-term rationale: see docs/DICTIONARY_JUSTIFICATION.md
#
# Matching rules (see src/matcher.py): word-boundary, longest-match-first,
# hyphen/space variants collapse to one canonical term, negation-aware.
# Variant spellings are therefore listed ONCE in canonical form.

# -----------------------------------------------------------------------------
# SIGNAL 1: NET-ZERO CLAIM DENSITY
# [IM TACTIC] Thematic manipulation — emphasis of positive/aspirational themes
#             (Merkl-Davies & Brennan 2007; optimistic tone: Cho, Roberts &
#             Patten 2010).
# [DIRECTION] Narrative side. High density alone = high stated ambition; it
#             becomes a greenwashing indicator only when paired with weak
#             performance disclosure (Signals 2 & 6) — the talk–walk gap.
# -----------------------------------------------------------------------------
NETZERO_KEYWORDS = [
    "net zero",
    "carbon neutral", "carbon neutrality",
    "climate neutral", "climate neutrality",
    "paris aligned", "paris agreement",
    "1.5 degrees", "1.5°c", "1.5 degree",
    "carbon negative", "climate positive",
    "zero emissions", "zero carbon",
    "net zero banking alliance", "nzba",
    "science based target", "sbti",
]

# -----------------------------------------------------------------------------
# SIGNAL 2: FINANCED EMISSIONS DISCLOSURE
# [IM TACTIC] Concealment by omission / disclosure selectivity — withholding
#             the one metric (Scope 3 Category 15) that reveals a bank's real
#             climate footprint (selectivity: Merkl-Davies & Brennan 2007;
#             voluntary-disclosure benchmark: Clarkson et al. 2008).
# [DIRECTION] Performance side. ABSENCE of these terms (while Signal 1 is
#             high) raises the greenwashing signal.
# -----------------------------------------------------------------------------
FINANCED_EMISSIONS_KEYWORDS = [
    "financed emissions", "financed carbon",
    "scope 3 category 15", "category 15",
    "portfolio emissions", "portfolio carbon",
    "pcaf",
    "financed greenhouse", "financed ghg",
    "lending emissions", "investment emissions",
    "portfolio decarbonisation", "portfolio decarbonization",
    "weighted average carbon intensity", "waci",
    "portfolio carbon intensity",
    "absolute financed emissions",
    "financed scope 3",
]

# -----------------------------------------------------------------------------
# SIGNAL 3A: FOSSIL FUEL EXIT LANGUAGE
# [IM TACTIC] None — this is the CREDIBLE-commitment benchmark against which
#             continuation language (3B) is compared. Verifiable policy verbs.
# [DIRECTION] Higher exit-share lowers the greenwashing signal.
# -----------------------------------------------------------------------------
FOSSIL_EXIT_KEYWORDS = [
    "phase out", "phasing out",
    "no new financing", "no new loans",
    "coal exclusion", "fossil fuel exclusion",
    "exclusion policy", "sector exclusion",
    "divest", "divestment", "divesting",
    "wind down", "winding down",
    "no new coal", "coal phase out",
    "fossil fuel free", "exit coal",
    "thermal coal", "coal financing ban",
    "decommission", "stranded asset",
]

# -----------------------------------------------------------------------------
# SIGNAL 3B: FOSSIL FUEL CONTINUATION LANGUAGE
# [IM TACTIC] Rhetorical manipulation — hedged, loophole-preserving phrasing
#             that permits continued fossil financing while sounding green
#             (Merkl-Davies & Brennan 2007).
# [DIRECTION] Higher continuation-share raises the greenwashing signal.
# [PRUNED v2] "client engagement", "stewardship" (standard investor-relations
#             vocabulary — fired on legitimate governance text), "just
#             transition" (ILO/Paris treaty terminology, not loophole-specific).
# -----------------------------------------------------------------------------
FOSSIL_CONTINUATION_KEYWORDS = [
    "transition finance", "energy transition finance",
    "bridge fuel", "bridging fuel",
    "continued support", "supporting the transition",
    "enabling clients", "accompanying clients",
    "orderly transition",
    "natural gas transition", "gas as transition",
    "managed phase down",
    "flexible approach", "case by case",
]

# -----------------------------------------------------------------------------
# SIGNAL 4: QUANTIFIED TARGETS (specificity)
# [IM TACTIC] Verifiability vs. vagueness — a SPECIFIC claim binds the firm
#             (number + baseline + horizon + metric); vague aspiration does
#             not (boilerplate/specificity: Lang & Stice-Lawrence 2015).
# [DIRECTION] Higher specificity-share lowers the greenwashing signal.
# -----------------------------------------------------------------------------
import re

SPECIFICITY_PATTERNS = [
    r'\d+\.?\d*\s*%',
    r'by\s+20[23456789]\d',
    r'\d+\.?\d*\s*(mt|kt|gt)co2',
    r'\d+\.?\d*\s*tco2e?',
    r'€\s*\d+\.?\d*\s*(billion|million|bn|m)',
    r'\$\s*\d+\.?\d*\s*(billion|million|bn|m)',
    r'\d{4}\s*baseline',
    r'from\s+\d{4}\s+to\s+\d{4}',
    r'reduce[sd]?\s+by\s+\d+',
    r'\d+\.?\d*\s*gwh',
    r'\d+\.?\d*\s*mwh',
]

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
    r'\bwe aim\b(?!\s+to\s+\d)',
    r'\bwe aspire\b',
    r'\bwe strive\b',
    r'\bwe endeavour\b',
]

# -----------------------------------------------------------------------------
# SIGNAL 5: FORWARD-LOOKING vs BACKWARD-LOOKING ORIENTATION
# [IM TACTIC] Thematic manipulation via temporal emphasis — promises (future)
#             crowd out accountability for results (past) (optimism bias in
#             environmental narrative: Cho, Roberts & Patten 2010).
# [DIRECTION] Higher forward-share raises the greenwashing signal.
# [PRUNED v2] "will" (auxiliary verb — fired on all report text: "shareholders
#             will vote"), "we have" (possessive, not past-action: "we have a
#             policy"), "cut" (ambiguous: "cost cuts", "cut-off date"),
#             "increased/grew/expanded" (direction-ambiguous and fired on
#             financial-results text unrelated to climate).
# [KNOWN LIMITATION] These dictionaries still run over the FULL report text;
#             restricting Signal 5 to climate-relevant sentences is planned
#             (see DICTIONARY_JUSTIFICATION.md §Future work).
# -----------------------------------------------------------------------------
FORWARD_LOOKING_KEYWORDS = [
    "aim to", "plan to", "intend to",
    "we commit", "we are committed to",
    "target to", "goal to", "objective to",
    "by 2025", "by 2030", "by 2035", "by 2040", "by 2050",
    "we aspire", "we strive", "we endeavour",
    "going forward", "in the future", "over the coming",
    "roadmap", "pathway", "trajectory",
]

BACKWARD_LOOKING_KEYWORDS = [
    "achieved", "delivered", "completed", "accomplished",
    "reduced", "decreased", "lowered",
    "reported", "measured", "disclosed", "published",
    "in 2024", "during 2024", "as of 2024",
    "in 2023", "during 2023", "as of 2023",
    "last year",
    "we reduced", "we achieved",
    "year on year", "compared to previous",
]

# -----------------------------------------------------------------------------
# SIGNAL 6: EU TAXONOMY ALIGNMENT DISCLOSURE
# [IM TACTIC] Concealment by omission of a MANDATED comparable metric — under
#             CSRD/Taxonomy Article 8, large banks must disclose GAR; silence
#             or burial of the figure while claiming green leadership is the
#             most concrete talk–walk gap available.
# [DIRECTION] Performance side. Absence raises the greenwashing signal.
# -----------------------------------------------------------------------------
TAXONOMY_KEYWORDS = [
    "taxonomy aligned",
    "taxonomy eligible",
    "green asset ratio", "gar",
    "btar", "banking book taxonomy alignment ratio",
    "taxonomy regulation",
    "article 8", "article 9",
    "eu taxonomy",
    "taxonomy substantial contribution",
    "do no significant harm", "dnsh",
    "minimum social safeguards",
    "taxonomy kpi", "taxonomy disclosure",
]

# -----------------------------------------------------------------------------
# LANGUAGE AUDIT: VAGUE vs SPECIFIC ESG VOCABULARY (boilerplate ratio)
# [IM TACTIC] Rhetorical manipulation / boilerplate — template language that
#             could appear in ANY firm's report without modification carries
#             no firm-specific information (Lang & Stice-Lawrence 2015).
# [DIRECTION] boilerplate_ratio = vague / (vague + specific); higher = worse.
# [PRUNED v2] "green"/"greener" (fired on legitimate product terms: "green
#             bond", "green mortgage"), "stakeholder(s)" (neutral governance
#             vocabulary required by ESRS itself).
# -----------------------------------------------------------------------------
VAGUE_ESG_WORDS = [
    "sustainable", "sustainability",
    "responsible", "responsibility",
    "commitment", "committed",
    "dedicated", "dedication",
    "holistic", "integrated",
    "mindful", "conscious",
    "eco friendly",
    "positive impact",
    "long term value",
    "purpose led", "purpose driven",
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
    "taxonomy aligned",
    "green asset ratio",
    "financed emissions",
    "science based target", "sbti",
    "sfdr", "article 8", "article 9",
    "double materiality",
    "esrs",
    "csrd",
    "basis points",
    "waci",
    "category 15",
    "limited assurance", "reasonable assurance",
    "absolute emissions",
    "intensity metric",
    "decarbonisation pathway",
    "net zero banking alliance",
]

# -----------------------------------------------------------------------------
# SECTION HEADER DETECTION (unchanged in v2)
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
# BANK METADATA (unchanged in v2)
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

# Scoring thresholds — PROVISIONAL labels for single-bank readability only.
# The thesis's statistical layer (FSDA Forward Search / robust regression)
# works on the CONTINUOUS signal values; these bins are display labels, not
# calibrated cut-offs, and are documented as such (see JUSTIFICATION §Thresholds).
GREENWASHING_THRESHOLDS = {
    "LOW":      (0.0, 3.0),
    "MODERATE": (3.0, 5.5),
    "HIGH":     (5.5, 7.5),
    "CRITICAL": (7.5, 10.0),
}

BOILERPLATE_THRESHOLDS = {
    "LOW":      0.45,
    "MODERATE": 0.65,
    "HIGH":     0.80,
}
