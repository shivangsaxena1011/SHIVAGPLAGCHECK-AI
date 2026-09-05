import Link from "next/link";
import { ShieldCheck, Search, Cpu, BookCheck, ArrowRight, FileUp, Database, FileSpreadsheet } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-16 sm:py-24 max-w-6xl mx-auto">
      {/* Hero Section */}
      <div className="text-center space-y-5 max-w-3xl">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold uppercase tracking-wider">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>SHIVANG PLAGCHECK AI &bull; Academic Integrity Platform</span>
        </div>
        
        <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight">
          Scholarly Similarity, <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400">AI-Writing</span> &amp; Citation Integrity
        </h1>

        <p className="text-gray-400 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
          The comprehensive academic verification suite. Combines robust Winnowing fingerprints, SBERT semantic paraphrasing, multi-signal AI likelihood estimation, and Crossref reference validation.
        </p>

        <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/new-check"
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-6 py-3 rounded-lg shadow-lg shadow-blue-500/25 transition"
          >
            <FileUp className="w-5 h-5" />
            <span>Upload Document</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/dashboard"
            className="flex items-center space-x-2 bg-gray-800/80 hover:bg-gray-700/80 border border-gray-700 text-gray-200 font-semibold px-6 py-3 rounded-lg transition"
          >
            <span>Open Dashboard</span>
          </Link>
        </div>
      </div>

      {/* Emulated Report Target Card */}
      <div className="w-full mt-16 p-6 rounded-2xl bg-[#111827] border border-[#1f2937] shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-800 pb-4 mb-6">
          <div>
            <h2 className="text-lg font-bold text-white">Live Academic Originality Target</h2>
            <p className="text-xs text-gray-400">Dynamic multi-layer evidence evaluation</p>
          </div>
          <span className="text-xs font-mono bg-blue-900/30 text-blue-400 border border-blue-800/50 px-2.5 py-1 rounded">
            Report Standards: 92-Page Emulation Ready
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-center">
          <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800">
            <p className="text-xs text-gray-400 uppercase font-semibold">Similarity</p>
            <p className="text-3xl font-extrabold text-red-400 my-1">27%</p>
            <p className="text-[11px] text-gray-500">Exact &amp; Semantic</p>
          </div>
          <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800">
            <p className="text-xs text-gray-400 uppercase font-semibold">AI Likelihood</p>
            <p className="text-3xl font-extrabold text-amber-400 my-1">52%</p>
            <p className="text-[11px] text-gray-500">Multi-Signal Ensemble</p>
          </div>
          <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800">
            <p className="text-xs text-gray-400 uppercase font-semibold">Sources Found</p>
            <p className="text-3xl font-extrabold text-blue-400 my-1">27+</p>
            <p className="text-[11px] text-gray-500">Corpus &amp; Databases</p>
          </div>
          <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800">
            <p className="text-xs text-gray-400 uppercase font-semibold">Words Analyzed</p>
            <p className="text-3xl font-extrabold text-emerald-400 my-1">14,664</p>
            <p className="text-[11px] text-gray-500">Positionally Mapped</p>
          </div>
          <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 col-span-2 sm:col-span-1">
            <p className="text-xs text-gray-400 uppercase font-semibold">Pages</p>
            <p className="text-3xl font-extrabold text-purple-400 my-1">92</p>
            <p className="text-[11px] text-gray-500">PDF / DOCX Preserved</p>
          </div>
        </div>
      </div>

      {/* Feature Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-12">
        <div className="p-6 rounded-xl bg-[#111827] border border-[#1f2937] hover:border-blue-500/50 transition">
          <div className="w-10 h-10 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center mb-4">
            <Search className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold text-white mb-2">Exact &amp; Semantic Plagiarism</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            Schleimer et al. Winnowing fingerprints combined with BLAST-adapted seed-and-extend passage alignment and Sentence Transformers embeddings.
          </p>
        </div>

        <div className="p-6 rounded-xl bg-[#111827] border border-[#1f2937] hover:border-amber-500/50 transition">
          <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center mb-4">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold text-white mb-2">Multi-Signal AI Detection</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            Language-calibrated AI analysis with stylometric variance, perplexity consistency, dual-tier GPT lexical tells, and sentence-level reasoning.
          </p>
        </div>

        <div className="p-6 rounded-xl bg-[#111827] border border-[#1f2937] hover:border-emerald-500/50 transition">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-4">
            <BookCheck className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold text-white mb-2">Citation &amp; Reference Integrity</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            Extracts in-text citations and validates bibliography DOIs against Crossref and OpenAlex to identify hallucinated or fabricated citations.
          </p>
        </div>
      </div>
    </div>
  );
}
