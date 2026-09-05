# SHIVANG PLAGCHECK AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js: 14](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg)](https://nextjs.org/)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-black.svg)](https://vercel.com)
[![Docker: Ready](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](docker-compose.yml)
[![Tests: Passing](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](tests/)

> **Academic Similarity, AI-Writing & Citation Integrity Platform**  
> *A privacy-respecting, production-grade open-source alternative to commercial plagiarism systems.*  
> GitHub: [https://github.com/shivangsaxena1011/SHIVAGPLAGCHECK-AI](https://github.com/shivangsaxena1011/SHIVAGPLAGCHECK-AI)

---

## Overview

**SHIVANG PLAGCHECK AI** is a complete, self-hostable academic integrity engine designed for educational institutions, peer-reviewed journals, and researchers. Unlike closed-source commercial platforms, SHIVANG PLAGCHECK AI never transmits student manuscripts to external corporate silos, never claims proprietary monopoly over open algorithms, and provides fully auditable, sentence-level mathematical evidence for every finding.

### Key Capabilities

- **Exact & Near-Exact Plagiarism Engine**: Sub-quadratic Karp-Rabin Winnowing ($k=20, w=10$) with BLAST-style seed-and-extend alignment and length thresholds ($\ge 40$ chars) to eliminate false positives on common academic phrases.
- **Dense Semantic Paraphrase Detection**: Sentence-BERT neural embeddings (`sentence-transformers/all-MiniLM-L6-v2`) with sliding sentence windowing and cosine similarity scoring ($\ge 0.78$).
- **Multi-Signal AI-Writing Likelihood Estimation**: Stylometric variance (Type-Token Ratio, Hapax Legomena, sentence length variance, nominalizations), GPT lexical transition markers (*"delve", "crucial", "testament", "tapestry"*), paragraph burstiness analysis, and calibrated English-as-a-Second-Language (ESL) compensation. Always reported as *probabilistic likelihood*, never as definitive proof.
- **Citation & Reference Integrity**: Regular expression parsing of APA and IEEE reference styles, DOI normalization, live Crossref / OpenAlex API verification, and synthetic hallucination detection.
- **Deterministic Interval Coverage Math**: Union character interval arithmetic ensuring similarity percentages never exceed 100% or double-count overlapping matches. Full support for quote and bibliography exclusion masking.
- **Dual Export System**: Generates self-contained interactive offline HTML reports and publication-grade vector PDF reports.
- **Full-Featured Web Application & CLI**: Interactive Next.js 14 split-view dashboard, corpus management repository, and headless command-line interface for batch processing or CI/CD pipelines.

---

## Deployment on Vercel

The Next.js 14 frontend is pre-configured for one-click deployment on **Vercel**:

### Direct GitHub Import
1. Go to [vercel.com/new](https://vercel.com/new).
2. Select your GitHub repository: `shivangsaxena1011/SHIVAGPLAGCHECK-AI`.
3. In the project settings:
   - If using root directory: leave as default (`vercel.json` automatically builds the `frontend` workspace).
   - Alternatively, set **Root Directory** to `frontend`.
4. Add the Environment Variable:
   - `NEXT_PUBLIC_API_URL`: URL of your deployed backend service (e.g., `https://your-backend-api.com/api/v1` or `http://localhost:8000/api/v1` for local testing).
5. Click **Deploy**.

---

## Quickstart

### Option 1: Docker Compose (Recommended)

Run the complete platform (Backend + Frontend + SQLite database) with a single command:

```bash
docker-compose up --build
```

- **Web Dashboard**: Open [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation**: Open [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: Open [http://localhost:8000/health](http://localhost:8000/health)

---

### Option 2: Local Development Setup

#### 1. Backend Service

```bash
# Clone the repository
git clone https://github.com/shivangsaxena1011/SHIVAGPLAGCHECK-AI.git
cd SHIVAGPLAGCHECK-AI

# Install Python dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Web Application

```bash
# In a separate terminal
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to access the user interface.

---

### Option 3: Headless Command-Line Interface (CLI)

The `plagcheck` CLI allows running complete analyses, managing comparison corpora, and generating reports directly from the terminal:

```bash
# Run integrity check on a document
python -m plagcheck check tests/fixtures/exact_copy.txt

# Run check with quote and bibliography exclusion flags
python -m plagcheck check my_paper.pdf --exclude-quotes --exclude-biblio

# Ingest a reference document into the comparison corpus
python -m plagcheck corpus add path/to/reference.txt

# View corpus status and indexed document count
python -m plagcheck corpus list

# View generated report paths
python -m plagcheck report <submission_id>
```

*(Note: `python -m shivangplagcheck` and `python -m originalguard` are also supported as aliases).*

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints (/checks, /corpus)
│   │   ├── core/            # Configuration, database engine, security
│   │   ├── models/          # SQLAlchemy async ORM models
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── services/
│   │   │   ├── ai_detection/        # Stylometry, burstiness, ESL calibration
│   │   │   ├── citations/           # In-text & bibliography parsers
│   │   │   ├── corpus/              # Inverted fingerprint index & ingestion
│   │   │   ├── document/            # PDF, DOCX, TXT coordinate extractor
│   │   │   ├── plagiarism/
│   │   │   │   ├── exact/           # Winnowing, alignment, interval coverage
│   │   │   │   └── semantic/        # SBERT dense cosine similarity
│   │   │   ├── reference_checker/   # Crossref & OpenAlex client utilities
│   │   │   ├── reporting/           # ReportLab PDF & Jinja2 HTML generators
│   │   │   └── scoring/             # Deterministic score fusion engine
│   │   ├── workers/         # Async analysis pipeline orchestrator
│   │   └── main.py          # FastAPI application entrypoint
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js 14 App Router pages
│   │   │   ├── checks/[id]/ # Interactive document viewer with split-view
│   │   │   ├── corpus/      # Reference corpus management
│   │   │   ├── dashboard/   # Submissions history and actions
│   │   │   ├── new-check/   # Multi-format upload and configuration
│   │   │   └── page.tsx     # Platform landing page
│   │   └── lib/             # API client, dynamic color palette generator
│   ├── vercel.json          # Frontend-scoped Vercel configuration
│   └── package.json
├── plagcheck/               # Standalone Python CLI package
├── shivangplagcheck/        # Branded CLI entrypoint package
├── originalguard/           # Backward-compatible CLI alias
├── tests/                   # Comprehensive automated test suite
├── docs/                    # Technical architecture, API, and methodology
│   ├── ARCHITECTURE.md      # Detailed system design & algorithms
│   ├── API.md               # REST API endpoints & schemas
│   ├── METHODOLOGY.md       # Similarity vs plagiarism & ethical AI scoring
│   ├── SOURCE_MAPPING.md    # Upstream open-source attribution matrix
│   └── THIRD_PARTY_NOTICES.md # Full Apache-2.0 and MIT licenses
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── vercel.json              # Root Vercel build configuration
├── LICENSE                  # MIT License
└── README.md
```

---

## Automated Test Suite

SHIVANG PLAGCHECK AI includes comprehensive automated test coverage validating every algorithmic subsystem:

```bash
# Run the complete test suite
pytest tests/ -v
```

### Verified Test Cases:
1. `test_exact_plagiarism.py`: Karp-Rabin winnowing, seed-and-extend, and identical match verification.
2. `test_semantic_plagiarism.py`: SBERT dense embedding paraphrase detection on modified phrasing.
3. `test_ai_detector.py`: Multi-signal stylometric analysis, GPT lexical transition markers, and burstiness.
4. `test_citations.py`: Citation regex parser, DOI normalization, and reference structure extraction.
5. `test_score_fusion.py`: Union interval coverage math, exclusion interval subtraction, and percentage bounds.
6. `test_api_e2e.py`: Complete asynchronous end-to-end integration test (upload, processing, result polling, PDF download, HTML download).

---

## Methodology & Ethical AI Guidelines

- **Similarity is not Plagiarism**: High similarity scores may stem from quoted material, standard mathematical equations, or institutional templates. SHIVANG PLAGCHECK AI separates exact, near-exact, and semantic matches and highlights the original sources for academic review.
- **AI Writing Probability Caveat**: The AI detector provides an *estimated likelihood* based on variance in sentence cadence and vocabulary predictability. It should **never** be used as sole punitive proof of academic misconduct.
- **Attribution & Upstream Lineage**: Incorporates algorithms adapted under Apache-2.0 and MIT licenses from Noplag Engine, Aegis Integrity, and RefChecker. Full details in [`docs/SOURCE_MAPPING.md`](docs/SOURCE_MAPPING.md) and [`docs/THIRD_PARTY_NOTICES.md`](docs/THIRD_PARTY_NOTICES.md).

---

## License

SHIVANG PLAGCHECK AI is released under the **MIT License**. See [LICENSE](LICENSE) for full details.
