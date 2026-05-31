#!/usr/bin/env bash
# Build the macOS app bundle. Run from a terminal in this folder.
# Output: dist/BinauralSoundZones.app
set -e

python3 -m pip install -r requirements.txt
python3 -m PyInstaller --noconfirm yebin.spec

echo
echo "Done. Launch: open dist/BinauralSoundZones.app"
