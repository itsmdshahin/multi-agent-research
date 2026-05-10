/**
 * useDocumentPoller — polls document status while any are processing.
 * Call once in a page that shows documents; auto-stops when all are ready.
 */
"use client";
import { useEffect, useRef } from "react";
import { useDocumentsStore } from "@/lib/stores/documentsStore";

export function useDocumentPoller(intervalMs = 4000) {
  const { documents, load } = useDocumentsStore();
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const hasProcessing = documents.some(
      (d) => d.status === "pending" || d.status === "processing"
    );

    if (hasProcessing && !timerRef.current) {
      timerRef.current = setInterval(() => {
        const stillProcessing = useDocumentsStore
          .getState()
          .documents.some((d) => d.status === "pending" || d.status === "processing");

        if (stillProcessing) {
          load();
        } else {
          if (timerRef.current) clearInterval(timerRef.current);
          timerRef.current = null;
        }
      }, intervalMs);
    }

    if (!hasProcessing && timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [documents]);
}
