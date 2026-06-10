# =============================================================================
# matcher.py — Validated Keyword Matching Engine
# =============================================================================
#
# WHY THIS MODULE EXISTS (methodology-chapter material):
# The first version of the pipeline used Python's str.count(), which performs
# raw SUBSTRING matching. This produced three measurement validity problems:
#
#   1. FALSE POSITIVES — "gar" matched inside "regarding", "will" inside
#      "goodwill", "green" inside "greenhouse". Counts were inflated by
#      construction.
#   2. DOUBLE COUNTING — overlapping dictionary entries were counted
#      independently: "net zero banking alliance" also fired "net zero".
#   3. NO NEGATION HANDLING — "we have NOT set a net-zero target" counted
#      as a net-zero claim.
#
# This module fixes all three with one matching strategy used by every signal:
#
#   * WORD-BOUNDARY matching: terms only match as whole words/phrases,
#     implemented with lookarounds so terms starting/ending in digits or
#     symbols (e.g. "1.5°c") are handled correctly.
#   * LONGEST-MATCH-FIRST, NON-OVERLAPPING: all terms in a dictionary are
#     compiled into a single alternation ordered by length, so the longest
#     applicable phrase wins and each character of text is counted at most
#     once per dictionary.
#   * HYPHEN/SPACE NORMALIZATION: "net zero", "net-zero" and "net  zero"
#     are treated as the same canonical term.
#   * NEGATION DETECTION: a match preceded (within the same sentence, inside
#     a small token window) by a negation cue is counted separately as
#     "negated" and excluded from the asserted count used for scoring.
#   * EVIDENCE TRAIL: every match stores a sentence-level snippet, so any
#     count in the thesis can be traced back to the exact text that
#     produced it (audit-style verifiability).
#
# All counting in the pipeline should go through match_terms() below.
# =============================================================================

import re
from dataclasses import dataclass, field

# Negation cues checked in the token window immediately before a match.
# Kept deliberately conservative: common verbal negations in corporate English.
NEGATION_CUES = {
    "not", "no", "never", "without", "neither", "nor",
    "don't", "doesn't", "didn't", "hasn't", "haven't", "isn't", "aren't",
    "won't", "wouldn't", "cannot", "can't",
    "lacks", "lacking", "absence", "absent", "excluding", "excludes",
}

# How many tokens before the match we scan for a negation cue.
NEGATION_WINDOW = 5

# Characters that end a sentence — negation scope does not cross these.
_SENT_BOUNDARY = re.compile(r"[.!?;:\n]")


def _canonical(term: str) -> str:
    """Normalize a dictionary term: lowercase, hyphens/extra spaces -> single space."""
    return re.sub(r"[\s\-]+", " ", term.lower()).strip()


def _term_pattern(term: str) -> str:
    """
    Build a regex fragment for one canonical term:
      - internal spaces match any run of spaces/hyphens/newlines
      - word boundaries via lookarounds (robust for digits/symbols)
    """
    parts = [re.escape(p) for p in term.split(" ")]
    body = r"[\s\-]+".join(parts)
    return r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])"


@dataclass
class TermMatches:
    """All matches for one dictionary against one text."""
    asserted: dict = field(default_factory=dict)   # canonical term -> count
    negated: dict = field(default_factory=dict)    # canonical term -> count
    evidence: list = field(default_factory=list)   # list of dicts (term, negated, snippet)

    @property
    def total_asserted(self) -> int:
        return sum(self.asserted.values())

    @property
    def total_negated(self) -> int:
        return sum(self.negated.values())

    def top_terms(self, n: int = 10) -> list:
        return sorted(self.asserted.items(), key=lambda x: x[1], reverse=True)[:n]


class KeywordMatcher:
    """
    Compile a term dictionary once, then run it over many texts.

    Usage:
        m = KeywordMatcher(NETZERO_KEYWORDS)
        res = m.match(report_text)
        res.total_asserted   # counts for scoring
        res.negated          # negated mentions (reported, not scored)
        res.evidence[:5]     # traceable snippets
    """

    def __init__(self, terms: list, negation_window: int = NEGATION_WINDOW):
        # Canonicalize and de-duplicate (e.g. "net zero" / "net-zero" collapse).
        canon = sorted({_canonical(t) for t in terms if t and t.strip()},
                       key=len, reverse=True)  # longest first => longest match wins
        self.terms = canon
        self.negation_window = negation_window
        if canon:
            self._rx = re.compile("|".join(f"({_term_pattern(t)})" for t in canon),
                                  re.IGNORECASE)
        else:
            self._rx = None
        # group index -> canonical term
        self._group_term = {i + 1: t for i, t in enumerate(canon)}

    def _is_negated(self, text: str, start: int) -> bool:
        """Check the token window before position `start` for a negation cue,
        without crossing a sentence boundary."""
        left = text[max(0, start - 120):start]
        # cut at the last sentence boundary so negation doesn't leak across sentences
        m = list(_SENT_BOUNDARY.finditer(left))
        if m:
            left = left[m[-1].end():]
        tokens = re.findall(r"[a-z']+", left.lower())
        return any(tok in NEGATION_CUES for tok in tokens[-self.negation_window:])

    def _snippet(self, text: str, start: int, end: int, radius: int = 90) -> str:
        lo, hi = max(0, start - radius), min(len(text), end + radius)
        snip = text[lo:hi].replace("\n", " ")
        return ("…" if lo > 0 else "") + snip.strip() + ("…" if hi < len(text) else "")

    def match(self, text: str, keep_evidence: int = 50) -> TermMatches:
        res = TermMatches()
        if not self._rx or not text:
            return res
        for m in self._rx.finditer(text):
            term = self._group_term[m.lastindex]
            negated = self._is_negated(text, m.start())
            bucket = res.negated if negated else res.asserted
            bucket[term] = bucket.get(term, 0) + 1
            if len(res.evidence) < keep_evidence:
                res.evidence.append({
                    "term": term,
                    "negated": negated,
                    "snippet": self._snippet(text, m.start(), m.end()),
                })
        return res


# Module-level cache so repeated calls with the same dictionary are cheap.
_CACHE = {}


def match_terms(text: str, terms: list) -> TermMatches:
    """Convenience wrapper with compiled-matcher caching."""
    key = tuple(sorted({_canonical(t) for t in terms}))
    matcher = _CACHE.get(key)
    if matcher is None:
        matcher = KeywordMatcher(terms)
        _CACHE[key] = matcher
    return matcher.match(text)


def count_terms(text: str, terms: list) -> tuple:
    """Backwards-compatible helper: returns (per_term_asserted_counts, total_asserted)."""
    res = match_terms(text, terms)
    return res.asserted, res.total_asserted
