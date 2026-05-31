"""Verify the PyInstaller bundle has everything needed to run."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist" / "BinauralSoundZones"
INTERNAL = DIST / "_internal"
EXE = DIST / "BinauralSoundZones.exe"

REQUIRED_FILES = [
    INTERNAL / "python313.dll",
    INTERNAL / "_ctypes.pyd",
    INTERNAL / "ffi-8.dll",
    INTERNAL / "_bz2.pyd",
    INTERNAL / "libbz2.dll",
    INTERNAL / "slab" / "data" / "mit_kemar_normal_pinna.bz2",
    INTERNAL / "_sounddevice_data" / "portaudio-binaries" / "libportaudio64bit.dll",
    DIST / "sounds",
]

REQUIRED_IMPORTS = [
    "pygame",
    "numpy",
    "scipy.fft",
    "sounddevice",
    "soundfile",
    "slab",
    "h5netcdf",
]


def check_files() -> list[str]:
    errors = []
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"MISSING: {path.relative_to(ROOT)}")
    return errors


def check_stdlib_pyds() -> list[str]:
    """Warn about .pyd files present in Python but absent from the bundle."""
    warnings = []
    base_dlls = Path(sys.base_prefix) / "DLLs"
    if not base_dlls.is_dir():
        return warnings
    for pyd in sorted(base_dlls.glob("*.pyd")):
        if not (INTERNAL / pyd.name).exists():
            warnings.append(f"NOT BUNDLED: {pyd.name}")
    return warnings


def check_imports() -> list[str]:
    errors = []
    for mod in REQUIRED_IMPORTS:
        try:
            __import__(mod)
        except Exception as exc:
            errors.append(f"IMPORT FAIL {mod}: {exc}")
    return errors


def check_hrtf() -> list[str]:
    errors = []
    try:
        from game.hrtf import BinauralHRTF
        h = BinauralHRTF()
        if h.n_taps < 100 or h.azimuths.size < 10:
            errors.append(f"HRTF looks wrong: taps={h.n_taps} az={h.azimuths.size}")
    except Exception as exc:
        errors.append(f"HRTF FAIL: {exc}")
    return errors


def check_exe_runtime(seconds: int = 15) -> list[str]:
    if not EXE.exists():
        return [f"EXE missing: {EXE}"]
    try:
        proc = subprocess.Popen(
            [str(EXE)],
            cwd=str(DIST),
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        try:
            code = proc.wait(timeout=seconds)
            if code not in (0, None):
                return [f"EXE exited early with code {code} (expected to stay up {seconds}s)"]
            return [f"EXE exited within {seconds}s with code {code}"]
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            return []
    except Exception as exc:
        return [f"EXE launch FAIL: {exc}"]


def main() -> int:
    print("=== Bundle file check ===")
    file_errors = check_files()
    for e in file_errors:
        print(e)
    if not file_errors:
        print("All required files present.")

    print("\n=== Dev import check (venv) ===")
    import_errors = check_imports()
    for e in import_errors:
        print(e)
    if not import_errors:
        print("All imports OK.")

    print("\n=== HRTF load check ===")
    hrtf_errors = check_hrtf()
    for e in hrtf_errors:
        print(e)
    if not hrtf_errors:
        print("KEMAR HRTF loads OK.")

    print("\n=== Stdlib .pyd gap (informational) ===")
    gaps = check_stdlib_pyds()
    # Only show a few; many are optional (tkinter, etc.)
    optional = {"_tkinter", "_testcapi", "_testinternalcapi", "_testbuffer", "_testimportmultiple",
                "_testmultiphase", "_testsinglephase", "_testconsole", "_testclinic",
                "_ctypes_test", "_elementtree", "_uuid"}
    serious = [g for g in gaps if Path(g.split()[-1]).stem not in optional
               and not g.endswith("_testcapi.pyd")]
    for g in serious[:15]:
        print(g)
    if len(serious) > 15:
        print(f"... and {len(serious) - 15} more")
    if not serious:
        print("All non-test stdlib .pyd modules bundled.")

    print(f"\n=== EXE runtime ({15}s) ===")
    exe_errors = check_exe_runtime(15)
    for e in exe_errors:
        print(e)
    if not exe_errors:
        print("EXE stayed running (no early crash).")

    failed = bool(file_errors or import_errors or hrtf_errors or exe_errors)
    print("\n" + ("FAILED" if failed else "ALL CHECKS PASSED"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
