import geopandas as gpd
from shapely.geometry import Polygon, LineString
import pytest

from map2loop.topology import Topology
from map2loop.m2l_enums import Datatype


class DummyMapData:
    """Minimal MapData replacement used for testing."""

    def __init__(self, geology, faults=None):
        self.GEOLOGY = geology
        self.FAULT = faults
        self.contacts = None

    def get_map_data(self, datatype):
        if datatype == Datatype.GEOLOGY:
            return self.GEOLOGY
        if datatype == Datatype.FAULT:
            return self.FAULT
        raise ValueError("Unexpected datatype")


def simple_geology():
    poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    poly2 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
    return gpd.GeoDataFrame(
        {
            "UNITNAME": ["A", "B"],
            "INTRUSIVE": [False, False],
            "SILL": [False, False],
            "geometry": [poly1, poly2],
        },
        geometry="geometry",
        crs="EPSG:28350",
    )


def crossing_faults():
    line1 = LineString([(0, 0), (2, 1)])
    line2 = LineString([(0, 1), (2, 0)])
    return gpd.GeoDataFrame(
        {"ID": [1, 2], "geometry": [line1, line2]}, geometry="geometry", crs="EPSG:28350"
    )


def test_initialisation_defaults():
    geology = simple_geology()
    faults = crossing_faults()
    topo = Topology(geology, faults)

    assert topo.sorted_units is None
    assert topo._fault_fault_relationships is None
    assert topo._unit_fault_relationships is None
    assert topo._unit_unit_relationships is None
    assert topo.buffer_radius == 500


def test_calculate_fault_fault_relationships():
    geology = simple_geology()
    faults = crossing_faults()
    md = DummyMapData(geology, faults)
    topo = Topology(geology, faults)
    topo.map_data = md
    topo.buffer_radius = 0.1

    df = topo.get_fault_fault_relationships()
    assert list(df.columns) == ["Fault1", "Fault2", "Angle", "Type"]
    assert len(df) == 1
    assert set(df.loc[0, ["Fault1", "Fault2"]]) == {1, 2}
    assert df.loc[0, "Angle"] == 60
    assert df.loc[0, "Type"] == "T"


def test_calculate_unit_fault_relationships():
    geology = simple_geology()
    faults = crossing_faults()
    md = DummyMapData(geology, faults)
    topo = Topology(geology, faults)
    topo.map_data = md
    topo.buffer_radius = 0.1

    df = topo.get_unit_fault_relationships()
    assert set(df["Unit"]) == {"A", "B"}
    assert set(df["Fault"]) == {1, 2}
    # each unit is intersected by both faults
    assert len(df) == 4


def test_calculate_unit_unit_relationships_with_contacts():
    geology = simple_geology()
    md = DummyMapData(geology, None)
    topo = Topology(geology, None)
    topo.map_data = md

    df = topo.get_unit_unit_relationships()
    assert list(df.columns) == ["UNITNAME_1", "UNITNAME_2"]
    assert len(df) == 1
    assert set(df.loc[0]) == {"A", "B"}


def test_reset_raises_attribute_error():
    geology = simple_geology()
    faults = crossing_faults()
    md = DummyMapData(geology, faults)
    topo = Topology(geology, faults)
    topo.map_data = md
    topo.buffer_radius = 0.1
    topo.get_fault_fault_relationships()

    with pytest.raises(AttributeError):
        topo.reset()