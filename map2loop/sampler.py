# internal imports
from .utils import set_z_values_from_raster_df

# external imports
from abc import ABC, abstractmethod
import beartype
import geopandas
import pandas
import shapely
import numpy
from typing import Optional
from osgeo import gdal


_SAMPLER_REGISTRY = {}

@beartype.beartype
def register_sampler(name: str):
    """
    Register a sampler function with a given name.

    Args:
        name (str): the name of the sampler
    """
    def decorator(func):
        _SAMPLER_REGISTRY[name] = func
        return func
    return decorator

@beartype.beartype
def get_sampler(name: str):
    """
    Get a sampler function by name.

    Args:
        name (str): the name of the sampler to retrieve
    """
    if name not in _SAMPLER_REGISTRY:
        raise ValueError(f"Sampler {name} not found")
    return _SAMPLER_REGISTRY[name]

@beartype.beartype
def sample_data(
    spatial_data: geopandas.GeoDataFrame,
    sampler_name: str,
    dtm_data: Optional[geopandas.GeoDataFrame] = None,
    geology_data: Optional[geopandas.GeoDataFrame] = None,
    **kwargs
)-> pandas.DataFrame:
    """
    Execute sampling method (abstract method)

    Args:
        spatial_data (geopandas.GeoDataFrame): data frame to sample

    Returns:
        pandas.DataFrame: data frame containing samples
    """
    sampler = get_sampler(sampler_name)
    if sampler_name == 'decimator':
        if dtm_data is None or geology_data is None:
            raise ValueError("sample decimator requires both dtm and geology data")
        return sampler(spatial_data=spatial_data, dtm_data=dtm_data, geology_data=geology_data, **kwargs)
    else:
        return sampler(spatial_data=spatial_data, **kwargs)

@register_sampler("decimator")
@beartype.beartype
def sample_decimator(
    spatial_data: geopandas.GeoDataFrame, 
    dtm_data: gdal.Dataset, 
    geology_data: geopandas.GeoDataFrame,
    decimation: int = 1
) -> pandas.DataFrame:
    """
    Execute sample method takes full point data, samples the data and returns the decimated points

    Args:
        spatial_data (geopandas.GeoDataFrame): the data frame to sample

    Returns:
        pandas.DataFrame: the sampled data points
    """
    decimation = max(decimation, 1)
    data = spatial_data.copy()
    data["X"] = data.geometry.x
    data["Y"] = data.geometry.y
    data["Z"] = set_z_values_from_raster_df(dtm_data, data)["Z"]

    data["layerID"] = geopandas.sjoin(
        data, geology_data, how='left'
    )['index_right']

    data.reset_index(drop=True, inplace=True)

    return pandas.DataFrame(data[:: decimation].drop(columns="geometry"))

@register_sampler("spacing")
@beartype.beartype
def sample_spacing(
    spatial_data: geopandas.GeoDataFrame,
    spacing: float = 50.0,
) -> pandas.DataFrame:
    """
    Execute sample method takes full point data, samples the data and returns the sampled points

    Args:
        spatial_data (geopandas.GeoDataFrame): the data frame to sample (must contain column ["ID"])

    Returns:
        pandas.DataFrame: the sampled data points
    """
    spacing = max(spacing, 1.0)
    schema = {"ID": str, "X": float, "Y": float, "featureId": str}
    df = pandas.DataFrame(columns=schema.keys()).astype(schema)
    for _, row in spatial_data.iterrows():
        if type(row.geometry) is shapely.geometry.multipolygon.MultiPolygon:
            targets = row.geometry.boundary.geoms
        elif type(row.geometry) is shapely.geometry.polygon.Polygon:
            targets = [row.geometry.boundary]
        elif type(row.geometry) is shapely.geometry.multilinestring.MultiLineString:
            targets = row.geometry.geoms
        elif type(row.geometry) is shapely.geometry.linestring.LineString:
            targets = [row.geometry]
        else:
            targets = []

        # For the main cases Polygon and LineString the list 'targets' has one element
        for a, target in enumerate(targets):
            df2 = pandas.DataFrame(columns=schema.keys()).astype(schema)
            distances = numpy.arange(0, target.length, spacing)[:-1]
            points = [target.interpolate(distance) for distance in distances]
            df2["X"] = [point.x for point in points]
            df2["Y"] = [point.y for point in points]

            # # account for holes//rings in polygons
            df2["featureId"] = str(a)
            # 1. check if line is "closed"
            if target.is_ring:
                target_polygon = shapely.geometry.Polygon(target)
                if target_polygon.exterior.is_ccw:  # if counterclockwise --> hole
                    for j, target2 in enumerate(targets):
                        # skip if line or point
                        if len(target2.coords) >= 2:
                            continue
                        # which poly is the hole in? assign featureId of the same poly
                        t2_polygon = shapely.geometry.Polygon(target2)
                        if target.within(t2_polygon):  #
                            df2['featureId'] = str(j)

            df2["ID"] = row["ID"] if "ID" in spatial_data.columns else 0
            df = df2 if len(df) == 0 else pandas.concat([df, df2])

    df.reset_index(drop=True, inplace=True)
    return df
