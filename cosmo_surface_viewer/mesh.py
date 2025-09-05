from __future__ import annotations

import numpy as np
import logging
from scipy.spatial import cKDTree

logger = logging.getLogger("cosmo_surface_viewer.mesh")


def build_faces(
    points: np.ndarray,
    surface_areas: np.ndarray,
    sphere_owners: np.ndarray,
    neighbor_radius: float = 1.0,
    max_neighbors: int = 15,
    neighbors_threshold: float = 1.5,
) -> np.ndarray:
    """Construct triangle faces using neighbor filtering and sphere ownership."""
    logger.debug("build_faces called: neighbor_radius=%s, max_neighbors=%s, neighbors_threshold=%s", neighbor_radius, max_neighbors, neighbors_threshold)
    tree = cKDTree(points)
    faces_set: set[tuple[int, int, int]] = set()

    # Precompute neighbors per point
    neighbors: list[list[int]] = []
    for i in range(len(points)):
        nbrs = tree.query_ball_point(points[i], neighbor_radius, workers=-1)
        owner_i = sphere_owners[i]
        nbrs = [j for j in nbrs if sphere_owners[j] == owner_i]
        if len(nbrs) > max_neighbors:
            dists = np.linalg.norm(points[nbrs] - points[i], axis=1)
            sorted_indices = np.argsort(dists)
            nbrs = [nbrs[idx] for idx in sorted_indices[:max_neighbors]]
        neighbors.append(nbrs)
    # Debug: log neighbor statistics
    try:
        counts = [len(n) for n in neighbors]
        import numpy as _np

        logger.debug("neighbor counts: mean=%.2f max=%d", float(_np.mean(counts)), int(_np.max(counts)) if counts else 0)
    except Exception:
        pass

    npts = len(points)
    for i in range(npts):
        if i % 100 == 0:
            logger.info("Building faces: %d/%d", i + 1, npts)
        r_i = float(np.sqrt(surface_areas[i] / np.pi))
        for j in neighbors[i]:
            if i == j:
                continue
            r_j = float(np.sqrt(surface_areas[j] / np.pi))
            dist_ij = float(np.linalg.norm(points[i] - points[j]))
            for k in neighbors[j]:
                if i == k:
                    continue
                r_k = float(np.sqrt(surface_areas[k] / np.pi))
                dist_ik = float(np.linalg.norm(points[i] - points[k]))

                if dist_ij < neighbors_threshold * (r_i + r_j) and dist_ik < neighbors_threshold * (r_i + r_k):
                    faces_set.add(tuple(sorted([i, j, k])))

                dist_jk = float(np.linalg.norm(points[j] - points[k]))
                if dist_jk < neighbors_threshold * (r_j + r_k) and dist_ik < neighbors_threshold * (r_i + r_k):
                    faces_set.add(tuple(sorted([j, k, i])))

    faces = np.array(list(faces_set), dtype=int)
    logger.info("Faces built: %d", len(faces))
    return faces


def map_colors(
    values: np.ndarray,
    vmin: float | None = None,
    vmax: float | None = None,
    cmap_name: str = "jet",
    robust: bool = False,
    robust_pct: float = 1.0,
) -> np.ndarray:
    """Map 1D values to RGB colors (0..255) using a Matplotlib colormap."""
    import matplotlib.pyplot as plt

    vals = np.asarray(values, dtype=float)
    if vals.ndim != 1:
        vals = vals.reshape(-1)
    if robust and (vmin is None or vmax is None):
        lo = np.percentile(vals, robust_pct)
        hi = np.percentile(vals, 100 - robust_pct)
        if vmin is None:
            vmin = float(lo)
        if vmax is None:
            vmax = float(hi)
    if vmin is None:
        vmin = float(vals.min())
    if vmax is None:
        vmax = float(vals.max())
    if vmin == vmax:
        vmax = vmin + 1e-12
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.get_cmap(cmap_name)
    colors = (cmap(norm(vals))[:, :3] * 255).astype(np.uint8)
    return colors
