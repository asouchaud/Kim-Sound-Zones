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
# Setup choices -> numbers
# ----------------------------------------------------------------------------
# Radius of the circle around the listener (the "hearing range").
LISTENER_RADIUS = {"small": 70.0, "medium": 120.0, "large": 180.0}

# Folder (next to the game / project) where the user drops their own .wav files.
USER_SOUNDS_DIRNAME = "sounds"

# ----------------------------------------------------------------------------
# Colours (R, G, B)
# ----------------------------------------------------------------------------
COLOR_BG = (248, 246, 242)  # off-white
COLOR_PLAYER = (45, 50, 62)
COLOR_TEXT = (40, 44, 52)
COLOR_TEXT_DIM = (100, 105, 115)
COLOR_ZONE_OUTLINE = (130, 130, 130)
COLOR_LISTENER = (210, 145, 55)
COLOR_LISTENER_OUTLINE = (130, 130, 130)

# Menu colours
COLOR_PANEL = (235, 233, 228)
COLOR_BUTTON = (220, 218, 212)
COLOR_BUTTON_HOVER = (200, 198, 192)
COLOR_BUTTON_TEXT = (40, 44, 52)
COLOR_ACCENT = (90, 200, 160)


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


def app_dir() -> str:
    """Folder the app "lives" in - next to the executable when frozen, or the
    project root when running from source. This is a writable location, unlike
    the bundled (read-only) resources, so it is where user files belong.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def user_sounds_dir() -> str:
    """Absolute path to the folder where the user drops their own .wav files.

    Created automatically if it does not exist yet.
    """
    path = os.path.join(app_dir(), USER_SOUNDS_DIRNAME)
    os.makedirs(path, exist_ok=True)
    return path
