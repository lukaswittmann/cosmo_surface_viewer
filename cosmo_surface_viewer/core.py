from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np
__version__ = "1.0.0"


def setup_logging(verbosity: int) -> None:
   import logging
   level = logging.WARNING
   if verbosity == 1:
      level = logging.INFO
   elif verbosity >= 2:
      level = logging.DEBUG
   logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")



from .parsers import parse_cpcm, parse_vrml_colors

ANGSTROM_PER_BOHR = 0.529177
from .mesh import build_faces, map_colors
from .io import write_vrml
from .render import render_wrl_to_png

logger = logging.getLogger("cosmo_surface_viewer")


def process_all(
   input: os.PathLike | str,
   output: os.PathLike | str,
   *,
   color_by: str = "charge",
   force: bool = False,
   off_screen: bool = True,
   neighbor_radius: float = 1.0,
   max_neighbors: int = 15,
   neighbors_threshold: float = 1.5,
   vmin: float | None = None,
   vmax: float | None = None,
   cmap: str = "jet",
   robust: bool = False,
   robust_pct: float = 1.0,
   window_size: tuple[int, int] = (4000, 3000),
   background: str = "white",
   smooth_shading: bool = False,
   enable_aa: bool = True,
) -> None:
   os.makedirs(output, exist_ok=True)

   # Echo mesh construction parameters for visibility
   print(f"Mesh params: neighbor_radius={neighbor_radius}, max_neighbors={max_neighbors}, neighbors_threshold={neighbors_threshold}")

   cpcm_files = sorted([f for f in os.listdir(input) if f.endswith(".cpcm")])
   total_cpcm = len(cpcm_files)
   print(f"Found {total_cpcm} .cpcm files in '{input}'")
   for idx, fname in enumerate(cpcm_files, start=1):
      in_path = os.path.join(input, fname)
      wrl_path = os.path.join(output, fname.replace(".cpcm", ".wrl"))

      if not os.path.exists(wrl_path) or force:
         print(f"[{idx}/{total_cpcm}] Building .wrl from: {fname}")
         logger.info("[WRL] Building: %s", fname)
         points, charges, potentials, areas, owners = parse_cpcm(in_path)
         faces = build_faces(
            points,
            areas,
            owners,
            neighbor_radius=neighbor_radius,
            max_neighbors=max_neighbors,
            neighbors_threshold=neighbors_threshold,
         )
         mode = str(color_by).lower()
         if mode in {"potential", "potentials"}:
            values = potentials
         elif mode in {"charge", "charges"}:
            values = charges
         elif mode in {"surface-charge", "surface_charge", "sigma"}:
            area_bohr = areas / (ANGSTROM_PER_BOHR ** 2)
            values = charges * area_bohr
         else:
            raise ValueError(f"Unsupported color_by option: {color_by}")
         colors = map_colors(values, vmin=vmin, vmax=vmax, cmap_name=cmap, robust=robust, robust_pct=robust_pct)
         write_vrml(points, faces, colors, wrl_path)
      else:
         print(f"[{idx}/{total_cpcm}] Skipping (exists): {fname}")
         logger.info("[WRL] Exists:   %s", fname)

   wrl_files = sorted([f for f in os.listdir(output) if f.endswith(".wrl")])
   total_wrl = len(wrl_files)
   print(f"Found {total_wrl} .wrl files in '{output}'")
   for idx, fname in enumerate(wrl_files, start=1):
      wrl_path = os.path.join(output, fname)
      png_path = os.path.join(output, fname.replace(".wrl", ".png"))
      if os.path.exists(png_path) and not force and off_screen:
         print(f"[{idx}/{total_wrl}] Skipping render (exists): {fname}")
         logger.info("[PNG] Exists:   %s", fname)
         continue
      if os.path.exists(png_path) and not force and not off_screen:
         print(f"[{idx}/{total_wrl}] Opening onscreen (exists): {fname}")
      else:
         print(f"[{idx}/{total_wrl}] Rendering .png from: {fname}")
      logger.info("[PNG] Rendering: %s", fname)
      render_wrl_to_png(
         wrl_path,
         png_path,
         off_screen=off_screen,
         window_size=window_size,
         background=background,
         smooth_shading=smooth_shading,
         enable_aa=enable_aa,
      )


def main(argv: Iterable[str] | None = None) -> int:
   parser = argparse.ArgumentParser(description="Build COSMO meshes from .cpcm and render .png from .wrl")
   parser.add_argument("--input", default="input", help="Input directory with .cpcm files")
   parser.add_argument("--output", default="output", help="Directory to write .wrl and .png files")
   parser.add_argument("--force", action="store_true", help="Rebuild .wrl and re-render .png even if they exist")
   # Rendering mode: prefer explicit offscreen/onscreen flags
   grp = parser.add_mutually_exclusive_group()
   grp.add_argument("--onscreen", dest="off_screen", action="store_false", help="Use on-screen rendering (disable off-screen)")
   grp.add_argument("--offscreen", dest="off_screen", action="store_true", help="Use off-screen rendering (default)")
   parser.set_defaults(off_screen=True)

   parser.add_argument("--neighbor-radius", type=float, default=1.0, help="Radius for neighbor search (Angstrom)")
   parser.add_argument("--max-neighbors", type=int, default=15, help="Max neighbors per point")
   parser.add_argument("--neighbors-threshold", type=float, default=1.5, help="Distance threshold factor for triangle acceptance")

   parser.add_argument("--vmin", type=float, default=None, help="Lower bound for color mapping")
   parser.add_argument("--vmax", type=float, default=None, help="Upper bound for color mapping")
   parser.add_argument(
      "--color-by",
      type=str,
      choices=["charge", "potential", "surface-charge"],
      default="charge",
      help="Color by 'charge' (default), 'potential', or 'surface-charge' (charge×area)",
   )
   parser.add_argument("--cmap", type=str, default="jet", help="Matplotlib colormap name (e.g., jet, viridis, turbo)")
   parser.add_argument("--robust", action="store_true", help="Use percentile clipping when vmin/vmax not provided")
   parser.add_argument("--robust-pct", type=float, default=1.0, help="Percentile for robust clipping (e.g., 1.0 → [1,99])")

   parser.add_argument("--window-width", type=int, default=4000, help="PNG width in pixels")
   parser.add_argument("--window-height", type=int, default=3000, help="PNG height in pixels")
   parser.add_argument("--background", type=str, default="white", help="Background color name or hex code")
   parser.add_argument("--no-aa", dest="aa", action="store_false", help="Disable anti-aliasing")

   parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (-v, -vv)")

   args = parser.parse_args(list(argv) if argv is not None else None)
   setup_logging(args.verbose)

   # Header
   width = 33
   header_lines = [
      "Simple Cosmo Surface Viewer",
      f"Version {__version__}",
      "L. Wittmann",
   ]
   print("-" * width)
   for ln in header_lines:
      print(ln.center(width))
   print("-" * width)
   print()

   window_size = (int(args.window_width), int(args.window_height))

   try:
      process_all(
         args.input,
         args.output,
         color_by=args.color_by,
         force=args.force,
         off_screen=bool(args.off_screen),
         neighbor_radius=args.neighbor_radius,
         max_neighbors=args.max_neighbors,
         neighbors_threshold=args.neighbors_threshold,
         vmin=args.vmin,
         vmax=args.vmax,
         cmap=args.cmap,
         robust=args.robust,
         robust_pct=args.robust_pct,
         window_size=window_size,
         background=args.background,
         enable_aa=args.aa,
      )
   except Exception as e:
      logger.error("Failed: %s", e)
      return 1
   return 0
