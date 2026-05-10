"use client";
import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Send, Globe, FileText, Loader2, X, ChevronDown } from "lucide-react";
import { useDocumentsStore } from "@/lib/stores/documentsStore";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string, docIds: string[], webSearch: boolean) => void;
  isStreaming: boolean;
  defaultDocumentIds?: string[];
}

export function ChatInput({ onSend, isStreaming, defaultDocumentIds = [] }: ChatInputProps) {
  const [value, setValue] = useState("");
  const [webSearch, setWebSearch] = useState(false);
  const [docPickerOpen, setDocPickerOpen] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState<string[]>(defaultDocumentIds);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { documents } = useDocumentsStore();
  const readyDocs = documents.filter((d) => d.status === "ready");

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
  }, [value]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed, selectedDocs, webSearch);
    setValue("");
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleDoc = (id: string) => {
    setSelectedDocs((prev) => prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]);
  };

  return (
    <div className="relative">
      {/* Document picker dropdown */}
      {docPickerOpen && readyDocs.length > 0 && (
        <div className="absolute bottom-full mb-2 left-0 right-0 bg-card border border-border rounded-xl shadow-xl overflow-hidden z-10 fade-in">
          <div className="p-2 border-b border-border flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-medium">Select documents to search</span>
            <button onClick={() => setDocPickerOpen(false)} className="text-muted-foreground hover:text-foreground">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="max-h-48 overflow-y-auto p-1.5 space-y-0.5">
            {readyDocs.map((doc) => (
              <label key={doc.id} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-muted cursor-pointer transition-colors">
                <input
                  type="checkbox"
                  checked={selectedDocs.includes(doc.id)}
                  onChange={() => toggleDoc(doc.id)}
                  className="rounded border-border accent-blue-500"
                />
                <FileText className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span className="text-xs text-foreground truncate flex-1">{doc.original_filename}</span>
                {doc.page_count && <span className="text-[10px] text-muted-foreground shrink-0">{doc.page_count}p</span>}
              </label>
            ))}
          </div>
          {selectedDocs.length > 0 && (
            <div className="px-3 py-2 border-t border-border flex items-center justify-between">
              <span className="text-[11px] text-blue-400">{selectedDocs.length} selected</span>
              <button onClick={() => setSelectedDocs([])} className="text-[11px] text-muted-foreground hover:text-foreground">Clear</button>
            </div>
          )}
        </div>
      )}

      {/* Main input area */}
      <div className="border border-border bg-card rounded-2xl overflow-hidden focus-within:ring-1 focus-within:ring-ring focus-within:border-ring transition-all">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKey}
          placeholder={isStreaming ? "Agents are working…" : "Ask anything about your documents…"}
          disabled={isStreaming}
          rows={1}
          className="w-full px-4 pt-3.5 pb-2 bg-transparent text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none disabled:opacity-60"
          style={{ maxHeight: "200px" }}
        />

        {/* Toolbar */}
        <div className="px-3 pb-2.5 flex items-center justify-between">
          <div className="flex items-center gap-1">
            {/* Document selector */}
            <button
              onClick={() => setDocPickerOpen((o) => !o)}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all",
                selectedDocs.length > 0
                  ? "bg-blue-500/15 text-blue-400 border border-blue-500/30"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
            >
              <FileText className="w-3.5 h-3.5" />
              {selectedDocs.length > 0 ? `${selectedDocs.length} doc${selectedDocs.length !== 1 ? "s" : ""}` : "Docs"}
              <ChevronDown className="w-3 h-3" />
            </button>

            {/* Web search toggle */}
            <button
              onClick={() => setWebSearch((w) => !w)}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all",
                webSearch
                  ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
            >
              <Globe className="w-3.5 h-3.5" />
              Web
            </button>
          </div>

          {/* Send button */}
          <button
            onClick={handleSend}
            disabled={!value.trim() || isStreaming}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg text-xs font-medium transition-colors"
          >
            {isStreaming ? (
              <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Working…</>
            ) : (
              <><Send className="w-3.5 h-3.5" /> Send</>
            )}
          </button>
        </div>
      </div>
      <p className="text-center text-[10px] text-muted-foreground mt-1.5">⏎ to send · Shift+⏎ for new line</p>
    </div>
  );
}
