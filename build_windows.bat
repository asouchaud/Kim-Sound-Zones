@echo off
REM Build the Windows executable. Run from a terminal in this folder.
REM Output: dist\BinauralSoundZones\BinauralSoundZones.exe

python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm yebin.spec

echo.
echo Done. Launch: dist\BinauralSoundZones\BinauralSoundZones.exe
