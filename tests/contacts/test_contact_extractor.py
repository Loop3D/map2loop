import types
import importlib.util
import sys
import logging
import pathlib
import geopandas as gpd
from shapely.geometry import Polygon

def load_contact_extractor():
    base = pathlib.Path(__file__).resolve().parents[2] / "map2loop"
    pkg = types.ModuleType("map2loop")
    pkg.loggers = {}
    pkg.ch = logging.StreamHandler()
    sys.modules["map2loop"] = pkg
    for name in ["logging", "m2l_enums", "contacts"]:
        spec = importlib.util.spec_from_file_location(f"map2loop.{name}", base / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "map2loop"
        sys.modules[f"map2loop.{name}"] = mod
        spec.loader.exec_module(mod)
    return sys.modules["map2loop.contacts"].ContactExtractor

ContactExtractor = load_contact_extractor()

def simple_geology():
    poly1 = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    poly2 = Polygon([(2, 0), (4, 0), (4, 2), (2, 2)])
    return gpd.GeoDataFrame(
        {
            "UNITNAME": ["A", "B"],
            "INTRUSIVE": [False, False],
            "SILL": [False, False],
            "geometry": [poly1, poly2],
        },
        crs="EPSG:3857",
    )

def test_extract_all_contacts_basic():
    ce = ContactExtractor()
    gdf = simple_geology()
    contacts = ce.extract_all_contacts(gdf)
    assert {"UNITNAME_1", "UNITNAME_2", "geometry", "length"} <= set(contacts.columns)
    assert len(contacts) > 0

def test_extract_basal_contacts_basic():
    ce = ContactExtractor(simple_geology())
    gdf = simple_geology()
    contacts = ce.extract_all_contacts(gdf)
    allc, basal = ce.extract_basal_contacts(contacts, ["A", "B"])
    assert len(allc) >= len(basal)
    assert "basal_unit" in allc.columns