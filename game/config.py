"""Global configuration, constants and resource-path resolution.

Keeping these values in one place makes it easy to tweak the look and feel of
the game and to keep the audio engine and the game loop in sync (they must
agree on sample rate and block size).
"""
from __future__ import annotations

import os
import sys

# ----------------------------------------------------------------------------
# Display / game loop
# ----------------------------------------------------------------------------
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60
WINDOW_TITLE = "Binaural Sound Zones"

# ----------------------------------------------------------------------------
# Audio engine
# ----------------------------------------------------------------------------
# KEMAR HRTFs are recorded at 44.1 kHz, so the whole engine runs at that rate.
SAMPLE_RATE = 44100
# Block size must be >= (HRIR length - 1) for single-block overlap-add to work.
# KEMAR impulse responses are 512 taps, so 1024 gives us comfortable headroom.
BLOCK_SIZE = 1024
# Master output gain applied after summing all zones (headroom against clipping).
MASTER_GAIN = 0.8

# ----------------------------------------------------------------------------
# Player
# ----------------------------------------------------------------------------
PLAYER_SPEED = 260.0  # pixels per second
PLAYER_SIZE = 14      # half-length of the cross arms in pixels

# ----------------------------------------------------------------------------
# Colours (R, G, B)
# ----------------------------------------------------------------------------
COLOR_BG = (18, 18, 24)
COLOR_GRID = (32, 34, 44)
COLOR_PLAYER = (240, 240, 245)
COLOR_TEXT = (200, 205, 215)
COLOR_TEXT_DIM = (120, 125, 135)
COLOR_ZONE_ACTIVE = (90, 200, 160)
COLOR_ZONE_IDLE = (70, 90, 130)


def resource_path(*parts: str) -> str:
    """Return an absolute path to a bundled resource.

    Works both when running from source and when frozen by PyInstaller, where
    data files are unpacked into the directory given by ``sys._MEIPASS``.
    """
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)
