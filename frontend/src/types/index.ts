// Core API types matching backend Pydantic schemas

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  status: "pending" | "processing" | "ready" | "failed";
  page_count?: number;
  word_count?: number;
  chunk_count?: number;
  doc_meta?: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  per_page: number;
}

export interface Citation {
  document_id: string;
  document_name: string;
  page_number: number;
  excerpt: string;
  similarity_score?: number;
}

export interface AgentActivity {
  agent: string;
  action: string;
  status: "running" | "done" | "error";
  detail?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: Citation[];
  agent_logs?: AgentActivity[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  description?: string;
  meta?: Record<string, unknown>;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface Report {
  id: string;
  title: string;
  report_type: string;
  content?: string;
  markdown_content?: string;
  status: "generating" | "ready" | "failed";
  document_ids?: string[];
  created_at: string;
  updated_at: string;
}

// SSE stream event shapes
export interface StreamEvent {
  type: "agent_activity" | "citations" | "response" | "done" | "error";
  data?: AgentActivity | Citation[];
  content?: string;
  message_id?: string;
  message?: string;
}
