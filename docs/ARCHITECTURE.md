# SHIVANG PLAGCHECK AI — System Architecture

**Subtitle**: Academic Similarity, AI-Writing & Citation Integrity Platform  
**Version**: 1.0.0 (Production Release)

---

## 1. System Overview

SHIVANG PLAGCHECK AI is an enterprise-grade, privacy-respecting, open-source integrity engine designed for universities, academic journals, research institutes, and students. It operates completely locally or on self-hosted infrastructure without sending user documents to external commercial plagiarism syndicates.

The platform provides a four-tier analysis pipeline:
1. **Exact & Near-Exact Plagiarism Detection**: Sub-quadratic Karp-Rabin Winnowing fingerprinting with BLAST-style seed-and-extend alignment.
2. **Semantic Similarity & Paraphrase Analysis**: Sentence-BERT dense vector embeddings (`all-MiniLM-L6-v2`) with cosine similarity scoring across sliding windows.
3. **Multi-Signal AI-Assisted Writing Estimation**: Stylometric variance (Type-Token Ratio, Hapax Legomena, sentence length variance, nominalizations), GPT lexical transition markers, sentence burstiness, and calibrated ESL compensation.
4. **Citation & Reference Integrity Verification**: Regex parsing of IEEE/APA references, DOI extraction, and live validation via Crossref & OpenAlex APIs.

All four tiers converge in a **Deterministic Interval Fusion Engine** that computes union character coverage over the document, ensuring mathematically rigorous percentages without double-counting overlapping passages.

---

## 2. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                  USER INTERFACE                                   |
|                                                                                   |
|  +--------------------------+    +--------------------------+    +-------------+  |
|  | Next.js 14 Web App       |    | Standalone HTML Report   |    | Python CLI  |  |
|  | (Split-View, Heatmaps,   |    | (Self-contained, offline |    | (Terminal & |  |
|  | Interactive Highlights)  |    | interactive viewer)      |    | CI/CD pipes)|  |
|  +------------+-------------+    +-------------+------------+    +------+------+  |
+---------------|--------------------------------|------------------------|---------+
                |                                |                        |
                | REST API (HTTP / JSON / Multi-part)                      |
                v                                v                        v
+-----------------------------------------------------------------------------------+
|                                FASTAPI BACKEND                                    |
|                                                                                   |
|  +------------------------+  +------------------------+  +---------------------+  |
|  | /api/v1/checks         |  | /api/v1/corpus         |  | /health             |  |
|  | Upload, Status, Report |  | Ingest, Search, Delete |  | Liveness / Readiness|  |
|  +-----------+------------+  +-----------+------------+  +---------------------+  |
+--------------|---------------------------|----------------------------------------+
               |                           |
               v                           v
+-----------------------------------------------------------------------------------+
|                        ASYNC PIPELINE ORCHESTRATION                               |
|                                                                                   |
|  [Step 1] Document Normalization & Structural Extraction                          |
|           • Format detectors: PDF (PyMuPDF / pypdf), DOCX (python-docx), TXT      |
|           • Page, paragraph, and sentence coordinate offset preservation          |
|                                                                                   |
|  [Step 2] Quote & Bibliography Exclusion Masking                                  |
|           • Inverted commas, blockquotes, reference section detection             |
|                                                                                   |
|  [Step 3] Parallel Engine Execution                                               |
|      ├── Exact Winnowing Fingerprinting (Karp-Rabin k=20, w=10)                   |
|      ├── Seed-and-Extend Local Alignment (Min match = 40 chars)                   |
|      ├── SBERT Paraphrase Matcher (Dense embeddings, Cosine threshold >= 0.78)    |
|      ├── Multi-Signal AI Likelihood Estimator (TTR, burstiness, ESL calibration)  |
|      └── Reference Integrity Checker (Crossref / OpenAlex DOI verification)       |
|                                                                                   |
|  [Step 4] Deterministic Coverage Fusion Engine                                    |
|           • Union interval arithmetic (O(N log N) interval merging)               |
|           • Non-overlapping segment percentage computation                        |
|                                                                                   |
|  [Step 5] Artifact Generation & Storage                                           |
|           • Interactive HTML Report (Standalone Jinja2 template)                  |
|           • Publication-Quality PDF Report (ReportLab vector rendering)           |
+-----------------------------------------------------------------------------------+
               |                           |
               v                           v
+-----------------------------------------------------------------------------------+
|                               STORAGE & INDICES                                   |
|                                                                                   |
|  +-------------------------+  +-----------------------+  +---------------------+  |
|  | Inverted Fingerprint    |  | SQLite / PostgreSQL   |  | Local File Storage  |  |
|  | Hash Index (In-Memory)  |  | (Metadata, Matches,   |  | (Uploaded files &   |  |
|  | Sub-second L1 filtering |  | AI findings, Reports) |  | generated reports)  |  |
|  +-------------------------+  +-----------------------+  +---------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Core Subsystems & Algorithmic Design

### 3.1 Document Extraction & Coordinate Preservation
The extractor (`app/services/document/extractor.py`) processes PDF, DOCX, and TXT files, generating a unified `ExtractedDocument` containing:
- Full normalized text.
- Page boundaries with exact character ranges `[start, end)`.
- Sentence boundaries with punctuation preservation.
- Pre-detected exclusion intervals (e.g. blockquotes, quoted dialogue, and bibliography sections).

