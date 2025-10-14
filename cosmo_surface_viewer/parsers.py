from __future__ import annotations

from pathlib import Path
import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger("cosmo_surface_viewer.parsers")


def parse_vrml_colors(filename: Path | str) -> np.ndarray:
    """Extract colors from a VRML Color node as an (N,3) float array in [0,1]."""
    color_values: list[float] = []
    inside = False
    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if s.startswith("color ["):
                inside = True
                s = s[len("color ["):].strip()
            if inside:
                if "]" in s:
                    s = s.split("]")[0]
                    inside = False
                tokens = s.replace(",", " ").split()
                for token in tokens:
                    try:
                        color_values.append(float(token))
                    except ValueError:
                        continue
    if not color_values:
        return np.empty((0, 3), dtype=float)
    try:
        colors_array = np.array(color_values, dtype=float).reshape(-1, 3)
    except ValueError:
        logger.warning("VRML colors length not divisible by 3; truncating")
        trunc = (len(color_values) // 3) * 3
        colors_array = np.array(color_values[:trunc], dtype=float).reshape(-1, 3)
    return colors_array


def parse_cpcm(input_file: Path | str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Parse a .cpcm file and return points, effective charges, potentials, areas, owners.

    Returns:
    - points: (N,3) in Angstrom
    - charges: (N,) effective charges
    - potentials: (N,) potentials
    - surface_areas: (N,)
    - sphere_owners: (N,) int
    """
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    num_surface_points = None
    start_index = None
    for i, line in enumerate(lines):
        if "# Number of surface points" in line:
            try:
                num_surface_points = int(line.split()[0])
            except Exception:
                pass
        if "SURFACE POINTS" in line:
            start_index = i + 3
            break
    if start_index is None or num_surface_points is None:
        raise ValueError("SURFACE POINTS section not found or malformed in .cpcm")

    points = []
    charges = []
    potentials = []
    surface_areas = []
    sphere_owners = []
    for line in lines[start_index : start_index + num_surface_points]:
        parts = line.split()
        if len(parts) < 10:
            continue
        x, y, z = map(float, parts[0:3])
        area = float(parts[3])
        effective_charge = float(parts[5])
        potential = float(parts[4])
        owner = int(parts[9])

        points.append([x, y, z])
        surface_areas.append(area)
        charges.append(effective_charge)
        potentials.append(potential)
        sphere_owners.append(owner)

    points = np.array(points, dtype=float)
    charges = np.array(charges, dtype=float)
    potentials = np.array(potentials, dtype=float)
    surface_areas = np.array(surface_areas, dtype=float)
    sphere_owners = np.array(sphere_owners, dtype=int)

    # Convert atomic units to Angstroms
    points *= 0.529177
    return points, charges, potentials, surface_areas, sphere_owners
