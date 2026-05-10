"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, MessageSquare, BookOpen, ArrowRight, Upload, Brain, TrendingUp } from "lucide-react";
import { useAuthStore } from "@/lib/stores/authStore";
import { useChatStore } from "@/lib/stores/chatStore";
import { useDocumentsStore } from "@/lib/stores/documentsStore";
import { reportsApi } from "@/lib/api";
import { timeAgo } from "@/lib/utils";
import type { Report } from "@/types";

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { conversations } = useChatStore();
  const { documents, load } = useDocumentsStore();
  const [reports, setReports] = useState<Report[]>([]);

  useEffect(() => {
    load();
    reportsApi.list().then(setReports).catch(() => {});
  }, []);

  const readyDocs = documents.filter((d) => d.status === "ready").length;
  const stats = [
    { label: "Documents",    value: documents.length, icon: FileText,       color: "text-blue-400",    bg: "bg-blue-500/10 border-blue-500/20" },
    { label: "Conversations",value: conversations.length, icon: MessageSquare, color: "text-violet-400",  bg: "bg-violet-500/10 border-violet-500/20" },
    { label: "Reports",      value: reports.length,   icon: BookOpen,       color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
    { label: "Indexed docs", value: readyDocs,        icon: Brain,          color: "text-cyan-400",    bg: "bg-cyan-500/10 border-cyan-500/20" },
  ];

  const quickActions = [
    { href: "/documents", icon: Upload,       label: "Upload PDF",        desc: "Add documents to your library", color: "hover:border-blue-500/40" },
    { href: "/chat",      icon: MessageSquare,label: "Start chatting",    desc: "Ask questions across your docs", color: "hover:border-violet-500/40" },
    { href: "/reports",   icon: BookOpen,     label: "Generate report",   desc: "Create AI research summaries",  color: "hover:border-emerald-500/40" },
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold">
          Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 18 ? "afternoon" : "evening"},{" "}
          <span className="text-blue-400">{user?.full_name || user?.username}</span>
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Your AI research workspace is ready.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {stats.map((s) => (
          <div key={s.label} className={`p-4 rounded-xl border bg-card ${s.bg} transition-all`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground font-medium">{s.label}</span>
              <s.icon className={`w-4 h-4 ${s.color}`} />
            </div>
            <p className="text-2xl font-semibold">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Quick actions */}
        <div className="lg:col-span-1">
          <h2 className="text-sm font-medium mb-3 text-muted-foreground uppercase tracking-wider">Quick actions</h2>
          <div className="space-y-2">
            {quickActions.map((a) => (
              <Link key={a.href} href={a.href} className={`flex items-center gap-3 p-3.5 rounded-xl border border-border bg-card ${a.color} transition-all group`}>
                <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center shrink-0">
                  <a.icon className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{a.label}</p>
                  <p className="text-xs text-muted-foreground">{a.desc}</p>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground shrink-0" />
              </Link>
            ))}
          </div>
        </div>

        {/* Recent documents */}
        <div className="lg:col-span-1">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Recent documents</h2>
            <Link href="/documents" className="text-xs text-blue-400 hover:text-blue-300 transition-colors">View all</Link>
          </div>
          <div className="space-y-1.5">
            {documents.length === 0 ? (
              <div className="p-4 rounded-xl border border-dashed border-border text-center">
                <FileText className="w-6 h-6 text-muted-foreground mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">No documents yet</p>
              </div>
            ) : (
              documents.slice(0, 5).map((doc) => (
                <div key={doc.id} className="flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-card hover:border-blue-500/30 transition-all">
                  <div className="w-7 h-7 rounded-md bg-blue-500/10 flex items-center justify-center shrink-0">
                    <FileText className="w-3.5 h-3.5 text-blue-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{doc.original_filename}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium status-${doc.status}`}>{doc.status}</span>
                      {doc.page_count && <span className="text-[10px] text-muted-foreground">{doc.page_count}p</span>}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent conversations */}
        <div className="lg:col-span-1">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Recent chats</h2>
            <Link href="/chat" className="text-xs text-blue-400 hover:text-blue-300 transition-colors">View all</Link>
          </div>
          <div className="space-y-1.5">
            {conversations.length === 0 ? (
              <div className="p-4 rounded-xl border border-dashed border-border text-center">
                <MessageSquare className="w-6 h-6 text-muted-foreground mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">No conversations yet</p>
              </div>
            ) : (
              conversations.slice(0, 5).map((conv) => (
                <Link key={conv.id} href={`/chat/${conv.id}`} className="flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-card hover:border-violet-500/30 transition-all">
                  <div className="w-7 h-7 rounded-md bg-violet-500/10 flex items-center justify-center shrink-0">
                    <MessageSquare className="w-3.5 h-3.5 text-violet-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{conv.title}</p>
                    <p className="text-[10px] text-muted-foreground">{timeAgo(conv.updated_at)}</p>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Agent architecture info */}
      <div className="mt-8 p-5 rounded-xl border border-border bg-card">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-medium">Active agent pipeline</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          {[
            ["Planner", "violet"], ["Retrieval", "cyan"], ["Research", "emerald"],
            ["Coding", "amber"], ["Citation", "rose"], ["Web Search", "blue"], ["Memory", "purple"]
          ].map(([name, color]) => (
            <div key={name} className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium bg-${color}-500/10 border-${color}-500/20 text-${color}-400`}>
              <div className={`w-1.5 h-1.5 rounded-full bg-${color}-400`} />
              {name}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
