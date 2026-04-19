"""
export.py — JSON export for CI integration.
"""

from __future__ import annotations

import json
from typing import List

from .spectrum import SpectrumResult


def to_json(results: List[SpectrumResult]) -> str:
    """Serialize analysis results to JSON."""
    records = []
    for r in results:
        records.append({
            "path": r.path,
            "num_lines": r.num_lines,
            "dominant_freq": r.dominant_freq,
            "dominant_magnitude": round(r.dominant_magnitude, 4),
            "spectral_entropy": r.spectral_entropy,
            "complexity_class": r.complexity_class,
            "top_frequencies": [
                {"freq": f, "magnitude": round(m, 4)} for f, m in r.top_frequencies
            ],
            "anomaly_bands": [
                {"freq_index": b.freq_index, "magnitude": round(b.magnitude, 4), "label": b.label}
                for b in r.bands if b.label == "anomaly"
            ],
        })
    return json.dumps({"version": "0.1.0", "files": records}, indent=2)
