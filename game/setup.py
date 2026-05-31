"""Bridges the friendly menu choices and the actual game objects.

* ``ZoneSpec`` is a plain description of one zone, as chosen in the menu
  (shape / size / speed / motion / sound), with no audio or pygame objects.
* ``SoundCatalog`` lists the sounds the player can pick: a few built-in
  generated sounds plus any .wav files found in the user's ``sounds`` folder.
* ``build_zone_from_spec`` turns a ``ZoneSpec`` into a ready-to-play
  :class:`SoundZone` (loads/generates the audio, picks a start position and a
  movement trajectory).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from . import sounds
from .config import user_sounds_dir
from .sound_zone import SoundZone
from .trajectories import Circular, LinearBounce, RandomWalk, Static

# The friendly option list shown in the menu (order matters for display).
MOTIONS = ["static", "bounce", "circular", "wander"]

# Slider ranges (pixels). Width/height are the full diameters of the oval.
WIDTH_RANGE = (40.0, 280.0)
HEIGHT_RANGE = (40.0, 280.0)
SPEED_RANGE = (0.0, 260.0)  # pixels per second
ROTATION_RANGE = (0.0, 180.0)  # degrees (an ellipse repeats every 180 deg)


@dataclass
class ZoneSpec:
    width: float = 120.0
    height: float = 120.0
    angle: float = 0.0
    speed: float = 100.0
    motion: str = "bounce"
    sound: str = "Tone 220 Hz"

    def summary(self) -> str:
        shape = "circle" if abs(self.width - self.height) < 6 else "oval"
        dims = f"{int(self.width)}x{int(self.height)}"
        rot = "" if (shape == "circle" or not self.angle) else f" @{int(self.angle)}deg"
        if self.motion == "static":
            motion = "still"
        else:
            motion = f"{self.motion} ({int(self.speed)})"
        return f"{shape} {dims}{rot}, {motion} - {self.sound}"


class SoundCatalog:
    """The set of sounds available to choose from in the menu."""

    def __init__(self):
        self._builtins = {
            "Tone 220 Hz": lambda: sounds.tone(220.0, harmonics=4),
            "Tone 330 Hz": lambda: sounds.tone(330.0, harmonics=3),
            "Tone 440 Hz": lambda: sounds.tone(440.0, harmonics=3),
            "Pink noise": lambda: sounds.pink_noise(seed=1),
            "Chirp": lambda: sounds.chirp(180.0, 900.0),
        }
        self._wavs: dict[str, str] = {}
        self.refresh()

    def refresh(self) -> None:
        """Re-scan the user's sounds folder for .wav and .mp3 files."""
        self._wavs = {}
        for name, path in sounds.list_user_sounds(user_sounds_dir()):
            label = name
            # Avoid clashing with a built-in name.
            while label in self._builtins or label in self._wavs:
                label += " "
            self._wavs[label] = path

    def names(self) -> list[str]:
        return list(self._builtins) + list(self._wavs)

    def render(self, name: str):
        """Return the mono numpy array for the named sound."""
        if name in self._builtins:
            return self._builtins[name]()
        if name in self._wavs:
            return sounds.load_audio(self._wavs[name])
        # Fallback if a previously-chosen file disappeared.
        return sounds.tone(330.0)


def build_zone_from_spec(zone_id: int, spec: ZoneSpec, catalog: SoundCatalog,
                         bounds: tuple[int, int]) -> SoundZone:
    w, h = bounds
    margin = 60.0
    sound = catalog.render(spec.sound)

    start_x = random.uniform(margin, w - margin)
    start_y = random.uniform(margin, h - margin)

    speed = float(spec.speed)
    if spec.motion == "static" or speed == 0.0:
        trajectory = Static(start_x, start_y)
    elif spec.motion == "bounce":
        angle = random.uniform(0, 2 * math.pi)
        trajectory = LinearBounce(start_x, start_y,
                                  math.cos(angle) * speed,
                                  math.sin(angle) * speed, margin=margin)
    elif spec.motion == "circular":
        orbit = min(w, h) * 0.32
        # Convert linear speed (px/s) to angular speed (rad/s) for this orbit.
        ang = speed / orbit if orbit > 0 else 0.0
        trajectory = Circular(w * 0.5, h * 0.5, orbit, angular_speed=ang,
                              phase=random.uniform(0, 2 * math.pi))
    else:  # wander
        trajectory = RandomWalk(start_x, start_y, speed=speed, margin=margin)

    return SoundZone(zone_id, sound, shape="ellipse", trajectory=trajectory,
                     width=spec.width, height=spec.height, angle=spec.angle,
                     label=spec.sound)
