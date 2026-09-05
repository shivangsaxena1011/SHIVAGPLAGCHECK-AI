# SHIVANG PLAGCHECK AI — Methodology & Scoring Principles

## 1. Important Legal and Academic Distinctions

### Similarity vs. Plagiarism
SHIVANG PLAGCHECK AI explicitly distinguishes between **text similarity** and **plagiarism determination**:

> **Academic Notice**:
> The similarity score indicates the mathematical proportion of analyzed text that overlaps with identified comparison sources. Human scholarly review is strictly required to determine whether an identified match constitutes plagiarism, appropriate attribution, fair use, standard disciplinary terminology, or accidental omission.

### AI Writing Likelihood Disclaimers
> **AI Detection Notice**:
> AI-writing likelihood is an automated statistical and machine-learning estimate based on stylometric variance, perplexity consistency, transition token clustering, and syntactical uniformity. It is an indicative probability, **never definitive proof of AI authorship**. Institutional policy must prohibit disciplinary action based solely on automated AI detection scores.

---

## 2. Plagiarism Detection Techniques

### Layer 1: Robust Winnowing Fingerprinting (Exact Retrieval)
Based on Schleimer, Wilkerson & Aiken (*SIGMOD 2003*):
- Text is normalized (Unicode NFKC, lowercase, whitespace collapse, bracketed citation removal).
- Sliding character $k$-grams ($k=5$) are generated and hashed with keyed-free Blake2b to 64-bit signed integers.
- A sliding window of size $w=8$ selects the rightmost minimum hash.
- Guarantees that any shared verbatim substring of length $\ge w + k - 1 = 12$ characters produces at least one identical fingerprint.

### Layer 0: Seed-and-Extend Alignment
Adapted from BLAST (*Altschul et al., 1990*):
- Seeds: Maximal exact substring matches of length $\ge 12$ characters between query and candidate passages.
- Outward walk: Advances across short substitutions and light paraphrasing within a 20-character lookahead window while match tolerance is satisfied.
- Merging: Nearby overlapping segments along the same query-candidate diagonal are merged into unified passage spans with exact start and end character offsets.

### Layer 2: Dense Semantic Matching (SBERT)
- Employs Sentence Transformers (`paraphrase-MiniLM-L6-v2`) mapping sentences to 384-dimensional dense vectors.
- Candidate passages exceeding a cosine similarity threshold of $0.82$ are flagged as concept-level paraphrases even when no exact words are identical.
- Optional cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) scores candidate pairs on a logit scale.

---

## 3. Multi-Signal AI Detection Ensemble

The AI likelihood assessment does not rely on a single black-box classification:
1. **Perplexity & Burstiness**: Measures syntactical predictability. Human prose exhibits high burstiness (fluctuating sentence lengths and complexity); AI text displays uniform low perplexity.
2. **Stylometric Profile**: Computes Type-Token Ratio (TTR), Hapax Legomena ratio, passive voice frequency, nominalization density, and sentence length standard deviation.
3. **Lexical Tells (Dual-Tier)**:
   - *Tier 1 (Strong)*: "delve into", "a testament to", "tapestry of", "harness the power", "in the realm of".
   - *Tier 2 (Weak / Contextual)*: Academic transition words ("furthermore", "moreover", "in conclusion") evaluated at reduced weight.
4. **ESL Calibration**: Multipliers adjust detection thresholds for non-native English writing patterns (Liang et al., Stanford 2023) to mitigate false-positive bias.

---

## 4. Match Fusion and Exclusion Engine

The score fusion engine prevents overlapping matches from being double-counted:
$$\text{Overall Similarity} = \frac{\text{length}\left(\bigcup_{i} [\text{start}_i, \text{end}_i)\right)}{\text{Total Analyzed Characters}} \times 100\%$$

### Exclusion Toggles
- `exclude_quotes=True`: Quoted strings within `""`, `“”`, `«»`, or block quotes are removed from numerator coverage.
- `exclude_bibliography=True`: References, Works Cited, and Bibliographies detected by heading analysis are excluded from similarity calculations.
- `exclude_small_matches=True`: Disregards passage fragments shorter than a configured threshold (default 10 words).
- `exclude_citations=True`: In-text parenthetical and numerical citations (e.g. `[1]`, `(Author, 2022)`) are excluded from overlap.
