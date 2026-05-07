"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Command, ArrowRight } from "lucide-react";

interface CommandItem {
  id: string;
  label: string;
  description: string;
  href: string;
  keywords?: string[];
}

const baseCommands: CommandItem[] = [
  {
    id: "search",
    label: "Search catalog",
    description: "Run a natural language search",
    href: "/",
    keywords: ["home", "query", "assets"],
  },
  {
    id: "lineage",
    label: "Lineage explorer",
    description: "Visualize upstream and downstream dependencies",
    href: "/lineage",
    keywords: ["graph", "impact"],
  },
  {
    id: "governance",
    label: "Governance dashboard",
    description: "Portfolio compliance and remediation",
    href: "/governance",
    keywords: ["trust", "risk"],
  },
  {
    id: "ask-ai",
    label: "Ask AI",
    description: "Chat with the intelligence layer",
    href: "/ask-ai",
    keywords: ["chat", "assistant"],
  },
  {
    id: "mcp",
    label: "MCP explorer",
    description: "Connect agents to MCP tools",
    href: "/mcp",
    keywords: ["tools", "config"],
  },
];

function parseAssetId(input: string): string | null {
  const cleaned = input.trim();
  if (!cleaned) return null;
  const match = cleaned.match(/^(asset:|id:|asset\s+|id\s+)(.+)$/i);
  if (match?.[2]) {
    return match[2].trim();
  }
  if (cleaned.length > 6 && cleaned.includes("-")) {
    return cleaned;
  }
  return null;
}

export default function CommandBar() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === "k" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setQuery("");
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setActiveIndex(0);
    }
  }, [isOpen]);

  const filteredCommands = useMemo(() => {
    if (!query.trim()) return baseCommands;
    const term = query.toLowerCase();
    return baseCommands.filter((item) => {
      const haystack = [
        item.label,
        item.description,
        ...(item.keywords ?? []),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(term);
    });
  }, [query]);

  const assetId = parseAssetId(query);

  const handleSubmit = () => {
    if (assetId) {
      router.push(`/assets/${assetId}`);
      setIsOpen(false);
      return;
    }

    const selected = filteredCommands[activeIndex] || filteredCommands[0];
    if (selected) {
      router.push(selected.href);
      setIsOpen(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] bg-background/80 backdrop-blur-sm flex items-start justify-center pt-24 px-4 pb-4 animate-in fade-in duration-200" onClick={() => setIsOpen(false)}>
      <div className="w-full max-w-2xl bg-card border border-border shadow-2xl rounded-xl overflow-hidden animate-in zoom-in-95 duration-200" onClick={(event) => event.stopPropagation()}>
        <div className="p-4 border-b border-border flex items-center gap-3">
          <Command className="w-5 h-5 text-muted-foreground" />
          <input
            ref={inputRef}
            className="flex-1 bg-transparent border-none text-foreground outline-none placeholder:text-muted-foreground text-lg"
            placeholder="Search commands or type asset: <id>"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setActiveIndex(0);
            }}
            onKeyDown={(event) => {
              if (event.key === "ArrowDown") {
                event.preventDefault();
                setActiveIndex((prev) => Math.min(prev + 1, filteredCommands.length - 1));
              }
              if (event.key === "ArrowUp") {
                event.preventDefault();
                setActiveIndex((prev) => Math.max(prev - 1, 0));
              }
              if (event.key === "Enter") {
                event.preventDefault();
                handleSubmit();
              }
            }}
          />
          <div className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">Esc to close</div>
        </div>

        <div className="max-h-96 overflow-y-auto p-2">
          {assetId && (
            <button
              type="button"
              className="w-full text-left p-3 rounded-lg flex items-center gap-3 hover:bg-muted focus:bg-muted outline-none group"
              onClick={handleSubmit}
            >
              <div className="bg-primary/10 p-2 rounded-md group-hover:bg-primary/20">
                <Search className="w-4 h-4 text-primary" />
              </div>
              <div className="flex-1">
                <div className="font-semibold text-foreground">Open asset: {assetId}</div>
                <div className="text-sm text-muted-foreground">Jump straight to the asset detail view.</div>
              </div>
              <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
          )}

          {filteredCommands.map((item, index) => (
            <button
              key={item.id}
              type="button"
              className={`w-full text-left p-3 rounded-lg flex items-center gap-3 outline-none group transition-colors ${index === activeIndex ? "bg-muted" : "hover:bg-muted"}`}
              onClick={() => {
                router.push(item.href);
                setIsOpen(false);
              }}
              onMouseEnter={() => setActiveIndex(index)}
            >
              <div className="flex-1">
                <div className="font-semibold text-foreground">{item.label}</div>
                <div className="text-sm text-muted-foreground">{item.description}</div>
              </div>
              {index === activeIndex && <ArrowRight className="w-4 h-4 text-muted-foreground" />}
            </button>
          ))}

          {filteredCommands.length === 0 && !assetId && (
            <div className="p-8 text-center text-muted-foreground">
              No matching commands. Try &quot;asset: &lt;id&gt;&quot; to jump to an asset.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
