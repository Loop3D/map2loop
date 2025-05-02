# %%
import geopandas as gpd
import shapely.geometry
from map2loop import data_checks


# Mock Datatype Enum
class Datatype:
    GEOLOGY = 0


# Mock Config class
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


# Mock data for the geology dataset
geology_data = {
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
}

# Create a GeoDataFrame for geology
geology_gdf = gpd.GeoDataFrame(geology_data, crs="EPSG:4326")

# Ensure that all string columns are of dtype str
for col in ["UNITNAME", "CODE", "GROUP", "SUPERGROUP", "DESCRIPTION", "ROCKTYPE1", "ROCKTYPE2"]:
    geology_gdf[col] = geology_gdf[col].astype(str)

from map2loop.mapdata import MapData

map_data = MapData()
map_data.config = MockConfig()
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.GEOLOGY] = geology_gdf

# Test the check_geology_fields_validity function
validity_check, message = data_checks.check_geology_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

########### should run with no issues

# %%
######## invalid geometries

invalid_geometry = shapely.geometry.Polygon(
    [(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)]  # This creates a self-intersecting polygon (bowtie)
)


geology_data = {
    "geometry": [invalid_geometry],
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
}
# Create a GeoDataFrame for geology
geology_gdf = gpd.GeoDataFrame(geology_data, crs="EPSG:4326")

# Ensure that all string columns are of dtype str
for col in ["UNITNAME", "CODE", "GROUP", "SUPERGROUP", "DESCRIPTION", "ROCKTYPE1", "ROCKTYPE2"]:
    geology_gdf[col] = geology_gdf[col].astype(str)

from map2loop.mapdata import MapData

map_data = MapData()
map_data.config = MockConfig()
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.GEOLOGY] = geology_gdf

# Test the check_geology_fields_validity function
validity_check, message = data_checks.check_geology_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
geology_data = {
    "geometry": [shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
    "UNITNAME": ["Sandstone"],
    # "CODE": ["SST"],  ##########################
    "GROUP": ["Sedimentary"],
    "SUPERGROUP": ["Mesozoic"],
    "DESCRIPTION": ["A type of sandstone"],
    "ROCKTYPE1": ["Clastic"],
    "ROCKTYPE2": ["Quartz"],
    "MIN_AGE": [150.0],
    "MAX_AGE": [200.0],
    "ID": [1],
}
# Create a GeoDataFrame for geology
geology_gdf = gpd.GeoDataFrame(geology_data, crs="EPSG:4326")

# Ensure that all string columns are of dtype str
# for col in ["UNITNAME", "CODE", "GROUP", "SUPERGROUP", "DESCRIPTION", "ROCKTYPE1", "ROCKTYPE2"]:
#     geology_gdf[col] = geology_gdf[col].astype(str)

from map2loop.mapdata import MapData

map_data = MapData()
map_data.config = MockConfig()
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.GEOLOGY] = geology_gdf

# Test the check_geology_fields_validity function
validity_check, message = data_checks.check_geology_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
geology_data = {
    "geometry": [shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
    "UNITNAME": ["Sandstone"],
    "CODE": [2],  ################################
    "GROUP": ["Sedimentary"],
    "SUPERGROUP": ["Mesozoic"],
    "DESCRIPTION": ["A type of sandstone"],
    "ROCKTYPE1": ["Clastic"],
    "ROCKTYPE2": ["Quartz"],
    "MIN_AGE": [150.0],
    "MAX_AGE": [200.0],
    "ID": [1],
}
# Create a GeoDataFrame for geology
geology_gdf = gpd.GeoDataFrame(geology_data, crs="EPSG:4326")

# Ensure that all string columns are of dtype str
# for col in ["UNITNAME", "CODE", "GROUP", "SUPERGROUP", "DESCRIPTION", "ROCKTYPE1", "ROCKTYPE2"]:
#     geology_gdf[col] = geology_gdf[col].astype(str)

from map2loop.mapdata import MapData

map_data = MapData()
map_data.config = MockConfig()
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.GEOLOGY] = geology_gdf


validity_check, message = data_checks.check_geology_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%

geology_data = {
    "geometry": [shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
    "UNITNAME": [''],  ###################################################
    "CODE": ['SSt'],
    "GROUP": ["Sedimentary"],
    "SUPERGROUP": ["Mesozoic"],
    "DESCRIPTION": ["A type of sandstone"],
    "ROCKTYPE1": ["Clastic"],
    "ROCKTYPE2": ["Quartz"],
    "MIN_AGE": [150.0],
    "MAX_AGE": [200.0],
    "ID": [1],
}
# Create a GeoDataFrame for geology
geology_gdf = gpd.GeoDataFrame(geology_data, crs="EPSG:4326")

# Ensure that all string columns are of dtype str
# for col in ["UNITNAME", "CODE", "GROUP", "SUPERGROUP", "DESCRIPTION", "ROCKTYPE1", "ROCKTYPE2"]:
#     geology_gdf[col] = geology_gdf[col].astype(str)

from map2loop.mapdata import MapData

map_data = MapData()
map_data.config = MockConfig()
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.GEOLOGY] = geology_gdf

