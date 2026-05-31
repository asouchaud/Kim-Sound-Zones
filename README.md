# Binaural Sound Zones

A small 2D game built with `pygame` and a real-time **binaural (3D) audio**
engine. You control a cross-shaped player that walks around a top-down world.
Moving shapes are **sound zones**: when you step inside one you hear its sound,
spatialised with a head-related transfer function (HRTF) so it appears to come
from the direction of the zone's centre relative to you.

> Use headphones. Binaural audio only works over headphones - on speakers the
> left/right ear cues are lost.

## How to play

1. Launch the game. You start on a **setup menu**.
2. On the left, drag the **Width**, **Height** and **Speed** sliders to shape an
   oval (equal width and height makes a circle), pick a **Motion** and a
   **Sound** with the `<` / `>` arrows, then click **"Add this zone"**. Add as
   many as you like - they appear in the list on the right.
3. Set the **listener hearing range** (how big your hearing circle is).
4. Click **Start**.
5. Move the cross with **WASD / arrow keys**. When your hearing circle overlaps
   a zone you hear its sound, coming from the zone's direction and getting louder
   as you get closer. Press **Esc** to return to the menu.

> Use headphones. Binaural audio only works over headphones - on speakers the
> left/right ear cues are lost.

## How it works

- **Player** (`game/player.py`): a cross with a fixed "up" heading and a
  *listener zone* (a circle around it). A sound plays only while its zone
  overlaps this circle.
- **Sound zones** (`game/sound_zone.py`): each is an oval (a circle when width
  equals height) with its own width, height, a mono sound, and a movement
  `Trajectory` (`game/trajectories.py`: static, bouncing, circular, wander).
- **Setup** (`game/setup.py`, `game/menu.py`): the menu produces simple
  `ZoneSpec` descriptions; `build_zone_from_spec` turns them into live zones,
  and `SoundCatalog` lists the built-in sounds plus your own `.wav` files.
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

Built-in sounds (tones, pink noise, a chirp) are always available. To add your
own, just drop `.wav` or `.mp3` files into the **`sounds/`** folder next to the
game (the folder contains a `HOW_TO_ADD_SOUNDS.txt` reminder). On the menu, click
**"Refresh sounds"** (or restart) and your files appear in the **Sound** option,
listed by their file name.

`.wav` and `.mp3` are supported (decoded via `soundfile`/libsndfile). Stereo
files are mixed to mono and any sample rate is converted automatically to the
engine's 44.1 kHz.

## Building a standalone executable

PyInstaller packages the game for **Windows** and **macOS**. You must build on each
OS separately (a Windows build cannot run on Mac, and vice versa). The first build
takes several minutes.

### Windows (build on a Windows PC)

Double-click **`build_windows.bat`** or run it in a terminal from this folder.

Output:

- **`dist\BinauralSoundZones\BinauralSoundZones.exe`** — double-click to play
- **`dist\BinauralSoundZones\sounds\`** — drop your `.wav` / `.mp3` files here

Copy the whole **`BinauralSoundZones`** folder to another Windows computer to share it.

### macOS (build on a Mac)

```bash
chmod +x build_macos.sh
./build_macos.sh
```

Output:

- **`dist/BinauralSoundZones.app`** — open with `open dist/BinauralSoundZones.app`
- Custom sounds: create **`dist/BinauralSoundZones.app/Contents/MacOS/sounds/`** and
  add your `.wav` / `.mp3` files there (then use **Refresh sounds** in the menu)

Copy **`BinauralSoundZones.app`** to another Mac to share it. If macOS blocks the
app the first time, right-click the app → **Open**, or allow it in **Privacy &
Security** settings.

## Project layout

```
main.py                 Entry point: menu -> game loop
game/
  config.py             Constants, mappings + paths (resource/user dirs)
  player.py             Player (the cross) + listener hearing circle
  trajectories.py       Zone movement patterns
  sound_zone.py         SoundZone shapes, geometry, intersection, playback
  sounds.py             Sound generators, load_wav(), list_user_wavs()
  setup.py              ZoneSpec, SoundCatalog, build_zone_from_spec
  menu.py               Mouse-driven setup screen
  hrtf.py               KEMAR HRTF loading + nearest-azimuth lookup
  audio_engine.py       Real-time binaural mixer (sounddevice)
sounds/                 Drop your own .wav files here
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
