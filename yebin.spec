# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Binaural Sound Zones game.

Build (run on the target OS - PyInstaller cannot cross-compile):

    pyinstaller yebin.spec

This bundles:
  * slab's data files (the KEMAR .sofa HRTF dataset),
  * sounddevice's bundled PortAudio shared library,
  * the local assets/ folder (drop your own .wav files here).
"""
import os

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# slab ships the KEMAR HRTF data; pull in everything it (and the HRTF/IO stack)
# needs. sounddevice/soundfile are handled by their own contrib hooks (they are
# single modules, not packages, so collect_all is not appropriate for them).
for pkg in ("slab", "h5netcdf", "h5py"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

hiddenimports += ["sounddevice", "soundfile", "cffi", "_cffi_backend"]

# Ship the "sounds" folder (with its how-to note) next to the executable so the
# user has an obvious place to drop their own .wav files.
if os.path.isdir("sounds"):
    datas.append(("sounds", "sounds"))

# slab imports matplotlib at import time, so matplotlib must stay - but we never
# plot, so exclude every GUI toolkit (matplotlib falls back to the headless Agg
# backend) and other large, unused dev/notebook dependencies. Excluding the Qt
# bindings also avoids PyInstaller's "multiple Qt bindings" build error.
excludes = [
    "PyQt5", "PyQt6", "PySide2", "PySide6", "tkinter",
    "IPython", "jedi", "notebook", "nbconvert", "nbformat", "jupyter",
    "sphinx", "docutils", "pytest", "black", "yapf",
]

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BinauralSoundZones",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="BinauralSoundZones",
)

# On macOS also produce a .app bundle.
import sys
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="BinauralSoundZones.app",
        icon=None,
        bundle_identifier="com.yebin.binauralsoundzones",
    )
