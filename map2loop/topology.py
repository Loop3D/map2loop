# internal imports
from .logging import getLogger

# external imports
import inspect
import geopandas as gpd
import pandas as pd
import numpy as np
import beartype
from beartype.typing import Dict

logger = getLogger(__name__)

_TOPOLOGY_REGISTRY = {}

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

@register_topology("fault_fault_relationships")
@beartype.beartype
def calculate_fault_fault_relationships(
    fault_layer: gpd.GeoDataFrame,
    buffer_radius: float = 500,
) -> pd.DataFrame:
    """Calculate fault to fault relationships."""
    faults = fault_layer.copy()
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

@register_topology("unit_fault_relationships")
@beartype.beartype
def calculate_unit_fault_relationships(
    fault_layer: gpd.GeoDataFrame,
    geology_layer: gpd.GeoDataFrame,
    buffer_radius: float = 500,
) -> pd.DataFrame:
    """Calculate unit to fault relationships."""
    units = geology_layer["UNITNAME"].unique()
    faults = fault_layer.copy().reset_index().drop(columns=["index"])
    adjacency_matrix = np.zeros((len(units), faults.shape[0]), dtype=bool)
    for i, u in enumerate(units):
        unit = geology_layer[geology_layer["UNITNAME"] == u]
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
@register_topology("unit_unit_relationships")
@beartype.beartype
def calculate_unit_unit_relationships(
    geology_layer: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """Calculate unit to unit relationships."""
    geology = geology_layer.dissolve(by="UNITNAME", as_index=False)
    units = geology["UNITNAME"].unique()
    contacts = []
    for i, unit1 in enumerate(units[:-1]):
        geom1 = geology.loc[geology["UNITNAME"] == unit1, "geometry"].unary_union
        for unit2 in units[i + 1 :]:
            geom2 = geology.loc[geology["UNITNAME"] == unit2, "geometry"].unary_union
            if not geom1.intersection(geom2).is_empty or geom1.touches(geom2):
                contacts.append((unit1, unit2))
    df = pd.DataFrame(contacts, columns=["UNITNAME_1", "UNITNAME_2"])
    return df

@beartype.beartype
def run_topology(
    fault_layer: gpd.GeoDataFrame,
    geology_layer: gpd.GeoDataFrame,
    topology_name: str = "default",
    **kwargs,
) -> Dict[str, pd.DataFrame]:
    """Execute a topology function by name."""
    runner = get_topology(topology_name)
    signature = inspect.signature(runner)
    call_args = {}
    if "fault_layer" in signature.parameters:
        call_args["fault_layer"] = fault_layer
    if "geology_layer" in signature.parameters:
        call_args["geology_layer"] = geology_layer
    call_args.update(kwargs)
    return runner(**call_args)

@register_topology("default")
@beartype.beartype
def topology_default(
    fault_layer: gpd.GeoDataFrame,
    geology_layer: gpd.GeoDataFrame,
    buffer_radius: float = 500,
) -> Dict[str, pd.DataFrame]:
    """Calculate topology relationships using basic geopandas operations."""
    ff_df = calculate_fault_fault_relationships(fault_layer, buffer_radius)
    uf_df = calculate_unit_fault_relationships(fault_layer, geology_layer, buffer_radius)
    uu_df = calculate_unit_unit_relationships(geology_layer)

    return {
        "fault_fault_relationships": ff_df,
        "unit_fault_relationships": uf_df,
        "unit_unit_relationships": uu_df,
    }
