import geopandas as gpd
import shapely.geometry
import pytest
import importlib.util
import pathlib
import types
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE_NAME = "map2loop"

if PACKAGE_NAME not in sys.modules:
    pkg = types.ModuleType(PACKAGE_NAME)
    pkg.__path__ = [str(ROOT / PACKAGE_NAME)]
    import logging
    pkg.loggers = {}
    pkg.ch = logging.StreamHandler()
    pkg.ch.setLevel(logging.WARNING)
    sys.modules[PACKAGE_NAME] = pkg

spec = importlib.util.spec_from_file_location(
    f"{PACKAGE_NAME}.contact_extractor",
    ROOT / PACKAGE_NAME / "contact_extractor.py",
)
module = importlib.util.module_from_spec(spec)
sys.modules[f"{PACKAGE_NAME}.contact_extractor"] = module
spec.loader.exec_module(module)
ContactExtractor = module.ContactExtractor


@pytest.fixture
def simple_geology():
    """Create a minimal geology dataset for testing."""

    poly1 = shapely.geometry.Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    poly2 = shapely.geometry.Polygon([(2, 0), (4, 0), (4, 2), (2, 2)])

    return gpd.GeoDataFrame(
        {
            "UNITNAME": ["unit1", "unit2"],
            "INTRUSIVE": [False, False],
            "SILL": [False, False],
            "geometry": [poly1, poly2],
        },
        crs="EPSG:4326",
    )


def test_extract_all_contacts(simple_geology):
    extractor = ContactExtractor(simple_geology)
    result = extractor.extract_all_contacts()
    assert len(result) == 1


def test_extract_basal_contacts(simple_geology):
    extractor = ContactExtractor(simple_geology)
    extractor.extract_all_contacts()
    basal = extractor.extract_basal_contacts(["unit1", "unit2"])
    assert list(basal["basal_unit"]) == ["unit1"]


