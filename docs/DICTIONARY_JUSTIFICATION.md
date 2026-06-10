# Dictionary Justification — Theory-Grounded Lexical Measurement (v2)

**Purpose.** This document records the theoretical basis for every keyword
dictionary in `src/config.py`, the terms removed in v2 and why, and the known
limitations. It is the audit trail for the measurement layer and the raw
material for the thesis methodology chapter.

---

## 1. Framework

The six signals operationalize **impression management (IM) tactics** from the
accounting narrative-disclosure literature. The anchor framework is
**Merkl-Davies & Brennan (2007)**, which classifies discretionary narrative
disclosure tactics into *concealment* (obfuscation of bad news / emphasis of
good news) and *attribution* (self-serving explanation of outcomes). Three
supporting strands:

- **Optimistic tone / temporal emphasis** in environmental narrative:
  Cho, Roberts & Patten (2010).
- **Boilerplate / low specificity** as low-information disclosure:
  Lang & Stice-Lawrence (2015).
- **Disclosure selectivity** relative to a verifiable benchmark:
  Clarkson, Li, Richardson & Vasvari (2008).

> ⚠️ **Citation check required (Simran):** verify each reference against the
> original papers before the proposal meeting — exact titles, journals, page
> ranges. Do not cite from this document alone.

**Mapping table:**

| Signal | Measures | IM tactic (anchor) | Side |
|---|---|---|---|
| 1. Net-zero claim density | Aspirational climate claims per 1,000 words | Thematic manipulation (positive emphasis) | Talk |
| 2. Financed-emissions disclosure | Presence/quality of Scope 3 Cat. 15 reporting | Concealment by omission | Walk |
| 3. Fossil exit vs. continuation | Ratio of binding exit verbs to hedged loophole phrasing | Rhetorical manipulation | Talk |
| 4. Target quantification | Share of claims with number + baseline + horizon | Vagueness vs. verifiability | Talk |
| 5. Forward vs. backward orientation | Promises vs. reported results | Thematic manipulation (temporal emphasis) | Talk |
| 6. Taxonomy/GAR disclosure | Presence/quality of mandated Article 8 metrics | Concealment of a mandated comparable metric | Walk |
| Boilerplate ratio | Vague ESG vocabulary share | Rhetorical manipulation (template language) | Talk |

The greenwashing construct is the **divergence between the Talk and Walk
sides** — not any single signal. This is what licenses the statistical
treatment as an outlier-detection problem (FSDA layer).

---

## 2. Terms removed in v2, with rationale

| Dictionary | Term removed | Reason |
|---|---|---|
| Forward-looking | `will` | Auxiliary verb; fires throughout non-climate text ("shareholders will vote"). Even word-bounded, the false-positive base rate dwarfs the signal. |
| Backward-looking | `we have` | Possessive, not past action ("we have a policy" is not a reported result). |
| Backward-looking | `cut` | Ambiguous ("cost cuts", "cut-off date"). |
| Backward-looking | `increased`, `grew`, `expanded` | Direction-ambiguous (emissions can increase) and dominated by financial-results usage unrelated to climate accountability. |
| Fossil continuation | `client engagement`, `stewardship` | Standard investor-relations vocabulary; presence does not distinguish loophole language from legitimate governance disclosure. |
| Fossil continuation | `just transition` | ILO / Paris Agreement treaty terminology; treating a treaty term as a greenwashing cue is not defensible. |
| Vague ESG | `green`, `greener` | Fires on legitimate product nouns ("green bond", "green mortgage") that are arguably *specific*. |
| Vague ESG | `stakeholder(s)` | Neutral governance vocabulary; ESRS itself mandates stakeholder language. |

**Decision rule applied:** a term stays in a "vague/loophole" list only if its
*dominant* use in bank sustainability reports is non-binding rhetoric, and a
term stays in any list only if its match is unambiguous at word-boundary level.
Borderline terms were removed rather than kept (conservative bias: we prefer
under-counting greenwashing language to over-counting it, since the index
flags banks for scrutiny).

---

## 3. Known limitations (state these in the thesis — do not hide them)

1. **Full-text scope of Signal 5.** Forward/backward dictionaries currently
   run over the entire report, including financial sections. Planned
   refinement: restrict to climate-relevant sentences (sentence-level topic
   filter) so temporal orientation is measured only where it is meaningful.
2. **Provisional thresholds.** The 0–10 score bins (LOW/…/CRITICAL) are
   readability labels for single-bank reports, not calibrated cut-offs. The
   thesis's inferential claims rest on the **continuous** signal values fed
   into the FSDA layer; cross-sectional outlierness is determined by the
   Forward Search, not by these bins.
3. **Dictionary completeness.** No lexicon is exhaustive; the lists capture
   recognized formulations, not all possible ones. Mitigation: evidence
   snippets (matcher.py) allow manual audit of what was and wasn't captured.
4. **Negation is detected, not interpreted.** Negated mentions are excluded
   from asserted counts and reported separately; the pipeline does not infer
   the *meaning* of a negation (e.g. "we do not finance coal" as an exit
   commitment). Documented design choice favoring simplicity and transparency.
5. **English-language reports only.** Deliberate scope decision: the author
   cannot verify output quality in languages she does not read.

---

## 4. Defense Q&A (practice these)

**Q: "Aren't your dictionaries just invented?"**
A: The *categories* come from the impression-management literature
(Merkl-Davies & Brennan 2007); each dictionary operationalizes one tactic.
The *terms* are drawn from the regulatory and industry vocabulary of CSRD,
the EU Taxonomy, PCAF and NZBA — i.e., the terms a bank must use if it has
actually done the work. Every inclusion and removal is documented with a
rationale, and every count is traceable to a sentence-level snippet.

**Q: "Why should absence of a term mean anything?"**
A: For Signals 2 and 6 the benchmark is not stylistic but regulatory: GAR
disclosure is mandated under Taxonomy Article 8, and financed emissions is
the standard metric (PCAF / Scope 3 Cat. 15) for a bank's material climate
impact. Absence of mandated or standard vocabulary while ambition language is
abundant is precisely the talk–walk gap the construct defines.

**Q: "How do you know your thresholds are right?"**
A: They are presentation labels, not inference. Inference happens in the
robust statistical layer on continuous values; a bank is "anomalous" because
the Forward Search identifies it as an outlier relative to the EU peer
cross-section, not because it crossed an invented cut-off.
