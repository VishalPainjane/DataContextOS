import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DataContextOS | AI Metadata Intelligence",
  description: "Agentic RAG and Observability platform for enterprise metadata.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <nav style={{
          padding: '20px 40px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: 'var(--glass-border)',
          background: 'rgba(10, 10, 11, 0.8)',
          backdropFilter: 'var(--glass-blur)',
          position: 'sticky',
          top: 0,
          zIndex: 100
        }}>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
            Data<span className="gradient-text">Context</span>OS
          </div>
          <div style={{ display: 'flex', gap: '24px', fontSize: '0.9rem', fontWeight: 500 }}>
            <a href="/" style={{ color: 'var(--text-primary)' }}>Search</a>
            <a href="#" style={{ color: 'var(--text-secondary)' }}>Lineage</a>
            <a href="#" style={{ color: 'var(--text-secondary)' }}>Governance</a>
            <a href="#" style={{ color: 'var(--text-secondary)' }}>Settings</a>
          </div>
        </nav>
        <main style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
          {children}
        </main>
      </body>
    </html>
  );
}
