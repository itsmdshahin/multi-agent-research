import { create } from "zustand";
import type { Report } from "@/types";
import { reportsApi } from "@/lib/api";

interface ReportsState {
  reports: Report[];
  isLoading: boolean;
  load: () => Promise<void>;
  create: (data: {
    title: string;
    document_ids: string[];
    prompt?: string;
    report_type?: string;
  }) => Promise<Report>;
  remove: (id: string) => Promise<void>;
  pollUntilReady: (id: string, onUpdate: (r: Report) => void) => void;
}

export const useReportsStore = create<ReportsState>((set, get) => ({
  reports: [],
  isLoading: false,

  load: async () => {
    set({ isLoading: true });
    try {
      const data = await reportsApi.list();
      set({ reports: data });
    } finally {
      set({ isLoading: false });
    }
  },

  create: async (data) => {
    const report = await reportsApi.create(data);
    set((s) => ({ reports: [report, ...s.reports] }));
    return report;
  },

  remove: async (id) => {
    await reportsApi.delete(id);
    set((s) => ({ reports: s.reports.filter((r) => r.id !== id) }));
  },

  pollUntilReady: (id, onUpdate) => {
    const poll = setInterval(async () => {
      try {
        const report = await reportsApi.get(id);
        onUpdate(report);
        // Update in store
        set((s) => ({
          reports: s.reports.map((r) => (r.id === id ? report : r)),
        }));
        if (report.status !== "generating") {
          clearInterval(poll);
        }
      } catch {
        clearInterval(poll);
      }
    }, 3000);
    // Auto-clear after 5 minutes
    setTimeout(() => clearInterval(poll), 5 * 60 * 1000);
  },
}));
