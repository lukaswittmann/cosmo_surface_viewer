import importlib


def test_package_version():
    pkg = importlib.import_module('cosmo_surface_viewer')
    assert hasattr(pkg, '__version__')
    assert pkg.__version__ == '1.0.0'


def test_core_api():
    pkg = importlib.import_module('cosmo_surface_viewer')
    names = set(dir(pkg))
    for fn in ('parse_cpcm','process_all','build_faces'):
        assert fn in names
