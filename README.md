# DataContextOS

An AI-Native Metadata Intelligence Platform with MCP, Agentic RAG, and Enterprise Observability.

## Overview

DataContextOS allows you to query your enterprise data assets — their meaning, lineage, ownership, and quality — through natural language.

### Key Features
- **Agentic RAG Engine:** Multi-agent LangGraph workflow with specialized agents for routing, retrieval, lineage traversal, and trust score computation.
- **MCP Server:** Expose data metadata to Claude and other LLMs via the Model Context Protocol.
- **Trust Scores:** Composite scores evaluating documentation, freshness, ownership, test coverage, and usage.
- **Dual-Mode Architecture:** Run in `prod` mode with premium APIs (OpenAI, Anthropic, Cohere, LangSmith) or in `free` mode entirely locally and zero-cost (Ollama, Gemini Flash, HuggingFace, ChromaDB).

## Getting Started

### 1. Setup Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
cp .env.example .env
```

### 2. Ingest Data
```bash
dcos ingest sample_data/
```

### 3. Run the API and MCP Server
```bash
docker-compose up -d
```
Or run the CLI directly:
```bash
dcos search "Who owns the orders table?"
```

## Architecture

1. **Ingestion**: Connectors parse dbt projects, SQL databases, OpenAPI specs, and markdown docs.
2. **Context Layer**: A vector store (pgvector/Chroma) indexes embeddings.
3. **Agentic RAG**: A LangGraph workflow processes queries, retrieves context, walks lineage graphs, and computes trust scores.
4. **API & Dashboard**: FastAPI backend with a Next.js dashboard.
