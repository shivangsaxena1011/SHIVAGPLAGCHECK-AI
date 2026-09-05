"""Interactive Standalone HTML Report Generator.

Creates a self-contained, responsive HTML report emulating professional academic
originality dashboards:
- Top-level cards: Similarity, AI Likelihood, Sources, Words, Pages.
- Side-by-side interactive layout: Document text on left with colored source highlights,
  source breakdown on right.
- AI analysis section with sentence-level signal markers.
- Reference verification table.
- Methodology & Disclaimer footer.
"""

from __future__ import annotations

import html
from pathlib import Path
from jinja2 import Template

# Clean modern academic report template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SHIVANG PLAGCHECK AI Report — {{ submission.title }}</title>
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: #1f2937;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --danger: #ef4444;
      --warning: #f59e0b;
      --success: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text-main);
      line-height: 1.6;
      padding: 24px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 24px;
    }
    .header-title h1 { font-size: 24px; font-weight: 700; color: #fff; }
    .header-title p { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .badge-primary { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }

    .score-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 20px;
    }
    .card-title { font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
    .card-value { font-size: 32px; font-weight: 800; margin: 8px 0; }
    .card-desc { font-size: 13px; color: var(--text-muted); }

    .val-similarity { color: #f87171; }
    .val-ai { color: #fbbf24; }
    .val-sources { color: #60a5fa; }
    .val-stats { color: #34d399; }

    .main-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
      margin-bottom: 32px;
    }
    @media (max-width: 1024px) {
      .main-grid { grid-template-columns: 1fr; }
    }

    .document-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 32px;
      height: 720px;
      overflow-y: auto;
    }
    .page-separator {
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 1px;
      padding: 12px 0 8px 0;
      margin-top: 24px;
      border-top: 1px dashed var(--card-border);
    }
    .doc-text {
      font-size: 15px;
      line-height: 1.8;
      color: #e5e7eb;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .source-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px;
      height: 720px;
      overflow-y: auto;
    }
    .source-panel h2 { font-size: 16px; font-weight: 700; margin-bottom: 16px; }
    .source-item {
      padding: 14px;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--card-border);
      margin-bottom: 12px;
      transition: border-color 0.2s;
    }
    .source-item:hover { border-color: var(--accent); }
    .source-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
    .source-title { font-size: 14px; font-weight: 600; color: #fff; line-height: 1.3; }
    .source-percent { font-size: 14px; font-weight: 700; color: #f87171; white-space: nowrap; margin-left: 8px; }
    .source-meta { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

    .highlight-exact { background: rgba(239, 68, 68, 0.35); border-bottom: 2px solid #ef4444; border-radius: 2px; padding: 1px 2px; }
    .highlight-near { background: rgba(245, 158, 11, 0.35); border-bottom: 2px solid #f59e0b; border-radius: 2px; padding: 1px 2px; }
    .highlight-semantic { background: rgba(59, 130, 246, 0.35); border-bottom: 2px solid #3b82f6; border-radius: 2px; padding: 1px 2px; }

    .section-box {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
    }
    .section-box h3 { font-size: 16px; font-weight: 700; margin-bottom: 16px; }

    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--card-border); }
    th { color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 11px; }

    .status-valid { color: #34d399; font-weight: 600; }
    .status-issue { color: #f87171; font-weight: 600; }

    .disclaimer {
      margin-top: 32px;
      padding: 20px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.6;
    }
  </style>
</head>
<body>

  <div class="header">
    <div class="header-title">
      <h1>SHIVANG PLAGCHECK AI &mdash; Analysis Report</h1>
      <p>Document: <strong>{{ submission.original_filename }}</strong> | Analyzed: {{ submission.created_at.strftime('%Y-%m-%d %H:%M UTC') }}</p>
    </div>
    <span class="badge badge-primary">SHIVANG PLAGCHECK AI v1.0</span>
  </div>

  <!-- Top Cards -->
  <div class="score-cards">
    <div class="card">
      <div class="card-title">Similarity Score</div>
      <div class="card-value val-similarity">{{ breakdown.overall_similarity }}%</div>
      <div class="card-desc">Exact: {{ breakdown.exact_similarity }}% | Semantic: {{ breakdown.semantic_similarity }}%</div>
    </div>
    <div class="card">
      <div class="card-title">AI Writing Likelihood</div>
      <div class="card-value val-ai">{{ ai_result.overall_likelihood }}%</div>
      <div class="card-desc">{{ ai_result.confidence_band }}</div>
    </div>
    <div class="card">
      <div class="card-title">Sources Found</div>
      <div class="card-value val-sources">{{ sources|length }}</div>
      <div class="card-desc">Across local corpus & databases</div>
    </div>
    <div class="card">
      <div class="card-title">Document Scope</div>
      <div class="card-value val-stats">{{ document.word_count }}</div>
      <div class="card-desc">{{ document.page_count }} Pages | {{ document.char_count }} Characters</div>
    </div>
  </div>

  <!-- Main Split Viewer -->
  <div class="main-grid">
    <div class="document-panel">
      <h2 style="font-size: 16px; margin-bottom: 16px;">Annotated Document Text</h2>
      {% for page in document.pages %}
        <div class="page-separator">PAGE {{ page.page_number }}</div>
        <div class="doc-text">{{ page.text|e }}</div>
      {% endfor %}
    </div>

    <div class="source-panel">
      <h2>Source Contributions ({{ sources|length }})</h2>
      {% if sources %}
        {% for s in sources %}
          <div class="source-item">
            <div class="source-header">
              <span class="source-title">{{ loop.index }}. {{ s.title }}</span>
              <span class="source-percent">{{ s.similarity_contribution }}%</span>
            </div>
            <div class="source-meta">
              {% if s.authors %}Authors: {{ s.authors }}<br/>{% endif %}
              Matched Words: {{ s.matched_words }} | Type: {{ s.primary_match_type }}
              {% if s.url %}<br/><a href="{{ s.url }}" target="_blank" style="color:#60a5fa; text-decoration:none;">View Source &rarr;</a>{% endif %}
            </div>
          </div>
        {% endfor %}
      {% else %}
        <p style="color: var(--text-muted); font-size: 14px;">No significant source matches detected in comparison corpus.</p>
      {% endif %}
    </div>
  </div>

  <!-- AI Analysis Breakdown -->
  <div class="section-box">
    <h3>AI Writing Signal Breakdown</h3>
    <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 16px;">
      Total sentences analyzed: {{ ai_result.total_sentences }} | High concern signals: {{ ai_result.high_signal_count }} | Moderate signals: {{ ai_result.medium_signal_count }}
    </p>
    <table>
      <thead>
        <tr>
          <th>Sentence #</th>
          <th>Text Sample</th>
          <th>AI Likelihood</th>
          <th>Primary Signal Reasoning</th>
        </tr>
      </thead>
      <tbody>
        {% for sig in ai_result.sentence_signals[:10] %}
        <tr>
          <td>{{ sig.sentence_index + 1 }}</td>
          <td>{{ sig.sentence_text[:90] }}...</td>
          <td><strong>{{ (sig.likelihood * 100)|round(1) }}%</strong></td>
          <td>{{ sig.primary_signal }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <!-- Citation Integrity Table -->
  <div class="section-box">
    <h3>Reference Verification & Citation Integrity</h3>
    {% if references %}
      <table>
        <thead>
          <tr>
            <th>Reference</th>
            <th>DOI</th>
            <th>Status</th>
            <th>Verification Details</th>
          </tr>
        </thead>
        <tbody>
          {% for ref in references %}
          <tr>
            <td>{{ ref.raw_text[:110] }}...</td>
            <td>{{ ref.doi or 'N/A' }}</td>
            <td class="{{ 'status-valid' if ref.verification_status == 'VALID' else 'status-issue' }}">
              {{ ref.verification_status }}
            </td>
            <td>{{ ref.issues|join(', ') if ref.issues else 'Verified against scholarly database' }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p style="color: var(--text-muted); font-size: 14px;">No formal bibliography detected or references provided.</p>
    {% endif %}
  </div>

  <!-- Disclaimer Footer -->
  <div class="disclaimer">
    <strong>Methodology & Academic Disclaimers:</strong><br/>
    1. <em>Similarity Determination</em>: Similarity scores reflect the proportion of textual overlap against comparison databases. Human academic review is required to evaluate context, fair use, and scholarly quotation.<br/>
    2. <em>AI Writing Signals</em>: AI-writing likelihood is an automated statistical and stylometric estimate based on language model burstiness, transition phrase density, and syntactical uniformity. It is not infallible proof of AI authorship.<br/>
    3. <em>Citation Integrity</em>: Verified against Crossref and OpenAlex academic metadata registries.
  </div>

</body>
</html>
"""


class HTMLReportGenerator:
    """Generates standalone HTML reports."""

    def __init__(self):
        self.template = Template(HTML_TEMPLATE)

    def generate_file(
        self,
        output_path: Path,
        submission: any,
        document: any,
        breakdown: any,
        sources: list,
        ai_result: any,
        references: list,
        matches: list,
    ) -> None:
        """Render and save HTML report to file."""
        rendered = self.template.render(
            submission=submission,
            document=document,
            breakdown=breakdown,
            sources=sources,
            ai_result=ai_result,
            references=references,
            matches=matches,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)
