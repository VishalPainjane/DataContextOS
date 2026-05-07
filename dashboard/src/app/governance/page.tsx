"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { buildApiUrl } from "../../lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Input } from "../../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Button } from "../../components/ui/button";
import { Search, ShieldAlert, ShieldCheck, Activity, BarChart3, AlertTriangle, AlertCircle, CheckCircle2, Database } from "lucide-react";

interface GovernanceStats {
  total_assets: number;
  avg_trust_score: number;
  compliant_percentage: number;
  assets_by_status: Record<string, number>;
  assets_by_domain: Record<string, number>;
}

interface GovernanceAttentionItem {
  asset_id: string;
  asset_name: string;
  domain?: string;
  owner?: string;
  issue: string;
  severity: "high" | "medium" | "low" | string;
}

export default function GovernanceDashboard() {
  const [stats, setStats] = useState<GovernanceStats | null>(null);
  const [attentionItems, setAttentionItems] = useState<GovernanceAttentionItem[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string | "all">("all");
  const [domainFilter, setDomainFilter] = useState<string | "all">("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [statsRes, attentionRes] = await Promise.all([
          fetch(buildApiUrl("/api/governance/stats")),
          fetch(buildApiUrl("/api/governance/attention?limit=6"))
        ]);

        if (!statsRes.ok) throw new Error("Failed to fetch governance stats");
        setStats(await statsRes.json());

        if (attentionRes.ok) {
          const attentionData = await attentionRes.json();
          setAttentionItems(attentionData.items || []);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (isLoading) return <div className="p-10 flex justify-center items-center h-64 text-muted-foreground animate-pulse">Loading governance dashboard...</div>;
  if (error) return <div className="p-10 text-destructive bg-destructive/10 rounded-xl m-10 border border-destructive/20 text-center">Error: {error}</div>;
  if (!stats) return null;

  const domains = Array.from(
    new Set(attentionItems.map((item) => item.domain || "General"))
  ).sort();

  const filteredAttentionItems = attentionItems.filter((item) => {
    if (severityFilter !== "all" && item.severity !== severityFilter) {
      return false;
    }
    const domain = item.domain || "General";
    if (domainFilter !== "all" && domain !== domainFilter) {
      return false;
    }
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      const haystack = `${item.asset_name} ${item.issue} ${domain} ${item.owner || ""}`.toLowerCase();
      return haystack.includes(term);
    }
    return true;
  });

  const getSeverityIcon = (severity: string) => {
    switch(severity) {
      case 'high': return <AlertCircle className="w-5 h-5 text-destructive" />;
      case 'medium': return <AlertTriangle className="w-5 h-5 text-warning" />;
      default: return <ShieldAlert className="w-5 h-5 text-emerald-500" />;
    }
  }

  const getSeverityColor = (severity: string) => {
    switch(severity) {
      case 'high': return 'text-destructive bg-destructive/10 border-destructive/20';
      case 'medium': return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
      default: return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
    }
  }

  return (
    <div className="flex flex-col gap-8 animate-in fade-in duration-500 pb-10">
      
      <div className="space-y-2">
        <h1 className="text-4xl font-extrabold tracking-tight flex items-center gap-3">
          <ShieldCheck className="w-9 h-9 text-primary" />
          Governance Dashboard
        </h1>
        <p className="text-xl text-muted-foreground">Portfolio-wide compliance and health metrics.</p>
      </div>

      {/* Top KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="p-6 flex flex-col gap-2">
            <div className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Database className="w-4 h-4" /> Total Assets
            </div>
            <div className="text-4xl font-bold">{stats.total_assets}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="p-6 flex flex-col gap-2">
            <div className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Activity className="w-4 h-4" /> Avg Trust Score
            </div>
            <div className="text-4xl font-bold text-primary">
              {Math.round(stats.avg_trust_score * 100)}%
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="p-6 flex flex-col gap-2">
            <div className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <ShieldCheck className="w-4 h-4" /> Compliant Assets
            </div>
            <div className="text-4xl font-bold text-emerald-500">
              {stats.compliant_percentage}%
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Compliance Breakdown */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <BarChart3 className="w-5 h-5" /> Compliance Status
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            {Object.entries(stats.assets_by_status).map(([status, count]) => {
              const colorClass = status === 'compliant' ? 'bg-emerald-500' : status === 'partial' ? 'bg-amber-500' : 'bg-destructive';
              const percentage = Math.round((count / stats.total_assets) * 100) || 0;
              return (
                <div key={status} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="capitalize font-medium text-muted-foreground">{status.replace('_', ' ')}</span>
                    <span className="font-semibold">{count} ({percentage}%)</span>
                  </div>
                  <div className="h-2.5 bg-muted rounded-full overflow-hidden">
                    <div className={`h-full ${colorClass} rounded-full transition-all duration-1000`} style={{ width: `${percentage}%` }} />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Action Items */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <AlertTriangle className="w-5 h-5" /> Recommended Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {attentionItems.length === 0 && (
              <div className="p-6 text-center border border-dashed rounded-xl text-muted-foreground bg-muted/20">
                <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-emerald-500/50" />
                No urgent governance gaps detected.
              </div>
            )}
            {attentionItems.slice(0, 3).map((item) => (
              <div key={item.asset_id} className={`p-4 rounded-xl border flex items-start gap-4 ${getSeverityColor(item.severity)}`}>
                <div className="mt-0.5">{getSeverityIcon(item.severity)}</div>
                <div className="flex-1 space-y-1">
                  <div className="font-semibold text-sm uppercase tracking-wider">{item.severity} SEVERITY</div>
                  <div className="font-medium">{item.issue}</div>
                  <p className="text-xs opacity-80 pt-1">
                    {item.asset_name} • {item.domain || "General"}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardHeader className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <CardTitle className="text-xl">Assets Needing Attention</CardTitle>
            <CardDescription>Showing {filteredAttentionItems.length} of {attentionItems.length} items</CardDescription>
          </div>
          
          {attentionItems.length > 0 && (
            <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search assets or issues..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 bg-background/50"
                />
              </div>
              
              <Select value={severityFilter} onValueChange={(val) => setSeverityFilter(val || "all")}>
                <SelectTrigger className="w-[130px] bg-background/50">
                  <SelectValue placeholder="Severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severities</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>

              <Select value={domainFilter} onValueChange={(val) => setDomainFilter(val || "all")}>
                <SelectTrigger className="w-[130px] bg-background/50">
                  <SelectValue placeholder="Domain" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Domains</SelectItem>
                  {domains.map((domain) => (
                    <SelectItem key={domain} value={domain}>{domain}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {(severityFilter !== "all" || domainFilter !== "all" || searchTerm) && (
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => { setSeverityFilter("all"); setDomainFilter("all"); setSearchTerm(""); }}
                  className="text-destructive hover:bg-destructive/10"
                >
                  Clear
                </Button>
              )}
            </div>
          )}
        </CardHeader>
        
        <CardContent className="p-0">
          {attentionItems.length === 0 ? (
             <div className="p-12 text-center text-muted-foreground flex flex-col items-center gap-3">
               <ShieldCheck className="w-12 h-12 text-muted-foreground/30" />
               <p>No critical remediation items right now.</p>
             </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/50 text-muted-foreground">
                  <tr>
                    <th className="px-6 py-4 font-medium">Asset</th>
                    <th className="px-6 py-4 font-medium">Issue</th>
                    <th className="px-6 py-4 font-medium">Severity</th>
                    <th className="px-6 py-4 font-medium">Owner</th>
                    <th className="px-6 py-4 font-medium">Domain</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {filteredAttentionItems.map((item) => (
                    <tr key={item.asset_id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-6 py-4 font-medium">
                        <Link href={`/assets/${item.asset_id}`} className="text-primary hover:underline">
                          {item.asset_name}
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">{item.issue}</td>
                      <td className="px-6 py-4">
                        <Badge variant={item.severity === 'high' ? 'destructive' : item.severity === 'medium' ? 'secondary' : 'outline'} className="uppercase text-[10px]">
                          {item.severity}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">{item.owner || "Unassigned"}</td>
                      <td className="px-6 py-4 text-muted-foreground">
                        <Badge variant="neutral">{item.domain || "General"}</Badge>
                      </td>
                    </tr>
                  ))}
                  {filteredAttentionItems.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                        No items match your filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
