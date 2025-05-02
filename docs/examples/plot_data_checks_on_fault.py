# %%
import geopandas as gpd
import shapely.geometry
from map2loop.mapdata import MapData
from map2loop.data_checks import check_fault_fields_validity


# Mock Datatype Enum
class Datatype:
    GEOLOGY = 0
    STRUCTURE = 1
    FAULT = 2


# Mock Config class
class MockConfig:
    def __init__(self):
        self.fault_config = {
            "structtype_column": "FEATURE",
            "fault_text": "Fault",
            "objectid_column": "ID",
        }


# Mock data for the fault dataset
valid_fault_data = {
    "geometry": [
        shapely.geometry.LineString([(0, 0), (1, 1)]),
        shapely.geometry.MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
    ],
    "FEATURE": ["Fault A", "Fault B"],
    "ID": [1, 2],
}

# Create a GeoDataFrame for valid fault data
valid_fault_gdf = gpd.GeoDataFrame(valid_fault_data, crs="EPSG:4326")

# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid fault data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.FAULT] = valid_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data with invalid geometry
invalid_geometry_fault_data = valid_fault_data.copy()
invalid_geometry_fault_data["geometry"] = [
    shapely.geometry.LineString([(0, 0), (1, 1)]),
    shapely.geometry.Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)]),  # Invalid geometry
]
invalid_geometry_fault_gdf = gpd.GeoDataFrame(invalid_geometry_fault_data, crs="EPSG:4326")

# Test with invalid geometry
map_data.raw_data[Datatype.FAULT] = invalid_geometry_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the fault dataset
valid_fault_data = {
    "geometry": [
        shapely.geometry.LineString([(0, 0), (1, 1)]),
        shapely.geometry.MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
    ],
    "FEATURE2": ["f A", "Fault B"],
    "ID": [1, 2],
}

# Create a GeoDataFrame for valid fault data
valid_fault_gdf = gpd.GeoDataFrame(valid_fault_data, crs="EPSG:4326")

# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid fault data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.FAULT] = valid_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the fault dataset
valid_fault_data = {
    "geometry": [
        shapely.geometry.LineString([(0, 0), (1, 1)]),
        shapely.geometry.MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
    ],
    "FEATURE": [5, 2],
    "ID": [1, 2],
}

# Create a GeoDataFrame for valid fault data
valid_fault_gdf = gpd.GeoDataFrame(valid_fault_data, crs="EPSG:4326")

# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid fault data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.FAULT] = valid_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the fault dataset
valid_fault_data = {
    "geometry": [
        shapely.geometry.LineString([(0, 0), (1, 1)]),
        shapely.geometry.MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
    ],
    "FEATURE": ["ult A", "faultB"],
    "ID": [1, 2],
}

# Create a GeoDataFrame for valid fault data
valid_fault_gdf = gpd.GeoDataFrame(valid_fault_data, crs="EPSG:4326")

# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid fault data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.FAULT] = valid_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the fault dataset
valid_fault_data = {
    "geometry": [
        shapely.geometry.LineString([(0, 0), (1, 1)]),
        shapely.geometry.MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
    ],
    "FEATURE": ["Fault", "Fault"],
    "NAME": ['Zuleika_1', 'Zuleika'],
    "ID": [1, 2],
}


class MockConfig:
    def __init__(self):
        self.fault_config = {
            "structtype_column": "FEATURE",
            "fault_text": "Fault",
            "objectid_column": "ID",
            "name_column": 'tEST',
        }


# Create a GeoDataFrame for valid fault data
valid_fault_gdf = gpd.GeoDataFrame(valid_fault_data, crs="EPSG:4326")

# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid fault data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.FAULT] = valid_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the fault dataset
valid_fault_data = {
    "geometry": [
        shapely.geometry.LineString([(0, 0), (1, 1)]),
        shapely.geometry.MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
    ],
    "FEATURE": ["Fault", "Fault"],
    "NAME": [1, 'Zuleika'],
    "ID": [1, 2],
}


class MockConfig:
    def __init__(self):
        self.fault_config = {
            "structtype_column": "FEATURE",
            "fault_text": "Fault",
            "objectid_column": "ID",
            "name_column": 'NAME',
        }


# Create a GeoDataFrame for valid fault data
valid_fault_gdf = gpd.GeoDataFrame(valid_fault_data, crs="EPSG:4326")

# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid fault data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.FAULT] = valid_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the fault dataset
valid_fault_data = {
    "geometry": [
        shapely.geometry.LineString([(0, 0), (1, 1)]),
        shapely.geometry.MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
    ],
    "FEATURE": ["Fault", "Fault"],
    "NAME": [None, 'Zuleika'],
    "ID": [1, 2],
}


