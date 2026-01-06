from __future__ import annotations

from pathlib import Path
import numpy as np
import logging

logger = logging.getLogger("cosmo_surface_viewer.io")


def write_pqr(points: np.ndarray, values: np.ndarray, filename: Path | str, radius: float = 0.300) -> None:
    """Write points and values to PQR format file.
    
    Args:
        points: (N,3) array of coordinates in Angstroms
        values: (N,) array of values (charges or potentials)
        filename: Output PQR filename
        radius: Radius value for each point (default 0.300)
    """
    p = Path(filename)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        for i, (point, value) in enumerate(zip(points, values), start=1):
            # GRIDPOINT index SPH CSP A 1 x y z value radius
            f.write(f"ATOM {i:6d} SPH  CSP A    1    {point[0]:8.3f}{point[1]:8.3f}{point[2]:8.3f} {value:8.4f} {radius:6.3f}\n")
    logger.info("Wrote PQR: %s", str(p))


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
