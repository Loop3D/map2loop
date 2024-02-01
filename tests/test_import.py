import pytest


def test_import_map2loop():
    try:
        import map2loop
    except ImportError:
        pytest.fail("Failed to import map2loop module")
