import pytest
import geopandas as gpd
import shapely.geometry
from map2loop.mapdata import MapData

# Datatype Enum
class Datatype:
    GEOLOGY = 0

# Config 
class MockConfig:
    def __init__(self):
        self.geology_config = {
            "unitname_column": "UNITNAME",
            "alt_unitname_column": "CODE",
            "group_column": "GROUP",
            "supergroup_column": "SUPERGROUP",
            "description_column": "DESCRIPTION",
            "rocktype_column": "ROCKTYPE1",
            "alt_rocktype_column": "ROCKTYPE2",
            "minage_column": "MIN_AGE",
            "maxage_column": "MAX_AGE",
            "objectid_column": "ID",
            "ignore_lithology_codes": [],
        }

@pytest.mark.parametrize(
    "geology_data, expected_validity, expected_message",
    [
        # Valid data
        (
            {
                "geometry": [shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
                "UNITNAME": ["Sandstone"],
                "CODE": ["SST"],
                "GROUP": ["Sedimentary"],
                "SUPERGROUP": ["Mesozoic"],
                "DESCRIPTION": ["A type of sandstone"],
                "ROCKTYPE1": ["Clastic"],
                "ROCKTYPE2": ["Quartz"],
                "MIN_AGE": [150.0],
                "MAX_AGE": [200.0],
                "ID": [1],
            },
            False,
            "",
        ),
        # Invalid geometry
        (
            {
                "geometry": [shapely.geometry.Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])],
                "UNITNAME": ["Sandstone"],
                "CODE": ["SST"],
                "GROUP": ["Sedimentary"],
                "SUPERGROUP": ["Mesozoic"],
                "DESCRIPTION": ["A type of sandstone"],
                "ROCKTYPE1": ["Clastic"],
                "ROCKTYPE2": ["Quartz"],
                "MIN_AGE": [150.0],
                "MAX_AGE": [200.0],
                "ID": [1],
            },
            True,
            "Invalid geometries found in datatype GEOLOGY",
        ),
        # Missing required column
        (
            {
                "geometry": [shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
                "UNITNAME": ["Sandstone"],
                # "CODE": ["SST"],  # Missing required column
                "GROUP": ["Sedimentary"],
                "SUPERGROUP": ["Mesozoic"],
                "DESCRIPTION": ["A type of sandstone"],
                "ROCKTYPE1": ["Clastic"],
                "ROCKTYPE2": ["Quartz"],
                "MIN_AGE": [150.0],
                "MAX_AGE": [200.0],
                "ID": [1],
            },
            True,
            "Datatype GEOLOGY: Required column with config key: 'alt_unitname_column' is missing from geology data.",
        ),
        # Non-string value in required column
        (
            {
                "geometry": [shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
                "UNITNAME": ["Sandstone"],
                "CODE": [2],  # Non-string value
                "GROUP": ["Sedimentary"],
                "SUPERGROUP": ["Mesozoic"],
                "DESCRIPTION": ["A type of sandstone"],
                "ROCKTYPE1": ["Clastic"],
                "ROCKTYPE2": ["Quartz"],
                "MIN_AGE": [150.0],
                "MAX_AGE": [200.0],
                "ID": [1],
            },
            True,
            "Datatype GEOLOGY: Column 'alt_unitname_column' must contain only string values. Please check that the column contains only string values.",
        ),
        # NaN or blank value in required column
        (
            {
                "geometry": [shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
                "UNITNAME": [""],  # Blank value
                "CODE": ["SST"],
                "GROUP": ["Sedimentary"],
                "SUPERGROUP": ["Mesozoic"],
                "DESCRIPTION": ["A type of sandstone"],
                "ROCKTYPE1": ["Clastic"],
                "ROCKTYPE2": ["Quartz"],
                "MIN_AGE": [150.0],
                "MAX_AGE": [200.0],
                "ID": [1],
            },
            True,
            "Datatype GEOLOGY: NaN or blank values found in required column 'unitname_column'. Please double check the column for blank values.",
        ),
        # Duplicate ID values
        (
            {
                "geometry": [
                    shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                    shapely.geometry.Polygon([(0, 0), (10, 0), (1, 1), (0, 10)]),
                ],
                "UNITNAME": ["fr", "df"],
                "CODE": ["SST", "FGH"],
                "GROUP": ["Sedimentary", "Ign"],
                "SUPERGROUP": ["Mesozoic", "Arc"],
                "DESCRIPTION": ["A", "B"],
                "ROCKTYPE1": ["A", "B"],
                "ROCKTYPE2": ["Quartz", "FDS"],
                "MIN_AGE": [150.0, 200],
                "MAX_AGE": [200.0, 250],
                "ID": [1, 1],  # Duplicate ID
            },
            True,
            "Datatype GEOLOGY: Duplicate values found in column 'ID' (config key: 'objectid_column').",
        ),
        # nan in id
        (
            {
                "geometry": [
                    shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                    shapely.geometry.Polygon([(0, 0), (10, 0), (1, 1), (0, 10)]),
                ],
                "UNITNAME": ["fr", "df"],
                "CODE": ["SST", "FGH"],
                "GROUP": ["Sedimentary", "Ign"],
                "SUPERGROUP": ["Mesozoic", "Arc"],
                "DESCRIPTION": ["A", "B"],
                "ROCKTYPE1": ["A", "B"],
                "ROCKTYPE2": ["Quartz", "FDS"],
                "MIN_AGE": [150.0, 200],
                "MAX_AGE": [200.0, 250],
                "ID": [1, None],  
            },
            True,
            "Datatype GEOLOGY: Column 'ID' (config key: 'objectid_column') contains NaN or null values.",
        ),
        # nan in unit name
        (
            {
                "geometry": [
                    shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                    shapely.geometry.Polygon([(0, 0), (10, 0), (1, 1), (0, 10)]),
                ],
                "UNITNAME": ["fr", None],
                "CODE": ["SST", "FGH"],
                "GROUP": ["Sedimentary", "Ign"],
                "SUPERGROUP": ["Mesozoic", "Arc"],
                "DESCRIPTION": ["A", "B"],
                "ROCKTYPE1": ["A", "B"],
                "ROCKTYPE2": ["Quartz", "FDS"],
                "MIN_AGE": [150.0, 200],
                "MAX_AGE": [200.0, 250],
                "ID": [1, 1],  # Duplicate ID
            },
            True,
            "Datatype GEOLOGY: Column 'unitname_column' must contain only string values. Please check that the column contains only string values.",
        ),
    ],
)



def test_check_geology_fields_validity(geology_data, expected_validity, expected_message):
    # Create a GeoDataFrame
    geology_gdf = gpd.GeoDataFrame(geology_data, crs="EPSG:4326")

    # Instantiate the MapData class with the mock config and data
    map_data = MapData()
    map_data.config = MockConfig()
    map_data.raw_data = [None] * len(Datatype.__dict__)
    map_data.raw_data[Datatype.GEOLOGY] = geology_gdf

    # Test the check_geology_fields_validity function
    validity_check, message = map_data.check_geology_fields_validity()
    assert validity_check == expected_validity
    assert message == expected_message