"""Head-related transfer function (HRTF) lookup for binaural rendering.

We load the in-built KEMAR HRTF that ships with the ``slab`` package, keep only
the sources on (or very near) the horizontal plane, and expose a fast
nearest-azimuth lookup that returns a pair of finite impulse responses
(left ear, right ear).

Azimuth convention used throughout the game
--------------------------------------------
We use *game azimuth* where ``0`` is straight ahead and **positive is to the
player's right**. KEMAR stores azimuth increasing counter-clockwise (90 deg is
the LEFT ear), so we convert with ``game_az = -kemar_az`` when building the
table. This was verified empirically: a KEMAR source at azimuth 90 has nearly
all of its energy in the left channel.
"""
from __future__ import annotations

import numpy as np


def _wrap180(deg: np.ndarray | float) -> np.ndarray | float:
    """Wrap angle(s) in degrees to the half-open range [-180, 180)."""
    return (np.asarray(deg) + 180.0) % 360.0 - 180.0


class BinauralHRTF:
    """Nearest-neighbour HRIR lookup over the horizontal plane."""

    def __init__(self, elevation_tolerance: float = 1.0):
        import slab  # imported lazily so importing the module stays cheap

        hrtf = slab.HRTF.kemar()
        self.samplerate = int(hrtf.samplerate)

        vertical_polar = np.asarray(hrtf.sources.vertical_polar)
        azimuth = vertical_polar[:, 0]
        elevation = vertical_polar[:, 1]

        horizontal = np.where(np.abs(elevation) <= elevation_tolerance)[0]
        if horizontal.size == 0:
            raise RuntimeError("No horizontal-plane sources found in KEMAR HRTF.")

        game_az = []
        left = []
        right = []
        for idx in horizontal:
            data = np.asarray(hrtf[int(idx)].data, dtype=np.float32)
            # data is (n_taps, 2): column 0 = left ear, column 1 = right ear.
            left.append(data[:, 0])
            right.append(data[:, 1])
            game_az.append(-float(azimuth[idx]))

        order = np.argsort(_wrap180(np.array(game_az)))
        self.azimuths = _wrap180(np.array(game_az))[order].astype(np.float32)
        self.left = np.stack(left)[order].astype(np.float32)
        self.right = np.stack(right)[order].astype(np.float32)
        self.n_taps = self.left.shape[1]

    @property
    def tail_length(self) -> int:
        """Number of overlap samples produced by a convolution (M - 1)."""
        return self.n_taps - 1

    def nearest_index(self, game_azimuth: float) -> int:
        """Return the table index whose azimuth is closest (circularly)."""
        diff = np.abs(_wrap180(self.azimuths - game_azimuth))
        return int(np.argmin(diff))

    def hrir(self, game_azimuth: float) -> tuple[np.ndarray, np.ndarray]:
        """Return ``(left_ir, right_ir)`` for the nearest stored azimuth."""
        i = self.nearest_index(game_azimuth)
        return self.left[i], self.right[i]
