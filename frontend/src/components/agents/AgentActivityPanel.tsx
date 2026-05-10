"use client";
import { cn, agentColors, agentLabels } from "@/lib/utils";
import type { AgentActivity } from "@/types";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

interface AgentActivityPanelProps {
  activities: AgentActivity[];
  isStreaming: boolean;
}

export function AgentActivityPanel({ activities, isStreaming }: AgentActivityPanelProps) {
  if (activities.length === 0 && !isStreaming) return null;

  return (
    <div className="px-3 py-2 bg-muted/50 border border-border rounded-xl text-xs mb-2">
      <p className="text-muted-foreground font-medium mb-1.5 uppercase tracking-wider text-[10px]">Agent workflow</p>
      <div className="space-y-1">
        {activities.map((a, i) => (
          <div key={i} className="flex items-center gap-2">
            {a.status === "running" ? (
              <Loader2 className="w-3 h-3 animate-spin text-blue-400 shrink-0" />
            ) : a.status === "done" ? (
              <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" />
            ) : (
              <XCircle className="w-3 h-3 text-destructive shrink-0" />
            )}
            <span className={cn("font-medium", agentColors[a.agent] || "text-foreground")}>
              {agentLabels[a.agent] || a.agent}
            </span>
            <span className="text-muted-foreground">—</span>
            <span className="text-muted-foreground truncate">{a.detail || a.action}</span>
          </div>
        ))}
        {isStreaming && activities.every((a) => a.status !== "running") && (
          <div className="flex items-center gap-2">
            <Loader2 className="w-3 h-3 animate-spin text-blue-400 shrink-0" />
            <span className="text-muted-foreground">Processing…</span>
          </div>
        )}
      </div>
    </div>
  );
}
