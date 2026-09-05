import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { ShieldCheck, FileText, Database, PlusCircle, History } from "lucide-react";

export const metadata: Metadata = {
  title: "SHIVANG PLAGCHECK AI — Academic Similarity, AI-Writing & Citation Integrity Platform",
  description: "Production-grade academic originality checking, multi-signal AI writing likelihood estimation, and citation integrity verification.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090d16] text-[#f3f4f6] flex flex-col">
        {/* Navigation Bar */}
        <header className="sticky top-0 z-50 border-b border-[#1f2937] bg-[#0d121f]/90 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Link href="/" className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <span className="font-bold text-lg text-white tracking-tight">SHIVANG PLAGCHECK<span className="text-blue-500"> AI</span></span>
                <span className="hidden sm:block text-[11px] text-gray-400 leading-none">Academic Integrity Platform</span>
              </div>
            </Link>
          </div>

          <nav className="flex items-center space-x-1 sm:space-x-2 text-sm font-medium">
            <Link href="/dashboard" className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-gray-300 hover:text-white hover:bg-gray-800/60 transition">
              <FileText className="w-4 h-4 text-blue-400" />
              <span>Dashboard</span>
            </Link>
            <Link href="/corpus" className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-gray-300 hover:text-white hover:bg-gray-800/60 transition">
              <Database className="w-4 h-4 text-emerald-400" />
              <span>Corpus</span>
            </Link>
            <Link href="/new-check" className="flex items-center space-x-1.5 bg-blue-600 hover:bg-blue-500 text-white px-3.5 py-1.5 rounded-md shadow-sm transition font-medium">
              <PlusCircle className="w-4 h-4" />
              <span>New Check</span>
            </Link>
          </nav>
        </header>

        {/* Main Content */}
        <main className="flex-1 flex flex-col">{children}</main>

        {/* Footer */}
        <footer className="border-t border-[#1f2937] py-6 px-8 text-center text-xs text-gray-500">
          <p>SHIVANG PLAGCHECK AI &bull; Academic Similarity, AI-Writing &amp; Citation Integrity Platform</p>
          <p className="mt-1">Powered by Noplag Winnowing, Aegis Integrity Ensemble &amp; RefChecker Verification.</p>
        </footer>
      </body>
    </html>
  );
}
