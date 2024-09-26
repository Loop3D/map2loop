import pytest
import geopandas as gpd
from shapely.geometry import LineString

from map2loop.mapdata import MapData
from map2loop.m2l_enums import VerboseLevel, Datatype

@pytest.fixture
def setup_map_data():
    # Create a mock MapData object with verbose level set to ALL
    map_data = MapData(verbose_level=VerboseLevel.ALL)

    # Simulate config with no minimum_fault_length set
    map_data.config.fault_config['minimum_fault_length'] = None

    return map_data

# for cases when there is no minimum_fault_length set in the config by user - does it update from map?
def test_update_minimum_fault_length_from_faults(setup_map_data):
    map_data = setup_map_data

    # Create a faults dataset with different fault lengths
    faults = gpd.GeoDataFrame({
        'geometry': [
            LineString([(0, 0), (1, 1)]),  # Length ~1.41
            LineString([(0, 0), (2, 2)]),  # Length ~2.83
        ]
    })

    # Set the raw data in the map_data object to simulate loaded fault data
    map_data.raw_data[Datatype.FAULT] = faults

    # Run the parsing logic which includes updating the minimum fault length
    map_data.parse_fault_map()

    # Assert that the minimum fault length was updated from the data
    assert map_data.config.fault_config['minimum_fault_length'] == pytest.approx(1.414, 0.001), \
        f"Expected minimum_fault_length to be 1.414, but got {map_data.config.fault_config['minimum_fault_length']}"

# are faults with length less than minimum_fault_length removed from the dataset? 
def test_cropping_faults_by_minimum_fault_length(setup_map_data):
    map_data = setup_map_data

    # Set minimum_fault_length in the config to 10
    map_data.config.fault_config['minimum_fault_length'] = 10.0

    map_data.config.fault_config['name_column'] = 'NAME'
    map_data.config.fault_config['dip_column'] = 'DIP'

    # Create a mock faults dataset with lengths < 10 and > 10
    faults = gpd.GeoDataFrame({
            'geometry': [
                LineString([(0, 0), (2, 2)]),  # Length ~2.83 (should be cropped)
                LineString([(0, 0), (5, 5)]),  # Length ~7.07 (should be cropped)
                LineString([(0, 0), (10, 10)])  # Length ~14.14 (should remain)
            ],
            'NAME': ['Fault_1', 'Fault_2', 'Fault_3'],  
            'DIP': [60, 45, 30],  
            'DIPDIR': [90, 120, 150]  
        })
    
    # Set the raw data in the map_data object to simulate loaded fault data
    map_data.raw_data[Datatype.FAULT] = faults
    map_data.parse_fault_map()
    cropped_faults =  map_data.data[Datatype.FAULT]
    
    # Assert that only 1 fault remains (the one with length ~14.14)
    assert len(cropped_faults) == 1, \
        f"Expected only 1 fault remaining after cropping, but found {len(cropped_faults)}"

    # Optionally, check that the remaining fault has the correct geometry (the long one)
    assert cropped_faults.iloc[0].geometry.length == pytest.approx(14.14, 0.01), \
        f"Expected remaining fault length to be 14.14, but got {cropped_faults.iloc[0].geometry.length}"