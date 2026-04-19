"""
spectrum.py — FFT-based spectral analysis of complexity signals.

Takes a 1-D complexity signal (from signals.py) and produces:
  - frequency-domain magnitudes
  - dominant frequency (the "complexity rhythm" of the file)
  - spectral entropy (how chaotic vs. structured the complexity is)
  - anomaly bands (frequency ranges where magnitude spikes indicate
    irregular structural patterns)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

import numpy as np

from .signals import FileSignal


@dataclass
class SpectralBand:
    """A notable frequency band in the spectrum."""
    freq_index: int
    magnitude: float
    label: str  # "dominant", "harmonic", "anomaly"


@dataclass
class SpectrumResult:
    """Full spectral analysis result for one file."""
    path: str
    num_lines: int
    magnitudes: np.ndarray
    dominant_freq: int
    dominant_magnitude: float
    spectral_entropy: float
    bands: List[SpectralBand] = field(default_factory=list)
    complexity_class: str = "stable"

    @property
    def top_frequencies(self) -> list[tuple[int, float]]:
        """Return top-5 frequency components by magnitude."""
        indices = np.argsort(self.magnitudes)[::-1][:5]
        return [(int(i), float(self.magnitudes[i])) for i in indices]


def analyze(signal: FileSignal, anomaly_threshold: float = 2.0) -> SpectrumResult:
    """Run spectral analysis on a file signal."""
    raw = np.array(signal.raw_array, dtype=np.float64)

    if len(raw) < 4:
        return SpectrumResult(
            path=str(signal.path), num_lines=signal.length,
            magnitudes=np.array([]), dominant_freq=0,
            dominant_magnitude=0.0, spectral_entropy=0.0,
            complexity_class="trivial",
        )

    # Remove DC component (mean complexity) and apply Hann window
    raw = raw - raw.mean()
    window = np.hanning(len(raw))
    windowed = raw * window

    # FFT — keep only positive frequencies
    fft_vals = np.fft.rfft(windowed)
    magnitudes = np.abs(fft_vals)[1:]  # drop DC bin

    if magnitudes.size == 0 or magnitudes.max() == 0:
        return SpectrumResult(
            path=str(signal.path), num_lines=signal.length,
            magnitudes=magnitudes, dominant_freq=0,
            dominant_magnitude=0.0, spectral_entropy=0.0,
            complexity_class="flat",
        )

    # Dominant frequency
    dominant_idx = int(np.argmax(magnitudes))
    dominant_mag = float(magnitudes[dominant_idx])

    # Spectral entropy (normalized)
    normed = magnitudes / magnitudes.sum()
    normed = normed[normed > 0]
    entropy = float(-np.sum(normed * np.log2(normed)))
    max_entropy = math.log2(len(magnitudes)) if len(magnitudes) > 1 else 1.0
    norm_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    # Detect anomaly bands — magnitudes > threshold * std above mean
    mean_mag = float(magnitudes.mean())
    std_mag = float(magnitudes.std())
    bands: list[SpectralBand] = []

    bands.append(SpectralBand(freq_index=dominant_idx, magnitude=dominant_mag, label="dominant"))

    for i, m in enumerate(magnitudes):
        if i == dominant_idx:
            continue
        if std_mag > 0 and (m - mean_mag) / std_mag > anomaly_threshold:
            bands.append(SpectralBand(freq_index=i, magnitude=float(m), label="anomaly"))

    # Complexity class heuristic
    if norm_entropy > 0.85:
        cclass = "chaotic"
    elif norm_entropy < 0.3:
        cclass = "rhythmic"
    elif len(bands) > 3:
        cclass = "spiky"
    else:
        cclass = "stable"

    return SpectrumResult(
        path=str(signal.path), num_lines=signal.length,
        magnitudes=magnitudes, dominant_freq=dominant_idx + 1,
        dominant_magnitude=dominant_mag, spectral_entropy=round(norm_entropy, 4),
        bands=bands, complexity_class=cclass,
    )
