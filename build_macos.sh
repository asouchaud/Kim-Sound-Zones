#!/usr/bin/env bash
# Build the macOS app. Run on a Mac from the project folder:
#   chmod +x build_macos.sh
#   ./build_macos.sh
#
# Output: dist/BinauralSoundZones.app
# Put your .wav / .mp3 files in: dist/BinauralSoundZones.app/Contents/MacOS/sounds/
#   (or next to the .app if you copy a "sounds" folder beside it — see README)

set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt -q

echo "Building app bundle (this may take several minutes)..."
.venv/bin/python -m PyInstaller --noconfirm --clean yebin.spec

# Writable sounds folder next to the app binary (for user's .wav / .mp3 files)
MACOS_SOUNDS="dist/BinauralSoundZones.app/Contents/MacOS/sounds"
mkdir -p "$MACOS_SOUNDS"
cp -R sounds/* "$MACOS_SOUNDS/" 2>/dev/null || true

echo
echo "Build succeeded."
echo "  Run:     open dist/BinauralSoundZones.app"
echo "  Sounds:  place files in dist/BinauralSoundZones.app/Contents/MacOS/sounds/"
echo "           (create the sounds folder if it is missing)"
echo
echo "Copy BinauralSoundZones.app to another Mac to share it."
