from __future__ import annotations

from pathlib import Path
import numpy as np
import logging
import pyvista as pv
import vtk

from .parsers import parse_vrml_colors

logger = logging.getLogger("cosmo_surface_viewer.render")


def render_wrl_to_png(
    wrl_filename: Path | str,
    png_filename: Path | str,
    *,
    off_screen: bool = True,
    window_size: tuple[int, int] = (4000, 3000),
    background: str = "white",
    smooth_shading: bool = False,
    enable_aa: bool = True,
) -> None:
    importer = vtk.vtkVRMLImporter()
    importer.SetFileName(str(wrl_filename))
    try:
        importer.Update()
    except Exception as e:
        raise RuntimeError(f"Failed to import VRML '{wrl_filename}': {e}") from e

    renderer = importer.GetRenderer()
    if renderer is None:
        raise RuntimeError("VRML importer did not provide a renderer")
    actors = renderer.GetActors()
    actors.InitTraversal()

    meshes: list[pv.PolyData] = []
    actor = actors.GetNextActor()
    while actor:
        mapper = actor.GetMapper()
        if mapper:
            polydata = mapper.GetInput()
            if polydata:
                meshes.append(pv.wrap(polydata))
        actor = actors.GetNextActor()

    if not meshes:
        raise RuntimeError("No mesh could be extracted from the VRML file.")
    mesh = meshes[0]
    for m in meshes[1:]:
        mesh = mesh.merge(m)

    plotter = pv.Plotter(off_screen=off_screen)

    colors_array = parse_vrml_colors(wrl_filename)
    if colors_array.shape[0] > mesh.n_points:
        colors_array = colors_array[: mesh.n_points]
    elif 0 < colors_array.shape[0] < mesh.n_points:
        n_repeat = int(np.ceil(mesh.n_points / colors_array.shape[0]))
        colors_array = np.tile(colors_array, (n_repeat, 1))[: mesh.n_points]
    if len(colors_array) == mesh.n_points + 1:
        colors_array = colors_array[: mesh.n_points]

    mesh.point_data["my_colors"] = colors_array
    plotter.add_mesh(mesh, scalars="my_colors", rgb=True, smooth_shading=smooth_shading)

    plotter.add_light(pv.Light(position=(0, 0, 1), color="white", intensity=0.2))
    if enable_aa:
        try:
            plotter.enable_anti_aliasing()
        except Exception:
            pass
    plotter.set_background(background, top=background)

    out = Path(png_filename)
    out.parent.mkdir(parents=True, exist_ok=True)
    # If off_screen is True, save a screenshot to disk; if onscreen (off_screen=False), open interactive window and do not overwrite file
    if off_screen:
        plotter.show(screenshot=str(out), window_size=list(window_size))
        logger.info("Rendered PNG: %s", str(out))
    else:
        plotter.show(window_size=list(window_size))
        logger.info("Opened interactive viewer for: %s", str(wrl_filename))
    plotter.close()
