# DataContextOS Usage Guide

This guide walks through running the API, MCP server, and dashboard locally.

## Prerequisites
- Python 3.11+
- Node.js 18+ (for the dashboard)
- A virtual environment (recommended)

## 1) Environment Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,test,free,prod]"
copy .env.example .env
```

## 2) Ingest Sample Data (Optional)

```bash
dcos ingest sample_data/
```

## 3) Start the FastAPI Backend

```bash
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Verify:
- http://localhost:8000/health
- http://localhost:8000/docs

## 4) Start the MCP Server

```bash
python mcp_server/server.py
```

## 5) Run the Dashboard

Create a dashboard env file:

```bash
# dashboard/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then start the UI:

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:3000

## 6) MCP Client Config Example

Add the server to your MCP client (example for Claude Desktop):

```json
{
  "mcpServers": {
    "datacontextos": {
      "command": "python",
      "args": ["mcp_server/server.py"],
      "env": {
        "DCOS_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Troubleshooting
- If the dashboard cannot reach the API, confirm `NEXT_PUBLIC_API_URL` in `dashboard/.env.local`.
- If you change env vars, restart the Next.js dev server.
- If the API returns empty results, run ingestion or load sample data.
