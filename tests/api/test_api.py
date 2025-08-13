import pandas as pd
import geopandas as gpd
import numpy as np
from unittest.mock import patch

from map2loop.api import (
    calculate_thickness,
    interpolate_orientations,
    extract_basal_contacts,
)


def test_calculate_thickness_dispatch_alpha():
    units = pd.DataFrame()
    strat = []
    basal = gpd.GeoDataFrame()
    structure = pd.DataFrame()
    geology = gpd.GeoDataFrame()
    sampled = pd.DataFrame()

    mock_return = pd.DataFrame()
    with patch(
        "map2loop.thickness_calculator.ThicknessCalculatorAlpha.compute",
        return_value=mock_return,
    ) as compute:
        result = calculate_thickness(
            "alpha",
            units,
            strat,
            basal,
            structure,
            geology,
            sampled,
        )
        compute.assert_called_once()
        assert result is mock_return


def test_interpolate_orientations_dispatch_normal_vector():
    bounding_box = {"minx": 0, "maxx": 1, "miny": 0, "maxy": 1}
    structure = pd.DataFrame()

    mock_return = np.zeros((1, 3))
    with patch(
        "map2loop.interpolators.NormalVectorInterpolator.__call__",
        return_value=mock_return,
    ) as call:
        result = interpolate_orientations("normal_vector", bounding_box, structure)
        call.assert_called_once()
        assert (result == mock_return).all()


def test_extract_basal_contacts_dispatch():
    geology = gpd.GeoDataFrame()
    strat_col = []

    mock_return = gpd.GeoDataFrame()
    with patch(
        "map2loop.contact_extractor.ContactExtractor.extract_basal_contacts",
        return_value=mock_return,
    ) as extract:
        result = extract_basal_contacts(geology, strat_col)
        extract.assert_called_once()
        assert result is mock_return
