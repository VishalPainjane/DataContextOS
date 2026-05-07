"""
DataContextOS CLI — Command-line interface for the `dcos` command.

Usage:
    dcos ingest [SOURCE_DIR]      Run the metadata ingestion pipeline
    dcos search QUERY             Search across data assets
    dcos info                     Show current configuration
    dcos version                  Print the version
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="dcos",
    help="DataContextOS — AI-Native Metadata Intelligence Platform",
    add_completion=False,
)
console = Console()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# ── Commands ─────────────────────────────────────────────────────────────────


@app.command()
def version() -> None:
    """Print the current DataContextOS version."""
    import importlib.metadata

    try:
        ver = importlib.metadata.version("datacontextos")
    except importlib.metadata.PackageNotFoundError:
        ver = "0.1.0"

    console.print(f"[bold cyan]DataContextOS[/] v{ver}")


@app.command()
def info() -> None:
    """Show the current configuration summary."""
    from config import settings

    table = Table(title="DataContextOS Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Mode", settings.mode.value)
    table.add_row("LLM Provider", f"{settings.llm_provider} / {settings.llm_model}")
    table.add_row("Embedding Provider", settings.embedding_provider)
    table.add_row("Embedding Model", settings.embedding_model)
    table.add_row("Vector Store", settings.vector_store)
    table.add_row("Database", settings.database)
    table.add_row("Reranker", settings.reranker)
    table.add_row("Tracer", settings.tracer)
    table.add_row("API", f"{settings.api_host}:{settings.api_port}")
    table.add_row("MCP", f"{settings.mcp_host}:{settings.mcp_port}")

    console.print(table)

    warnings = settings.validate_api_keys()
    if warnings:
        console.print("\n[bold yellow]⚠ Configuration Warnings:[/]")
        for w in warnings:
            console.print(f"  [yellow]• {w}[/]")


@app.command()
def ingest(
    source_dir: str = typer.Argument(
        "sample_data",
        help="Path to directory containing metadata sources (dbt_manifest.json, docs/)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Run the metadata ingestion pipeline on a source directory."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    source_path = Path(source_dir)
    if not source_path.exists():
        console.print(f"[red]Error:[/] Source directory not found: {source_dir}")
        raise typer.Exit(code=1)

    console.print(f"[cyan]►[/] Ingesting from [bold]{source_dir}[/]...")

    async def _run() -> dict:
        from ingestion.pipeline import run_ingestion

        return await run_ingestion(source_dir)

    try:
        summary = asyncio.run(_run())
        console.print(
            f"\n[bold green]✓ Ingestion complete![/]\n"
            f"  Assets ingested : [cyan]{summary['assets_ingested']}[/]\n"
            f"  Lineage edges   : [cyan]{summary['lineage_edges']}[/]\n"
            f"  Source          : [dim]{summary['source_dir']}[/]"
        )
    except Exception as exc:
        console.print(f"[bold red]✗ Ingestion failed:[/] {exc}")
        if verbose:
            import traceback

            traceback.print_exc()
        raise typer.Exit(code=1)


@app.command()
def api(
    host: str = typer.Option(None, help="Host to bind to"),
    port: int = typer.Option(None, help="Port to bind to"),
) -> None:
    """Start the DataContextOS FastAPI server."""
    from config import settings
    import uvicorn

    h = host or settings.api_host
    p = port or settings.api_port
    
    console.print(f"[cyan]►[/] Starting API server on [bold]{h}:{p}[/]...")
    uvicorn.run("api.main:app", host=h, port=p, reload=settings.debug)


@app.command()
def mcp(
    host: str = typer.Option(None, help="Host to bind to"),
    port: int = typer.Option(None, help="Port to bind to"),
) -> None:
    """Start the DataContextOS MCP server."""
    from config import settings
    from mcp_server.server import mcp as mcp_app

    h = host or settings.mcp_host
    p = port or settings.mcp_port
    
    console.print(f"[cyan]►[/] Starting MCP server on [bold]{h}:{p}[/]...")
    mcp_app.run()


@app.command()
def search(
    query: str = typer.Argument(..., help="Natural language query to search for"),
) -> None:
    """Search for data assets using the Agentic RAG Engine."""
    console.print(f'[cyan]►[/] Asking AI: "[bold]{query}[/]"...')

    async def _run() -> None:
        from context_layer.rag_engine import RagEngine
        from database.engine import init_db

        await init_db()
        engine = RagEngine()
        response = await engine.run(query)

        if not response.results:
            console.print("[yellow]No assets found. Run [bold]dcos ingest[/] first.[/]")
            return

        # 1. Show AI Synthesis
        console.print("\n[bold]✨ AI Synthesis[/]")
        console.print(f"{response.answer}")
        console.print(f"[dim]Confidence: {int(response.confidence * 100)}% | Sources: {', '.join(response.citations)}[/]")

        # 2. Show Retrieved Assets
        table = Table(title=f"Retrieved Assets", show_header=True, box=None)
        table.add_column("Asset Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Domain", style="yellow")
        table.add_column("Owner", style="magenta")
        table.add_column("Score", style="white")

        for res in response.results:
            # Format score: show as % if in [0,1], otherwise as raw float
            if 0 <= res.relevance_score <= 1.0:
                score_str = f"{int(res.relevance_score * 100)}%"
            else:
                score_str = f"{res.relevance_score:.2f}"
                
            table.add_row(
                res.asset_name,
                res.asset_type,
                res.domain or "—",
                res.owner or "—",
                score_str
            )

        console.print("\n")
        console.print(table)

    try:
        asyncio.run(_run())
    except Exception as exc:
        console.print(f"[bold red]✗ Search failed:[/] {exc}")
        raise typer.Exit(code=1)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
