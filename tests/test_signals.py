"""Tests for the signals module."""

import tempfile
from pathlib import Path

from spectralint.signals import extract_signal


def test_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        f.flush()
        sig = extract_signal(Path(f.name))
    assert sig.length == 0


def test_basic_scoring():
    code = """
def hello():
    if True:
        for i in range(10):
            print(i)
    return None
""".strip()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        sig = extract_signal(Path(f.name))
    assert sig.length == 5
    # The for-loop line should have the highest score (deepest + branch keyword)
    scores = sig.raw_array
    assert scores[2] > scores[0]  # for-loop line > def line


def test_blank_lines_score_zero():
    code = "x = 1\n\n\ny = 2\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        sig = extract_signal(Path(f.name))
    assert sig.raw_array[1] == 0.0
    assert sig.raw_array[2] == 0.0
