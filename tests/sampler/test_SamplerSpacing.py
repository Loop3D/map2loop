import pandas
from map2loop.sampler import sample_data
from beartype.roar import BeartypeCallHintParamViolation
import pytest
import shapely
import geopandas
import numpy

# add test for SamplerSpacing specifically


@pytest.fixture
def sampler_spacing():
    return 1.0


@pytest.fixture
def correct_geodata():
    data = {
        'geometry': [
            shapely.LineString([(0, 0), (1, 1), (2, 2)]),
            shapely.Polygon([(0, 0), (1, 1), (1, 0), (0, 0)]),
            shapely.MultiLineString(
                [shapely.LineString([(0, 0), (1, 1)]), shapely.LineString([(2, 2), (3, 3)])]
            ),
        ],
        'ID': ['1', '2', '3'],
    }
    return geopandas.GeoDataFrame(data, geometry='geometry')


@pytest.fixture
def incorrect_geodata():
    data = {'geometry': [shapely.Point(0, 0), "Not a geometry"], 'ID': ['1', '2']}
    return pandas.DataFrame(data)


# test if correct outputs are generated from the right input
def test_sample_function_correct_data(sampler_spacing, correct_geodata):
    result = sample_data(
        spatial_data = correct_geodata,
        sampler_name = 'spacing',
        spacing = sampler_spacing
    )
    assert isinstance(result, pandas.DataFrame)
    assert 'X' in result.columns
    assert 'Y' in result.columns
    assert 'featureId' in result.columns


# add test for incorrect inputs - does it raise a BeartypeCallHintParamViolation error?
def test_sample_function_incorrect_data(sampler_spacing, incorrect_geodata):
    with pytest.raises(BeartypeCallHintParamViolation):
        sample_data(
            spatial_data = incorrect_geodata,
            sampler_name = 'spacing',
            spacing = sampler_spacing
        )


# for a specific >2 case
def test_sample_function_target_less_than_or_equal_to_2(sampler_spacing):
    data = {
        'geometry': [shapely.LineString([(0, 0), (0, 1)]), shapely.LineString([(0, 0), (1, 0)])],
        'ID': ['1', '2'],
    }
    gdf = geopandas.GeoDataFrame(data, geometry='geometry')
    result = sample_data(
        spatial_data = gdf,
        sampler_name = 'spacing',
        spacing = sampler_spacing
    )
    assert len(result) == 0  # No points should be sampled from the linestring


# Test if the extracted points are correct
def test_sample_function_extracted_points(sampler_spacing, correct_geodata):

    result = sample_data(
        spatial_data=correct_geodata,
        sampler_name = 'spacing',
        spacing = sampler_spacing
    )

    expected_points = [
        (0.0, 0.0),
        (0.707107, 0.707107),
        (0.0, 0.0),
        (0.707107, 0.707107),
        (1.0, 0.414214),
        (0.0, 0.0),
        [2.0, 2.0],
    ]

    sampled_points = list(zip(result['X'], result['Y']))

    distances = [
        shapely.geometry.Point(xy).distance(shapely.geometry.Point(ex))
        for xy, ex in zip(sampled_points, expected_points)
    ]

    assert numpy.absolute(distances).all() == 0.0
