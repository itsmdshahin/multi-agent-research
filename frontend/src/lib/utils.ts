import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatDistanceToNow } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function timeAgo(date: string): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}

export function truncate(str: string, n: number): string {
  return str.length > n ? str.slice(0, n) + "…" : str;
}

export const agentColors: Record<string, string> = {
  planner:    "text-violet-400",
  retrieval:  "text-cyan-400",
  research:   "text-emerald-400",
  coding:     "text-amber-400",
  citation:   "text-rose-400",
  web_search: "text-blue-400",
  memory:     "text-purple-400",
  synthesizer:"text-indigo-400",
};

export const agentLabels: Record<string, string> = {
  planner:    "Planner",
  retrieval:  "Retrieval",
  research:   "Research",
  coding:     "Coding",
  citation:   "Citation",
  web_search: "Web Search",
  memory:     "Memory",
  synthesizer:"Synthesizer",
};
