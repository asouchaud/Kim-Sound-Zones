"""PyInstaller runtime hook: pre-import numpy.core for KEMAR pickle compatibility."""
import importlib

for _name in (
    "numpy.core.multiarray",
    "numpy.core._multiarray_umath",
    "numpy.core.umath",
):
    try:
        importlib.import_module(_name)
    except ImportError:
        pass
