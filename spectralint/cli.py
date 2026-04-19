"""
cli.py — Click-based CLI for spectralint.
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from . import __version__
from .scanner import scan_directory, DEFAULT_EXTENSIONS
from .render import render_table, render_detail


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="spectralint")
@click.pass_context
def main(ctx: click.Context) -> None:
    """⚡ spectralint — Spectral complexity analyzer for codebases."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("--top", "-n", default=30, help="Show top N files by entropy.")
@click.option("--threshold", "-t", default=2.0, help="Anomaly detection threshold (std deviations).")
@click.option("--min-lines", "-m", default=5, help="Skip files shorter than this.")
@click.option("--ext", "-e", multiple=True, help="Extra file extensions to include (e.g. .vue .svelte).")
def scan(path: str, top: int, threshold: float, min_lines: int, ext: tuple[str, ...]) -> None:
    """Scan a directory and display spectral analysis."""
    console = Console()
    root = Path(path)
    exts = set(DEFAULT_EXTENSIONS)
    for e in ext:
        exts.add(e if e.startswith(".") else f".{e}")

    console.print(f"[dim]Scanning {root} …[/dim]")
    results = list(scan_directory(root, extensions=exts, anomaly_threshold=threshold, min_lines=min_lines))

    if not results:
        console.print("[yellow]No source files found.[/yellow]")
        return

    render_table(results, console=console, top_n=top)


@main.command()
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option("--threshold", "-t", default=2.0, help="Anomaly detection threshold.")
def inspect(filepath: str, threshold: float) -> None:
    """Inspect a single file in detail."""
    console = Console()
    from .signals import extract_signal
    from .spectrum import analyze

    p = Path(filepath)
    sig = extract_signal(p)
    result = analyze(sig, anomaly_threshold=threshold)
    render_detail(result, console=console)

    # Also show top frequencies
    if result.top_frequencies:
        console.print("[bold]Top frequency components:[/bold]")
        for freq, mag in result.top_frequencies:
            console.print(f"  freq={freq:>4d}  magnitude={mag:.2f}")
