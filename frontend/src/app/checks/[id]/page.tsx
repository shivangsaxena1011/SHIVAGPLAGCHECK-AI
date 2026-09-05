"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  api,
  CheckResult,
  CheckStatus,
  MatchEvidence,
  SourceContribution,
  AIFinding,
  ReferenceItem,
} from "@/lib/api-client";
import { getSourceColor } from "@/lib/color-palette";

export default function CheckDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [result, setResult] = useState<CheckResult | null>(null);
  const [status, setStatus] = useState<CheckStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active view tab
  const [activeTab, setActiveTab] = useState<"document" | "ai" | "citations">("document");

  // Selected item
  const [selectedMatch, setSelectedMatch] = useState<MatchEvidence | null>(null);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);

  // Highlighting filters
  const [showExact, setShowExact] = useState(true);
  const [showNearExact, setShowNearExact] = useState(true);
  const [showSemantic, setShowSemantic] = useState(true);
  const [showAIHighlights, setShowAIHighlights] = useState(false);

  // Poll status or fetch result
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    async function load() {
      try {
        const s = await api.getCheckStatus(id);
        setStatus(s);

        if (s.status === "COMPLETED") {
          const res = await api.getCheckResult(id);
          setResult(res);
          setLoading(false);
          if (interval) clearInterval(interval);
        } else if (s.status === "FAILED") {
          setError(s.error_message || "Analysis failed");
          setLoading(false);
          if (interval) clearInterval(interval);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load report");
        setLoading(false);
        if (interval) clearInterval(interval);
      }
    }

    load();
    interval = setInterval(load, 2500);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [id]);

  // Map source ID to color index
  const sourceColorMap = useMemo(() => {
    const map = new Map<string, number>();
    if (!result) return map;
    result.sources.forEach((src) => {
      map.set(src.source_id, src.color_index);
    });
    return map;
  }, [result]);

  // Filtered matches based on toggles
  const activeMatches = useMemo(() => {
    if (!result) return [];
    return result.matches.filter((m) => {
      if (m.detection_type === "EXACT" && !showExact) return false;
      if (m.detection_type === "NEAR_EXACT" && !showNearExact) return false;
      if (m.detection_type === "SEMANTIC" && !showSemantic) return false;
      if (selectedSourceId && m.source_id !== selectedSourceId) return false;
      return true;
    });
  }, [result, showExact, showNearExact, showSemantic, selectedSourceId]);

  // Scroll to match element
  const scrollToMatch = (matchId: string) => {
    const el = document.getElementById(`match-span-${matchId}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("ring-2", "ring-indigo-400");
      setTimeout(() => el.classList.remove("ring-2", "ring-indigo-400"), 2000);
    }
  };

  if (loading && !result) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="inline-block p-4 rounded-full bg-slate-800 border border-slate-700 mb-6">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <h2 className="text-2xl font-bold mb-2">Analyzing Document...</h2>
        <p className="text-slate-400 mb-6">
          {status?.current_stage || "Extracting text, computing winnowing hashes, and running neural models..."}
        </p>
        <div className="w-full max-w-md mx-auto bg-slate-800 rounded-full h-3 overflow-hidden border border-slate-700">
          <div
            className="bg-indigo-600 h-full transition-all duration-500 rounded-full"
            style={{ width: `${status?.progress || 10}%` }}
          ></div>
        </div>
        <p className="text-xs text-slate-500 mt-2">{status?.progress || 10}% completed</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-8 mb-6">
          <span className="text-4xl mb-4 block">⚠️</span>
          <h2 className="text-2xl font-bold text-red-400 mb-2">Analysis Failed or Unavailable</h2>
          <p className="text-slate-300 mb-6">{error || "Submission could not be found or processed."}</p>
          <div className="flex justify-center gap-4">
            <Link
              href="/dashboard"
              className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm transition"
            >
              Back to Dashboard
            </Link>
            <Link
              href="/new-check"
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm transition"
            >
              Try New Submission
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const { scores, ai_summary, citation_summary, sources } = result;

  // Render Document with Highlight Spans
  const fullDocumentText = result.pages.map((p) => p.text).join("\n\n");

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link href="/dashboard" className="text-slate-400 hover:text-slate-200 text-sm">
              ← Dashboard
            </Link>
            <span className="text-slate-600">•</span>
            <span className="text-xs uppercase tracking-wider font-semibold text-indigo-400">
              Integrity Report
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">{result.title}</h1>
          <p className="text-xs text-slate-400 mt-1">
            Filename: <span className="text-slate-300 font-mono">{result.original_filename}</span> | {result.word_count.toLocaleString()} words | {result.page_count} pages | Processed on {new Date(result.created_at).toLocaleDateString()}
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <a
            href={api.getReportPdfUrl(result.id)}
            download
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-sm transition"
          >
            <span>📥</span> Download Academic PDF
          </a>
          <a
            href={api.getReportHtmlUrl(result.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-2 transition"
          >
            <span>🌐</span> Standalone HTML
          </a>
        </div>
      </div>

      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 my-6">
        {/* Overall Similarity */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Overall Similarity</span>
            <span
              className={`text-xs px-2 py-0.5 rounded font-bold ${
                scores.overall_similarity > 25
                  ? "bg-red-500/20 text-red-400 border border-red-500/30"
                  : scores.overall_similarity > 10
                  ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                  : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              }`}
            >
              {scores.overall_similarity}%
            </span>
          </div>
          <div className="mt-3 text-3xl font-extrabold text-white">{scores.overall_similarity}%</div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-2">
            <span>Exact: <strong className="text-slate-200">{scores.exact_similarity}%</strong></span>
            <span>Near: <strong className="text-slate-200">{scores.near_exact_similarity}%</strong></span>
            <span>Paraphrase: <strong className="text-slate-200">{scores.semantic_similarity}%</strong></span>
          </div>
        </div>

        {/* AI Likelihood */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AI Likelihood</span>
            <span
              className={`text-xs px-2 py-0.5 rounded font-bold ${
                ai_summary.overall_likelihood > 50
                  ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                  : "bg-slate-700 text-slate-300"
              }`}
            >
              {ai_summary.confidence_band}
            </span>
          </div>
          <div className="mt-3 text-3xl font-extrabold text-white">{ai_summary.overall_likelihood}%</div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-2">
            <span>{ai_summary.high_signal_sections} high-signal sections</span>
            <span>{ai_summary.total_sentences} sentences</span>
          </div>
        </div>

        {/* Citations */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Citation Integrity</span>
            <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 font-bold">
              {citation_summary.verified_count} / {citation_summary.total_references} Valid
            </span>
          </div>
          <div className="mt-3 text-3xl font-extrabold text-white">
            {citation_summary.total_references > 0
              ? `${Math.round((citation_summary.verified_count / citation_summary.total_references) * 100)}%`
              : "N/A"}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-2">
            <span>Hallucinated: <strong className="text-red-400">{citation_summary.hallucinated_count}</strong></span>
            <span>Mismatched: <strong className="text-amber-400">{citation_summary.mismatch_count}</strong></span>
          </div>
        </div>

        {/* Source count */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Sources Matched</span>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-bold">
              {sources.length} total
            </span>
          </div>
          <div className="mt-3 text-3xl font-extrabold text-white">{sources.length}</div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-2">
            <span>Matched words: <strong className="text-slate-200">{scores.matched_word_count}</strong></span>
            <span>Quotes excluded: <strong className="text-slate-200">{scores.excluded_quote_words}</strong></span>
          </div>
        </div>
      </div>

      {/* Tabs navigation */}
      <div className="flex items-center justify-between border-b border-slate-800 mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab("document")}
            className={`pb-3 px-3 text-sm font-medium border-b-2 transition ${
              activeTab === "document"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            📑 Interactive Document & Sources ({result.matches.length} matches)
          </button>
          <button
            onClick={() => setActiveTab("ai")}
            className={`pb-3 px-3 text-sm font-medium border-b-2 transition ${
              activeTab === "ai"
                ? "border-purple-500 text-purple-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            🤖 AI-Writing Analysis ({result.ai_findings.length} sentences)
          </button>
          <button
            onClick={() => setActiveTab("citations")}
            className={`pb-3 px-3 text-sm font-medium border-b-2 transition ${
              activeTab === "citations"
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            📚 Citation Verification ({result.references.length} references)
          </button>
        </div>

        {/* View toggles when in document tab */}
        {activeTab === "document" && (
          <div className="hidden sm:flex items-center gap-3 text-xs text-slate-400 pb-2">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={showExact}
                onChange={(e) => setShowExact(e.target.checked)}
                className="rounded border-slate-700 text-red-600 focus:ring-0"
              />
              <span className="text-slate-300">Exact</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={showNearExact}
                onChange={(e) => setShowNearExact(e.target.checked)}
                className="rounded border-slate-700 text-amber-600 focus:ring-0"
              />
              <span className="text-slate-300">Near-Exact</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={showSemantic}
                onChange={(e) => setShowSemantic(e.target.checked)}
                className="rounded border-slate-700 text-blue-600 focus:ring-0"
              />
              <span className="text-slate-300">Paraphrase</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer ml-2">
              <input
                type="checkbox"
                checked={showAIHighlights}
                onChange={(e) => setShowAIHighlights(e.target.checked)}
                className="rounded border-slate-700 text-purple-600 focus:ring-0"
              />
              <span className="text-purple-300">AI Heatmap</span>
            </label>
            {selectedSourceId && (
              <button
                onClick={() => setSelectedSourceId(null)}
                className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded text-xs hover:bg-slate-700 ml-2"
              >
                Clear filter ✕
              </button>
            )}
          </div>
        )}
      </div>

      {/* Tab 1: Interactive Document & Sources Split-View */}
      {activeTab === "document" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Document Viewer with Highlights */}
          <div className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800 text-xs text-slate-400">
              <span className="font-semibold uppercase tracking-wider text-slate-300">Submitted Document Text</span>
              <span>Click highlighted text to inspect evidence</span>
            </div>

            {/* Document Content with Segment Highlighting */}
            <div className="prose prose-invert max-w-none font-mono text-sm leading-relaxed text-slate-300 whitespace-pre-wrap max-h-[750px] overflow-y-auto pr-3">
              {result.pages.map((page) => {
                // Find matches on this page
                const pageMatches = activeMatches.filter((m) => m.submission_page === page.page_number);

                return (
                  <div key={page.page_number} className="mb-8 pb-6 border-b border-slate-800/60 last:border-0">
                    <div className="text-xs font-semibold text-indigo-400 uppercase tracking-widest mb-3 select-none">
                      Page {page.page_number}
                    </div>
                    <div>
                      {renderHighlightedPage(
                        page.text,
                        pageMatches,
                        result.ai_findings.filter((f) => f.page_number === page.page_number),
                        sourceColorMap,
                        showAIHighlights,
                        (match) => {
                          setSelectedMatch(match);
                          setSelectedSourceId(match.source_id || null);
                        }
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Source Matches List & Inspector */}
          <div className="lg:col-span-4 space-y-4">
            {/* Selected Match Inspector Drawer */}
            {selectedMatch && (
              <div className="bg-indigo-950/40 border border-indigo-500/40 rounded-xl p-4 shadow-lg animate-fadeIn">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">
                    Match Inspector
                  </span>
                  <button
                    onClick={() => setSelectedMatch(null)}
                    className="text-slate-400 hover:text-white text-xs"
                  >
                    ✕
                  </button>
                </div>
                <div className="text-sm font-semibold text-white mb-1">
                  {selectedMatch.title || "Matched Source"}
                </div>
                <div className="text-xs text-slate-400 mb-3">
                  Type: <span className="font-mono text-indigo-300">{selectedMatch.detection_type}</span> | Similarity:{" "}
                  <strong className="text-white">{Math.round(selectedMatch.similarity * 100)}%</strong>
                </div>

                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400 font-semibold block mb-1">Submitted Document Passage:</span>
                    <div className="bg-slate-900/90 border border-slate-800 rounded p-2 text-slate-200 font-mono text-[11px] max-h-28 overflow-y-auto">
                      "{selectedMatch.submitted_text}"
                    </div>
                  </div>
                  {selectedMatch.source_text && (
                    <div>
                      <span className="text-slate-400 font-semibold block mb-1">Original Source Passage:</span>
                      <div className="bg-slate-900/90 border border-slate-800 rounded p-2 text-amber-200/90 font-mono text-[11px] max-h-28 overflow-y-auto">
                        "{selectedMatch.source_text}"
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-3 flex justify-between items-center text-xs pt-2 border-t border-indigo-500/20">
                  <button
                    onClick={() => scrollToMatch(selectedMatch.id)}
                    className="text-indigo-300 hover:text-indigo-200 underline"
                  >
                    Scroll to passage
                  </button>
                  {selectedMatch.doi && (
                    <a
                      href={`https://doi.org/${selectedMatch.doi}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 underline"
                    >
                      DOI: {selectedMatch.doi}
                    </a>
                  )}
                </div>
              </div>
            )}

            {/* Sources List */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Top Matched Sources ({sources.length})
                </span>
                {selectedSourceId && (
                  <button
                    onClick={() => setSelectedSourceId(null)}
                    className="text-xs text-indigo-400 hover:text-indigo-300"
                  >
                    Show all
                  </button>
                )}
              </div>

              {sources.length === 0 ? (
                <p className="text-xs text-slate-500 py-4 text-center">No significant source matches found.</p>
              ) : (
                <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
                  {sources.map((src) => {
                    const color = getSourceColor(src.color_index);
                    const isSelected = selectedSourceId === src.source_id;

                    return (
                      <div
                        key={src.source_id}
                        onClick={() => {
                          setSelectedSourceId(isSelected ? null : src.source_id);
                          // Select first match of this source
                          const firstM = result.matches.find((m) => m.source_id === src.source_id);
                          if (firstM) {
                            setSelectedMatch(firstM);
                            scrollToMatch(firstM.id);
                          }
                        }}
                        className={`p-3 rounded-lg border cursor-pointer transition text-xs ${
                          isSelected
                            ? "bg-slate-800 border-indigo-500 shadow-md"
                            : "bg-slate-900/60 border-slate-800 hover:bg-slate-800/80"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2 mb-1.5">
                          <div className="flex items-center gap-2">
                            <span
                              className="w-3 h-3 rounded-full shrink-0"
                              style={{ backgroundColor: color.border }}
                            />
                            <span className="font-semibold text-slate-200 line-clamp-1">{src.title}</span>
                          </div>
                          <span
                            className="font-bold shrink-0 px-2 py-0.5 rounded text-[11px]"
                            style={{
                              backgroundColor: color.badgeBg,
                              color: color.text,
                              border: `1px solid ${color.border}40`,
                            }}
                          >
                            {src.similarity_contribution}%
                          </span>
                        </div>

                        <div className="text-[11px] text-slate-400 pl-5 space-y-0.5">
                          {src.authors && <div className="line-clamp-1">By: {src.authors}</div>}
                          <div className="flex items-center gap-3">
                            <span>{src.matched_words} matched words</span>
                            <span>•</span>
                            <span className="font-mono text-slate-500">{src.primary_match_type}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: AI-Writing Likelihood Sentence Map */}
      {activeTab === "ai" && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-lg font-bold text-white">Sentence-by-Sentence AI Probability Distribution</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Stylometric variance, GPT lexical tells, burstiness analysis & ESL calibration.
                </p>
              </div>
              <div className="text-xs text-slate-400 bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700">
                Detector: <span className="font-semibold text-purple-400">{ai_summary.detector_version}</span>
              </div>
            </div>

            <div className="mt-4 p-4 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-400 leading-relaxed">
              <strong className="text-slate-300">Methodology & Caution: </strong>
              {ai_summary.methodology_notes}
            </div>

            {/* Sentence table */}
            <div className="mt-6 overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                    <th className="py-2.5 px-3">#</th>
                    <th className="py-2.5 px-3">Sentence Passage</th>
                    <th className="py-2.5 px-3 w-32">Likelihood</th>
                    <th className="py-2.5 px-3">Primary Signal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {result.ai_findings.map((finding) => (
                    <tr
                      key={finding.id}
                      className={`hover:bg-slate-800/40 transition ${
                        finding.likelihood_score >= 0.7 ? "bg-purple-950/20" : ""
                      }`}
                    >
                      <td className="py-3 px-3 font-mono text-slate-500">{finding.sentence_index + 1}</td>
                      <td className="py-3 px-3 text-slate-200 font-serif max-w-xl">"{finding.sentence_text}"</td>
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700">
                            <div
                              className={`h-full rounded-full ${
                                finding.likelihood_score >= 0.7
                                  ? "bg-purple-500"
                                  : finding.likelihood_score >= 0.4
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                              }`}
                              style={{ width: `${Math.round(finding.likelihood_score * 100)}%` }}
                            />
                          </div>
                          <span className="font-mono font-bold text-slate-300">
                            {Math.round(finding.likelihood_score * 100)}%
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 border border-slate-700 text-slate-300">
                          {finding.primary_signal}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Citation Verification */}
      {activeTab === "citations" && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-lg font-bold text-white">Reference Verification & Citation Integrity</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Academic DOI lookup, Crossref & OpenAlex matching, and hallucination diagnostics.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold">
                  {citation_summary.verified_count} Verified
                </span>
                <span className="text-xs px-2.5 py-1 rounded bg-red-500/10 text-red-400 border border-red-500/30 font-semibold">
                  {citation_summary.hallucinated_count} Hallucinated
                </span>
                <span className="text-xs px-2.5 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 font-semibold">
                  {citation_summary.mismatch_count} Mismatches
                </span>
              </div>
            </div>

            {result.references.length === 0 ? (
              <p className="text-xs text-slate-500 py-8 text-center">No references or bibliography detected in document.</p>
            ) : (
              <div className="mt-6 space-y-4">
                {result.references.map((ref, idx) => (
                  <div
                    key={ref.id || idx}
                    className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 flex flex-col md:flex-row md:items-start justify-between gap-4"
                  >
                    <div className="space-y-1 text-xs">
                      <div className="font-serif text-slate-200 text-sm">{ref.raw_text}</div>
                      {(ref.parsed_title || ref.parsed_authors) && (
                        <div className="text-slate-400 pt-1">
                          {ref.parsed_authors && <span>Authors: {ref.parsed_authors} • </span>}
                          {ref.parsed_year && <span>Year: {ref.parsed_year} • </span>}
                          {ref.parsed_title && <span className="italic">"{ref.parsed_title}"</span>}
                        </div>
                      )}
                      {ref.doi && (
                        <div className="pt-1">
                          <a
                            href={`https://doi.org/${ref.doi}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-400 hover:text-blue-300 underline font-mono"
                          >
                            https://doi.org/{ref.doi}
                          </a>
                        </div>
                      )}
                      {ref.issues && ref.issues.length > 0 && (
                        <div className="pt-2 text-red-400 font-mono text-[11px]">
                          Issues: {ref.issues.join(", ")}
                        </div>
                      )}
                    </div>

                    {/* Status Badge */}
                    <div className="shrink-0">
                      <span
                        className={`px-2.5 py-1 rounded text-xs font-bold font-mono tracking-wider ${
                          ref.verification_status === "VALID"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : ref.verification_status === "HALLUCINATED"
                            ? "bg-red-500/20 text-red-400 border border-red-500/30"
                            : ref.verification_status === "MISMATCH"
                            ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                            : "bg-slate-800 text-slate-400 border border-slate-700"
                        }`}
                      >
                        {ref.verification_status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Helper: Render Page Text with Highlight Spans
function renderHighlightedPage(
  pageText: string,
  matches: MatchEvidence[],
  aiFindings: AIFinding[],
  sourceColorMap: Map<string, number>,
  showAIHeatmap: boolean,
  onSelectMatch: (m: MatchEvidence) => void
) {
  if (matches.length === 0 && !showAIHeatmap) {
    return <span>{pageText}</span>;
  }

  // Find intervals of interest
  type Interval = {
    start: number;
    end: number;
    match?: MatchEvidence;
    aiFinding?: AIFinding;
  };

  const intervals: Interval[] = [];

  matches.forEach((m) => {
    // Find occurrence of submitted_text in page
    if (m.submitted_text && pageText.includes(m.submitted_text)) {
      let idx = 0;
      while ((idx = pageText.indexOf(m.submitted_text, idx)) !== -1) {
        intervals.push({
          start: idx,
          end: idx + m.submitted_text.length,
          match: m,
        });
        idx += m.submitted_text.length;
      }
    }
  });

  if (showAIHeatmap) {
    aiFindings.forEach((f) => {
      if (f.likelihood_score >= 0.5 && f.sentence_text && pageText.includes(f.sentence_text)) {
        let idx = 0;
        while ((idx = pageText.indexOf(f.sentence_text, idx)) !== -1) {
          intervals.push({
            start: idx,
            end: idx + f.sentence_text.length,
            aiFinding: f,
          });
          idx += f.sentence_text.length;
        }
      }
    });
  }

  // Sort intervals
  intervals.sort((a, b) => a.start - b.start);

  const elements: React.ReactNode[] = [];
  let currentPos = 0;

  intervals.forEach((iv, i) => {
    if (iv.start > currentPos) {
      elements.push(
        <span key={`text-${currentPos}`}>{pageText.slice(currentPos, iv.start)}</span>
      );
    }

    if (iv.start >= currentPos) {
      const segmentText = pageText.slice(iv.start, iv.end);

      if (iv.match) {
        const colorIdx = sourceColorMap.get(iv.match.source_id || "") || 0;
        const color = getSourceColor(colorIdx);

        elements.push(
          <mark
            key={`match-${iv.match.id}-${i}`}
            id={`match-span-${iv.match.id}`}
            onClick={() => onSelectMatch(iv.match!)}
            className="cursor-pointer rounded px-0.5 transition hover:opacity-80 underline decoration-2 font-medium"
            style={{
              backgroundColor: color.bg,
              color: "#ffffff",
              borderBottomColor: color.border,
            }}
            title={`${iv.match.title || "Match"} (${Math.round(iv.match.similarity * 100)}%)`}
          >
            {segmentText}
          </mark>
        );
      } else if (iv.aiFinding) {
        elements.push(
          <mark
            key={`ai-${iv.aiFinding.id}-${i}`}
            className="rounded px-0.5 bg-purple-500/25 text-purple-200 border-b-2 border-purple-400 font-medium"
            title={`AI Likelihood: ${Math.round(iv.aiFinding.likelihood_score * 100)}%`}
          >
            {segmentText}
          </mark>
        );
      }

      currentPos = Math.max(currentPos, iv.end);
    }
  });

  if (currentPos < pageText.length) {
    elements.push(<span key={`text-end`}>{pageText.slice(currentPos)}</span>);
  }

  return <>{elements}</>;
}
