# Binaural Sound Zones

A small 2D game built with `pygame` and a real-time **binaural (3D) audio**
engine. You control a cross-shaped player that walks around a top-down world.
Moving shapes are **sound zones**: when you step inside one you hear its sound,
spatialised with a head-related transfer function (HRTF) so it appears to come
from the direction of the zone's centre relative to you.

> Use headphones. Binaural audio only works over headphones - on speakers the
> left/right ear cues are lost.

## How it works

- **Player** (`game/player.py`): a cross with a fixed "up" heading. Move with
  `WASD` or the arrow keys; `Esc` quits.
- **Sound zones** (`game/sound_zone.py`): each has a shape (circle, rectangle,
  or polygon), a size, a mono sound, and a movement `Trajectory`
  (`game/trajectories.py`: static, bouncing, circular, random walk). The sound
  gets louder as you move toward the centre.
- **HRTF** (`game/hrtf.py`): loads the in-built KEMAR HRTF from `slab`, keeps the
  horizontal-plane impulse responses, and looks up the nearest azimuth. Game
  azimuth is `0` straight ahead, positive to your right.
- **Audio engine** (`game/audio_engine.py`): a `sounddevice` output stream
  convolves each audible zone's audio with the left/right HRIRs using
  overlap-add, crossfades when the direction changes, ramps gain to avoid
  clicks, sums all zones, and plays the stereo result in real time.

## Run from source

```bash
pip install -r requirements.txt
python main.py
```

The first launch shows a brief "Loading HRTF data..." screen while the KEMAR
dataset is read.

## Using your own sounds

Placeholder sounds (tones, pink noise, a chirp) are generated in code so the
game works out of the box. To use your own audio, load a `.wav` file and pass it
to a `SoundZone` in `build_zones()` inside `main.py`:

```python
from game import sounds
my_sound = sounds.load_wav("assets/sounds/my_clip.wav")
SoundZone(4, my_sound, shape="circle", radius=100, label="my clip")
```

`load_wav` converts to mono and resamples to the engine's 44.1 kHz rate. Stereo
files are averaged to mono. Drop files in `assets/sounds/` so they get bundled
into the executable.

## Building a standalone executable

PyInstaller is used for packaging. It **cannot cross-compile**, so build on each
target OS. The same `yebin.spec` works for both and bundles the KEMAR HRTF data,
PortAudio, and the `assets/` folder.

### Windows

```bat
build_windows.bat
```

Produces `dist\BinauralSoundZones\BinauralSoundZones.exe`.

### macOS

```bash
chmod +x build_macos.sh
./build_macos.sh
```

Produces `dist/BinauralSoundZones.app` (launch with `open dist/BinauralSoundZones.app`).

## Project layout

```
main.py                 Entry point and game loop
game/
  config.py             Constants + resource_path() for bundled data
  player.py             Player (the cross)
  trajectories.py       Zone movement patterns
  sound_zone.py         SoundZone shapes, geometry, looping playback
  sounds.py             Placeholder sound generators + load_wav()
  hrtf.py               KEMAR HRTF loading + nearest-azimuth lookup
  audio_engine.py       Real-time binaural mixer (sounddevice)
assets/sounds/          Drop your own .wav files here
yebin.spec              PyInstaller build spec
build_windows.bat       Windows build helper
build_macos.sh          macOS build helper
requirements.txt
```

## Notes / extending

- Heading is fixed pointing up. Adding rotation (e.g. `Q`/`E`) is easy: rotate
  `player.heading` and subtract that angle in `SoundZone.azimuth_to`.
- The world is top-down, so elevation is fixed at 0 and only azimuth + distance
  matter. The HRTF lookup already exposes the data needed to add elevation later.
```
