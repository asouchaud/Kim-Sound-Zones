"""Real-time binaural audio engine.

A ``sounddevice`` output stream drives a callback on the audio thread. For every
audible zone the callback:

  1. pulls the next mono block (looping),
  2. picks the nearest-azimuth HRIR pair from the KEMAR table,
  3. convolves the block with each ear's impulse response using single-block
     overlap-add (persistent per-zone tail buffers preserve continuity),
  4. crossfades over one block whenever the chosen HRIR changes, and applies a
     per-sample gain ramp,

then sums all zones, applies the master gain and clips.

The game (main) thread only ever calls :meth:`update_zone`, which writes the
live ``(active, gain, azimuth)`` parameters under a short lock. The audio thread
reads a snapshot of those parameters under the same lock and owns everything
else (read positions, tails, smoothing state).
"""
from __future__ import annotations

import threading

import numpy as np
import sounddevice as sd
from scipy.signal import fftconvolve

from .config import BLOCK_SIZE, MASTER_GAIN, SAMPLE_RATE
from .hrtf import BinauralHRTF
from .sound_zone import SoundZone


class AudioEngine:
    def __init__(self, hrtf: BinauralHRTF,
                 sample_rate: int = SAMPLE_RATE, block_size: int = BLOCK_SIZE):
        self.hrtf = hrtf
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.tail_len = hrtf.tail_length

        self._zones: list[SoundZone] = []
        self._lock = threading.Lock()
        self._stream: sd.OutputStream | None = None

    # ------------------------------------------------------------------
    # Registration / control (game thread)
    # ------------------------------------------------------------------
    def register(self, zone: SoundZone) -> None:
        zone.tail_l = np.zeros(self.tail_len, dtype=np.float32)
        zone.tail_r = np.zeros(self.tail_len, dtype=np.float32)
        zone.cur_gain = 0.0
        zone._prev_idx = -1
        with self._lock:
            self._zones.append(zone)

    def clear(self) -> None:
        """Remove all zones (used when returning to the menu)."""
        with self._lock:
            self._zones = []

    def update_zone(self, zone: SoundZone, active: bool,
                    azimuth: float, gain: float) -> None:
        with self._lock:
            zone.active = active
            zone.target_azimuth = float(azimuth)
            zone.target_gain = float(gain)

    def start(self) -> None:
        self._stream = sd.OutputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=2,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    # ------------------------------------------------------------------
    # Audio thread
    # ------------------------------------------------------------------
    def _ola(self, x: np.ndarray, h: np.ndarray,
             tail: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Single-block overlap-add convolution.

        Returns ``(block_out, new_tail)`` where ``block_out`` has ``len(x)``
        samples and ``new_tail`` has ``len(h) - 1`` samples to carry forward.
        """
        full = fftconvolve(x, h)
        l1 = tail.size
        full[:l1] += tail
        n = x.size
        return full[:n], full[n:].copy()

    def _callback(self, outdata, frames, time_info, status):  # noqa: ARG002
        with self._lock:
            snapshot = [
                (z, z.active, z.target_gain, z.target_azimuth)
                for z in self._zones
            ]

        mix = np.zeros((frames, 2), dtype=np.float32)

        for zone, active, target_gain, azimuth in snapshot:
            target = target_gain if active else 0.0
            g0 = zone.cur_gain

            # Fully silent and staying silent: skip work, reset state cleanly.
            if g0 <= 1e-4 and target <= 1e-4:
                zone.cur_gain = 0.0
                zone.tail_l.fill(0.0)
                zone.tail_r.fill(0.0)
                zone._prev_idx = -1
                continue

            gain_ramp = np.linspace(g0, target, frames, dtype=np.float32)
            zone.cur_gain = target

            mono = zone.next_block(frames)
            idx = self.hrtf.nearest_index(azimuth)
            left_ir = self.hrtf.left[idx]
            right_ir = self.hrtf.right[idx]

            out_l, tail_l = self._ola(mono, left_ir, zone.tail_l)
            out_r, tail_r = self._ola(mono, right_ir, zone.tail_r)

            # Crossfade across the block when the HRIR direction changes.
            if zone._prev_idx != -1 and zone._prev_idx != idx:
                prev_l = self.hrtf.left[zone._prev_idx]
                prev_r = self.hrtf.right[zone._prev_idx]
                old_l, _ = self._ola(mono, prev_l, zone.tail_l)
                old_r, _ = self._ola(mono, prev_r, zone.tail_r)
                fade = np.linspace(0.0, 1.0, frames, dtype=np.float32)
                out_l = old_l * (1.0 - fade) + out_l * fade
                out_r = old_r * (1.0 - fade) + out_r * fade

            zone.tail_l[:] = tail_l
            zone.tail_r[:] = tail_r
            zone._prev_idx = idx

            mix[:, 0] += gain_ramp * out_l
            mix[:, 1] += gain_ramp * out_r

        mix *= MASTER_GAIN
        np.clip(mix, -1.0, 1.0, out=mix)
        outdata[:] = mix
