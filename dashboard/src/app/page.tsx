"use client";

import { useState } from "react";

// Mock Data representing search results
const mockResults = [
  {
    id: "1",
    name: "finance_analytics.fct_orders",
    type: "table",
    domain: "finance",
    owner: "data_eng_team",
    description: "Core fact table containing all processed orders with calculated revenue and tax metrics.",
    trustScore: 0.92,
    trustLabel: "trusted"
  },
  {
    id: "2",
    name: "marketing.stg_campaigns",
    type: "view",
    domain: "marketing",
    owner: "growth_team",
    description: "Staging view for active marketing campaigns from various ad platforms.",
    trustScore: 0.65,
    trustLabel: "review"
  },
  {
    id: "3",
    name: "Executive Revenue Dashboard",
    type: "dashboard",
    domain: "leadership",
    owner: "bi_team",
    description: "High-level daily revenue aggregations and forecast comparisons.",
    trustScore: 0.88,
    trustLabel: "trusted"
  }
];

export default function Home() {
  const [query, setQuery] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsLoading(true);
    // Simulate API delay
    setTimeout(() => {
      setIsLoading(false);
      setHasSearched(true);
    }, 800);
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '40px', marginTop: hasSearched ? '20px' : '15vh', transition: 'all 0.5s ease' }}>
      
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

      {hasSearched && (
        <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '20px' }} className="animate-fade-in">
          
          <div className="glass-panel" style={{ padding: '24px', marginBottom: '10px' }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '12px', color: 'var(--text-secondary)' }}>✨ AI Synthesis</h3>
            <p style={{ lineHeight: 1.6 }}>
              Based on the metadata context, the <span style={{color: "var(--accent-primary)", fontWeight: "bold"}}>orders table</span> is owned by the <strong>Data Engineering Team</strong>. It is a core fact table within the Finance domain and currently maintains a high trust score of 0.92, making it reliable for production analytics.
            </p>
          </div>

          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            Retrieved Assets
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
            {mockResults.map((result, idx) => (
              <div key={result.id} className="glass-panel animate-fade-in" style={{ padding: '24px', animationDelay: `${idx * 0.1}s` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div style={{ fontWeight: 600, fontSize: '1.1rem', wordBreak: 'break-all' }}>{result.name}</div>
                  <span className={`badge badge-${result.trustLabel}`}>{result.trustLabel}</span>
                </div>
                
                <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                  <span style={{ fontSize: '0.8rem', background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '10px', color: 'var(--text-tertiary)' }}>{result.type}</span>
                  <span style={{ fontSize: '0.8rem', background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '10px', color: 'var(--text-tertiary)' }}>{result.domain}</span>
                </div>

                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.5, marginBottom: '20px' }}>
                  {result.description}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px', fontSize: '0.9rem' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>Owner: <strong style={{color: 'var(--text-primary)'}}>{result.owner}</strong></span>
                  <button style={{ background: 'transparent', border: '1px solid var(--border-strong)', color: 'white', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer' }}>View Lineage</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
