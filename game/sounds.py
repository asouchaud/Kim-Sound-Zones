"""Mono sound sources for the sound zones.

Everything here returns a 1-D ``float32`` numpy array normalised to roughly
[-1, 1] at the engine sample rate. The audio engine loops these arrays while a
zone is audible, so they are designed to loop seamlessly (an integer number of
periods, or steady-state noise).

Placeholder generators (tone / pink noise / chirp) work out of the box; the
``load_wav`` helper lets you drop in your own files later.
"""
from __future__ import annotations

import numpy as np
from scipy import signal
from scipy.io import wavfile

from .config import SAMPLE_RATE


def _normalize(x: np.ndarray, peak: float = 0.9) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    m = float(np.max(np.abs(x))) if x.size else 0.0
    if m > 0:
        x = x * (peak / m)
    return x.astype(np.float32)


def tone(freq: float = 220.0, duration: float = 1.0,
         sr: int = SAMPLE_RATE, harmonics: int = 1) -> np.ndarray:
    """A looping sine (optionally with a few harmonics for a richer timbre).

    The duration is snapped so the waveform contains a whole number of periods,
    which guarantees a click-free loop point.
    """
    period_samples = sr / freq
    n_periods = max(1, round(duration * freq))
    n = int(round(n_periods * period_samples))
    t = np.arange(n) / sr
    wave = np.zeros(n, dtype=np.float64)
    for k in range(1, harmonics + 1):
        wave += (1.0 / k) * np.sin(2 * np.pi * freq * k * t)
    return _normalize(wave)


def pink_noise(duration: float = 2.0, sr: int = SAMPLE_RATE,
               seed: int | None = None) -> np.ndarray:
    """Steady-state pink-ish noise (loops fine because it is stationary)."""
    rng = np.random.default_rng(seed)
    n = int(round(duration * sr))
    white = rng.standard_normal(n)
    # Voss-style 1/f shaping via a simple one-pole filter cascade approximation.
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1.0, -2.494956002, 2.017265875, -0.522189400]
    pink = signal.lfilter(b, a, white)
    return _normalize(pink)


def chirp(f0: float = 200.0, f1: float = 1200.0, duration: float = 1.5,
          sr: int = SAMPLE_RATE) -> np.ndarray:
    """An up/down frequency sweep that returns to its start for a clean loop."""
    n = int(round(duration * sr))
    t = np.arange(n) / sr
    half = n // 2
    up = signal.chirp(t[:half], f0=f0, f1=f1, t1=t[half - 1] if half > 1 else 1.0,
                      method="logarithmic")
    down = up[::-1]
    sweep = np.concatenate([up, down])
    if sweep.size < n:
        sweep = np.pad(sweep, (0, n - sweep.size))
    return _normalize(sweep[:n])


def load_wav(path: str, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Load a ``.wav`` file as mono float32 resampled to the engine rate.

    Stereo (and multi-channel) files are averaged down to mono. Integer PCM
    formats are scaled to [-1, 1].
    """
    file_sr, data = wavfile.read(path)
    data = np.asarray(data)

    if data.dtype.kind in "iu":
        max_val = float(np.iinfo(data.dtype).max)
        data = data.astype(np.float32) / max_val
    else:
        data = data.astype(np.float32)

    if data.ndim > 1:
        data = data.mean(axis=1)

    if file_sr != sr and data.size:
        n_out = int(round(data.size * sr / file_sr))
        data = signal.resample(data, n_out)

    return _normalize(data, peak=0.95)
