"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import {
  UploadCloud,
  FileText,
  Settings2,
  CheckCircle2,
  ArrowRight,
  Loader2,
  AlertCircle,
  FileCheck,
} from "lucide-react";

export default function NewCheckPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [dragOver, setDragOver] = useState(false);

  // Options
  const [scanLocal, setScanLocal] = useState(true);
  const [scanExternal, setScanExternal] = useState(false);
  const [runAi, setRunAi] = useState(true);
  const [verifyCitations, setVerifyCitations] = useState(true);
  const [excludeQuotes, setExcludeQuotes] = useState(true);
  const [excludeBib, setExcludeBib] = useState(true);
  const [excludeSmall, setExcludeSmall] = useState(true);
  const [excludeCitations, setExcludeCitations] = useState(true);

  // Progress state
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("");
  const [checkId, setCheckId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      if (!title) {
        setTitle(selected.name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      setFile(selected);
      if (!title) {
        setTitle(selected.name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  const pollStatus = async (id: string) => {
    try {
      const st = await api.getCheckStatus(id);
      setProgress(st.progress);
      setStage(st.current_stage);

      if (st.status === "COMPLETED") {
        setIsCompleted(true);
        setUploading(false);
        // Navigate to result after 1s
        setTimeout(() => {
          router.push(`/checks/?id=${id}`);
        }, 1200);
      } else if (st.status === "FAILED") {
        setErrorMessage(st.error_message || "Analysis failed during processing.");
        setUploading(false);
      } else {
        setTimeout(() => pollStatus(id), 600);
      }
    } catch (err) {
      setTimeout(() => pollStatus(id), 1000);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setErrorMessage(null);
    setProgress(5);
    setStage("Uploading document to secure analysis worker...");

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (title.trim()) formData.append("title", title.trim());
      formData.append("scan_local_corpus", String(scanLocal));
      formData.append("scan_external", String(scanExternal));
      formData.append("run_ai_detection", String(runAi));
      formData.append("verify_citations", String(verifyCitations));
      formData.append("exclude_quotes", String(excludeQuotes));
      formData.append("exclude_bibliography", String(excludeBib));
      formData.append("exclude_small_matches", String(excludeSmall));
      formData.append("exclude_citations", String(excludeCitations));

      const res = await api.uploadCheck(formData);
      setCheckId(res.id);
      pollStatus(res.id);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to start analysis check.");
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 w-full">
      <div className="border-b border-[#1f2937] pb-6 mb-8">
        <h1 className="text-2xl font-bold text-white tracking-tight">Run Originality &amp; AI Analysis</h1>
        <p className="text-sm text-gray-400 mt-1">
          Upload an academic paper, essay, thesis, or manuscript in PDF, DOCX, or TXT format.
        </p>
      </div>

      {uploading || isCompleted ? (
        /* Progress View */
        <div className="bg-[#111827] border border-[#1f2937] rounded-2xl p-8 sm:p-12 text-center shadow-2xl space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-blue-600/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mx-auto">
            {isCompleted ? (
              <CheckCircle2 className="w-8 h-8 text-emerald-400 animate-bounce" />
            ) : (
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            )}
          </div>

          <div>
            <h2 className="text-xl font-bold text-white">
              {isCompleted ? "Analysis Complete!" : "Analyzing Document..."}
            </h2>
            <p className="text-sm text-gray-400 mt-1">{stage || "Processing evidence..."}</p>
          </div>

          <div className="max-w-md mx-auto space-y-2">
            <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  isCompleted ? "bg-emerald-500" : "bg-blue-500"
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500 font-mono">
              <span>{progress}%</span>
              <span>{isCompleted ? "Ready" : "In Progress"}</span>
            </div>
          </div>

          {isCompleted && checkId && (
            <button
              onClick={() => router.push(`/checks/?id=${checkId}`)}
              className="inline-flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-6 py-2.5 rounded-lg shadow-lg transition"
            >
              <span>View Originality Report</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      ) : (
        /* Upload Form */
        <form onSubmit={handleSubmit} className="space-y-8">
          {errorMessage && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center space-x-2.5">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Drag & Drop Box */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition flex flex-col items-center justify-center space-y-4 ${
              dragOver
                ? "border-blue-500 bg-blue-500/5"
                : file
                ? "border-emerald-500/60 bg-emerald-500/5"
                : "border-[#1f2937] hover:border-gray-600 bg-[#111827]"
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.docx,.txt"
              className="hidden"
            />
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
                file ? "bg-emerald-500/10 text-emerald-400" : "bg-blue-500/10 text-blue-400"
              }`}
            >
              {file ? <FileCheck className="w-7 h-7" /> : <UploadCloud className="w-7 h-7" />}
            </div>

            <div>
              <p className="text-base font-semibold text-white">
                {file ? file.name : "Drag & drop your document here, or browse"}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {file
                  ? `${(file.size / 1024 / 1024).toFixed(2)} MB &bull; Ready for analysis`
                  : "Supports PDF, DOCX, and TXT (up to 50 MB)"}
              </p>
            </div>
          </div>

          {/* Title Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Document Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Master's Thesis: Neural Representation of Language"
              className="w-full bg-[#111827] border border-[#1f2937] rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
            />
          </div>

          {/* Analysis Configuration */}
          <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-6 space-y-4">
            <div className="flex items-center space-x-2 border-b border-gray-800 pb-3">
              <Settings2 className="w-4 h-4 text-blue-400" />
              <h2 className="text-sm font-semibold text-white uppercase tracking-wider">Analysis Configuration</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <label className="flex items-center space-x-3 cursor-pointer p-2.5 rounded-lg hover:bg-white/[0.02]">
                <input
                  type="checkbox"
                  checked={scanLocal}
                  onChange={(e) => setScanLocal(e.target.checked)}
                  className="rounded border-gray-700 text-blue-600 focus:ring-0 bg-gray-800"
                />
                <div>
                  <span className="font-medium text-gray-200">Local Corpus Matching</span>
                  <p className="text-[11px] text-gray-500">Winnowing &amp; SBERT against local documents</p>
                </div>
              </label>

              <label className="flex items-center space-x-3 cursor-pointer p-2.5 rounded-lg hover:bg-white/[0.02]">
                <input
                  type="checkbox"
                  checked={runAi}
                  onChange={(e) => setRunAi(e.target.checked)}
                  className="rounded border-gray-700 text-blue-600 focus:ring-0 bg-gray-800"
                />
                <div>
                  <span className="font-medium text-gray-200">Multi-Signal AI Detection</span>
                  <p className="text-[11px] text-gray-500">Stylometry, burstiness &amp; lexical tells</p>
                </div>
              </label>

              <label className="flex items-center space-x-3 cursor-pointer p-2.5 rounded-lg hover:bg-white/[0.02]">
                <input
                  type="checkbox"
                  checked={verifyCitations}
                  onChange={(e) => setVerifyCitations(e.target.checked)}
                  className="rounded border-gray-700 text-blue-600 focus:ring-0 bg-gray-800"
                />
                <div>
                  <span className="font-medium text-gray-200">Reference Verification</span>
                  <p className="text-[11px] text-gray-500">Crossref DOI &amp; hallucination checks</p>
                </div>
              </label>

              <label className="flex items-center space-x-3 cursor-pointer p-2.5 rounded-lg hover:bg-white/[0.02]">
                <input
                  type="checkbox"
                  checked={scanExternal}
                  onChange={(e) => setScanExternal(e.target.checked)}
                  className="rounded border-gray-700 text-blue-600 focus:ring-0 bg-gray-800"
                />
                <div>
                  <span className="font-medium text-gray-200">External Web / Scholarly Discovery</span>
                  <p className="text-[11px] text-gray-500">Query OpenAlex &amp; Crossref APIs</p>
                </div>
              </label>
            </div>

            <div className="border-t border-gray-800 pt-3">
              <span className="text-xs font-semibold text-gray-400 block mb-2">Exclusion Rules:</span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-gray-300">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={excludeQuotes}
                    onChange={(e) => setExcludeQuotes(e.target.checked)}
                    className="rounded text-blue-600"
                  />
                  <span>Exclude Quotes</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={excludeBib}
                    onChange={(e) => setExcludeBib(e.target.checked)}
                    className="rounded text-blue-600"
                  />
                  <span>Exclude Bibliography</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={excludeSmall}
                    onChange={(e) => setExcludeSmall(e.target.checked)}
                    className="rounded text-blue-600"
                  />
                  <span>Exclude Small Matches</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={excludeCitations}
                    onChange={(e) => setExcludeCitations(e.target.checked)}
                    className="rounded text-blue-600"
                  />
                  <span>Exclude Citations</span>
                </label>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={!file}
            className={`w-full py-3.5 rounded-xl font-semibold shadow-lg transition flex items-center justify-center space-x-2 ${
              file
                ? "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-500/20"
                : "bg-gray-800 text-gray-500 cursor-not-allowed"
            }`}
          >
            <FileText className="w-5 h-5" />
            <span>Start Originality Analysis</span>
          </button>
        </form>
      )}
    </div>
  );
}