### 3.2 Karp-Rabin Winnowing Fingerprinting
Implements the landmark Schleimer, Wilkerson, and Aiken (2003) algorithm (`app/services/plagiarism/exact/winnowing.py`):
1. **Normalization**: Strips whitespace, case, and punctuation.
2. **K-Gram Generation**: Slide window of length $k=20$ across tokens.
3. **Rolling Hash**: Computes Karp-Rabin polynomial rolling hashes over $k$-grams.
4. **Window Selection**: Over windows of size $w=10$, selects the minimum hash value (breaking ties by selecting the rightmost occurrence). This guarantees that any shared substring of length $\ge k + w - 1$ (29 tokens) is guaranteed to be detected.

### 3.3 BLAST-Style Seed-and-Extend Local Alignment
When two fingerprints match, the engine performs seed extension (`app/services/plagiarism/exact/alignment.py`):
- Uses the matching $k$-gram position as an anchor.
- Extends forward and backward character-by-character while matching score remains above threshold.
- Filters out short, spurious matches (< 40 characters) to eliminate false positives on common academic phrases.

### 3.4 SBERT Semantic Similarity & Paraphrasing
Dense neural matching (`app/services/plagiarism/semantic/semantic.py`):
- Chunks text into sliding overlapping sentence windows.
- Encodes chunks into 384-dimensional dense vectors using `sentence-transformers/all-MiniLM-L6-v2`.
- Computes cosine similarity matrix against candidate corpus passages.
- Matches with cosine similarity $\ge 0.78$ and exact match overlap $< 0.85$ are flagged as **Semantic Paraphrases**.

### 3.5 Multi-Signal AI Writing Detection
To eliminate the brittle false positives of single-signal classifiers, `app/services/ai_detection/` combines 4 distinct signals:
1. **Stylometric Profile**: Type-Token Ratio (TTR), Hapax Legomena ratio (words occurring exactly once), sentence length standard deviation, passive voice frequency, nominalization frequency.
2. **GPT Lexical Tells**: Dual-tier heuristic scanner checking transition words favored by LLMs (*"delve", "crucial", "testament", "tapestry", "fosters"*) alongside uniform sentence structures.
3. **Burstiness Analysis**: Evaluates variance in sentence length and complexity across neighboring paragraphs (human writing exhibits high burstiness; LLMs exhibit uniform sentence pacing).
4. **ESL Calibration**: Distinguishes English-as-a-Second-Language formal vocabulary usage from AI-generated text by adjusting thresholds based on vocabulary diversity metrics.
- Output: Probabilistic score ($0-100\%$) labeled **"Estimated AI-writing likelihood"** accompanied by sentence-level evidentiary reasoning.

### 3.6 Reference & Citation Verification
Parsed via regex for standard citation formats (APA, IEEE, Harvard) and verified against public scholarly metadata:
- DOI normalization and format validation.
- Live Crossref REST API querying (`api.crossref.org`) with rate-limiting and graceful fallback.
- Title and author fuzzy matching via Jaccard distance on normalized token sets.
- Hallucination detection: identifies synthesized references that cite non-existent DOIs or mix real authors with fake paper titles.

### 3.7 Deterministic Interval Fusion Math
Turnitin and basic plagiarism checkers often misreport totals by summing individual source percentages, yielding impossible results (>100%). SHIVANG PLAGCHECK AI solves this via Interval Arithmetic (`app/services/plagiarism/exact/intervals.py` and `app/services/scoring/score_fusion.py`):
$$\text{Matched Intervals} = \bigcup_{m \in \text{Matches}} [s_m, e_m)$$
$$\text{Effective Matched} = \text{Matched Intervals} \setminus \left( \bigcup_{ex \in \text{Exclusions}} [s_{ex}, e_{ex}) \right)$$
$$\text{Overall Similarity \%} = \frac{|\text{Effective Matched}|}{|\text{Total Characters}| - |\text{Exclusions}|} \times 100$$
This guarantees strictly bounded percentages in $[0, 100]\%$.

---

## 4. Database Schema

The system uses SQLAlchemy 2.0 async ORM supporting SQLite and PostgreSQL:
- **`submissions`**: Document metadata, total words, pages, status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`), error tracking.
- **`documents`**: Document storage path, checksum, extracted plain text.
- **`document_pages`**: Page numbers with coordinate character offsets.
- **`sources`**: Reference corpus items (title, authors, publication, DOI, source type).
- **`source_chunks`**: Chunk text, embeddings, offset markers.
- **`fingerprints`**: Inverted index entries storing `(hash, source_id, chunk_id, offset)`.
- **`match_evidences`**: Match records linking submission offsets to source offsets with detection type and confidence.
- **`ai_findings`**: Sentence-by-sentence AI likelihood scores and diagnostic notes.
- **`references`**: Parsed reference entries, verification status, and issue logs.
- **`reports`**: Cached HTML and PDF generation metadata.

---

## 5. Security & Privacy Architecture

- **File Signature Validation**: Magic byte header inspection prevents extension spoofing (`%PDF-` for PDF, `PK\x03\x04` for DOCX).
- **Path Traversal Prevention**: Filenames are sanitized via `re.sub(r'[^a-zA-Z0-9_.-]', '_', name)` and resolved relative to sandboxed storage paths.
- **No External Text Leaks**: Submission texts are never sent to third-party AI APIs or commercial plagiarism databases. All embeddings and detection models run locally.
- **Auditability**: Every match provides exact character offsets and the original source text for human review.