validity_check, message = data_checks.check_geology_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%

geology_data = {
    "geometry": [shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
    "UNITNAME": ['fr'],
    "CODE": ['SSt'],
    "GROUP": ["Sedimentary"],
    "SUPERGROUP": ["Mesozoic"],
    "DESCRIPTION": ["A"],
    "ROCKTYPE1": ["A"],
    "ROCKTYPE2": ["Quartz"],
    "MIN_AGE": ["150.0"],
    "MAX_AGE": [200.0],
    "ID": [1],
}
# Create a GeoDataFrame for geology
geology_gdf = gpd.GeoDataFrame(geology_data, crs="EPSG:4326")

# Ensure that all string columns are of dtype str
# for col in ["UNITNAME", "CODE", "GROUP", "SUPERGROUP", "DESCRIPTION", "ROCKTYPE1", "ROCKTYPE2"]:
#     geology_gdf[col] = geology_gdf[col].astype(str)

from map2loop.mapdata import MapData

map_data = MapData()
map_data.config = MockConfig()
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.GEOLOGY] = geology_gdf


validity_check, message = data_checks.check_geology_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
message

# %%

geology_data = {
    "geometry": [
        shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        shapely.geometry.Polygon([(0, 0), (10, 0), (1, 1), (0, 10)]),
    ],
    "UNITNAME": ['fr', 'df'],
    "CODE": ['SSt', 'fgh'],
    "GROUP": ["Sedimentary", "ign"],
    "SUPERGROUP": ["Mesozoic", "arc"],
    "DESCRIPTION": ["A", "B"],
    "ROCKTYPE1": ["A", "B"],
    "ROCKTYPE2": ["Quartz", "FDs"],
    "MIN_AGE": [150.0, 200],
    "MAX_AGE": [200.0, 250],
    "ID": [1, 1],
}
# Create a GeoDataFrame for geology
geology_gdf = gpd.GeoDataFrame(geology_data, crs="EPSG:4326")

# Ensure that all string columns are of dtype str
# for col in ["UNITNAME", "CODE", "GROUP", "SUPERGROUP", "DESCRIPTION", "ROCKTYPE1", "ROCKTYPE2"]:
#     geology_gdf[col] = geology_gdf[col].astype(str)

from map2loop.mapdata import MapData

map_data = MapData()
map_data.config = MockConfig()
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.GEOLOGY] = geology_gdf

validity_check, message = data_checks.check_geology_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%

geology_data = {
    "geometry": [
        shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        shapely.geometry.Polygon([(0, 0), (10, 0), (1, 1), (0, 10)]),
    ],
    "UNITNAME": ['fr', 'df'],
    "CODE": ['SSt', 'fgh'],
    "GROUP": ["Sedimentary", "ign"],
    "SUPERGROUP": ["Mesozoic", "arc"],
    "DESCRIPTION": ["A", "B"],
    "ROCKTYPE1": ["A", None],
    "ROCKTYPE2": ["Quartz", "FDs"],
    "MIN_AGE": [150.0, 200],
    "MAX_AGE": [200.0, 250],
    "ID": [1, None],
}
# Create a GeoDataFrame for geology
geology_gdf = gpd.GeoDataFrame(geology_data, crs="EPSG:4326")

# Ensure that all string columns are of dtype str
# for col in ["UNITNAME", "CODE", "GROUP", "SUPERGROUP", "DESCRIPTION", "ROCKTYPE1", "ROCKTYPE2"]:
#     geology_gdf[col] = geology_gdf[col].astype(str)

from map2loop.mapdata import MapData

map_data = MapData()
map_data.config = MockConfig()
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.GEOLOGY] = geology_gdf

validity_check, message = data_checks.check_geology_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%

geology_data = {
    "geometry": [
        shapely.geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        shapely.geometry.Polygon([(0, 0), (10, 0), (1, 1), (0, 10)]),
    ],
    "UNITNAME": ['fr', None],
    "CODE": ['SSt', 'fgh'],
    "GROUP": ["Sedimentary", "ign"],
    "SUPERGROUP": ["Mesozoic", "arc"],
    "DESCRIPTION": ["A", "B"],
    "ROCKTYPE1": ["A", None],
    "ROCKTYPE2": ["Quartz", "FDs"],
    "MIN_AGE": [150.0, 200],
    "MAX_AGE": [200.0, 250],
    "ID": [1, 4],
}
# Create a GeoDataFrame for geology
geology_gdf = gpd.GeoDataFrame(geology_data, crs="EPSG:4326")

# Ensure that all string columns are of dtype str
# for col in ["UNITNAME", "CODE", "GROUP", "SUPERGROUP", "DESCRIPTION", "ROCKTYPE1", "ROCKTYPE2"]:
#     geology_gdf[col] = geology_gdf[col].astype(str)

from map2loop.mapdata import MapData

map_data = MapData()
map_data.config = MockConfig()
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.GEOLOGY] = geology_gdf

validity_check, message = data_checks.check_geology_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
