/**
 * useStream — manages SSE streaming state.
 * Provides helpers to parse and accumulate stream events from the backend.
 */
"use client";
import { useState, useCallback, useRef } from "react";
import type { AgentActivity, Citation, StreamEvent } from "@/types";

interface StreamState {
  isStreaming: boolean;
  content: string;
  activities: AgentActivity[];
  citations: Citation[];
  error: string | null;
  messageId: string | null;
}

interface UseStreamReturn extends StreamState {
  startStream: (responsePromise: Promise<Response>) => Promise<void>;
  reset: () => void;
}

const INITIAL_STATE: StreamState = {
  isStreaming: false,
  content: "",
  activities: [],
  citations: [],
  error: null,
  messageId: null,
};

export function useStream(): UseStreamReturn {
  const [state, setState] = useState<StreamState>(INITIAL_STATE);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState(INITIAL_STATE);
  }, []);

  const startStream = useCallback(async (responsePromise: Promise<Response>) => {
    setState({ ...INITIAL_STATE, isStreaming: true });

    try {
      const response = await responsePromise;
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: "Stream failed" }));
        setState((s) => ({ ...s, isStreaming: false, error: err.detail || "Request failed" }));
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        setState((s) => ({ ...s, isStreaming: false, error: "No response stream" }));
        return;
      }

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
            handleEvent(event);
          } catch {
            // Malformed SSE line — skip
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name !== "AbortError") {
        setState((s) => ({ ...s, isStreaming: false, error: err.message }));
      }
    }
  }, []);

  function handleEvent(event: StreamEvent) {
    switch (event.type) {
      case "agent_activity":
        setState((s) => ({
          ...s,
          activities: [...s.activities, event.data as AgentActivity],
        }));
        break;
      case "citations":
        setState((s) => ({ ...s, citations: event.data as Citation[] }));
        break;
      case "response":
        setState((s) => ({ ...s, content: event.content || "" }));
        break;
      case "done":
        setState((s) => ({
          ...s,
          isStreaming: false,
          messageId: event.message_id || null,
        }));
        break;
      case "error":
        setState((s) => ({
          ...s,
          isStreaming: false,
          error: event.message || "Unknown stream error",
        }));
        break;
    }
  }

  return { ...state, startStream, reset };
}
