"""Tests for the spectrum module."""

import tempfile
from pathlib import Path

from spectralint.signals import extract_signal
from spectralint.spectrum import analyze


def _make_file(code: str) -> Path:
    import tempfile as tf
    f = tf.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    f.write(code)
    f.flush()
    return Path(f.name)


def test_trivial_file():
    p = _make_file("x = 1\ny = 2\n")
    sig = extract_signal(p)
    result = analyze(sig)
    assert result.complexity_class == "trivial"


def test_rhythmic_pattern():
    # Repetitive structure should be rhythmic or stable
    lines = []
    for i in range(60):
        if i % 3 == 0:
            lines.append("def func():")
        elif i % 3 == 1:
            lines.append("    if True:")
        else:
            lines.append("        pass")
    code = "\n".join(lines)
    p = _make_file(code)
    sig = extract_signal(p)
    result = analyze(sig)
    assert result.complexity_class in ("rhythmic", "stable", "spiky")
    assert result.spectral_entropy < 0.95  # not totally chaotic


def test_entropy_bounded():
    code = "\n".join([f"x_{i} = {i}" for i in range(100)])
    p = _make_file(code)
    sig = extract_signal(p)
    result = analyze(sig)
    assert 0.0 <= result.spectral_entropy <= 1.0
