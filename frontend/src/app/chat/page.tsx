"use client";
import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { MessageSquare, Plus, Trash2, Clock } from "lucide-react";
import { useChatStore } from "@/lib/stores/chatStore";
import { timeAgo } from "@/lib/utils";

export default function ChatIndexPage() {
  const router = useRouter();
  const { conversations, loadConversations, createConversation, deleteConversation } = useChatStore();

  useEffect(() => { loadConversations(); }, []);

  const handleNew = async () => {
    const conv = await createConversation();
    router.push(`/chat/${conv.id}`);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Conversations</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{conversations.length} conversation{conversations.length !== 1 ? "s" : ""}</p>
        </div>
        <button onClick={handleNew} className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-medium transition-colors">
          <Plus className="w-4 h-4" /> New chat
        </button>
      </div>

      {conversations.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 border border-dashed border-border rounded-2xl">
          <MessageSquare className="w-10 h-10 text-muted-foreground mb-3" />
          <h3 className="font-medium mb-1">No conversations yet</h3>
          <p className="text-sm text-muted-foreground mb-4">Start by uploading a PDF and asking a question.</p>
          <button onClick={handleNew} className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-medium transition-colors">
            <Plus className="w-4 h-4" /> Start first conversation
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {conversations.map((conv) => (
            <div key={conv.id} className="group flex items-center gap-3 p-4 rounded-xl border border-border bg-card hover:border-blue-500/30 transition-all">
              <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center shrink-0">
                <MessageSquare className="w-4 h-4 text-violet-400" />
              </div>
              <Link href={`/chat/${conv.id}`} className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{conv.title}</p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Clock className="w-3 h-3 text-muted-foreground" />
                  <p className="text-xs text-muted-foreground">{timeAgo(conv.updated_at)}</p>
                </div>
              </Link>
              <button
                onClick={() => deleteConversation(conv.id)}
                className="opacity-0 group-hover:opacity-100 p-1.5 text-muted-foreground hover:text-destructive transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
