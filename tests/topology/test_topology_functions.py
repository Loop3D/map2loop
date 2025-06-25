import sys
import types

osgeo_stub = types.ModuleType("osgeo")
osgeo_stub.gdal = types.ModuleType("gdal")
osgeo_stub.osr = types.ModuleType("osr")
def _noop():
    pass
osgeo_stub.gdal.UseExceptions = _noop
class _Dataset:
    def GetGeoTransform(self):
        return (0, 1, 0, 0, 0, 1)
osgeo_stub.gdal.Dataset = _Dataset
def InvGeoTransform(gt):
    return gt
osgeo_stub.gdal.InvGeoTransform = InvGeoTransform
sys.modules.setdefault("osgeo", osgeo_stub)
sys.modules.setdefault("osgeo.gdal", osgeo_stub.gdal)
sys.modules.setdefault("osgeo.osr", osgeo_stub.osr)

import geopandas as gpd
from shapely.geometry import LineString, Polygon
import pandas as pd

from map2loop.mapdata import MapData
from map2loop.m2l_enums import Datatype, Datastate
from map2loop.topology import (
    calculate_fault_fault_relationships,
    calculate_unit_fault_relationships,
    calculate_unit_unit_relationships,
    register_topology,
    run_topology,
)


def _create_basic_mapdata():
    md = MapData()
    faults = gpd.GeoDataFrame(
        {
            "geometry": [
                LineString([(0, 0), (1, 0)]),
                LineString([(0, 0), (0, 1)]),
            ],
            "ID": ["F1", "F2"],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )
    md.data[Datatype.FAULT] = faults
    md.data_states[Datatype.FAULT] = Datastate.COMPLETE
    md.dirtyflags[Datatype.FAULT] = False

    geology = gpd.GeoDataFrame(
        {
            "UNITNAME": ["U1", "U2"],
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
            ],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )
    md.data[Datatype.GEOLOGY] = geology
    md.data_states[Datatype.GEOLOGY] = Datastate.COMPLETE
    md.dirtyflags[Datatype.GEOLOGY] = False

    contacts = pd.DataFrame(
        {
            "UNITNAME_1": ["U1"],
            "UNITNAME_2": ["U2"],
            "length": [1.0],
            "geometry": [LineString([(1, 0), (1, 1)])],
        }
    )
    md.contacts = contacts
    return md


def test_calculate_fault_fault_relationships():
    md = _create_basic_mapdata()
    df = calculate_fault_fault_relationships(md, buffer_radius=0.1)
    assert len(df) == 1
    assert set(df.iloc[0][["Fault1", "Fault2"]]) == {"F1", "F2"}


def test_calculate_unit_fault_relationships():
    md = _create_basic_mapdata()
    df = calculate_unit_fault_relationships(md, buffer_radius=0.1)
    pairs = {tuple(row) for row in df[["Unit", "Fault"]].to_records(index=False)}
    assert pairs == {("U1", "F1"), ("U1", "F2"), ("U2", "F1")}


def test_calculate_unit_unit_relationships():
    md = _create_basic_mapdata()
    df = calculate_unit_unit_relationships(md)
    assert list(df.columns) == ["UNITNAME_1", "UNITNAME_2"]
    assert df.iloc[0]["UNITNAME_1"] == "U1"
    assert df.iloc[0]["UNITNAME_2"] == "U2"


def test_registry_and_runner():
    called = {}

    @register_topology("test")
    def run_test(map_data: MapData):
        called["executed"] = True
        return {"dummy": pd.DataFrame()}

    md = _create_basic_mapdata()
    result = run_topology(md, "test")
    assert "executed" in called
    assert list(result.keys()) == ["dummy"]
    assert isinstance(result["dummy"], pd.DataFrame)
