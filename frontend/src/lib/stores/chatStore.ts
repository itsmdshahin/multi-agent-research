import { create } from "zustand";
import type { Conversation, Message, Citation, AgentActivity, StreamEvent } from "@/types";
import { chatApi } from "@/lib/api";

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Record<string, Message[]>;
  isStreaming: boolean;
  streamingContent: string;
  streamingActivities: AgentActivity[];
  streamingCitations: Citation[];

  // Actions
  loadConversations: () => Promise<void>;
  setActiveConversation: (id: string) => void;
  createConversation: (title?: string, documentIds?: string[]) => Promise<Conversation>;
  loadMessages: (conversationId: string) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  sendMessage: (
    conversationId: string,
    content: string,
    documentIds?: string[],
    enableWebSearch?: boolean
  ) => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: {},
  isStreaming: false,
  streamingContent: "",
  streamingActivities: [],
  streamingCitations: [],

  loadConversations: async () => {
    const convs = await chatApi.listConversations();
    set({ conversations: convs });
  },

  setActiveConversation: (id) => set({ activeConversationId: id }),

  createConversation: async (title = "New Conversation", documentIds = []) => {
    const conv = await chatApi.createConversation({ title, document_ids: documentIds });
    set((s) => ({ conversations: [conv, ...s.conversations], activeConversationId: conv.id }));
    return conv;
  },

  loadMessages: async (conversationId) => {
    const msgs = await chatApi.getMessages(conversationId);
    set((s) => ({ messages: { ...s.messages, [conversationId]: msgs } }));
  },

  deleteConversation: async (id) => {
    await chatApi.deleteConversation(id);
    set((s) => ({
      conversations: s.conversations.filter((c) => c.id !== id),
      activeConversationId: s.activeConversationId === id ? null : s.activeConversationId,
    }));
  },

  sendMessage: async (conversationId, content, documentIds = [], enableWebSearch = false) => {
    // Optimistically add user message
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    set((s) => ({
      messages: {
        ...s.messages,
        [conversationId]: [...(s.messages[conversationId] || []), userMsg],
      },
      isStreaming: true,
      streamingContent: "",
      streamingActivities: [],
      streamingCitations: [],
    }));

    try {
      const response = await chatApi.sendMessage({
        conversation_id: conversationId,
        message: content,
        document_ids: documentIds,
        enable_web_search: enableWebSearch,
      });

      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event: StreamEvent = JSON.parse(line.slice(6));

            if (event.type === "agent_activity") {
              set((s) => ({
                streamingActivities: [...s.streamingActivities, event.data as AgentActivity],
              }));
            } else if (event.type === "citations") {
              set({ streamingCitations: event.data as Citation[] });
            } else if (event.type === "response") {
              set({ streamingContent: event.content || "" });
            } else if (event.type === "done") {
              // Replace streaming with persisted assistant message
              const finalMsg: Message = {
                id: event.message_id || crypto.randomUUID(),
                role: "assistant",
                content: get().streamingContent,
                citations: get().streamingCitations,
                agent_logs: get().streamingActivities,
                created_at: new Date().toISOString(),
              };
              set((s) => ({
                isStreaming: false,
                messages: {
                  ...s.messages,
                  [conversationId]: [...(s.messages[conversationId] || []), finalMsg],
                },
                // Update conversation title
                conversations: s.conversations.map((c) =>
                  c.id === conversationId
                    ? { ...c, title: content.slice(0, 60) + (content.length > 60 ? "…" : "") }
                    : c
                ),
              }));
            } else if (event.type === "error") {
              throw new Error(event.message || "Stream error");
            }
          } catch {}
        }
      }
    } catch (err) {
      set({ isStreaming: false });
      throw err;
    }
  },
}));
