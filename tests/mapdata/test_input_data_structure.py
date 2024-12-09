import pytest
import geopandas as gpd
import shapely.geometry
from map2loop.mapdata import MapData

# Datatype Enum
class Datatype:
    STRUCTURE = 1

# Config
class MockConfig:
    def __init__(self):
        self.structure_config = {
            "dipdir_column": "DIPDIR",
            "dip_column": "DIP",
            "description_column": "DESCRIPTION",
            "overturned_column": "OVERTURNED",
            "objectid_column": "ID",
        }

@pytest.mark.parametrize(
    "structure_data, expected_validity, expected_message",
    [
        # Valid data
        (
            {
                "geometry": [
                    shapely.geometry.Point(0, 0),
                    shapely.geometry.Point(1, 1)
                ],
                "DIPDIR": [45.0, 135.0],
                "DIP": [30.0, 45.0],
                "DESCRIPTION": ["Description1", "Description2"],
                "OVERTURNED": ["Yes", "No"],
                "ID": [1, 2]
            },
            False,
            "",
        ),
        # Invalid geometry
        (
            {
                "geometry": [
                    shapely.geometry.Point(0, 0),
                    shapely.geometry.Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])  # Invalid geometry
                ],
                "DIPDIR": [45.0, 135.0],
                "DIP": [30.0, 45.0],
                "DESCRIPTION": ["Description1", "Description2"],
                "OVERTURNED": ["Yes", "No"],
                "ID": [1, 2]
            },
            True,
            "Invalid geometries found in datatype STRUCTURE",
        ),
        # Missing required column
        (
            {
                "geometry": [
                    shapely.geometry.Point(0, 0),
                    shapely.geometry.Point(1, 1)
                ],
                # "DIPDIR": [45.0, 135.0],  # Missing required column
                "DIP": [30.0, 45.0],
                "DESCRIPTION": ["Description1", "Description2"],
                "OVERTURNED": ["Yes", "No"],
                "ID": [1, 2]
            },
            True,
            "Datatype STRUCTURE: Required column with config key: 'dipdir_column' is missing from structure data.",
        ),
        # Non-numeric value in numeric column
        (
            {
                "geometry": [
                    shapely.geometry.Point(0, 0),
                    shapely.geometry.Point(1, 1)
                ],
                "DIPDIR": ["A", "B"],  # Non-numeric value
                "DIP": [30.0, 45.0],
                "DESCRIPTION": ["Description1", "Description2"],
                "OVERTURNED": ["Yes", "No"],
                "ID": [1, 2]
            },
            True,
            "Datatype STRUCTURE: Column 'dipdir_column' must contain only numeric values. Please check that the column contains only numeric values.",
        ),
        # NaN or blank value in required column
        (
            {
                "geometry": [
                    shapely.geometry.Point(0, 0),
                    shapely.geometry.Point(1, 1)
                ],
                "DIPDIR": [None, 3],  # NaN value
                "DIP": [30.0, 45.0],
                "DESCRIPTION": ["Description1", "Description2"],
                "OVERTURNED": ["Yes", "No"],
                "ID": [1, 2]
            },
            True,
            "Datatype STRUCTURE: NaN or blank values found in required column 'dipdir_column'. Please double check the column for blank values.",
        ),
        # Duplicate ID column
        (
            {
                "geometry": [
                    shapely.geometry.Point(0, 0),
                    shapely.geometry.Point(1, 1)
                ],
                "DIPDIR": [45.0, 135.0],
                "DIP": [30.0, 45.0],
                "DESCRIPTION": ["Description1", "Description2"],
                "OVERTURNED": ["Yes", "No"],
                "ID": [1, 1]  # Duplicate ID
            },
            True,
            "Datatype STRUCTURE: ID column 'ID' (config key: 'objectid_column') contains duplicate values.",
        ),
    ],
)
def test_check_structure_fields_validity(structure_data, expected_validity, expected_message):
    # Create a GeoDataFrame
    structure_gdf = gpd.GeoDataFrame(structure_data, crs="EPSG:4326")

    # Instantiate the MapData class with the mock config and data
    map_data = MapData()
    map_data.config = MockConfig()
    map_data.raw_data = [None] * len(Datatype.__dict__)
    map_data.raw_data[Datatype.STRUCTURE] = structure_gdf

    # Test the check_structure_fields_validity function
    validity_check, message = map_data.check_structure_fields_validity()
    assert validity_check == expected_validity
    assert message == expected_message
