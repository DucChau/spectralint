"""
render.py — Rich terminal rendering for spectral analysis results.
"""

from __future__ import annotations

from typing import List

import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .spectrum import SpectrumResult

_SPARK_CHARS = "▁▂▃▄▅▆▇█"
_CLASS_COLORS = {
    "chaotic": "bold red",
    "spiky": "bold yellow",
    "rhythmic": "bold cyan",
    "stable": "bold green",
    "flat": "dim",
    "trivial": "dim",
}


def _sparkline(values: np.ndarray, width: int = 40) -> str:
    """Render a numpy array as a unicode sparkline."""
    if len(values) == 0:
        return ""
    # Resample to `width` bins
    if len(values) > width:
        indices = np.linspace(0, len(values) - 1, width).astype(int)
        sampled = values[indices]
    else:
        sampled = values
    mn, mx = sampled.min(), sampled.max()
    rng = mx - mn if mx != mn else 1.0
    normalized = (sampled - mn) / rng
    return "".join(_SPARK_CHARS[min(int(v * (len(_SPARK_CHARS) - 1)), len(_SPARK_CHARS) - 1)] for v in normalized)


def render_table(results: List[SpectrumResult], console: Console | None = None, top_n: int = 30) -> None:
    """Print a summary table of spectral results."""
    console = console or Console()

    # Sort by spectral entropy descending (most chaotic first)
    ranked = sorted(results, key=lambda r: r.spectral_entropy, reverse=True)[:top_n]

    table = Table(title="⚡ spectralint — Codebase Spectral Analysis", show_lines=False, padding=(0, 1))
    table.add_column("File", style="bold white", max_width=50, no_wrap=True)
    table.add_column("Lines", justify="right", style="cyan")
    table.add_column("Dom.Freq", justify="right", style="magenta")
    table.add_column("Entropy", justify="right")
    table.add_column("Class", justify="center")
    table.add_column("Spectrum", min_width=42)

    for r in ranked:
        color = _CLASS_COLORS.get(r.complexity_class, "white")
        entropy_str = f"{r.spectral_entropy:.3f}"
        spark = _sparkline(r.magnitudes) if len(r.magnitudes) > 0 else "—"

        table.add_row(
            _truncate(r.path, 50),
            str(r.num_lines),
            str(r.dominant_freq),
            Text(entropy_str, style="bold" if r.spectral_entropy > 0.8 else ""),
            Text(r.complexity_class, style=color),
            spark,
        )

    console.print()
    console.print(table)
    console.print()

    # Summary panel
    total = len(results)
    chaotic = sum(1 for r in results if r.complexity_class == "chaotic")
    spiky = sum(1 for r in results if r.complexity_class == "spiky")
    rhythmic = sum(1 for r in results if r.complexity_class == "rhythmic")

    summary = (
        f"[bold]Total files analyzed:[/bold] {total}\n"
        f"[red]Chaotic:[/red] {chaotic}  [yellow]Spiky:[/yellow] {spiky}  "
        f"[cyan]Rhythmic:[/cyan] {rhythmic}  [green]Stable:[/green] {total - chaotic - spiky - rhythmic}"
    )
    console.print(Panel(summary, title="Summary", border_style="blue"))


def render_detail(result: SpectrumResult, console: Console | None = None) -> None:
    """Print detailed spectral breakdown for a single file."""
    console = console or Console()
    color = _CLASS_COLORS.get(result.complexity_class, "white")

    console.print(f"\n[bold]📄 {result.path}[/bold]")
    console.print(f"   Lines: {result.num_lines}  |  Class: [{color}]{result.complexity_class}[/{color}]"
                  f"  |  Entropy: {result.spectral_entropy:.4f}")

    if len(result.magnitudes) > 0:
        console.print(f"   Spectrum: {_sparkline(result.magnitudes, width=60)}")

    if result.bands:
        console.print("   Bands:")
        for b in result.bands:
            icon = "🔴" if b.label == "anomaly" else "🔵"
            console.print(f"     {icon} freq={b.freq_index}  mag={b.magnitude:.2f}  [{b.label}]")
    console.print()


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else "…" + s[-(n - 1):]
