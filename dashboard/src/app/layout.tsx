import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import CommandBar from "../components/CommandBar";
import { Playfair_Display, Inter } from "next/font/google";
import { cn } from "@/lib/utils";
import { Search, GitMerge, ShieldCheck, MessageSquare, Box, Activity } from "lucide-react";

const playfair = Playfair_Display({ subsets: ['latin'], variable: '--font-serif' });
const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });

export const metadata: Metadata = {
  title: "DataContextOS | AI-Native Metadata Platform",
  description: "Governance, Lineage, and Trust for the Modern Data Stack",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("dark font-sans", playfair.variable, inter.variable)}>
      <body className="bg-background text-foreground min-h-screen flex antialiased">
        <div className="flex min-h-screen w-full">
          {/* Sidebar - Solid and professional with a subtle shadow */}
          <aside className="w-64 bg-card border-r border-border shadow-[4px_0_24px_rgba(0,0,0,0.02)] flex flex-col fixed h-screen z-50">
            <div className="p-6 flex items-center gap-3 border-b border-border/40">
              <div className="flex items-center justify-center w-9 h-9 relative shrink-0">
                <div className="absolute inset-0 bg-primary/20 rounded-xl blur-md" />
                <svg viewBox="0 0 24 24" fill="none" className="w-8 h-8 text-primary relative z-10 drop-shadow-[0_0_8px_rgba(0,230,138,0.8)]" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <span className="font-serif font-bold text-xl tracking-tight text-glow mt-1">DataContextOS</span>
            </div>

            <nav className="flex-1 flex flex-col gap-1.5 p-4 overflow-y-auto">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-3">
                Platform
              </div>
              <Link href="/" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/80 hover:shadow-sm transition-all font-medium">
                <Search className="w-4 h-4" />
                <span>Search</span>
              </Link>
              <Link href="/lineage" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/80 hover:shadow-sm transition-all font-medium">
                <GitMerge className="w-4 h-4" />
                <span>Lineage</span>
              </Link>
              <Link href="/governance" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/80 hover:shadow-sm transition-all font-medium">
                <ShieldCheck className="w-4 h-4" />
                <span>Governance</span>
              </Link>
              <div className="my-2 h-px bg-border/60 mx-3" />
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-3">
                Intelligence
              </div>
              <Link href="/ask-ai" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/80 hover:shadow-sm transition-all font-medium">
                <MessageSquare className="w-4 h-4" />
                <span>Ask AI</span>
              </Link>
              <Link href="/mcp" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/80 hover:shadow-sm transition-all font-medium">
                <Box className="w-4 h-4" />
                <span>MCP Tools</span>
              </Link>
            </nav>

            <div className="p-4 border-t border-border/40 bg-muted/20">
              <div className="rounded-xl border border-border bg-card p-4 text-sm shadow-soft">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-muted-foreground text-xs font-medium">Status</div>
                  <div className="flex items-center gap-1.5 text-emerald-600 font-medium text-xs bg-emerald-500/10 px-2 py-0.5 rounded-full">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Healthy
                  </div>
                </div>
                <div className="font-semibold text-foreground tracking-tight text-[13px] flex items-center gap-2">
                  <Activity className="w-3.5 h-3.5 text-primary" />
                  Production Cluster
                </div>
              </div>
              <div className="text-[10px] text-muted-foreground text-center mt-3 font-medium">
                Cmd/Ctrl + K for commands
              </div>
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="flex-1 ml-64 p-8 lg:p-12 min-h-screen relative z-10 overflow-x-hidden">
            <div className="max-w-[1200px] mx-auto">
              {children}
            </div>
          </main>
        </div>
        <CommandBar />
      </body>
    </html>
  );
}
