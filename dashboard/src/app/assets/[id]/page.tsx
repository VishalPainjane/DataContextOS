"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { buildApiUrl } from "../../../lib/api";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../../components/ui/card";
import { Badge } from "../../../components/ui/badge";
import { Sparkles, Key, GitMerge, FileText, CheckCircle2, AlertTriangle, ShieldCheck, Database } from "lucide-react";

interface Column {
  name: string;
  data_type: string;
  description?: string;
}

interface Asset {
  id: string;
  asset_name: string;
  asset_type: string;
  description: string;
  owner: string;
  domain: string;
  sensitivity: string;
  last_updated?: string;
  columns: Column[];
}

interface TrustScore {
  score: number;
  label: string;
  documentation_score: number;
  freshness_score: number;
  ownership_score: number;
  test_coverage_score: number;
  usage_score: number;
  explanation: string;
}

interface GovernanceCheck {
  check_name: string;
  passed: boolean;
  details: string;
  severity: string;
  remediation?: string;
}

interface Governance {
  status: string;
  score: number;
  checks: GovernanceCheck[];
}

export default function AssetDetail() {
  const { id } = useParams();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [trust, setTrust] = useState<TrustScore | null>(null);
  const [governance, setGovernance] = useState<Governance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // AI Chat state
  const [chatQuery, setChatQuery] = useState("");
  const [chatAnswer, setChatAnswer] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [assetRes, trustRes, govRes] = await Promise.all([
          fetch(buildApiUrl(`/api/assets/${id}`)),
          fetch(buildApiUrl(`/api/assets/${id}/trust`)),
          fetch(buildApiUrl(`/api/governance/${id}`))
        ]);

        if (!assetRes.ok) throw new Error("Failed to fetch asset");
        
        setAsset(await assetRes.json());
        setTrust(await trustRes.json());
        setGovernance(await govRes.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setIsLoading(false);
      }
    };

    if (id) fetchData();
  }, [id]);

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatQuery.trim()) return;
    
    setIsChatLoading(true);
    try {
      const res = await fetch(buildApiUrl("/api/search"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: `Regarding asset ${asset?.asset_name}: ${chatQuery}` })
      });
      const data = await res.json();
      setChatAnswer(data.answer);
    } catch (_err) {
      setChatAnswer("Sorry, I couldn't process that question right now.");
    } finally {
      setIsChatLoading(false);
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

  if (isLoading) return <div className="p-12 text-center text-muted-foreground animate-pulse flex flex-col items-center gap-4"><Database className="w-8 h-8 opacity-50" /> Loading asset details...</div>;
  if (error || !asset) return <div className="p-10 m-10 border border-destructive/20 bg-destructive/10 text-destructive rounded-xl text-center">Error: {error || "Asset not found"}</div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-8 pb-12 animate-in fade-in duration-500">
      
      {/* Left Column: Details */}
      <div className="flex flex-col gap-8">
        
        {/* Header Section */}
        <Card className="bg-card/50 backdrop-blur-xl border-border/50 shadow-md">
          <CardContent className="p-8 lg:p-10">
            <div className="flex justify-between items-start mb-6">
              <div className="space-y-2">
                <div className="text-xs font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                  <Database className="w-3.5 h-3.5" />
                  {asset.asset_type} <span className="opacity-40">•</span> {asset.domain || 'General'}
                </div>
                <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight">{asset.asset_name}</h1>
              </div>
              {trust && (
                <div className="text-right flex flex-col items-end gap-2">
                  <Badge variant={getTrustBadgeVariant(trust.label)} className="text-sm px-3 py-1 shadow-sm">
                    {trust.label}
                  </Badge>
                  <div className="text-xs font-medium text-muted-foreground">Trust Score: <span className="text-foreground">{Math.round(trust.score * 100)}%</span></div>
                </div>
              )}
            </div>
            
            <p className="text-lg leading-relaxed text-muted-foreground mb-8 max-w-3xl">
              {asset.description}
            </p>

            <div className="grid grid-cols-3 gap-6 pt-6 border-t border-border/40">
              <div className="space-y-1.5">
                <div className="text-sm font-medium text-muted-foreground flex items-center gap-1.5"><Key className="w-4 h-4" /> Owner</div>
                <div className="font-semibold">{asset.owner || 'Unassigned'}</div>
              </div>
              <div className="space-y-1.5">
                <div className="text-sm font-medium text-muted-foreground flex items-center gap-1.5"><ShieldCheck className="w-4 h-4" /> Sensitivity</div>
                <div className={`font-semibold uppercase tracking-wider text-sm ${asset.sensitivity === 'public' ? 'text-emerald-500' : asset.sensitivity === 'confidential' ? 'text-destructive' : 'text-foreground'}`}>
                  {asset.sensitivity}
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="text-sm font-medium text-muted-foreground flex items-center gap-1.5"><FileText className="w-4 h-4" /> Last Updated</div>
                <div className="font-semibold">{asset.last_updated ? new Date(asset.last_updated).toLocaleDateString() : 'Unknown'}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Trust Breakdown */}
        {trust && (
          <Card className="bg-card/50 backdrop-blur-sm border-border/50">
            <CardHeader>
              <CardTitle className="text-xl">Trust Signals</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                  { label: 'Documentation', val: trust.documentation_score },
                  { label: 'Freshness', val: trust.freshness_score },
                  { label: 'Ownership', val: trust.ownership_score },
                  { label: 'Test Coverage', val: trust.test_coverage_score }
                ].map(s => (
                  <div key={s.label} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium text-muted-foreground">{s.label}</span>
                      <span className="font-bold">{Math.round(s.val * 100)}%</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-primary rounded-full transition-all duration-1000" style={{ width: `${s.val * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-4 rounded-lg bg-primary/5 border border-primary/10 text-sm text-muted-foreground italic border-l-4 border-l-primary flex gap-3">
                <Sparkles className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <p>&ldquo;{trust.explanation}&rdquo;</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Schema Section */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50 overflow-hidden">
          <div className="p-6 border-b border-border/50 flex justify-between items-center bg-muted/20">
            <CardTitle className="text-xl">Schema <Badge variant="secondary" className="ml-2 font-mono">{asset.columns?.length || 0}</Badge></CardTitle>
            <Button variant="outline" size="sm">Export CSV</Button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/30 text-muted-foreground">
                <tr>
                  <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Name</th>
                  <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Type</th>
                  <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {asset.columns?.map(col => (
                  <tr key={col.name} className="hover:bg-muted/20 transition-colors">
                    <td className="px-6 py-4 font-semibold text-primary">{col.name}</td>
                    <td className="px-6 py-4">
                      <code className="bg-muted px-1.5 py-0.5 rounded text-[13px] text-muted-foreground">{col.data_type}</code>
                    </td>
                    <td className="px-6 py-4 text-muted-foreground">{col.description || '-'}</td>
                  </tr>
                ))}
                {(!asset.columns || asset.columns.length === 0) && (
                  <tr>
                    <td colSpan={3} className="px-6 py-12 text-center text-muted-foreground">
                      No schema available for this asset.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Right Column: Sidebar */}
      <div className="flex flex-col gap-6">
        
        {/* Ask AI Side Panel */}
        <Card className="flex flex-col h-[500px] border-border/50 bg-card/60 backdrop-blur-xl shadow-lg">
          <CardHeader className="pb-4 border-b border-border/30">
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              Ask AI Context
            </CardTitle>
            <CardDescription>
              Chat specifically about this asset.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-4 overflow-hidden gap-4">
            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
              {!chatAnswer && !isChatLoading && (
                <div className="text-sm text-muted-foreground text-center p-4 border border-dashed rounded-lg bg-muted/20">
                  Ask anything about this asset&apos;s provenance, quality, or usage.
                </div>
              )}
              {isChatLoading && (
                <div className="flex gap-2 items-center text-sm text-primary font-medium animate-pulse">
                  <Sparkles className="w-4 h-4" /> Thinking...
                </div>
              )}
              {chatAnswer && (
                <div className="text-sm bg-primary/10 border border-primary/20 p-4 rounded-xl text-foreground leading-relaxed animate-in fade-in slide-in-from-bottom-2">
                  {chatAnswer}
                </div>
              )}
            </div>
            <form onSubmit={handleChatSubmit} className="relative mt-auto">
              <Input
                type="text"
                placeholder="Can I use this for rollup?"
                className="pr-20 h-12 bg-background/50"
                value={chatQuery}
                onChange={(e) => setChatQuery(e.target.value)}
              />
              <Button
                type="submit"
                size="sm"
                className="absolute right-1.5 top-1.5 bottom-1.5 h-auto"
                disabled={isChatLoading || !chatQuery.trim()}
              >
                Send
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Governance Report */}
        {governance && (
          <Card className="border-border/50 bg-card/60 backdrop-blur-xl shadow-lg">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-primary" /> Governance Report
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-full border-4 border-primary flex items-center justify-center font-bold text-lg text-primary bg-primary/5">
                  {Math.round(governance.score * 100)}%
                </div>
                <div>
                  <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">Status</div>
                  <div className={`font-semibold ${governance.status === 'compliant' ? 'text-emerald-500' : 'text-amber-500'}`}>
                    <span className="capitalize">{governance.status}</span>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                {governance.checks.map(check => (
                  <div key={check.check_name} className="text-sm space-y-1.5">
                    <div className="flex justify-between items-start gap-2">
                      <span className={`font-medium ${check.passed ? 'text-foreground' : 'text-muted-foreground'}`}>{check.check_name}</span>
                      {check.passed ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                      )}
                    </div>
                    {!check.passed && check.remediation && (
                      <div className="text-xs text-destructive bg-destructive/10 border border-destructive/20 p-2.5 rounded-md mt-1">
                        <span className="font-semibold">Fix:</span> {check.remediation}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <div className="flex flex-col gap-3 mt-2">
          <Link href={`/lineage?asset=${asset.id}`} className="w-full">
            <Button className="w-full h-12 text-base font-semibold shadow-md">
              <GitMerge className="w-4 h-4 mr-2" /> Explore Lineage
            </Button>
          </Link>
          <Button variant="outline" className="w-full h-12 text-base font-semibold bg-background/50 backdrop-blur-sm">
            Request Access
          </Button>
        </div>

      </div>

    </div>
  );
}
