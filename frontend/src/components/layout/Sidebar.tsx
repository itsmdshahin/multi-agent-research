"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Brain, LayoutDashboard, MessageSquare, FileText,
  BookOpen, Settings, LogOut, Plus, ChevronRight
} from "lucide-react";
import { useAuthStore } from "@/lib/stores/authStore";
import { useChatStore } from "@/lib/stores/chatStore";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/chat",      icon: MessageSquare,   label: "Chat" },
  { href: "/documents", icon: FileText,         label: "Documents" },
  { href: "/reports",   icon: BookOpen,         label: "Reports" },
  { href: "/settings",  icon: Settings,         label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { conversations, createConversation } = useChatStore();

  const handleNewChat = async () => {
    const conv = await createConversation();
    router.push(`/chat/${conv.id}`);
  };

  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-[var(--sidebar-width)] bg-card border-r border-border flex flex-col z-40">
      {/* Logo */}
      <div className="h-14 flex items-center gap-2.5 px-4 border-b border-border shrink-0">
        <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
          <Brain className="w-4 h-4 text-blue-400" />
        </div>
        <span className="font-semibold text-sm">ResearchAI</span>
      </div>

      {/* New Chat button */}
      <div className="px-3 py-3 border-b border-border shrink-0">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-dashed border-border hover:border-blue-500/40 hover:bg-blue-500/5 text-muted-foreground hover:text-foreground text-xs font-medium transition-all"
        >
          <Plus className="w-3.5 h-3.5" /> New conversation
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-2">
        <div className="px-2 space-y-0.5">
          {NAV.map(({ href, icon: Icon, label }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all",
                  active
                    ? "bg-blue-600/15 text-blue-400 border border-blue-500/20"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                )}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {label}
              </Link>
            );
          })}
        </div>

        {/* Recent conversations */}
        {conversations.length > 0 && (
          <div className="mt-4 px-3">
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium mb-1.5">Recent</p>
            <div className="space-y-0.5">
              {conversations.slice(0, 8).map((conv) => {
                const active = pathname === `/chat/${conv.id}`;
                return (
                  <Link
                    key={conv.id}
                    href={`/chat/${conv.id}`}
                    className={cn(
                      "flex items-center gap-2 px-2 py-1.5 rounded-md text-xs transition-all truncate",
                      active ? "text-foreground bg-muted" : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    )}
                  >
                    <MessageSquare className="w-3 h-3 shrink-0" />
                    <span className="truncate">{conv.title || "Untitled"}</span>
                  </Link>
                );
              })}
              {conversations.length > 8 && (
                <Link href="/chat" className="flex items-center gap-1 px-2 py-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors">
                  View all <ChevronRight className="w-3 h-3" />
                </Link>
              )}
            </div>
          </div>
        )}
      </nav>

      {/* User footer */}
      <div className="border-t border-border p-3 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-blue-500/20 flex items-center justify-center text-xs font-semibold text-blue-400 shrink-0">
            {(user?.username?.[0] || "U").toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium truncate">{user?.username}</p>
            <p className="text-[10px] text-muted-foreground truncate">{user?.email}</p>
          </div>
          <button onClick={handleLogout} className="p-1 text-muted-foreground hover:text-foreground transition-colors" title="Sign out">
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
