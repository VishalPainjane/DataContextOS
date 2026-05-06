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
    from datacontextos import __version__

    console.print(f"[bold cyan]DataContextOS[/] v{__version__}")


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
def search(
    query: str = typer.Argument(..., help="Natural language query to search for"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results to return"),
    domain: Optional[str] = typer.Option(None, "--domain", "-d", help="Filter by domain"),
) -> None:
    """Search for data assets using natural language."""
    console.print(f'[cyan]►[/] Searching: "[bold]{query}[/]"...')

    async def _run() -> None:
        from sqlalchemy import select

        from database.engine import get_session_factory, init_db
        from database.tables import AssetRecord

        await init_db()
        factory = get_session_factory()

        async with factory() as session:
            stmt = select(AssetRecord).limit(top_k * 10)
            if domain:
                stmt = stmt.where(AssetRecord.domain == domain)
            result = await session.execute(stmt)
            records = result.scalars().all()

        if not records:
            console.print("[yellow]No assets found. Run [bold]dcos ingest[/] first.[/]")
            return

        table = Table(title=f'Search Results for "{query}"', show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Asset Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Domain", style="yellow")
        table.add_column("Description", style="white", max_width=60)

        # Simple keyword filter as a placeholder for vector search
        query_lower = query.lower()
        matches = [
            r for r in records
            if query_lower in r.asset_name.lower()
            or query_lower in (r.description or "").lower()
            or query_lower in (r.domain or "").lower()
        ][:top_k]

        for i, rec in enumerate(matches or records[:top_k], start=1):
            table.add_row(
                str(i),
                rec.asset_name,
                rec.asset_type,
                rec.domain or "—",
                (rec.description or "")[:80],
            )

        console.print(table)

    try:
        asyncio.run(_run())
    except Exception as exc:
        console.print(f"[bold red]✗ Search failed:[/] {exc}")
        raise typer.Exit(code=1)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
