"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CorpusItem } from "@/lib/api-client";

export default function CorpusManagementPage() {
  const [items, setItems] = useState<CorpusItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);

  // Add form state
  const [title, setTitle] = useState("");
  const [authors, setAuthors] = useState("");
  const [publication, setPublication] = useState("");
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadCorpus = async () => {
    try {
      setLoading(true);
      const data = await api.listCorpus();
      setItems(data);
    } catch (err: any) {
      console.error("Failed to load corpus:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCorpus();
  }, []);

  const handleAddDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !text.trim()) {
      setFormError("Title and text content are required.");
      return;
    }

    try {
      setSubmitting(true);
      setFormError(null);
      await api.addCorpusDocument({
        title: title.trim(),
        text: text.trim(),
        authors: authors.trim() || undefined,
        publication: publication.trim() || undefined,
      });
      setTitle("");
      setAuthors("");
      setPublication("");
      setText("");
      setShowAddModal(false);
      await loadCorpus();
    } catch (err: any) {
      setFormError(err.message || "Failed to ingest reference document");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to remove this document from the reference corpus?")) {
      return;
    }
    try {
      await api.deleteCorpusItem(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err: any) {
      alert("Failed to delete corpus item: " + err.message);
    }
  };

  const filteredItems = items.filter(
    (item) =>
      item.title.toLowerCase().includes(search.toLowerCase()) ||
      (item.authors && item.authors.toLowerCase().includes(search.toLowerCase())) ||
      (item.publication && item.publication.toLowerCase().includes(search.toLowerCase()))
  );

  const totalWords = items.reduce((sum, item) => sum + item.word_count, 0);
  const totalChunks = items.reduce((sum, item) => sum + item.chunks_count, 0);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Reference Corpus Management
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Maintain institutional repositories, published literature, and comparison databases for exact and semantic indexing.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold transition flex items-center gap-2 self-start sm:self-auto shadow-sm"
        >
          <span>➕</span> Ingest Reference Paper
        </button>
      </div>

      {/* Stats summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 my-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Indexed Documents
          </div>
          <div className="text-2xl font-bold text-white mt-1">{items.length}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Fingerprint Chunks
          </div>
          <div className="text-2xl font-bold text-white mt-1">{totalChunks.toLocaleString()}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Total Corpus Words
          </div>
          <div className="text-2xl font-bold text-white mt-1">{totalWords.toLocaleString()}</div>
        </div>
      </div>

      {/* Search & Actions Bar */}
      <div className="flex items-center justify-between gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search by title, author, or publication..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <span className="absolute left-3 top-2.5 text-slate-500 text-sm">🔍</span>
        </div>
        <button
          onClick={loadCorpus}
          className="px-3 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-lg text-xs transition"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Corpus Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading corpus repository...</div>
        ) : filteredItems.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <span className="text-3xl block mb-2">📁</span>
            {search ? "No documents match your search query." : "No documents in corpus yet. Ingest your first reference paper above."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/40 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Title & Details</th>
                  <th className="py-3 px-4">Source Type</th>
                  <th className="py-3 px-4">Words / Chunks</th>
                  <th className="py-3 px-4">Checksum</th>
                  <th className="py-3 px-4">Added</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-4 max-w-sm">
                      <div className="font-semibold text-slate-200 text-sm">{item.title}</div>
                      <div className="text-slate-400 text-xs mt-0.5">
                        {item.authors && <span>By {item.authors}</span>}
                        {item.publication && <span> • {item.publication}</span>}
                        {item.year && <span> ({item.year})</span>}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        {item.source_type}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      <div>{item.word_count.toLocaleString()} words</div>
                      <div className="text-slate-500 text-[11px]">{item.chunks_count} chunks</div>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-400">
                      {item.checksum ? item.checksum.substring(0, 12) + "..." : "—"}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="px-2.5 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded text-xs transition"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Ingest Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h3 className="text-lg font-bold text-white">Ingest Reference Document</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs">
                {formError}
              </div>
            )}

            <form onSubmit={handleAddDocument} className="space-y-4 mt-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Document Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Deep Residual Learning for Image Recognition"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Authors (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g., He, K., Zhang, X., Ren, S., Sun, J."
                    value={authors}
                    onChange={(e) => setAuthors(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Publication / Journal (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g., IEEE CVPR 2016"
                    value={publication}
                    onChange={(e) => setPublication(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Document Text Content *</label>
                <textarea
                  required
                  rows={8}
                  placeholder="Paste the full text or abstract of the reference paper here..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 placeholder-slate-600 font-mono text-xs focus:outline-none focus:border-indigo-500 leading-relaxed"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold rounded-lg transition"
                >
                  {submitting ? "Indexing..." : "Index Document"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