class MockConfig:
    def __init__(self):
        self.fault_config = {
            "structtype_column": "FEATURE",
            "fault_text": "Fault",
            "objectid_column": "ID",
            "name_column": 'NAME',
        }


# Create a GeoDataFrame for valid fault data
valid_fault_gdf = gpd.GeoDataFrame(valid_fault_data, crs="EPSG:4326")

# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid fault data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.FAULT] = valid_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the fault dataset
valid_fault_data = {
    "geometry": [
        shapely.geometry.LineString([(0, 0), (1, 1)]),
        shapely.geometry.MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
    ],
    "FEATURE": ["Fault", "Fault"],
    "NAME": ['Zuleika', 'Zuleika'],
    "ID": [1, 2],
    "DIP": [45, 50],
}


class MockConfig:
    def __init__(self):
        self.fault_config = {
            "structtype_column": "FEATURE",
            "fault_text": "Fault",
            "objectid_column": "ID",
            "name_column": 'NAME',
            "dip_column": 'DIP2',
        }


# Create a GeoDataFrame for valid fault data
valid_fault_gdf = gpd.GeoDataFrame(valid_fault_data, crs="EPSG:4326")

# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid fault data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.FAULT] = valid_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the fault dataset
valid_fault_data = {
    "geometry": [
        shapely.geometry.LineString([(0, 0), (1, 1)]),
        shapely.geometry.MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
    ],
    "FEATURE": ["Fault", "Fault"],
    "NAME": ['Zuleika', 'Zuleika'],
    "ID": [1, 2],
    "DIP": ['A', 50],
}


class MockConfig:
    def __init__(self):
        self.fault_config = {
            "structtype_column": "FEATURE",
            "fault_text": "Fault",
            "objectid_column": "ID",
            "name_column": 'NAME',
            "dip_column": 'DIP',
        }


# Create a GeoDataFrame for valid fault data
valid_fault_gdf = gpd.GeoDataFrame(valid_fault_data, crs="EPSG:4326")

# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid fault data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.FAULT] = valid_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the fault dataset
valid_fault_data = {
    "geometry": [
        shapely.geometry.LineString([(0, 0), (1, 1)]),
        shapely.geometry.MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
    ],
    "FEATURE": ["Fault", "Fault"],
    "NAME": ['Zuleika', 'Zuleika'],
    "ID": [1, 2],
    "DIP": [70, 50],
    "STRIKE": [150, None],
    'DEC': ["north_east", "southt"],
}


class MockConfig:
    def __init__(self):
        self.fault_config = {
            "structtype_column": "FEATURE",
            "fault_text": "Fault",
            "objectid_column": "ID",
            "name_column": 'NAME',
            "dip_column": 'DIP',
            "dipdir_column": 'STRIKE',
            "dip_estimate_column": 'DEC',
        }


# Create a GeoDataFrame for valid fault data
valid_fault_gdf = gpd.GeoDataFrame(valid_fault_data, crs="EPSG:4326")

# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid fault data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.FAULT] = valid_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
# Mock data for the fault dataset
fhg = None
valid_fault_data = {
    "geometry": [
        shapely.geometry.LineString([(0, 0), (1, 1)]),
        shapely.geometry.MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
    ],
    "FEATURE": ["Fault", "Fault"],
    "NAME": ['Zuleika', 'Zuleika'],
    "ID": [fhg, 2],
    "DIP": [70, 50],
    "STRIKE": [150, None],
    'DEC': ["north_east", "southt"],
}


class MockConfig:
    def __init__(self):
        self.fault_config = {
            "structtype_column": "FEATURE",
            "fault_text": "Fault",
            "objectid_column": "ID",
            "name_column": 'NAME',
            "dip_column": 'DIP',
            "dipdir_column": 'STRIKE',
            # "dip_estimate_column": 'DEC'
        }


# Create a GeoDataFrame for valid fault data
valid_fault_gdf = gpd.GeoDataFrame(valid_fault_data, crs="EPSG:4326")

# Instantiate the MapData class with the mock config and data
map_data = MapData()
map_data.config = MockConfig()

# Test with valid fault data
map_data.raw_data = [None] * len(Datatype.__dict__)
map_data.raw_data[Datatype.FAULT] = valid_fault_gdf
validity_check, message = check_fault_fields_validity(map_data)
print(f"Validity Check: {validity_check}, Message: {message}")

# %%
