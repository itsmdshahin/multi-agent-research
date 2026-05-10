"use client";
import { useEffect, useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import {
  FileText, Upload, Trash2, RefreshCw, Clock,
  CheckCircle, AlertCircle, Loader2, FileSearch
} from "lucide-react";
import { useDocumentsStore } from "@/lib/stores/documentsStore";
import { useChatStore } from "@/lib/stores/chatStore";
import { formatBytes, timeAgo, cn } from "@/lib/utils";
import { useRouter } from "next/navigation";
import type { Document } from "@/types";

function StatusBadge({ status }: { status: Document["status"] }) {
  const icons = {
    pending:    <Clock className="w-2.5 h-2.5" />,
    processing: <Loader2 className="w-2.5 h-2.5 animate-spin" />,
    ready:      <CheckCircle className="w-2.5 h-2.5" />,
    failed:     <AlertCircle className="w-2.5 h-2.5" />,
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium status-${status}`}>
      {icons[status]} {status}
    </span>
  );
}

export default function DocumentsPage() {
  const { documents, isLoading, load, upload, remove } = useDocumentsStore();
  const { createConversation } = useChatStore();
  const router = useRouter();
  const [uploading, setUploading] = useState<string[]>([]);
  const [pollTimer, setPollTimer] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    load();
    // Poll while any document is processing
    const timer = setInterval(() => {
      const hasProcessing = useDocumentsStore.getState().documents.some(
        (d) => d.status === "pending" || d.status === "processing"
      );
      if (hasProcessing) load();
    }, 4000);
    setPollTimer(timer);
    return () => clearInterval(timer);
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      setUploading((u) => [...u, file.name]);
      try {
        await upload(file);
      } finally {
        setUploading((u) => u.filter((n) => n !== file.name));
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxSize: 50 * 1024 * 1024,
  });

  const handleChatWithDoc = async (doc: Document) => {
    const conv = await createConversation(`Chat: ${doc.original_filename}`, [doc.id]);
    router.push(`/chat/${conv.id}`);
  };

  const readyCount = documents.filter((d) => d.status === "ready").length;
  const processingCount = documents.filter((d) => d.status === "processing" || d.status === "pending").length;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Documents</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {readyCount} indexed · {processingCount > 0 ? `${processingCount} processing` : "0 processing"}
          </p>
        </div>
        <button onClick={() => load()} className="flex items-center gap-1.5 px-3 py-1.5 border border-border rounded-lg text-xs text-muted-foreground hover:text-foreground transition-colors">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Upload zone */}
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all mb-6",
          isDragActive
            ? "border-blue-500/60 bg-blue-500/5"
            : "border-border hover:border-blue-500/40 hover:bg-blue-500/3"
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          <div className={cn(
            "w-12 h-12 rounded-2xl flex items-center justify-center transition-colors",
            isDragActive ? "bg-blue-500/20 border border-blue-500/30" : "bg-muted border border-border"
          )}>
            <Upload className={cn("w-5 h-5 transition-colors", isDragActive ? "text-blue-400" : "text-muted-foreground")} />
          </div>
          <div>
            <p className="text-sm font-medium">{isDragActive ? "Drop your PDFs here" : "Upload PDF documents"}</p>
            <p className="text-xs text-muted-foreground mt-1">Drag & drop or click to select · Max 50MB per file</p>
          </div>
        </div>
      </div>

      {/* Uploading indicators */}
      {uploading.length > 0 && (
        <div className="mb-4 space-y-2">
          {uploading.map((name) => (
            <div key={name} className="flex items-center gap-3 p-3 rounded-xl bg-blue-500/5 border border-blue-500/20">
              <Loader2 className="w-4 h-4 text-blue-400 animate-spin shrink-0" />
              <span className="text-sm text-blue-400 truncate">Uploading {name}…</span>
            </div>
          ))}
        </div>
      )}

      {/* Document list */}
      {isLoading && documents.length === 0 ? (
        <div className="space-y-2">
          {[1,2,3].map((i) => (
            <div key={i} className="h-16 rounded-xl shimmer" />
          ))}
        </div>
      ) : documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <FileText className="w-10 h-10 text-muted-foreground mb-3" />
          <h3 className="font-medium mb-1">No documents yet</h3>
          <p className="text-sm text-muted-foreground">Upload your first PDF to get started.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <div key={doc.id} className="group flex items-center gap-3 p-4 rounded-xl border border-border bg-card hover:border-blue-500/20 transition-all">
              <div className="w-9 h-9 rounded-xl bg-blue-500/10 flex items-center justify-center shrink-0">
                <FileText className="w-4.5 h-4.5 text-blue-400" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-sm font-medium truncate max-w-xs">{doc.original_filename}</p>
                  <StatusBadge status={doc.status} />
                </div>
                <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                  <span>{formatBytes(doc.file_size)}</span>
                  {doc.page_count && <span>{doc.page_count} pages</span>}
                  {doc.chunk_count && <span>{doc.chunk_count} chunks</span>}
                  {doc.word_count && <span>{doc.word_count.toLocaleString()} words</span>}
                  <span>{timeAgo(doc.created_at)}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {doc.status === "ready" && (
                  <button
                    onClick={() => handleChatWithDoc(doc)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600/15 border border-blue-500/30 text-blue-400 hover:bg-blue-600/25 rounded-lg text-xs font-medium transition-colors"
                  >
                    <FileSearch className="w-3.5 h-3.5" /> Chat
                  </button>
                )}
                <button
                  onClick={() => remove(doc.id)}
                  className="p-1.5 text-muted-foreground hover:text-destructive transition-colors rounded-lg hover:bg-destructive/10"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
