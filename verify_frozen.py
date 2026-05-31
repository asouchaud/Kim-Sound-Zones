"""Simulate frozen (PyInstaller) environment using the built _internal folder."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist" / "BinauralSoundZones"
INTERNAL = DIST / "_internal"

sys.frozen = True
sys._MEIPASS = str(INTERNAL)
os.chdir(DIST)
sys.path.insert(0, sys._MEIPASS)
if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    os.add_dll_directory(sys._MEIPASS)

errors = []

try:
    import pygame
    pygame.init()
    pygame.display.set_mode((400, 300))
except Exception as exc:
    errors.append(f"pygame: {exc}")

try:
    from game.hrtf import BinauralHRTF
    BinauralHRTF()
except Exception as exc:
    errors.append(f"HRTF: {exc}")

try:
    from game.config import user_sounds_dir
    from game.sounds import list_user_sounds
    folder = user_sounds_dir()
    list_user_sounds(folder)
except Exception as exc:
    errors.append(f"sounds: {exc}")

try:
    import sounddevice as sd
    sd.query_devices()
except Exception as exc:
    errors.append(f"sounddevice query: {exc}")

try:
    from game.audio_engine import AudioEngine
    from game.hrtf import BinauralHRTF
    eng = AudioEngine(BinauralHRTF())
    eng.start()
    eng.stop()
except Exception as exc:
    errors.append(f"audio engine: {exc}")

pygame.quit()

if errors:
    print("FROZEN SIMULATION FAILED:")
    for e in errors:
        print(" ", e)
    sys.exit(1)
print("FROZEN SIMULATION OK (pygame + HRTF + audio + sounds path)")
