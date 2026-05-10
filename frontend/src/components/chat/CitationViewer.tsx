"use client";
import { useState } from "react";
import { BookOpen, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import type { Citation } from "@/types";
import { cn } from "@/lib/utils";

export function CitationViewer({ citations }: { citations: Citation[] }) {
  const [open, setOpen] = useState(false);
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
      >
        <BookOpen className="w-3 h-3" />
        <span>{citations.length} source{citations.length !== 1 ? "s" : ""}</span>
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>

      {open && (
        <div className="mt-2 space-y-1.5 fade-in">
          {citations.map((c, i) => (
            <div key={i} className="flex gap-2 p-2.5 rounded-lg border border-border bg-muted/40 text-xs">
              <span className="text-[10px] font-mono text-muted-foreground mt-0.5 shrink-0 w-4">[{i + 1}]</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
                  <span className="font-medium text-foreground truncate max-w-[200px]">{c.document_name}</span>
                  <span className="text-muted-foreground">·</span>
                  <span className="text-muted-foreground">Page {c.page_number}</span>
                  {c.similarity_score !== undefined && (
                    <>
                      <span className="text-muted-foreground">·</span>
                      <span className={cn(
                        "font-medium",
                        c.similarity_score > 0.85 ? "text-emerald-400" :
                        c.similarity_score > 0.7  ? "text-blue-400" : "text-amber-400"
                      )}>
                        {(c.similarity_score * 100).toFixed(0)}% match
                      </span>
                    </>
                  )}
                </div>
                {c.excerpt && (
                  <p className="text-muted-foreground leading-relaxed line-clamp-2">{c.excerpt}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
