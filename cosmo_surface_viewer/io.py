from __future__ import annotations

from pathlib import Path
import numpy as np
import logging

logger = logging.getLogger("cosmo_surface_viewer.io")


def write_vrml(vertices: np.ndarray, faces: np.ndarray, colors: np.ndarray, filename: Path | str) -> None:
    p = Path(filename)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write("#VRML V2.0 utf8\n")
        f.write("Shape {\n")
        f.write("  geometry IndexedFaceSet {\n")
        f.write("    coord Coordinate {\n")
        f.write("      point [\n")
        for v in vertices:
            f.write(f"        {v[0]:.6f} {v[1]:.6f} {v[2]:.6f},\n")
        f.write("      ]\n")
        f.write("    }\n")
        f.write("    color Color {\n")
        f.write("      color [\n")
        for c in colors:
            f.write(f"        {c[0]/255:.3f} {c[1]/255:.3f} {c[2]/255:.3f},\n")
        f.write("      ]\n")
        f.write("    }\n")
        f.write("    coordIndex [\n")
        for face in faces:
            f.write(f"      {face[0]} {face[1]} {face[2]} -1,\n")
        f.write("    ]\n")
        f.write("  }\n")
        f.write("}\n")
    logger.info("Wrote VRML: %s", str(p))
