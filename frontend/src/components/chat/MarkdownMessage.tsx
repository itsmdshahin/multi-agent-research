"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Check } from "lucide-react";
import { useState } from "react";
import type { Components } from "react-markdown";

interface MarkdownProps {
  content: string;
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="relative group my-3">
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#0d1117] border border-border rounded-t-lg border-b-0">
        <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">
          {language || "code"}
        </span>
        <button
          onClick={copy}
          className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors opacity-0 group-hover:opacity-100"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <SyntaxHighlighter
        language={language || "text"}
        style={oneDark}
        customStyle={{
          margin: 0,
          borderRadius: "0 0 8px 8px",
          fontSize: "0.8rem",
          border: "1px solid hsl(var(--border))",
          borderTop: "none",
        }}
        wrapLongLines
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

// react-markdown v9 uses a different component API — no "inline" prop.
// We detect inline code by checking whether the parent is a <pre> block.
const components: Components = {
  code(props) {
    const { className, children, node, ...rest } = props;
    const match = /language-(\w+)/.exec(className || "");
    const codeString = String(children).replace(/\n$/, "");

    // If it has a language class OR contains newlines → treat as block code
    const isBlock = Boolean(match) || codeString.includes("\n");

    if (isBlock) {
      return <CodeBlock language={match?.[1] ?? ""} code={codeString} />;
    }

    // Inline code
    return (
      <code
        className="px-1.5 py-0.5 bg-muted border border-border rounded text-cyan-400 text-[0.8em] font-mono"
        {...rest}
      >
        {children}
      </code>
    );
  },

  table({ children }) {
    return (
      <div className="overflow-x-auto my-3">
        <table className="w-full">{children}</table>
      </div>
    );
  },
};

export function MarkdownMessage({ content }: MarkdownProps) {
  return (
    <div className="prose text-sm leading-relaxed">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
