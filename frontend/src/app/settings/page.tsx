"use client";
import { useState } from "react";
import { User, Shield, Bell, Cpu, CheckCircle } from "lucide-react";
import { useAuthStore } from "@/lib/stores/authStore";

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [saved, setSaved] = useState(false);
  const [model, setModel] = useState("gpt-4o");

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const models = [
    { value: "gpt-4o",               label: "GPT-4o",              desc: "Best quality, slower" },
    { value: "gpt-4o-mini",          label: "GPT-4o Mini",         desc: "Fast, cost-effective" },
    { value: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet", desc: "Anthropic's flagship" },
  ];

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-semibold mb-6">Settings</h1>

      <div className="space-y-4">
        {/* Profile */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="flex items-center gap-2.5 p-4 border-b border-border">
            <User className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-sm font-medium">Profile</h2>
          </div>
          <div className="p-4 space-y-3">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-blue-500/20 flex items-center justify-center text-lg font-semibold text-blue-400">
                {(user?.username?.[0] || "U").toUpperCase()}
              </div>
              <div>
                <p className="font-medium text-sm">{user?.full_name || user?.username}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 font-medium mt-0.5 inline-block">{user?.role}</span>
              </div>
            </div>
          </div>
        </div>

        {/* AI Model */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="flex items-center gap-2.5 p-4 border-b border-border">
            <Cpu className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-sm font-medium">AI Model</h2>
          </div>
          <div className="p-4 space-y-2">
            <p className="text-xs text-muted-foreground mb-3">Choose the default language model for your conversations.</p>
            {models.map((m) => (
              <label key={m.value} className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all ${model === m.value ? "border-blue-500/40 bg-blue-500/10" : "border-border hover:border-blue-500/20 hover:bg-muted/30"}`}>
                <input type="radio" name="model" value={m.value} checked={model === m.value} onChange={() => setModel(m.value)} className="accent-blue-500" />
                <div>
                  <p className="text-sm font-medium">{m.label}</p>
                  <p className="text-xs text-muted-foreground">{m.desc}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Security */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="flex items-center gap-2.5 p-4 border-b border-border">
            <Shield className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-sm font-medium">Security</h2>
          </div>
          <div className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">JWT Authentication</p>
                <p className="text-xs text-muted-foreground">All API requests are authenticated with signed tokens.</p>
              </div>
              <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                <CheckCircle className="w-3.5 h-3.5" /> Active
              </span>
            </div>
          </div>
        </div>

        {/* Save */}
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-medium transition-colors"
          >
            {saved ? <><CheckCircle className="w-4 h-4" /> Saved!</> : "Save changes"}
          </button>
        </div>
      </div>
    </div>
  );
}
