import { create } from "zustand";
import type { Document } from "@/types";
import { documentsApi } from "@/lib/api";

interface DocumentsState {
  documents: Document[];
  isLoading: boolean;
  total: number;
  load: (page?: number) => Promise<void>;
  upload: (file: File) => Promise<Document>;
  remove: (id: string) => Promise<void>;
  getById: (id: string) => Document | undefined;
}

export const useDocumentsStore = create<DocumentsState>((set, get) => ({
  documents: [],
  isLoading: false,
  total: 0,

  load: async (page = 1) => {
    set({ isLoading: true });
    try {
      const res = await documentsApi.list(page);
      set({ documents: res.documents, total: res.total, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  upload: async (file) => {
    const doc = await documentsApi.upload(file);
    set((s) => ({ documents: [doc, ...s.documents] }));
    return doc;
  },

  remove: async (id) => {
    await documentsApi.delete(id);
    set((s) => ({ documents: s.documents.filter((d) => d.id !== id) }));
  },

  getById: (id) => get().documents.find((d) => d.id === id),
}));
