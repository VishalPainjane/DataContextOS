"use client";

import { useState } from "react";

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
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setResponse(null);
    
    try {
      const res = await fetch("http://localhost:8000/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: query, top_k: 5 }),
      });
      
      if (!res.ok) {
        throw new Error(`Error: ${res.status} ${res.statusText}`);
      }
      
      const data: QueryResponse = await res.json();
      setResponse(data);
    } catch (err: any) {
      console.error("Search failed:", err);
      setError(err.message || "Failed to connect to API");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '40px', marginTop: response || isLoading || error ? '20px' : '15vh', transition: 'all 0.5s ease' }}>
      
      <div style={{ textAlign: 'center', maxWidth: '700px' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: 800, marginBottom: '16px', lineHeight: 1.2 }}>
          Ask your <span className="gradient-text">Data Stack</span> anything.
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', lineHeight: 1.6 }}>
          Agentic RAG powered search for tables, dashboards, lineage, and governance metrics.
        </p>
      </div>

      <form onSubmit={handleSearch} style={{ width: '100%', maxWidth: '650px', position: 'relative' }}>
        <input 
          type="text" 
          className="input-glass" 
          placeholder="e.g. Who owns the orders table? What feeds into the revenue dashboard?"
          style={{ padding: '20px 24px', fontSize: '1.1rem', borderRadius: '12px', paddingRight: '120px' }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button 
          type="submit" 
          className="btn-primary"
          style={{ position: 'absolute', right: '8px', top: '8px', bottom: '8px', padding: '0 24px' }}
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && (
        <div className="glass-panel animate-fade-in" style={{ width: '100%', padding: '24px', borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '8px' }}>Connection Error</h3>
          <p>{error}</p>
          <p style={{ fontSize: '0.9rem', marginTop: '12px', opacity: 0.8 }}>Ensure the FastAPI backend is running on http://localhost:8000.</p>
        </div>
      )}

      {response && (
        <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '20px' }} className="animate-fade-in">
          
          <div className="glass-panel" style={{ padding: '24px', marginBottom: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ fontSize: '1.1rem', color: 'var(--text-secondary)' }}>✨ AI Synthesis</h3>
              <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.2)', color: 'var(--accent-primary)' }}>
                Confidence: {(response.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <p style={{ lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
              {response.answer}
            </p>
            
            {response.citations && response.citations.length > 0 && (
              <div style={{ marginTop: '16px', fontSize: '0.85rem', color: 'var(--text-tertiary)' }}>
                <strong>Sources:</strong> {response.citations.join(', ')}
              </div>
            )}
          </div>

          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            Retrieved Assets ({response.results.length})
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
            {response.results.map((result, idx) => (
              <div key={result.asset_id} className="glass-panel animate-fade-in" style={{ padding: '24px', animationDelay: `${idx * 0.1}s` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div style={{ fontWeight: 600, fontSize: '1.1rem', wordBreak: 'break-all' }}>{result.asset_name}</div>
                  {result.trust_score ? (
                    <span className={`badge badge-${result.trust_score.label.toLowerCase()}`}>{result.trust_score.label}</span>
                  ) : (
                    <span className="badge" style={{ background: 'rgba(255,255,255,0.1)', color: 'var(--text-secondary)' }}>UNKNOWN</span>
                  )}
                </div>
                
                <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                  <span style={{ fontSize: '0.8rem', background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '10px', color: 'var(--text-tertiary)' }}>{result.asset_type}</span>
                  <span style={{ fontSize: '0.8rem', background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '10px', color: 'var(--text-tertiary)' }}>{result.domain || 'general'}</span>
                </div>

                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.5, marginBottom: '20px' }}>
                  {result.description}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px', fontSize: '0.9rem' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>Owner: <strong style={{color: 'var(--text-primary)'}}>{result.owner || 'Unassigned'}</strong></span>
                  <button style={{ background: 'transparent', border: '1px solid var(--border-strong)', color: 'white', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer' }}>View Lineage</button>
                </div>
              </div>
            ))}
            
            {response.results.length === 0 && (
              <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px', color: 'var(--text-tertiary)' }}>
                No precise asset matches found in the index.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
