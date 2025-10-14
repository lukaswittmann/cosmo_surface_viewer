import importlib
import sys
import types
from pathlib import Path

import numpy as np


def _import_cosmo():
    # Provide light stubs for heavy optional deps so module can import in CI
    sys.modules.setdefault('pyvista', types.ModuleType('pyvista'))
    sys.modules.setdefault('vtk', types.ModuleType('vtk'))
    # Import the package directly from its __init__.py to avoid import path issues
    from importlib import util

    pkg_path = Path('cosmo_surface_viewer') / '__init__.py'
    spec = util.spec_from_file_location('cosmo_surface_viewer', str(pkg_path))
    pkg = util.module_from_spec(spec)
    sys.modules['cosmo_surface_viewer'] = pkg
    spec.loader.exec_module(pkg)
    return pkg


def test_parse_cpcm(tmp_path):
    cosmo = _import_cosmo()
    sample = tmp_path / 'sample.cpcm'
    content = []
    content.append('3 # Number of surface points\n')
    content.append('OTHER HEADER LINE\n')
    content.append('SURFACE POINTS\n')
    content.append('hdr1\n')
    content.append('hdr2\n')
    # three data lines, ensure at least 10 columns
    content.append('0.0 0.0 0.0 0.1 0.2 0.5 0 0 0 1\n')
    content.append('1.0 0.0 0.0 0.1 0.3 0.6 0 0 0 1\n')
    content.append('0.0 1.0 0.0 0.1 0.4 0.7 0 0 0 1\n')
    sample.write_text(''.join(content))

    points, charges, potentials, areas, owners = cosmo.parse_cpcm(sample)
    assert points.shape == (3, 3)
    assert charges.shape == (3,)
    assert potentials.shape == (3,)
    assert areas.shape == (3,)
    assert owners.shape == (3,)
    # spot check values
    assert np.isclose(points[0, 0], 0.0)
    assert np.isclose(charges[1], 0.6)
    assert np.isclose(potentials[2], 0.4)
    assert owners.dtype == int


def test_build_faces_simple():
    cosmo = _import_cosmo()
    pts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    areas = np.array([10.0, 10.0, 10.0])
    owners = np.array([1, 1, 1])
    faces = cosmo.build_faces(pts, areas, owners, neighbor_radius=2.0, max_neighbors=10, neighbors_threshold=2.0)
    assert faces.ndim == 2
    assert faces.shape[1] == 3
    # should include triangle with indices 0,1,2 (order sorted inside function)
    found = any(set(face) == {0, 1, 2} for face in faces)
    assert found


def test_map_colors():
    cosmo = _import_cosmo()
    vals = np.array([-1.0, 0.0, 1.0])
    colors = cosmo.map_colors(vals, cmap_name='viridis')
    assert colors.shape == (3, 3)
    assert colors.dtype == np.uint8


def test_write_vrml(tmp_path):
    cosmo = _import_cosmo()
    verts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    faces = np.array([[0, 1, 2]])
    colors = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255]], dtype=np.uint8)
    out = tmp_path / 'out.wrl'
    cosmo.write_vrml(verts, faces, colors, out)
    txt = out.read_text()
    assert '#VRML V2.0 utf8' in txt
    assert 'coord Coordinate' in txt
    assert 'color Color' in txt
