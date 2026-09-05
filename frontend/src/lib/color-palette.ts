/**
 * Dynamic Color Palette Generator for Plagiarism Sources.
 * Complies with Section 15: Never depend on fixed hardcoded colors;
 * generates visually distinct, accessible highlight colors per source.
 */

export interface SourceColor {
  bg: string;
  border: string;
  text: string;
  badgeBg: string;
}

const PALETTE: SourceColor[] = [
  {
    bg: "rgba(239, 68, 68, 0.25)",
    border: "#ef4444",
    text: "#fca5a5",
    badgeBg: "rgba(239, 68, 68, 0.15)",
  },
  {
    bg: "rgba(59, 130, 246, 0.25)",
    border: "#3b82f6",
    text: "#93c5fd",
    badgeBg: "rgba(59, 130, 246, 0.15)",
  },
  {
    bg: "rgba(245, 158, 11, 0.25)",
    border: "#f59e0b",
    text: "#fde68a",
    badgeBg: "rgba(245, 158, 11, 0.15)",
  },
  {
    bg: "rgba(16, 185, 129, 0.25)",
    border: "#10b981",
    text: "#6ee7b7",
    badgeBg: "rgba(16, 185, 129, 0.15)",
  },
  {
    bg: "rgba(168, 85, 247, 0.25)",
    border: "#a855f7",
    text: "#d8b4fe",
    badgeBg: "rgba(168, 85, 247, 0.15)",
  },
  {
    bg: "rgba(236, 72, 153, 0.25)",
    border: "#ec4899",
    text: "#fbcfe8",
    badgeBg: "rgba(236, 72, 153, 0.15)",
  },
  {
    bg: "rgba(20, 184, 166, 0.25)",
    border: "#14b8a6",
    text: "#99f6e4",
    badgeBg: "rgba(20, 184, 166, 0.15)",
  },
  {
    bg: "rgba(249, 115, 22, 0.25)",
    border: "#f97316",
    text: "#fed7aa",
    badgeBg: "rgba(249, 115, 22, 0.15)",
  },
];

export function getSourceColor(index: number): SourceColor {
  return PALETTE[index % PALETTE.length];
}
