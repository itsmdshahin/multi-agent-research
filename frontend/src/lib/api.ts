/**
 * Axios API client with JWT auth interceptors.
 * Automatically attaches Bearer tokens and handles 401 refresh.
 */
import axios, { AxiosInstance, AxiosError } from "axios";
import Cookies from "js-cookie";
import type {
  TokenResponse,
  User,
  Document,
  DocumentListResponse,
  Conversation,
  Message,
  Report,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}${API_PREFIX}`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// ─────────────────────── Request interceptor ───────────────────────
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─────────────────────── Response interceptor ───────────────────────
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      const refreshToken = Cookies.get("refresh_token");
      if (refreshToken) {
        try {
          const res = await axios.post<TokenResponse>(
            `${BASE_URL}${API_PREFIX}/auth/refresh`,
            { refresh_token: refreshToken }
          );
          Cookies.set("access_token", res.data.access_token, { expires: 1 });
          Cookies.set("refresh_token", res.data.refresh_token, { expires: 30 });
          error.config!.headers!.Authorization = `Bearer ${res.data.access_token}`;
          return api.request(error.config!);
        } catch {
          Cookies.remove("access_token");
          Cookies.remove("refresh_token");
          window.location.href = "/auth/login";
        }
      } else {
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  }
);

// ─────────────────────── Auth API ───────────────────────

export const authApi = {
  register: async (data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }): Promise<User> => {
    const res = await api.post<User>("/auth/register", data);
    return res.data;
  },

  login: async (email: string, password: string): Promise<TokenResponse> => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);
    const res = await api.post<TokenResponse>("/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    Cookies.set("access_token", res.data.access_token, { expires: 1 });
    Cookies.set("refresh_token", res.data.refresh_token, { expires: 30 });
    return res.data;
  },

  logout: () => {
    Cookies.remove("access_token");
    Cookies.remove("refresh_token");
  },

  me: async (): Promise<User> => {
    const res = await api.get<User>("/auth/me");
    return res.data;
  },
};

// ─────────────────────── Documents API ───────────────────────

export const documentsApi = {
  upload: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await api.post<Document>("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  list: async (page = 1, perPage = 20): Promise<DocumentListResponse> => {
    const res = await api.get<DocumentListResponse>("/documents/", {
      params: { page, per_page: perPage },
    });
    return res.data;
  },

  get: async (id: string): Promise<Document> => {
    const res = await api.get<Document>(`/documents/${id}`);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/documents/${id}`);
  },
};

// ─────────────────────── Chat API ───────────────────────

export const chatApi = {
  createConversation: async (data: {
    title?: string;
    document_ids?: string[];
  }): Promise<Conversation> => {
    const res = await api.post<Conversation>("/chat/conversations", data);
    return res.data;
  },

  listConversations: async (): Promise<Conversation[]> => {
    const res = await api.get<Conversation[]>("/chat/conversations");
    return res.data;
  },

  getMessages: async (conversationId: string): Promise<Message[]> => {
    const res = await api.get<Message[]>(
      `/chat/conversations/${conversationId}/messages`
    );
    return res.data;
  },

  deleteConversation: async (id: string): Promise<void> => {
    await api.delete(`/chat/conversations/${id}`);
  },

  /**
   * Send a message and return an EventSource-compatible fetch stream.
   * Returns the raw Response so callers can read the SSE stream.
   */
  sendMessage: async (payload: {
    conversation_id: string;
    message: string;
    document_ids?: string[];
    enable_web_search?: boolean;
    model?: string;
  }): Promise<Response> => {
    const token = Cookies.get("access_token");
    return fetch(`${BASE_URL}${API_PREFIX}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
  },
};

// ─────────────────────── Reports API ───────────────────────

export const reportsApi = {
  create: async (data: {
    title: string;
    document_ids: string[];
    prompt?: string;
    report_type?: string;
  }): Promise<Report> => {
    const res = await api.post<Report>("/reports/", data);
    return res.data;
  },

  list: async (): Promise<Report[]> => {
    const res = await api.get<Report[]>("/reports/");
    return res.data;
  },

  get: async (id: string): Promise<Report> => {
    const res = await api.get<Report>(`/reports/${id}`);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/reports/${id}`);
  },

  exportMarkdown: async (id: string): Promise<string> => {
    const token = Cookies.get("access_token");
    const res = await fetch(
      `${BASE_URL}${API_PREFIX}/reports/${id}/export/markdown`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return res.text();
  },
};
