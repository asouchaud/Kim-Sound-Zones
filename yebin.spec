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
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


def _python_stdlib_dlls() -> list[tuple[str, str]]:
    """Bundle stdlib .pyd modules and their Conda DLL dependencies.

    Builds from Anaconda/Miniconda often miss companion DLLs (libffi, libbz2,
    etc.) unless they are copied into ``_internal`` next to the .pyd files.
    """
    extra: list[tuple[str, str]] = []
    seen: set[str] = set()
    base = Path(getattr(sys, "base_prefix", sys.prefix))

    def add(path: Path, dest: str = ".") -> None:
        key = path.name.lower()
        if path.is_file() and key not in seen:
            seen.add(key)
            extra.append((str(path), dest))

    if sys.platform == "win32":
        dlls = base / "DLLs"
        if dlls.is_dir():
            for pyd in dlls.glob("*.pyd"):
                add(pyd)
        lib_bin = base / "Library" / "bin"
        if lib_bin.is_dir():
            for pattern in (
                "lib*.dll", "ffi*.dll", "zlib*.dll", "bz2*.dll",
                "libbz2*.dll", "liblzma*.dll", "libexpat*.dll",
            ):
                for dll in lib_bin.glob(pattern):
                    add(dll)
    elif sys.platform == "darwin":
        for lib_dir in (base / "lib", Path(sys.prefix) / "lib"):
            if not lib_dir.is_dir():
                continue
            for pattern in ("libffi*.dylib", "libbz2*.dylib", "libz*.dylib"):
                for dylib in lib_dir.glob(pattern):
                    add(dylib)
    return extra


datas = []
binaries = _python_stdlib_dlls()
hiddenimports = []

# slab ships the KEMAR HRTF data; pull in everything it (and the HRTF/IO stack)
# needs. sounddevice/soundfile are handled by their own contrib hooks (they are
# single modules, not packages, so collect_all is not appropriate for them).
for pkg in ("numpy", "slab", "h5netcdf"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

hiddenimports += [
    "sounddevice", "soundfile", "cffi", "_cffi_backend",
    "numpy.core", "numpy.core.multiarray", "numpy.core._multiarray_umath",
    "numpy.core.umath",
]

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
    hooksconfig={"matplotlib": {"backends": ["Agg"]}},
    runtime_hooks=["rthook_numpy_compat.py", "rthook_dll_path.py"],
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
