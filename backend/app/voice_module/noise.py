from __future__ import annotations

import numpy as np


def normalize_audio(samples: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(samples))) if samples.size else 0.0
    if peak <= 0.0:
        return samples
    return samples / peak


def spectral_gate_placeholder(samples: np.ndarray, threshold: float = 0.015) -> np.ndarray:
    """Simple low-amplitude gate; replace with RNNoise/WebRTC NS for production."""
    cleaned = samples.copy()
    cleaned[np.abs(cleaned) < threshold] = 0
    return normalize_audio(cleaned)
