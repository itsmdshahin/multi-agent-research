"use client";
import { Brain, User } from "lucide-react";
import type { Message } from "@/types";
import { MarkdownMessage } from "./MarkdownMessage";
import { CitationViewer } from "./CitationViewer";
import { AgentActivityPanel } from "@/components/agents/AgentActivityPanel";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3 py-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center shrink-0 mt-0.5">
          <Brain className="w-3.5 h-3.5 text-blue-400" />
        </div>
      )}

      <div className={cn("max-w-[80%]", isUser ? "items-end" : "items-start", "flex flex-col gap-1")}>
        {/* Agent activities (only for assistant messages) */}
        {!isUser && message.agent_logs && message.agent_logs.length > 0 && (
          <AgentActivityPanel activities={message.agent_logs} isStreaming={false} />
        )}

        {/* Bubble */}
        <div
          className={cn(
            "px-4 py-3 rounded-2xl text-sm",
            isUser
              ? "bg-blue-600 text-white rounded-tr-sm"
              : "bg-card border border-border rounded-tl-sm"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <MarkdownMessage content={message.content} />
          )}
        </div>

        {/* Citations */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <CitationViewer citations={message.citations} />
        )}
      </div>

      {isUser && (
        <div className="w-7 h-7 rounded-full bg-muted border border-border flex items-center justify-center shrink-0 mt-0.5">
          <User className="w-3.5 h-3.5 text-muted-foreground" />
        </div>
      )}
    </div>
  );
}
