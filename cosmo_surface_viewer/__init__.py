"""cosmo_surface_viewer package

Expose core functions for importable API.
"""
from .parsers import parse_cpcm, parse_vrml_colors
from .mesh import build_faces, map_colors
from .io import write_vrml, write_pqr
from .render import render_wrl_to_png
from .core import process_all, main

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "parse_cpcm",
    "parse_vrml_colors",
    "build_faces",
    "map_colors",
    "write_vrml",
    "write_pqr",
    "render_wrl_to_png",
    "process_all",
    "main",
]
