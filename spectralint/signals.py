"""
signals.py — Convert source files into complexity signals.

Each line of code is scored by a lightweight heuristic that accounts for:
  - indentation depth (nesting)
  - token density (non-whitespace characters)
  - branching keywords (if, for, while, try, match, switch, case)
  - string/comment noise ratio

The resulting 1-D signal (one float per line) is the raw input to the
spectral analysis pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# Language-agnostic branching keywords (covers Python, Go, TS, Rust, C, etc.)
_BRANCH_KEYWORDS = re.compile(
    r"\b(if|else|elif|for|while|do|switch|case|match|try|except|catch|finally|"
    r"with|async|await|return|yield|raise|throw|break|continue)\b"
)

_COMMENT_PATTERNS = re.compile(r"(#.*|//.*|/\*.*?\*/)", re.DOTALL)


@dataclass
class LineSignal:
    """Complexity signal for a single line."""
    lineno: int
    indent_depth: int
    token_density: float
    branch_hits: int
    raw_score: float


@dataclass
class FileSignal:
    """Full complexity signal for a file."""
    path: Path
    lines: List[LineSignal] = field(default_factory=list)

    @property
    def raw_array(self) -> list[float]:
        return [ls.raw_score for ls in self.lines]

    @property
    def length(self) -> int:
        return len(self.lines)


def _score_line(lineno: int, line: str) -> LineSignal:
    stripped = line.rstrip()
    if not stripped:
        return LineSignal(lineno=lineno, indent_depth=0, token_density=0.0, branch_hits=0, raw_score=0.0)

    # Indent depth (tabs -> 4 spaces equiv)
    expanded = stripped.expandtabs(4)
    indent = len(expanded) - len(expanded.lstrip())
    indent_depth = indent // 4

    # Token density — ratio of non-whitespace chars to line length
    non_ws = len(re.sub(r"\s", "", stripped))
    token_density = non_ws / max(len(stripped), 1)

    # Branching keyword hits
    code_only = _COMMENT_PATTERNS.sub("", stripped)
    branch_hits = len(_BRANCH_KEYWORDS.findall(code_only))

    # Composite score
    raw_score = (indent_depth * 1.5) + (token_density * 2.0) + (branch_hits * 3.0)
    return LineSignal(lineno=lineno, indent_depth=indent_depth, token_density=token_density,
                      branch_hits=branch_hits, raw_score=raw_score)


def extract_signal(path: Path) -> FileSignal:
    """Read a source file and return its per-line complexity signal."""
    text = path.read_text(errors="replace")
    lines = text.splitlines()
    fs = FileSignal(path=path)
    for i, line in enumerate(lines, start=1):
        fs.lines.append(_score_line(i, line))
    return fs
