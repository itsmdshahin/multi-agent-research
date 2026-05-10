"use client";
import { useEffect, useState } from "react";
import {
  BookOpen, Plus, Download, Loader2, CheckCircle,
  AlertCircle, Clock, Trash2, FileText, X
} from "lucide-react";
import { reportsApi } from "@/lib/api";
import { useDocumentsStore } from "@/lib/stores/documentsStore";
import { timeAgo, cn } from "@/lib/utils";
import type { Report } from "@/types";
import { MarkdownMessage } from "@/components/chat/MarkdownMessage";

function ReportStatusIcon({ status }: { status: Report["status"] }) {
  if (status === "generating") return <Loader2 className="w-3.5 h-3.5 animate-spin text-violet-400" />;
  if (status === "ready") return <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />;
  return <AlertCircle className="w-3.5 h-3.5 text-destructive" />;
}

function NewReportModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const { documents, load } = useDocumentsStore();
  const [form, setForm] = useState({
    title: "",
    report_type: "research_summary",
    prompt: "",
    document_ids: [] as string[],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { load(); }, []);
  const readyDocs = documents.filter((d) => d.status === "ready");

  const toggleDoc = (id: string) => {
    setForm((f) => ({
      ...f,
      document_ids: f.document_ids.includes(id)
        ? f.document_ids.filter((d) => d !== id)
        : [...f.document_ids, id],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.document_ids.length === 0) { setError("Select at least one document"); return; }
    if (!form.title.trim()) { setError("Report title is required"); return; }
    setLoading(true);
    try {
      await reportsApi.create(form);
      onCreated();
      onClose();
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to create report");
    } finally { setLoading(false); }
  };

  const types = [
    { value: "research_summary", label: "Research Summary" },
    { value: "comparison",       label: "Comparison Report" },
    { value: "technical",        label: "Technical Deep-Dive" },
  ];

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-2xl w-full max-w-lg shadow-2xl fade-in">
        <div className="flex items-center justify-between p-5 border-b border-border">
          <h2 className="font-semibold">Generate research report</h2>
          <button onClick={onClose} className="p-1 text-muted-foreground hover:text-foreground transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/30 text-destructive text-sm">
              <AlertCircle className="w-4 h-4" /> {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1.5">Report title</label>
            <input
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="e.g. Comparison of attention mechanisms"
              className="w-full px-3 py-2 rounded-lg bg-input border border-border text-sm focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1.5">Report type</label>
            <select
              value={form.report_type}
              onChange={(e) => setForm((f) => ({ ...f, report_type: e.target.value }))}
              className="w-full px-3 py-2 rounded-lg bg-input border border-border text-sm focus:outline-none focus:ring-1 focus:ring-ring"
            >
              {types.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1.5">Custom instructions (optional)</label>
            <textarea
              value={form.prompt}
              onChange={(e) => setForm((f) => ({ ...f, prompt: e.target.value }))}
              placeholder="Focus on experimental results and limitations…"
              rows={2}
              className="w-full px-3 py-2 rounded-lg bg-input border border-border text-sm focus:outline-none focus:ring-1 focus:ring-ring resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
              Documents ({form.document_ids.length} selected)
            </label>
            {readyDocs.length === 0 ? (
              <p className="text-xs text-muted-foreground p-3 bg-muted rounded-lg">No indexed documents. Upload PDFs first.</p>
            ) : (
              <div className="max-h-40 overflow-y-auto rounded-lg border border-border divide-y divide-border">
                {readyDocs.map((doc) => (
                  <label key={doc.id} className="flex items-center gap-2.5 px-3 py-2 hover:bg-muted cursor-pointer transition-colors">
                    <input type="checkbox" checked={form.document_ids.includes(doc.id)} onChange={() => toggleDoc(doc.id)} className="accent-blue-500" />
                    <FileText className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                    <span className="text-xs truncate flex-1">{doc.original_filename}</span>
                    <span className="text-[10px] text-muted-foreground shrink-0">{doc.page_count}p</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 border border-border rounded-xl text-sm hover:bg-muted transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white rounded-xl text-sm font-medium transition-colors">
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {loading ? "Generating…" : "Generate report"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  const loadReports = async () => {
    try {
      const data = await reportsApi.list();
      setReports(data);
    } finally { setLoading(false); }
  };

  useEffect(() => {
    loadReports();
    const timer = setInterval(() => {
      if (reports.some((r) => r.status === "generating")) loadReports();
    }, 5000);
    return () => clearInterval(timer);
  }, [reports.length]);

  const handleExport = async (report: Report) => {
    const md = await reportsApi.exportMarkdown(report.id);
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${report.title}.md`; a.click();
    URL.revokeObjectURL(url);
  };

  const handleDelete = async (id: string) => {
    await reportsApi.delete(id);
    setReports((r) => r.filter((rep) => rep.id !== id));
    if (selectedReport?.id === id) setSelectedReport(null);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {showModal && (
        <NewReportModal onClose={() => setShowModal(false)} onCreated={loadReports} />
      )}

      {/* List panel */}
      <div className={cn("flex flex-col border-r border-border bg-card", selectedReport ? "w-72 shrink-0" : "flex-1")}>
        <div className="p-4 border-b border-border flex items-center justify-between shrink-0">
          <div>
            <h1 className="text-base font-semibold">Reports</h1>
            <p className="text-xs text-muted-foreground">{reports.length} report{reports.length !== 1 ? "s" : ""}</p>
          </div>
          <button onClick={() => setShowModal(true)} className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors">
            <Plus className="w-3.5 h-3.5" /> New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
          {loading ? (
            [1,2,3].map((i) => <div key={i} className="h-16 rounded-xl shimmer" />)
          ) : reports.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-center">
              <BookOpen className="w-8 h-8 text-muted-foreground mb-2" />
              <p className="text-sm font-medium mb-1">No reports yet</p>
              <p className="text-xs text-muted-foreground">Generate your first AI research report.</p>
            </div>
          ) : (
            reports.map((r) => (
              <div
                key={r.id}
                onClick={() => setSelectedReport(r)}
                className={cn(
                  "group p-3 rounded-xl border cursor-pointer transition-all",
                  selectedReport?.id === r.id
                    ? "border-blue-500/40 bg-blue-500/10"
                    : "border-border bg-card hover:border-blue-500/20 hover:bg-muted/40"
                )}
              >
                <div className="flex items-start gap-2">
                  <ReportStatusIcon status={r.status} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{r.title}</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5 capitalize">{r.report_type.replace("_", " ")}</p>
                    <p className="text-[10px] text-muted-foreground">{timeAgo(r.created_at)}</p>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(r.id); }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-muted-foreground hover:text-destructive transition-all"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Report viewer */}
      {selectedReport && (
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-border flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2 min-w-0">
              <ReportStatusIcon status={selectedReport.status} />
              <h2 className="font-semibold truncate">{selectedReport.title}</h2>
              <span className={`text-xs px-2 py-0.5 rounded-full status-${selectedReport.status} shrink-0`}>{selectedReport.status}</span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {selectedReport.status === "ready" && (
                <button onClick={() => handleExport(selectedReport)} className="flex items-center gap-1.5 px-3 py-1.5 border border-border rounded-lg text-xs hover:bg-muted transition-colors">
                  <Download className="w-3.5 h-3.5" /> Export MD
                </button>
              )}
              <button onClick={() => setSelectedReport(null)} className="p-1.5 text-muted-foreground hover:text-foreground transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-6">
            {selectedReport.status === "generating" ? (
              <div className="flex flex-col items-center justify-center h-48">
                <Loader2 className="w-8 h-8 text-violet-400 animate-spin mb-3" />
                <p className="text-sm font-medium">Generating report…</p>
                <p className="text-xs text-muted-foreground mt-1">AI agents are analyzing your documents</p>
              </div>
            ) : selectedReport.status === "failed" ? (
              <div className="flex flex-col items-center justify-center h-48">
                <AlertCircle className="w-8 h-8 text-destructive mb-3" />
                <p className="text-sm font-medium">Generation failed</p>
              </div>
            ) : (
              <div className="max-w-3xl">
                <MarkdownMessage content={selectedReport.markdown_content || selectedReport.content || ""} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
