"""
scanner.py — Walk a directory tree, filter source files, yield analysis results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator, Set

from .signals import extract_signal
from .spectrum import SpectrumResult, analyze

# Default extensions to scan
DEFAULT_EXTENSIONS: Set[str] = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".c", ".cpp", ".h",
    ".java", ".kt", ".rb", ".swift", ".cs", ".lua", ".zig", ".ex", ".exs",
    ".sh", ".bash", ".zsh",
}

IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build",
    ".tox", ".mypy_cache", ".ruff_cache", "target", ".next", "vendor",
}


def scan_directory(
    root: Path,
    extensions: Set[str] | None = None,
    anomaly_threshold: float = 2.0,
    min_lines: int = 5,
) -> Generator[SpectrumResult, None, None]:
    """Walk *root* and yield SpectrumResult for each matching source file."""
    exts = extensions or DEFAULT_EXTENSIONS
    for p in sorted(root.rglob("*")):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        if p.is_file() and p.suffix in exts:
            sig = extract_signal(p)
            if sig.length >= min_lines:
                yield analyze(sig, anomaly_threshold=anomaly_threshold)
