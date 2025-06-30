import pytest
import geopandas as gpd
import shapely.geometry

from map2loop.contacts import ContactExtractor


def simple_geology():
    poly1 = shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    poly2 = shapely.geometry.Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
    return gpd.GeoDataFrame(
        {
            "UNITNAME": ["A", "B"],
            "INTRUSIVE": [False, False],
            "SILL": [False, False],
            "geometry": [poly1, poly2],
        },
        crs="EPSG:4326",
    )


def test_extract_all_contacts_simple():
    geology = simple_geology()
    extractor = ContactExtractor(geology)
    contacts = extractor.extract_all_contacts()
    assert len(contacts) == 1
    boundary = shapely.geometry.LineString([(1, 0), (1, 1)])
    assert contacts.geometry.iloc[0].intersects(boundary)
    assert contacts.length.iloc[0] > 0


def test_extract_basal_contacts_simple():
    geology = simple_geology()
    extractor = ContactExtractor(geology)
    contact_data = extractor.extract_all_contacts()
    all_contacts, basal = extractor.extract_basal_contacts(contact_data, ["A", "B"])
    assert len(all_contacts) == 1
    assert len(basal) == 1
    assert basal.iloc[0]["basal_unit"] == "A"
    assert basal.iloc[0]["type"] == "BASAL"


def test_extract_basal_contacts_missing_unit():
    geology = simple_geology()
    extractor = ContactExtractor(geology)
    contact_data = extractor.extract_all_contacts()
    with pytest.raises(ValueError):
        extractor.extract_basal_contacts(contact_data, ["B"])
