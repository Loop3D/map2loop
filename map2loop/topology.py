# internal imports
from .mapdata import MapData
from .logging import getLogger

# external imports
import geopandas as gpd
import pandas as pd
import numpy as np
import beartype
from beartype.typing import Dict

logger = getLogger(__name__)

_TOPOLOGY_REGISTRY = {}

@beartype.beartype
def calculate_fault_fault_relationships(
    map_data: MapData,
    buffer_radius: float = 500,
) -> pd.DataFrame:
    """Calculate fault to fault relationships."""
    faults = map_data.FAULT.copy()
    faults.reset_index(inplace=True)
    buffers = faults.buffer(buffer_radius)
    intersection = gpd.sjoin(
        gpd.GeoDataFrame(geometry=buffers),
        gpd.GeoDataFrame(geometry=faults["geometry"]),
    )
    intersection["index_left"] = intersection.index
    intersection.reset_index(inplace=True)

    adjacency_matrix = np.zeros((faults.shape[0], faults.shape[0]), dtype=bool)
    adjacency_matrix[
        intersection.loc[:, "index_left"],
        intersection.loc[:, "index_right"],
    ] = True
    f1, f2 = np.where(np.tril(adjacency_matrix, k=-1))
    df = pd.DataFrame(
        {
            "Fault1": faults.loc[f1, "ID"].to_list(),
            "Fault2": faults.loc[f2, "ID"].to_list(),
        }
    )
    df["Angle"] = 60
    df["Type"] = "T"
    return df

@beartype.beartype
def calculate_unit_fault_relationships(
    map_data: MapData,
    buffer_radius: float = 500,
) -> pd.DataFrame:
    """Calculate unit to fault relationships."""
    units = map_data.GEOLOGY["UNITNAME"].unique()
    faults = map_data.FAULT.copy().reset_index().drop(columns=["index"])
    adjacency_matrix = np.zeros((len(units), faults.shape[0]), dtype=bool)
    for i, u in enumerate(units):
        unit = map_data.GEOLOGY[map_data.GEOLOGY["UNITNAME"] == u]
        intersection = gpd.sjoin(
            gpd.GeoDataFrame(geometry=faults["geometry"]),
            gpd.GeoDataFrame(geometry=unit["geometry"]),
        )
        intersection["index_left"] = intersection.index
        intersection.reset_index(inplace=True)
        adjacency_matrix[i, intersection.loc[:, "index_left"]] = True
    u_idx, f_idx = np.where(adjacency_matrix)
    df = pd.DataFrame({"Unit": units[u_idx].tolist(), "Fault": faults.loc[f_idx, "ID"].to_list()})
    return df

@beartype.beartype
def calculate_unit_unit_relationships(map_data: MapData) -> pd.DataFrame:
    """Calculate unit to unit relationships."""
    if map_data.contacts is None:
        map_data.extract_all_contacts()
    return map_data.contacts.copy().drop(columns=["length", "geometry"])

@beartype.beartype
def register_topology(name: str):
    """Register a topology function with a given name."""
    def decorator(func):
        _TOPOLOGY_REGISTRY[name] = func
        return func
    return decorator

@beartype.beartype
def get_topology(name: str):
    """Retrieve a registered topology function."""
    if name not in _TOPOLOGY_REGISTRY:
        raise ValueError(f"Topology {name} not found")
    return _TOPOLOGY_REGISTRY[name]

@beartype.beartype
def run_topology(
    map_data: MapData,
    topology_name: str = "default",
    **kwargs,
) -> Dict[str, pd.DataFrame]:
    """Execute a topology function by name."""
    runner = get_topology(topology_name)
    return runner(map_data=map_data, **kwargs)

@register_topology("default")
@beartype.beartype
def topology_default(
    map_data: MapData,
    buffer_radius: float = 500,
) -> Dict[str, pd.DataFrame]:
    """Calculate topology relationships using basic geopandas operations."""
    ff_df = calculate_fault_fault_relationships(map_data, buffer_radius)
    uf_df = calculate_unit_fault_relationships(map_data, buffer_radius)
    uu_df = calculate_unit_unit_relationships(map_data)

    return {
        "fault_fault_relationships": ff_df,
        "unit_fault_relationships": uf_df,
        "unit_unit_relationships": uu_df,
    }
