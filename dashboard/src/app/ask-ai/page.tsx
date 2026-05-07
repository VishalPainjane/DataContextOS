"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent } from "../../components/ui/card";
import { buildApiUrl } from "../../lib/api";
import { Send, Link as LinkIcon, Sparkles } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: string[];
  confidence?: number;
}

export default function AskAI() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm your DataContextOS AI agent. I can answer questions about your data assets, lineage, governance, and schema. How can I help you today?"
    }
  ]);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    const userQuery = query;
    setQuery("");
    setMessages(prev => [...prev, { role: "user", content: userQuery }]);
    setIsLoading(true);

    try {
      const res = await fetch(buildApiUrl("/api/search"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userQuery, top_k: 3 })
      });
      
      if (!res.ok) throw new Error("API request failed");
      
      const data = await res.json();
      
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: data.answer || "I found some assets, but couldn't generate a specific answer.",
        citations: data.citations,
        confidence: data.confidence
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: "Sorry, I encountered an error connecting to the intelligence layer. Please ensure the backend is running." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] max-w-4xl mx-auto animate-in fade-in duration-500">
      
      <div className="mb-8 text-center space-y-2">
        <h1 className="text-4xl font-extrabold tracking-tight flex items-center justify-center gap-3">
          <Sparkles className="w-8 h-8 text-primary" />
          Global Ask AI
        </h1>
        <p className="text-lg text-muted-foreground">Chat with your entire data catalog context.</p>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden border-border/50 shadow-xl bg-card/40 backdrop-blur-xl">
        
        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8 flex flex-col gap-6">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 max-w-[85%] ${msg.role === 'user' ? 'self-end' : 'self-start'}`}>
              {msg.role === 'assistant' && (
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shrink-0 shadow-md">
                  <Sparkles className="w-5 h-5 text-primary-foreground" />
                </div>
              )}
              
              <div className={`
                px-5 py-4 rounded-2xl shadow-sm
                ${msg.role === 'user' 
                  ? 'bg-primary text-primary-foreground rounded-tr-sm' 
                  : 'bg-muted/50 border border-border/50 text-foreground rounded-tl-sm'
                }
              `}>
                <div className="leading-relaxed whitespace-pre-wrap text-[15px]">{msg.content}</div>
                
                {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-border/50 text-xs text-muted-foreground flex gap-2 items-start">
                    <LinkIcon className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold mr-1">Sources:</span> 
                      {msg.citations.join(', ')}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-4 self-start animate-pulse">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shrink-0 opacity-50">
                <Sparkles className="w-5 h-5 text-primary-foreground" />
              </div>
              <div className="px-5 py-4 bg-muted/50 border border-border/50 rounded-2xl rounded-tl-sm text-muted-foreground flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 md:p-6 bg-card border-t border-border">
          <form onSubmit={handleSubmit} className="relative flex items-center gap-3">
            <Input
              type="text"
              placeholder="e.g. Which table should I use for monthly revenue by region?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isLoading}
              className="h-14 pl-6 pr-14 text-base rounded-2xl bg-muted/30 border-border focus-visible:ring-primary/30"
            />
            <Button
              type="submit"
              size="icon"
              disabled={isLoading || !query.trim()}
              className="absolute right-2 h-10 w-10 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground transition-all"
            >
              <Send className="w-4 h-4 ml-0.5" />
            </Button>
          </form>
          <div className="text-center mt-3 text-xs text-muted-foreground/60">
            AI agents can make mistakes. Consider verifying critical information.
          </div>
        </div>

      </Card>
    </div>
  );
}

