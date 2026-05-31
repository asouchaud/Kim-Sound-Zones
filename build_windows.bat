@echo off
REM Build the Windows app. Run this file from the project folder (double-click or terminal).
REM Output folder: dist\BinauralSoundZones\
REM   Run: dist\BinauralSoundZones\BinauralSoundZones.exe
REM   Put your .wav / .mp3 files in: dist\BinauralSoundZones\sounds\

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing dependencies...
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -q

echo Building executable (this may take several minutes)...
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean yebin.spec

if errorlevel 1 (
    echo Build FAILED.
    exit /b 1
)

REM Writable sounds folder next to the .exe (for user's .wav / .mp3 files)
if exist "dist\BinauralSoundZones\sounds" rmdir /S /Q "dist\BinauralSoundZones\sounds" 2>nul
if exist "dist\BinauralSoundZones\sounds" del /F "dist\BinauralSoundZones\sounds" 2>nul
mkdir "dist\BinauralSoundZones\sounds"
xcopy /E /Y /I "sounds" "dist\BinauralSoundZones\sounds\" >nul

echo.
echo Build succeeded.
echo   Run:     dist\BinauralSoundZones\BinauralSoundZones.exe
echo   Sounds:  dist\BinauralSoundZones\sounds\
echo.
echo You can copy the whole "BinauralSoundZones" folder to another Windows PC.
echo.
echo Optional: run verify_bundle.py and verify_frozen.py to test the build.
pause
