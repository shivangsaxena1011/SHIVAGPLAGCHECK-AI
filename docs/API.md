# SHIVANG PLAGCHECK AI — REST API Reference

**Base URL**: `http://localhost:8000/api/v1`  
**OpenAPI Specification**: Interactive Swagger docs available at `http://localhost:8000/docs`  
**ReDoc**: Available at `http://localhost:8000/redoc`

---

## 1. Submissions & Checks (`/checks`)

### 1.1 Submit Document for Analysis
Submits a document (PDF, DOCX, or TXT) to the analysis pipeline.

- **Method**: `POST /checks`
- **Content-Type**: `multipart/form-data`
- **Request Body Parameters**:
  | Parameter | Type | Required | Default | Description |
  |---|---|---|---|---|
  | `file` | Binary File | Yes | — | PDF (`.pdf`), Word (`.docx`), or Plain Text (`.txt`) file. |
  | `title` | String | No | Filename | Human-readable title for the submission. |
  | `exclude_quotes` | Boolean | No | `true` | Exclude quoted text from similarity percentages. |
  | `exclude_biblio` | Boolean | No | `true` | Exclude bibliography and references from similarity. |
  | `min_match_words` | Integer | No | `8` | Minimum word threshold for exact match reporting. |
- **Response**: `200 OK`
  ```json
  {
    "id": "c1f76d91-e407-4221-8eb7-f6d3f233be8b",
    "status": "PROCESSING",
    "progress": 0,
    "current_stage": "Document accepted for processing",
    "error_message": null,
    "created_at": "2026-09-05T08:20:00Z",
    "updated_at": "2026-09-05T08:20:00Z"
  }
  ```

---

### 1.2 Get Analysis Status
Polls processing progress ($0-100\%$) and current stage.

