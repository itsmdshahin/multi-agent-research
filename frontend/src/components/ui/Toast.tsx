"use client";
import { useState, useCallback, useEffect } from "react";
import { CheckCircle, XCircle, AlertCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
}

// Global toast queue (singleton pattern)
let _addToast: ((t: Omit<Toast, "id">) => void) | null = null;

export const toast = {
  success: (title: string, message?: string) => _addToast?.({ type: "success", title, message }),
  error: (title: string, message?: string) => _addToast?.({ type: "error", title, message }),
  warning: (title: string, message?: string) => _addToast?.({ type: "warning", title, message }),
  info: (title: string, message?: string) => _addToast?.({ type: "info", title, message }),
};

const ICONS: Record<ToastType, React.ElementType> = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertCircle,
  info: Info,
};

const COLORS: Record<ToastType, string> = {
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  error: "border-red-500/30 bg-red-500/10 text-red-400",
  warning: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  info: "border-blue-500/30 bg-blue-500/10 text-blue-400",
};

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onRemove(toast.id), 4000);
    return () => clearTimeout(timer);
  }, [toast.id]);

  const Icon = ICONS[toast.type];

  return (
    <div className={cn(
      "flex items-start gap-3 p-3.5 rounded-xl border shadow-xl backdrop-blur-sm fade-in max-w-sm",
      "bg-card/95",
      COLORS[toast.type].split(" ")[0], // border color
    )}>
      <Icon className={cn("w-4 h-4 mt-0.5 shrink-0", COLORS[toast.type].split(" ").pop())} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground">{toast.title}</p>
        {toast.message && <p className="text-xs text-muted-foreground mt-0.5">{toast.message}</p>}
      </div>
      <button onClick={() => onRemove(toast.id)} className="text-muted-foreground hover:text-foreground transition-colors shrink-0">
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

export function ToastProvider() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((t: Omit<Toast, "id">) => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev.slice(-4), { ...t, id }]); // max 5
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Register global handler
  useEffect(() => {
    _addToast = addToast;
    return () => { _addToast = null; };
  }, [addToast]);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onRemove={removeToast} />
      ))}
    </div>
  );
}
