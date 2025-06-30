import geopandas as gpd
import shapely.geometry
import pytest

from map2loop.mapdata import MapData


@pytest.fixture
def simple_mapdata():
    # Create two adjacent square polygons representing two units
    poly1 = shapely.geometry.Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    poly2 = shapely.geometry.Polygon([(2, 0), (4, 0), (4, 2), (2, 2)])

    data = gpd.GeoDataFrame(
        {
            "UNITNAME": ["unit1", "unit2"],
            "INTRUSIVE": [False, False],
            "SILL": [False, False],
            "geometry": [poly1, poly2],
        },
        crs="EPSG:4326",
    )

    md = MapData()
    md.data[0] = data  # Datatype.GEOLOGY == 0
    md.data_states[0] = 5  # Datastate.COMPLETE
    md.dirtyflags[0] = False
    return md


def test_extract_all_contacts(simple_mapdata):
    result = simple_mapdata.contact_extractor.extract_all_contacts()
    assert len(result) == 1
    assert simple_mapdata.contacts is not None


def test_extract_basal_contacts(simple_mapdata):
    simple_mapdata.contact_extractor.extract_all_contacts()
    contacts = simple_mapdata.contact_extractor.extract_basal_contacts([
        "unit1",
        "unit2",
    ])
    assert list(contacts["basal_unit"]) == ["unit1"]
    assert simple_mapdata.basal_contacts is not None
