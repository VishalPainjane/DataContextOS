"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { buildApiUrl } from "../lib/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../components/ui/card";
import { Search, Database, LayoutDashboard, Component, Link as LinkIcon, AlertCircle, Cpu, Network, MessageSquare } from "lucide-react";

// Types matching the FastAPI response
interface SearchResult {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  domain: string;
  owner: string;
  description: string;
  snippet: string;
  trust_score?: {
    score: number;
    label: string;
  };
}

interface QueryResponse {
  query: string;
  answer: string;
  results: SearchResult[];
  citations: string[];
  confidence: number;
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [selectedAssetType, setSelectedAssetType] = useState<string | null>(null);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentQueries, setRecentQueries] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const domains = ["Finance", "Marketing", "Engineering", "Sales", "Product"];
  const assetTypes = [
    { label: "Table", value: "table" },
    { label: "View", value: "view" },
    { label: "Dashboard", value: "dashboard" },
    { label: "Pipeline", value: "pipeline" },
    { label: "Model", value: "model" },
  ];
  const suggestedQueries = [
    "finance tables with freshness SLA under 6 hours",
    "dashboards related to revenue",
    "lineage for orders_raw",
    "assets owned by data engineering",
  ];

  useEffect(() => {
    const stored = window.localStorage.getItem("dcos.recentQueries");
    if (stored) {
      try {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setRecentQueries(JSON.parse(stored));
      } catch {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setRecentQueries([]);
      }
    }

    const handler = (event: KeyboardEvent) => {
      if (event.key === "/" && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        inputRef.current?.focus();
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setResponse(null);
    
    try {
      const res = await fetch(buildApiUrl("/api/search"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          query: query, 
          top_k: 5,
          domain: selectedDomain,
          asset_type: selectedAssetType,
        }),
      });
      
      if (!res.ok) {
        throw new Error(`Error: ${res.status} ${res.statusText}`);
      }
      
      const data: QueryResponse = await res.json();
      setResponse(data);
      setRecentQueries((prev) => {
        const next = [query, ...prev.filter((item) => item !== query)].slice(0, 5);
        window.localStorage.setItem("dcos.recentQueries", JSON.stringify(next));
        return next;
      });
    } catch (err) {
      console.error("Search failed:", err);
      setError(err instanceof Error ? err.message : "Failed to connect to API");
    } finally {
      setIsLoading(false);
    }
  };

  const getAssetIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'table': return <Database className="w-4 h-4 text-blue-500" />;
      case 'dashboard': return <LayoutDashboard className="w-4 h-4 text-purple-500" />;
      case 'pipeline': return <Network className="w-4 h-4 text-green-500" />;
      case 'model': return <Cpu className="w-4 h-4 text-orange-500" />;
      default: return <Component className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTrustBadgeVariant = (label: string) => {
    switch (label.toLowerCase()) {
      case 'trusted': return 'default';
      case 'needs review': return 'secondary';
      case 'deprecated': return 'destructive';
      default: return 'outline';
    }
  };

  return (
    <div className="flex flex-col gap-10 animate-in fade-in duration-500 pb-12">
      <div className="max-w-3xl space-y-4 pt-4">
        <h1 className="font-serif text-4xl font-extrabold tracking-tight lg:text-6xl text-foreground">
          Search Metadata
        </h1>
        <p className="text-xl text-muted-foreground leading-relaxed">
          Ask questions about your data stack in natural language.
        </p>
      </div>

      <div className="flex flex-col gap-8 max-w-4xl">
        <form onSubmit={handleSearch} className="relative w-full shadow-elegant rounded-2xl bg-card border border-border/60 hover:border-primary/30 transition-all duration-300 group">
          <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none">
            <Search className="h-6 w-6 text-muted-foreground group-focus-within:text-primary transition-colors" />
          </div>
          <Input
            type="text"
            placeholder="e.g. show me all tables related to revenue in the finance domain"
            className="h-16 pl-14 pr-32 text-[1.05rem] rounded-2xl border-none bg-transparent shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-muted-foreground/70"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            ref={inputRef}
          />
          <Button
            type="submit"
            size="lg"
            className="absolute right-2 top-2 bottom-2 rounded-xl px-6 font-semibold shadow-sm"
            disabled={isLoading}
          >
            {isLoading ? 'Searching...' : 'Search'}
          </Button>
        </form>

        <div className="flex flex-col gap-5">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm font-semibold text-muted-foreground uppercase tracking-wider w-20">Domain</span>
            {domains.map(domain => (
              <button
                key={domain}
                type="button"
                onClick={() => setSelectedDomain(selectedDomain === domain ? null : domain)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                  selectedDomain === domain 
                    ? 'bg-foreground text-background shadow-md' 
                    : 'bg-card border border-border text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                {domain}
              </button>
            ))}
            {selectedDomain && (
              <button type="button" onClick={() => setSelectedDomain(null)} className="text-xs text-destructive hover:underline px-2">
                Clear
              </button>
            )}
          </div>
          
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm font-semibold text-muted-foreground uppercase tracking-wider w-20">Type</span>
            {assetTypes.map(type => (
              <button
                key={type.value}
                type="button"
                onClick={() => setSelectedAssetType(selectedAssetType === type.value ? null : type.value)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                  selectedAssetType === type.value 
                    ? 'bg-foreground text-background shadow-md' 
                    : 'bg-card border border-border text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                {type.label}
              </button>
            ))}
            {selectedAssetType && (
              <button type="button" onClick={() => setSelectedAssetType(null)} className="text-xs text-destructive hover:underline px-2">
                Clear
              </button>
            )}
          </div>
        </div>

        <div className="space-y-3 pt-2">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Suggested queries</h3>
          <div className="flex flex-wrap gap-2">
            {suggestedQueries.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => setQuery(prompt)}
                className="px-3 py-1.5 rounded-lg bg-muted/50 hover:bg-muted text-sm text-foreground/80 transition-colors border border-border/40"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {recentQueries.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Recent searches</h3>
            <div className="flex flex-wrap gap-2">
              {recentQueries.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setQuery(item)}
                  className="px-3 py-1.5 rounded-lg bg-card hover:bg-muted text-sm text-muted-foreground transition-colors border border-dashed border-border"
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {error && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-destructive flex items-center gap-2 text-lg">
              <AlertCircle className="h-5 w-5" /> Connection Error
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{error}</p>
            <p className="text-xs text-muted-foreground/70 mt-2">Ensure the FastAPI backend is running.</p>
          </CardContent>
        </Card>
      )}

      {response && (
        <div className="flex flex-col gap-8 animate-in slide-in-from-bottom-4 duration-500 max-w-6xl mx-auto w-full">
          
          <Card className="border-primary/40 shadow-glow overflow-hidden relative bg-card/60 backdrop-blur-md">
            <div className="absolute top-0 left-0 w-1 h-full bg-primary shadow-glow" />
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-primary text-glow" /> AI Synthesis
                </CardTitle>
                <Badge variant="secondary" className="bg-primary/20 text-primary border border-primary/50 shadow-glow font-medium">
                  Confidence: {(response.confidence * 100).toFixed(0)}%
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-base leading-relaxed whitespace-pre-wrap text-foreground/90">
                {response.answer}
              </p>
              
              {response.citations && response.citations.length > 0 && (
                <div className="mt-6 pt-4 border-t border-border/40 flex items-start gap-2 text-sm text-muted-foreground">
                  <LinkIcon className="h-4 w-4 mt-0.5 shrink-0" />
                  <div>
                    <span className="font-semibold text-foreground/80 mr-2">Sources:</span>
                    {response.citations.join(', ')}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-bold tracking-tight text-foreground">
                Results <Badge variant="secondary" className="ml-2 bg-muted/60 border border-border">{response.results.length}</Badge>
              </h3>
              <span className="text-sm text-muted-foreground font-medium">Sorted by Relevance</span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {response.results.map((result, idx) => (
                <Card key={result.asset_id} className="flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500 hover:shadow-glow transition-all border-border/40 hover:border-primary/50 bg-card/40 backdrop-blur-sm" style={{ animationDelay: `${idx * 50}ms` }}>
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start gap-4 mb-2">
                      <Link href={`/assets/${result.asset_id}`} className="font-semibold text-lg line-clamp-1 hover:text-primary transition-colors" title={result.asset_name}>
                        {result.asset_name}
                      </Link>
                      {result.trust_score ? (
                        <Badge variant={getTrustBadgeVariant(result.trust_score.label)} className="shrink-0 whitespace-nowrap">
                          {result.trust_score.label}
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="shrink-0 text-muted-foreground">UNKNOWN</Badge>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="secondary" className="flex items-center gap-1.5 uppercase text-[10px] tracking-wider py-0">
                        {getAssetIcon(result.asset_type)}
                        {result.asset_type}
                      </Badge>
                      <Badge variant="outline" className="uppercase text-[10px] tracking-wider py-0 text-muted-foreground">
                        {result.domain || 'General'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pb-4 flex-1">
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {result.description}
                    </p>
                  </CardContent>
                  <CardFooter className="pt-4 border-t border-border flex items-center justify-between mt-auto bg-muted/20">
                    <div className="text-xs text-muted-foreground truncate pr-2">
                      Owner: <span className="font-medium text-foreground">{result.owner || 'Unassigned'}</span>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <Link href={`/lineage?asset=${result.asset_id}`}>
                        <Button variant="outline" size="sm" className="h-8">
                          Lineage
                        </Button>
                      </Link>
                      <Link href={`/assets/${result.asset_id}`}>
                        <Button size="sm" className="h-8">
                          Details
                        </Button>
                      </Link>
                    </div>
                  </CardFooter>
                </Card>
              ))}
              
              {response.results.length === 0 && (
                <div className="col-span-full flex flex-col items-center justify-center p-12 text-center rounded-xl border border-dashed border-border bg-card/30">
                  <Database className="h-10 w-10 text-muted-foreground mb-4" />
                  <p className="text-lg font-medium text-foreground">No precise asset matches found.</p>
                  <p className="text-sm text-muted-foreground mt-1">Try broadening your search or checking the domain filters.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
