# internal imports
from .m2l_enums import VerboseLevel

# external imports
import geopandas as gpd
import pandas as pd
import numpy as np

from .logging import getLogger

logger = getLogger(__name__)


def run_map2model(
    geology_data: gpd.GeoDataFrame=None,
    fault_data: gpd.GeoDataFrame=None,
    contact_data: gpd.GeoDataFrame=None,
    sorted_units = None,
    verbose_level: VerboseLevel = None
):
    """
    The main execute function that prepares, runs and parse the output of the map2model process

    Args:
        geology_data (geopandas.GeoDataFrame):
        fault_data (geopandas.GeoDataFrame):
        contact_data(geopandas.GeoDataFrame):
        verbose_level (VerboseLevel, optional):
            How much console output is sent. Defaults to None

    Returns:
        fault_fault_relationships: None or pandas.DataFrame
        data frame of fault to fault relationships with columns ["Fault1", "Fault2", "Type", "Angle"]
        unit_fault_relationships: None or pandas.DataFrame
            data frame of unit fault relationships with columns ["Unit", "Fault"]
        unit_unit_relationships: None or pandas.DataFrame
            data frame of unit unit relationships with columns ["Index1", "UnitName1", "Index2", "UnitName2"]
    """

    result = {}
    if fault_data:
        result["fault_fault_relationships"] = calculate_fault_fault_relationships(fault_data)
        if geology_data:
            result["unit_fault_relationships"] = calculate_unit_fault_relationships(geology_data, fault_data)
    if contact_data:
        result["unit_unit_relationships"] = calculate_unit_unit_relationships(contact_data)
    
    return result


def calculate_fault_fault_relationships(fault_data, buffer_radius = 500):
    faults = fault_data.copy()
    # reset index so that we can index the adjacency matrix with the index
    faults.reset_index(inplace=True)
    buffers = faults.buffer(buffer_radius)
    # create the adjacency matrix
    intersection = gpd.sjoin(
        gpd.GeoDataFrame(geometry=buffers), gpd.GeoDataFrame(geometry=faults["geometry"])
    )
    intersection["index_left"] = intersection.index
    intersection.reset_index(inplace=True)

    adjacency_matrix = np.zeros((faults.shape[0], faults.shape[0]), dtype=bool)
    adjacency_matrix[
        intersection.loc[:, "index_left"], intersection.loc[:, "index_right"]
    ] = True
    f1, f2 = np.where(np.tril(adjacency_matrix, k=-1))
    df = pd.DataFrame(
        {'Fault1': faults.loc[f1, 'ID'].to_list(), 'Fault2': faults.loc[f2, 'ID'].to_list()}
    )
    df['Angle'] = 60  # make it big to prevent LS from making splays
    df['Type'] = 'T'
    return df


def calculate_unit_fault_relationships(geology_data, fault_data):
    """Calculate unit/fault relationships using geopandas sjoin.
    This will return
    """
    units = geology_data["UNITNAME"].unique()
    faults = fault_data.reset_index().drop(columns=['index'])
    adjacency_matrix = np.zeros((len(units), faults.shape[0]), dtype=bool)
    for i, u in enumerate(units):
        unit = geology_data[geology_data["UNITNAME"] == u]
        intersection = gpd.sjoin(
            gpd.GeoDataFrame(geometry=faults["geometry"]),
            gpd.GeoDataFrame(geometry=unit["geometry"]),
        )
        intersection["index_left"] = intersection.index
        intersection.reset_index(inplace=True)
        adjacency_matrix[i, intersection.loc[:, "index_left"]] = True
    u, f = np.where(adjacency_matrix)
    df = pd.DataFrame({"Unit": units[u].tolist(), "Fault": faults.loc[f, "ID"].to_list()})
    return df


def calculate_unit_unit_relationships(contacts_data):
    unit_unit_relationships = contacts_data.copy().drop(
        columns=['length', 'geometry']
    )
    return unit_unit_relationships


def get_sorted_units():
    """
    Getter for the map2model sorted units

    Returns:
        list: The map2model stratigraphic column estimate
    """
    raise NotImplementedError("This method is not implemented")