import pandas
from map2loop.sampler import SamplerSpacing
from beartype.roar import BeartypeCallHintParamViolation
import pytest
import shapely
import geopandas

# add test for SamplerSpacing specifically

@pytest.fixture
def sampler_spacing():
    return SamplerSpacing(spacing=1.0)

@pytest.fixture
def correct_geodata():
    data = {
        'geometry': [
            shapely.LineString([(0, 0), (1, 1), (2, 2)]),
            shapely.Polygon([(0, 0), (1, 1), (1, 0), (0, 0)]),
            shapely.MultiLineString([shapely.LineString([(0, 0), (1, 1)]), shapely.LineString([(2, 2), (3, 3)])])
        ],
        'ID': ['1', '2', '3']
    }
    return geopandas.GeoDataFrame(data, geometry='geometry')

@pytest.fixture
def incorrect_geodata():
    data = {
        'geometry': [shapely.Point(0, 0), "Not a geometry"],
        'ID': ['1', '2']
    }
    return pandas.DataFrame(data)

# test if correct outputs are generated from the right input
def test_sample_function_correct_data(sampler_spacing, correct_geodata):
    result = sampler_spacing.sample(correct_geodata)
    assert isinstance(result, pandas.DataFrame)
    assert 'X' in result.columns
    assert 'Y' in result.columns
    assert 'featureId' in result.columns

# add test for incorrect inputs - does it raise a BeartypeCallHintParamViolation error?
def test_sample_function_incorrect_data(sampler_spacing, incorrect_geodata):
    with pytest.raises(BeartypeCallHintParamViolation):
        sampler_spacing.sample(spatial_data=incorrect_geodata)

# for a specific >2 case
def test_sample_function_target_less_than_or_equal_to_2():
    sampler_spacing = SamplerSpacing(spacing=1.0)
    data = {
        'geometry': [
            shapely.LineString([(0, 0), (0, 1)]),  
            shapely.LineString([(0, 0), (1, 0)]) 
        ],
        'ID': ['1', '2']
    }
    gdf = geopandas.GeoDataFrame(data, geometry='geometry')
    result = sampler_spacing.sample(spatial_data = gdf)
    assert len(result) == 0  # No points should be sampled from the linestring