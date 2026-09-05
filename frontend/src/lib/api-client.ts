/**
 * SHIVANG PLAGCHECK AI API Client.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export interface CheckStatus {
  id: string;
  status: string;
  progress: number;
  current_stage: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface SimilarityBreakdown {
  overall_similarity: number;
  exact_similarity: number;
  near_exact_similarity: number;
  semantic_similarity: number;
  self_plagiarism_similarity: number;
  matched_word_count: number;
  total_words: number;
  excluded_quote_words: number;
  excluded_bibliography_words: number;
}

export interface SourceContribution {
  source_id: string;
  title: string;
  authors?: string;
  publication?: string;
  year?: string;
  url?: string;
  doi?: string;
  source_type: string;
  similarity_contribution: number;
  matched_words: number;
  primary_match_type: string;
  color_index: number;
}

export interface AISummary {
  overall_likelihood: number;
  confidence_band: string;
  high_signal_sections: number;
  medium_signal_sections: number;
  total_sentences: number;
  detector_version: string;
  methodology_notes: string;
}

export interface CitationSummary {
  total_references: number;
  verified_count: number;
  mismatch_count: number;
  hallucinated_count: number;
  unresolvable_count: number;
  in_text_citations_count: number;
}

export interface MatchEvidence {
  id: string;
  submission_id: string;
  source_id?: string;
  source_type: string;
  detection_type: string;
  confidence: number;
  similarity: number;
  source_similarity_contribution: number;
  submitted_text: string;
  source_text?: string;
  submission_page: number;
  submission_start: number;
  submission_end: number;
  evidence_reason?: string;
  url?: string;
  doi?: string;
  title?: string;
  authors?: string;
}

export interface AIFinding {
  id: string;
  sentence_index: number;
  sentence_text: string;
  char_start: number;
  char_end: number;
  page_number: number;
  likelihood_score: number;
  confidence: number;
  primary_signal: string;
}

export interface ReferenceItem {
  id: string;
  raw_text: string;
  parsed_title?: string;
  parsed_authors?: string;
  parsed_year?: string;
  doi?: string;
  verification_status: "VALID" | "MISMATCH" | "HALLUCINATED" | "NOT_FOUND" | "UNRESOLVABLE" | "UNVERIFIED";
  confidence: number;
  issues: string[];
}

export interface DocumentPage {
  page_number: number;
  char_start: number;
  char_end: number;
  text: string;
}

export interface CheckResult {
  id: string;
  title: string;
  original_filename: string;
  file_type: string;
  word_count: number;
  char_count: number;
  page_count: number;
  created_at: string;
  scores: SimilarityBreakdown;
  sources: SourceContribution[];
  ai_summary: AISummary;
  citation_summary: CitationSummary;
  pages: DocumentPage[];
  matches: MatchEvidence[];
  ai_findings: AIFinding[];
  references: ReferenceItem[];
}

export interface CorpusItem {
  id: string;
  title: string;
  authors?: string;
  publication?: string;
  year?: string;
  url?: string;
  doi?: string;
  source_type: string;
  checksum: string;
  word_count: number;
  chunks_count: number;
  created_at: string;
}

export const api = {
  async uploadCheck(formData: FormData): Promise<CheckStatus> {
    const res = await fetch(`${API_BASE}/checks`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Upload failed");
    }
    return res.json();
  },

  async getCheckStatus(id: string): Promise<CheckStatus> {
    const res = await fetch(`${API_BASE}/checks/${id}/status`);
    if (!res.ok) throw new Error("Failed to fetch check status");
    return res.json();
  },

  async getCheckResult(id: string): Promise<CheckResult> {
    const res = await fetch(`${API_BASE}/checks/${id}/result`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to fetch result" }));
      throw new Error(err.detail || "Failed to fetch result");
    }
    return res.json();
  },

  async listChecks(): Promise<CheckStatus[]> {
    const res = await fetch(`${API_BASE}/checks`);
    if (!res.ok) throw new Error("Failed to list checks");
    return res.json();
  },

  async deleteCheck(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/checks/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete check");
  },

  async listCorpus(): Promise<CorpusItem[]> {
    const res = await fetch(`${API_BASE}/corpus`);
    if (!res.ok) throw new Error("Failed to list corpus");
    return res.json();
  },

  async addCorpusDocument(data: { title: string; text: string; authors?: string; publication?: string }): Promise<CorpusItem> {
    const res = await fetch(`${API_BASE}/corpus/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to add to corpus" }));
      throw new Error(err.detail || "Failed to add to corpus");
    }
    return res.json();
  },

  async deleteCorpusItem(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/corpus/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete corpus item");
  },

  getReportPdfUrl(id: string): string {
    return `${API_BASE}/checks/${id}/report/pdf`;
  },

  getReportHtmlUrl(id: string): string {
    return `${API_BASE}/checks/${id}/report/html`;
  },
};
