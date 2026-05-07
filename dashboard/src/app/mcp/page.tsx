import { API_BASE_URL } from "../../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Box, Plug, Terminal, Code2 } from "lucide-react";

export default function MCPExplorer() {
  return (
    <div className="flex flex-col gap-8 max-w-4xl mx-auto animate-in fade-in duration-500 pb-10">
      
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-extrabold tracking-tight flex items-center justify-center gap-3">
          <Box className="w-10 h-10 text-primary" />
          MCP Server
        </h1>
        <p className="text-lg text-muted-foreground">
          Connect your AI agents to the DataContextOS intelligence layer.
        </p>
      </div>

      <Card className="bg-card/50 backdrop-blur-sm border-border/50 shadow-md">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-2">
            <Plug className="w-6 h-6 text-primary" /> What is MCP?
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <p className="text-base text-muted-foreground leading-relaxed">
            The Model Context Protocol (MCP) allows tools like Claude Desktop, Cursor, and VS Code to natively query the DataContextOS metadata index. 
            By connecting via MCP, your AI assistant instantly becomes &quot;data-aware&quot; for your specific enterprise catalog.
          </p>
          
          <div className="bg-muted/30 p-6 rounded-xl border border-border/50">
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
              <Code2 className="w-4 h-4 text-muted-foreground" /> Available Tools
            </h3>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <li className="space-y-1">
                <span className="text-primary font-bold font-mono text-sm">search_assets</span>
                <p className="text-muted-foreground text-sm">Search the catalog using natural language.</p>
              </li>
              <li className="space-y-1">
                <span className="text-primary font-bold font-mono text-sm">get_lineage</span>
                <p className="text-muted-foreground text-sm">Traverse upstream/downstream dependencies.</p>
              </li>
              <li className="space-y-1">
                <span className="text-primary font-bold font-mono text-sm">get_trust_score</span>
                <p className="text-muted-foreground text-sm">Compute composite trust scores and signals.</p>
              </li>
              <li className="space-y-1">
                <span className="text-primary font-bold font-mono text-sm">find_owner</span>
                <p className="text-muted-foreground text-sm">Lookup the owning team or person for an asset.</p>
              </li>
              <li className="space-y-1">
                <span className="text-primary font-bold font-mono text-sm">get_schema</span>
                <p className="text-muted-foreground text-sm">Retrieve table schema and column descriptions.</p>
              </li>
              <li className="space-y-1">
                <span className="text-primary font-bold font-mono text-sm">assess_governance</span>
                <p className="text-muted-foreground text-sm">Check compliance status and remediation steps.</p>
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-card/50 backdrop-blur-sm border-border/50 shadow-md">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-2">
            <Terminal className="w-6 h-6 text-primary" /> Connection Instructions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <h3 className="text-lg font-semibold">Claude Desktop</h3>
            <p className="text-sm text-muted-foreground">Add this to your <code className="bg-muted px-1.5 py-0.5 rounded text-foreground font-mono">claude_desktop_config.json</code> file:</p>
            <pre className="bg-black/40 p-5 rounded-xl border border-border/50 overflow-x-auto text-sm text-emerald-400 shadow-inner font-mono">
{`{
  "mcpServers": {
    "datacontextos": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "mcp_server/server.py"
      ],
      "env": {
        "DCOS_API_URL": "${API_BASE_URL}"
      }
    }
  }
}`}
            </pre>
          </div>
        </CardContent>
      </Card>

    </div>
  );
}
