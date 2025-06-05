# %%
import geopandas as gpd
from map2loop.mapdata import MapData
from map2loop import data_checks
import shapely.geometry


# Mock Datatype Enum
class Datatype:
    GEOLOGY = 0
    STRUCTURE = 1


# Mock Config class
class MockConfig:
    def __init__(self):
        self.structure_config = {
            "dipdir_column": "DIPDIR",
            "dip_column": "DIP",
            "description_column": "DESCRIPTION",
            "overturned_column": "OVERTURNED",
            "objectid_column": "ID",
        }


# Mock data for the structure dataset
valid_structure_data = {
    "geometry": [shapely.geometry.Point(0, 0), shapely.geometry.Point(1, 1)],
    "DIPDIR": [45.0, 135.0],
    "DIP": [30.0, 45.0],
    "DESCRIPTION": ["Description1", "Description2"],
    "OVERTURNED": ["Yes", "No"],
    "ID": [1, 2],
}

# Create a GeoDataFrame for valid structure data
valid_structure_gdf = gpd.GeoDataFrame(valid_structure_data, crs="EPSG:4326")


# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid structure data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.STRUCTURE] = valid_structure_gdf
validity_check, message = data_checks.check_structure_fields_validity(map_data)
print("Test 1 - Valid Data:")
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data with invalid geometry
invalid_geometry_structure_data = valid_structure_data.copy()
invalid_geometry_structure_data["geometry"] = [
    shapely.geometry.Point(0, 0),
    shapely.geometry.Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)]),  # Invalid geometry
]
invalid_geometry_structure_gdf = gpd.GeoDataFrame(invalid_geometry_structure_data, crs="EPSG:4326")


# Test with invalid geometry
map_data.raw_data[Datatype.STRUCTURE] = invalid_geometry_structure_gdf
validity_check, message = data_checks.check_structure_fields_validity(map_data)
print("\nTest 3 - Invalid Geometry:")
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data with missing required columns
missing_column_structure_data = valid_structure_data.copy()
del missing_column_structure_data["DIPDIR"]
missing_column_structure_gdf = gpd.GeoDataFrame(missing_column_structure_data, crs="EPSG:4326")

# Test with missing required column
map_data.raw_data[Datatype.STRUCTURE] = missing_column_structure_gdf
validity_check, message = data_checks.check_structure_fields_validity(map_data)
print("\nTest 2 - Missing Required Column:")
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the structure dataset
invalid_structure_data = {
    "geometry": [shapely.geometry.Point(0, 0), shapely.geometry.Point(1, 1)],
    "DIPDIR": ["A", "B"],
    "DIP": [30.0, 45.0],
    "DESCRIPTION": ["Description1", "Description2"],
    "OVERTURNED": ["Yes", "No"],
    "ID": [1, 2],
}

map_data.raw_data[Datatype.STRUCTURE] = invalid_structure_data
validity_check, message = data_checks.check_structure_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the structure dataset
invalid_structure_data = gpd.GeoDataFrame(
    {
        "geometry": [shapely.geometry.Point(0, 0), shapely.geometry.Point(1, 1)],
        "DIPDIR": ["A", "B"],
        "DIP": [30.0, 45.0],
        "DESCRIPTION": ["Description1", "Description2"],
        "OVERTURNED": ["Yes", "No"],
        "ID": [1, 2],
    }
)

map_data.raw_data[Datatype.STRUCTURE] = invalid_structure_data
validity_check, message = data_checks.check_structure_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the structure dataset
invalid_structure_data = gpd.GeoDataFrame(
    {
        "geometry": [shapely.geometry.Point(0, 0), shapely.geometry.Point(1, 1)],
        "DIPDIR": [None, 3],
        "DIP": [30.0, 45.0],
        "DESCRIPTION": ["Description1", "Description2"],
        "OVERTURNED": ["Yes", "No"],
        "ID": [1, 2],
    }
)

map_data.raw_data[Datatype.STRUCTURE] = invalid_structure_data
validity_check, message = data_checks.check_structure_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the structure dataset
invalid_structure_data = gpd.GeoDataFrame(
    {
        "geometry": [shapely.geometry.Point(0, 0), shapely.geometry.Point(1, 1)],
        "DIPDIR": [5, 3],
        "DIP": [120.0, 45.0],
        "DESCRIPTION": ["Description1", "Description2"],
        "OVERTURNED": ["Yes", "No"],
        "ID": [1, 2],
    }
)

map_data.raw_data[Datatype.STRUCTURE] = invalid_structure_data
validity_check, message = data_checks.check_structure_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the structure dataset
invalid_structure_data = gpd.GeoDataFrame(
    {
        "geometry": [shapely.geometry.Point(0, 0), shapely.geometry.Point(1, 1)],
        "DIPDIR": [5, 3],
        "DIP": [90, 45.0],
        "DESCRIPTION": [None, "Description2"],
        "OVERTURNED": ["Yes", "No"],
        "ID": [1, 2],
    }
)

map_data.raw_data[Datatype.STRUCTURE] = invalid_structure_data
validity_check, message = data_checks.check_structure_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the structure dataset
invalid_structure_data = gpd.GeoDataFrame(
    {
        "geometry": [shapely.geometry.Point(0, 0), shapely.geometry.Point(1, 1)],
        "DIPDIR": [5, 3],
        "DIP": [90, 45.0],
        "DESCRIPTION": [None, "Description2"],
        "OVERTURNED": ["Yes", "No"],
        "ID": [1, 1],
    }
)

map_data.raw_data[Datatype.STRUCTURE] = invalid_structure_data
validity_check, message = data_checks.check_structure_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
