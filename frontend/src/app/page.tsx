"use client";
import Link from "next/link";
import {
  Brain, FileText, Search, Zap, Shield, GitBranch,
  ArrowRight, ChevronRight, Sparkles, Database, Globe
} from "lucide-react";

const features = [
  { icon: Brain, title: "Multi-Agent Orchestration", desc: "LangGraph-powered agents — Planner, Retrieval, Research, Coding, Citation — working in concert to handle complex queries.", color: "text-blue-400" },
  { icon: FileText, title: "Multi-PDF Chat", desc: "Upload dozens of research papers and chat across all of them simultaneously. Compare methodologies, extract findings, generate summaries.", color: "text-violet-400" },
  { icon: Database, title: "Vector RAG", desc: "Qdrant-powered semantic search with hybrid retrieval, context compression, and cosine reranking for pinpoint accuracy.", color: "text-cyan-400" },
  { icon: Globe, title: "Web Search Integration", desc: "Blend uploaded document context with live web search via Tavily to get answers grounded in both your files and the internet.", color: "text-emerald-400" },
  { icon: Zap, title: "Streaming Responses", desc: "Token-by-token streaming via SSE with live agent-activity panels so you see exactly what each agent is doing in real time.", color: "text-amber-400" },
  { icon: Shield, title: "Citation Tracking", desc: "Every answer is backed by source citations with document name, page number, and relevance score — no hallucinations.", color: "text-rose-400" },
];

const stack = [
  "FastAPI", "LangGraph", "LangChain", "Qdrant", "PostgreSQL",
  "Redis", "OpenAI", "Claude", "PyMuPDF", "Next.js 15", "Docker",
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2 font-semibold text-base">
            <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
              <Brain className="w-4 h-4 text-blue-400" />
            </div>
            <span>ResearchAI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/auth/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5">
              Sign in
            </Link>
            <Link href="/auth/register" className="text-sm px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium">
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-24 px-6 text-center overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-blue-500/5 rounded-full blur-3xl" />
          <div className="absolute top-1/3 left-1/3 w-[400px] h-[300px] bg-violet-500/5 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-400 text-xs font-medium mb-8">
            <Sparkles className="w-3 h-3" />
            Production-ready · 8 specialized AI agents · Real-time streaming
          </div>

          <h1 className="text-5xl sm:text-6xl font-semibold tracking-tight mb-6 leading-tight">
            Your AI research team,
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-violet-400 to-cyan-400">
              working in parallel
            </span>
          </h1>

          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
            Upload PDFs, ask complex questions, and watch a fleet of specialized AI agents collaborate — retrieving, reasoning, citing, and synthesizing — to deliver research-grade answers.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="/auth/register" className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-all text-sm shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30">
              Start for free <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/auth/login" className="flex items-center gap-2 px-6 py-3 bg-card border border-border hover:border-blue-500/40 rounded-xl font-medium transition-all text-sm">
              Sign in <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </Link>
          </div>
        </div>
      </section>

      {/* Agent flow diagram */}
      <section className="py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="relative p-6 rounded-2xl border border-border bg-card overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/3 to-violet-500/3" />
            <div className="relative">
              <p className="text-xs text-muted-foreground mb-4 uppercase tracking-wider font-medium">Live agent workflow</p>
              <div className="flex flex-wrap gap-2">
                {[
                  { label: "User Query", color: "border-blue-500/50 bg-blue-500/10 text-blue-400" },
                  { label: "→", color: "text-muted-foreground bg-transparent border-transparent" },
                  { label: "Planner", color: "border-violet-500/50 bg-violet-500/10 text-violet-400" },
                  { label: "→", color: "text-muted-foreground bg-transparent border-transparent" },
                  { label: "Retrieval", color: "border-cyan-500/50 bg-cyan-500/10 text-cyan-400" },
                  { label: "→", color: "text-muted-foreground bg-transparent border-transparent" },
                  { label: "Research", color: "border-emerald-500/50 bg-emerald-500/10 text-emerald-400" },
                  { label: "→", color: "text-muted-foreground bg-transparent border-transparent" },
                  { label: "Citation", color: "border-amber-500/50 bg-amber-500/10 text-amber-400" },
                  { label: "→", color: "text-muted-foreground bg-transparent border-transparent" },
                  { label: "Response", color: "border-rose-500/50 bg-rose-500/10 text-rose-400" },
                ].map((item, i) => (
                  <span key={i} className={`px-3 py-1 rounded-lg border text-xs font-medium ${item.color}`}>
                    {item.label}
                  </span>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-3">
                + Memory Agent · Web Search Agent · Coding Agent running in parallel
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-semibold mb-3">Everything you need for serious research</h2>
            <p className="text-muted-foreground">Built for researchers, engineers, and analysts who need more than a chatbot.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map((f) => (
              <div key={f.title} className="p-6 rounded-xl border border-border bg-card hover:border-blue-500/30 transition-all group">
                <div className={`w-9 h-9 rounded-lg bg-card border border-border flex items-center justify-center mb-4 group-hover:border-blue-500/30 transition-colors`}>
                  <f.icon className={`w-5 h-5 ${f.color}`} />
                </div>
                <h3 className="font-semibold mb-2 text-sm">{f.title}</h3>
                <p className="text-muted-foreground text-xs leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech stack */}
      <section className="py-16 px-6 border-t border-border">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-xs uppercase tracking-wider text-muted-foreground mb-6 font-medium">Built with</p>
          <div className="flex flex-wrap justify-center gap-2">
            {stack.map((t) => (
              <span key={t} className="px-3 py-1 rounded-md bg-muted text-muted-foreground text-xs border border-border font-mono">
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <div className="p-8 rounded-2xl border border-blue-500/20 bg-blue-500/5">
            <h2 className="text-2xl font-semibold mb-3">Ready to start researching?</h2>
            <p className="text-muted-foreground mb-6 text-sm">Upload your first PDF and ask your first question in under 60 seconds.</p>
            <Link href="/auth/register" className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-all text-sm">
              Create free account <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-border py-8 px-6 text-center text-xs text-muted-foreground">
        ResearchAI — Multi-Agent AI Research Assistant. Built with FastAPI, LangGraph &amp; Next.js 15.
      </footer>
    </div>
  );
}