- **Method**: `GET /checks/{submission_id}/status`
- **Response**: `200 OK`
  ```json
  {
    "id": "c1f76d91-e407-4221-8eb7-f6d3f233be8b",
    "status": "COMPLETED",
    "progress": 100,
    "current_stage": "Completed",
    "error_message": null,
    "created_at": "2026-09-05T08:20:00Z",
    "updated_at": "2026-09-05T08:20:05Z"
  }
  ```
  *Status values*: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`.

---

### 1.3 Get Comprehensive Report Result
Returns full integrity report including similarity breakdown, matched sources, AI findings, references, and page texts.

- **Method**: `GET /checks/{submission_id}/result`
- **Response**: `200 OK`
  ```json
  {
    "id": "c1f76d91-e407-4221-8eb7-f6d3f233be8b",
    "title": "Quantum Computing Analysis",
    "original_filename": "quantum_paper.pdf",
    "file_type": "pdf",
    "word_count": 2840,
    "char_count": 18450,
    "page_count": 6,
    "created_at": "2026-09-05T08:20:00Z",
    "scores": {
      "overall_similarity": 34.2,
      "exact_similarity": 28.5,
      "near_exact_similarity": 3.2,
      "semantic_similarity": 2.5,
      "self_plagiarism_similarity": 0.0,
      "matched_word_count": 971,
      "total_words": 2840,
      "excluded_quote_words": 42,
      "excluded_bibliography_words": 310
    },
    "sources": [
      {
        "source_id": "src_001",
        "title": "Introduction to Quantum Error Correction",
        "authors": "Nielsen, M. A., & Chuang, I. L.",
        "publication": "Cambridge University Press",
        "year": "2010",
        "url": "https://example.com/quantum",
        "doi": "10.1017/CBO9780511976667",
        "source_type": "INSTITUTIONAL",
        "similarity_contribution": 34.2,
        "matched_words": 971,
        "primary_match_type": "EXACT",
        "color_index": 0
      }
    ],
    "ai_summary": {
      "overall_likelihood": 12.0,
      "confidence_band": "LOW",
      "high_signal_sections": 0,
      "medium_signal_sections": 1,
      "total_sentences": 120,
      "detector_version": "v1.0-stylometric-gpttells-calibrated",
      "methodology_notes": "Estimated likelihood based on stylometric variance and burstiness. Not proof of AI generation."
    },
    "citation_summary": {
      "total_references": 15,
      "verified_count": 14,
      "mismatch_count": 1,
      "hallucinated_count": 0,
      "unresolvable_count": 0,
      "in_text_citations_count": 22
    },
    "pages": [...],
    "matches": [...],
    "ai_findings": [...],
    "references": [...]
  }
  ```

---

### 1.4 Export Academic PDF Report
Generates and streams a vector-rendered publication-grade PDF report.

- **Method**: `GET /checks/{submission_id}/report/pdf`
- **Response**: `200 OK` (`application/pdf`)
- **Headers**: `Content-Disposition: attachment; filename="SHIVANG_PLAGCHECK_{id}.pdf"`

---

### 1.5 Export Standalone HTML Report
Generates and streams a self-contained offline interactive HTML report.

- **Method**: `GET /checks/{submission_id}/report/html`
- **Response**: `200 OK` (`text/html`)
- **Headers**: `Content-Disposition: inline; filename="SHIVANG_PLAGCHECK_{id}.html"`

---

### 1.6 List Submissions History
Returns past submissions and their processing status.

- **Method**: `GET /checks`
- **Response**: `200 OK` (Array of `CheckStatus`)

---

### 1.7 Delete Submission
Permanently removes submission record, extracted texts, and generated reports.

- **Method**: `DELETE /checks/{submission_id}`
- **Response**: `200 OK` (`{"status": "deleted"}`)

---

## 2. Reference Corpus Management (`/corpus`)

### 2.1 List Indexed Documents
Lists all comparison documents currently indexed in the inverted fingerprint and embedding repository.

- **Method**: `GET /corpus`
- **Response**: `200 OK`
  ```json
  [
    {
      "id": "0dfbc4aa-813c-41f2-972f-5ea9195b05fa",
      "title": "Attention Is All You Need",
      "authors": "Vaswani et al.",
      "publication": "NeurIPS 2017",
      "year": "2017",
      "url": "https://arxiv.org/abs/1706.03762",
      "doi": "10.48550/arXiv.1706.03762",
      "source_type": "JOURNAL",
      "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "word_count": 8250,
      "chunks_count": 32,
      "created_at": "2026-09-05T08:00:00Z"
    }
  ]
  ```

---

### 2.2 Add Reference Document (JSON)
Ingests text into the reference corpus with immediate chunking and fingerprinting.

- **Method**: `POST /corpus/add`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "title": "BERT: Pre-training of Deep Bidirectional Transformers",
    "text": "We introduce a new language representation model called BERT...",
    "authors": "Devlin, Chang, Lee, Toutanova",
    "publication": "NAACL 2019",
    "year": "2019",
    "url": "https://arxiv.org/abs/1810.04805",
    "doi": "10.48550/arXiv.1810.04805"
  }
  ```
- **Response**: `200 OK` (Returns the newly created `CorpusItem`)

---

### 2.3 Upload Reference Document (File)
Uploads and indexes a PDF/DOCX/TXT file into the reference corpus.

- **Method**: `POST /corpus/upload`
- **Content-Type**: `multipart/form-data`
- **Request Parameters**:
  | Parameter | Type | Description |
  |---|---|---|
  | `file` | Binary File | Reference paper file |
  | `title` | String (Optional) | Custom title |
  | `authors` | String (Optional) | Author list |
  | `publication` | String (Optional) | Publication venue |
- **Response**: `200 OK` (Returns `CorpusItem`)

---

### 2.4 Delete Reference Document
Deletes a document from the reference corpus, removing its fingerprints from the inverted index.

- **Method**: `DELETE /corpus/{source_id}`
- **Response**: `200 OK` (`{"status": "deleted"}`)

---

## 3. System Health (`/health`)

- **Method**: `GET /health`
- **Response**: `200 OK`
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "corpus_sources": 14,
    "fingerprint_index_size": 18240
  }
  ```
