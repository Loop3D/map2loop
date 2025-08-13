"""High level API for common map2loop operations.

This module provides convenience wrapper functions exposing the
functionality of the thickness calculators, interpolators and
contact extraction utilities.  These wrappers offer a simplified
interface so that callers do not need to instantiate the underlying
classes directly.
"""

from __future__ import annotations

from typing import Any, Optional, List

import beartype
import pandas
import geopandas
import numpy
from osgeo import gdal
from scipy.interpolate import Rbf, LinearNDInterpolator

from .thickness_calculator import (
    ThicknessCalculatorAlpha,
    InterpolatedStructure,
    StructuralPoint,
)
from .interpolators import (
    NormalVectorInterpolator,
    DipDipDirectionInterpolator,
)
from .contact_extractor import ContactExtractor


__all__ = [
    "calculate_thickness",
    "interpolate_orientations",
    "extract_basal_contacts",
]


@beartype.beartype
def calculate_thickness(
    method: str,
    units: pandas.DataFrame,
    stratigraphic_order: List[str],
    basal_contacts: geopandas.GeoDataFrame,
    structure_data: pandas.DataFrame,
    geology_data: geopandas.GeoDataFrame,
    sampled_contacts: pandas.DataFrame,
    dtm_data: Optional[gdal.Dataset] = None,
    bounding_box: Optional[dict] = None,
    max_line_length: Optional[float] = None,
) -> pandas.DataFrame:
    """Calculate thickness values for geological units.

    This function dispatches to one of the available thickness calculator
    implementations based on *method* and returns the resulting units
    dataframe with thickness columns populated.

    Args:
        method: Name of the thickness calculator to use. Supported values
            are ``"alpha"``, ``"interpolated_structure"`` and
            ``"structural_point"``.
        units: Data frame of units to add thickness information to.
        stratigraphic_order: List of unit names from youngest to oldest.
        basal_contacts: Basal contact geometry data.
        structure_data: Sampled structural orientation data.
        geology_data: Geology polygons with unit names.
        sampled_contacts: Data frame of sampled contact points.
        dtm_data: Digital terrain model used by certain calculators.
        bounding_box: Bounding box dictionary for generating grids when
            required by the calculator.
        max_line_length: Optional maximum length used when searching for
            line intersections.

    Returns:
        Units dataframe augmented with thickness columns.
    """

    name = method.lower()
    if name == "alpha":
        calculator = ThicknessCalculatorAlpha()
    elif name in {"interpolated_structure", "interpolated"}:
        calculator = InterpolatedStructure(
            dtm_data=dtm_data, bounding_box=bounding_box, max_line_length=max_line_length
        )
    elif name in {"structural_point", "structuralpoint"}:
        calculator = StructuralPoint(
            dtm_data=dtm_data, bounding_box=bounding_box, max_line_length=max_line_length
        )
    else:
        raise ValueError(f"Unknown thickness calculator '{method}'")

    return calculator.compute(
        units=units,
        stratigraphic_order=stratigraphic_order,
        basal_contacts=basal_contacts,
        structure_data=structure_data,
        geology_data=geology_data,
        sampled_contacts=sampled_contacts,
    )


@beartype.beartype
def interpolate_orientations(
    method: str,
    bounding_box: dict,
    structure_data: pandas.DataFrame,
    data_type: Any = None,
    interpolator: Any = Rbf,
) -> numpy.ndarray:
    """Interpolate structural orientation data.

    Args:
        method: Name of the interpolator to use. Supported values are
            ``"normal_vector"`` and ``"dip_dip_direction"``.
        bounding_box: Dictionary describing the interpolation area.
        structure_data: Sampled structural orientation data.
        data_type: Optional data type argument passed to
            :class:`DipDipDirectionInterpolator`.
        interpolator: Backend interpolator to use, e.g.
            :class:`scipy.interpolate.Rbf` or
            :class:`scipy.interpolate.LinearNDInterpolator`.

    Returns:
        Numpy array of interpolated values.
    """

    name = method.lower()
    if name in {"normal_vector", "normalvector"}:
        interp = NormalVectorInterpolator()
    elif name in {"dip_dip_direction", "dipdipdirection"}:
        interp = DipDipDirectionInterpolator(data_type=data_type)
    else:
        raise ValueError(f"Unknown interpolator '{method}'")

    return interp(bounding_box, structure_data, interpolator=interpolator)


@beartype.beartype
def extract_basal_contacts(
    geology: geopandas.GeoDataFrame,
    stratigraphic_column: List[str],
    faults: Optional[geopandas.GeoDataFrame] = None,
    save_contacts: bool = True,
) -> geopandas.GeoDataFrame:
    """Extract basal contacts from geology polygons.

    Args:
        geology: Geology dataset containing unit polygons.
        stratigraphic_column: Ordered list of unit names from youngest to
            oldest.
        faults: Optional faults dataset to be considered when extracting
            contacts.
        save_contacts: If ``True``, contacts are stored on the underlying
            :class:`ContactExtractor` instance.

    Returns:
        GeoDataFrame containing basal contacts.
    """

    extractor = ContactExtractor(geology=geology, faults=faults)
    return extractor.extract_basal_contacts(
        stratigraphic_column=stratigraphic_column, save_contacts=save_contacts
    )
