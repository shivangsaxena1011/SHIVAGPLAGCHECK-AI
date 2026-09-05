"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CheckStatus } from "@/lib/api-client";
import {
  FileText,
  PlusCircle,
  Clock,
  CheckCircle2,
  AlertCircle,
  Download,
  Trash2,
  ExternalLink,
  RefreshCw,
} from "lucide-react";

export default function DashboardPage() {
  const [checks, setChecks] = useState<CheckStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchChecks = async () => {
    try {
      setRefreshing(true);
      const data = await api.listChecks();
      setChecks(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchChecks();
    const interval = setInterval(fetchChecks, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this analysis check?")) return;
    try {
      await api.deleteCheck(id);
      setChecks((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      alert("Failed to delete check");
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1f2937] pb-6 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Analysis Dashboard</h1>
          <p className="text-sm text-gray-400 mt-1">
            Manage document originality scans, review detected sources, and export reports.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchChecks}
            disabled={refreshing}
            className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 transition"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-blue-400" : ""}`} />
          </button>
          <Link
            href="/new-check"
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white font-medium px-4 py-2 rounded-lg shadow transition text-sm"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Check</span>
          </Link>
        </div>
      </div>

      {/* Submissions Table */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-[#1f2937] flex items-center justify-between">
          <h2 className="text-base font-semibold text-white">Recent Analyses ({checks.length})</h2>
          <span className="text-xs text-gray-400">Auto-refreshes every 5s</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-gray-400 text-sm">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
            Loading submissions...
          </div>
        ) : checks.length === 0 ? (
          <div className="p-16 text-center text-gray-400">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-600" />
            <p className="font-semibold text-white">No documents analyzed yet</p>
            <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
              Upload a PDF, DOCX, or TXT file to run exact plagiarism, semantic similarity, and AI writing detection.
            </p>
            <Link
              href="/new-check"
              className="mt-4 inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Start First Analysis</span>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#0d121f] text-gray-400 uppercase text-[11px] font-semibold tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">Document / ID</th>
                  <th className="py-3.5 px-4">Status &amp; Stage</th>
                  <th className="py-3.5 px-4">Progress</th>
                  <th className="py-3.5 px-4">Date</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f2937] text-gray-300">
                {checks.map((check) => (
                  <tr key={check.id} className="hover:bg-white/[0.02] transition">
                    <td className="py-3.5 px-4">
                      <Link
                        href={`/checks/${check.id}`}
                        className="font-semibold text-white hover:text-blue-400 transition flex items-center space-x-2"
                      >
                        <FileText className="w-4 h-4 text-blue-400 shrink-0" />
                        <span className="truncate max-w-xs">{check.id.slice(0, 8)}...</span>
                      </Link>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-2">
                        {check.status === "COMPLETED" ? (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Completed</span>
                          </span>
                        ) : check.status === "FAILED" ? (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
                            <AlertCircle className="w-3 h-3" />
                            <span>Failed</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                            <Clock className="w-3 h-3 animate-pulse" />
                            <span>{check.status}</span>
                          </span>
                        )}
                        <span className="text-xs text-gray-400 truncate max-w-xs">{check.current_stage}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="w-32 bg-gray-800 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full transition-all duration-300 ${
                            check.status === "COMPLETED"
                              ? "bg-emerald-500"
                              : check.status === "FAILED"
                              ? "bg-red-500"
                              : "bg-blue-500"
                          }`}
                          style={{ width: `${check.progress}%` }}
                        />
                      </div>
                      <span className="text-[11px] text-gray-500 mt-0.5 block">{check.progress}%</span>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-gray-400 whitespace-nowrap">
                      {new Date(check.created_at).toLocaleDateString()}{" "}
                      {new Date(check.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        {check.status === "COMPLETED" && (
                          <>
                            <Link
                              href={`/checks/${check.id}`}
                              className="px-2.5 py-1 rounded bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 text-xs font-medium transition"
                            >
                              Report
                            </Link>
                            <a
                              href={api.getReportPdfUrl(check.id)}
                              target="_blank"
                              rel="noreferrer"
                              className="p-1 rounded text-gray-400 hover:text-white transition"
                              title="Download PDF"
                            >
                              <Download className="w-4 h-4" />
                            </a>
                          </>
                        )}
                        <button
                          onClick={() => handleDelete(check.id)}
                          className="p-1 rounded text-gray-500 hover:text-red-400 transition"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
