"use client";
import { useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { Brain, MessageSquare } from "lucide-react";
import { useChatStore } from "@/lib/stores/chatStore";
import { useDocumentsStore } from "@/lib/stores/documentsStore";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { AgentActivityPanel } from "@/components/agents/AgentActivityPanel";
import { MarkdownMessage } from "@/components/chat/MarkdownMessage";
import { CitationViewer } from "@/components/chat/CitationViewer";

export default function ChatConversationPage() {
  const { id } = useParams<{ id: string }>();
  const {
    messages, loadMessages, sendMessage,
    isStreaming, streamingContent, streamingActivities, streamingCitations,
    conversations,
  } = useChatStore();
  const { load } = useDocumentsStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  const conv = conversations.find((c) => c.id === id);
  const convMessages = messages[id] || [];

  useEffect(() => {
    if (id) {
      loadMessages(id);
      load();
    }
  }, [id]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [convMessages.length, streamingContent]);

  const handleSend = async (text: string, docIds: string[], webSearch: boolean) => {
    const convDocIds = ((conv?.meta as { document_ids?: string[] })?.document_ids) || [];
    await sendMessage(id, text, [...convDocIds, ...docIds], webSearch);
  };

  const convDocIds = ((conv?.meta as { document_ids?: string[] })?.document_ids) || [];

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="h-14 border-b border-border bg-card/60 backdrop-blur flex items-center px-6 shrink-0">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium truncate max-w-md">{conv?.title || "Conversation"}</span>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-3xl mx-auto">
          {convMessages.length === 0 && !isStreaming && (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <div className="w-12 h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4">
                <Brain className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="font-medium mb-1">Start your research</h3>
              <p className="text-sm text-muted-foreground max-w-xs">
                Ask any question about your documents. The AI agents will retrieve, analyze, and cite relevant sources.
              </p>
            </div>
          )}

          {convMessages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* Streaming response */}
          {isStreaming && (
            <div className="flex gap-3 py-3">
              <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center shrink-0 mt-0.5">
                <Brain className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <div className="flex-1 max-w-[80%]">
                <AgentActivityPanel activities={streamingActivities} isStreaming={isStreaming} />
                {streamingContent ? (
                  <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-card border border-border text-sm">
                    <MarkdownMessage content={streamingContent} />
                    <span className="inline-block w-0.5 h-4 bg-blue-400 ml-0.5 cursor-blink" />
                  </div>
                ) : (
                  <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-card border border-border">
                    <div className="flex gap-1 items-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                )}
                {streamingCitations.length > 0 && (
                  <CitationViewer citations={streamingCitations} />
                )}
              </div>
            </div>
          )}
          <div ref={scrollRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-border bg-background/80 backdrop-blur px-6 py-4 shrink-0">
        <div className="max-w-3xl mx-auto">
          <ChatInput
            onSend={handleSend}
            isStreaming={isStreaming}
            defaultDocumentIds={convDocIds}
          />
        </div>
      </div>
    </div>
  );
}
