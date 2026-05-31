"""PyInstaller runtime hook: ensure bundled DLLs are found on Windows."""
import os
import sys

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
        os.add_dll_directory(sys._MEIPASS)
