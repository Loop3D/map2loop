# internal imports
from .logging import getLogger
from map2loop.map_data import MapData

# external imports
import inspect
import geopandas
import pandas
import numpy
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
    fault_layer: geopandas.GeoDataFrame,
    buffer_radius: float = 500,
) -> pandas.DataFrame:
    """Calculate fault to fault relationships."""
    faults = fault_layer.copy()
    faults.reset_index(inplace=True)
    buffers = faults.buffer(buffer_radius)
    intersection = geopandas.sjoin(
        geopandas.GeoDataFrame(geometry=buffers),
        geopandas.GeoDataFrame(geometry=faults["geometry"]),
    )
    intersection["index_left"] = intersection.index
    intersection.reset_index(inplace=True)

    adjacency_matrix = numpy.zeros((faults.shape[0], faults.shape[0]), dtype=bool)
    adjacency_matrix[
        intersection.loc[:, "index_left"],
        intersection.loc[:, "index_right"],
    ] = True
    f1, f2 = numpy.where(numpy.tril(adjacency_matrix, k=-1))
    df = pandas.DataFrame(
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
    fault_layer: geopandas.GeoDataFrame,
    geology_layer: geopandas.GeoDataFrame,
    buffer_radius: float = 500,
) -> pandas.DataFrame:
    """Calculate unit to fault relationships."""
    units = geology_layer["UNITNAME"].unique()
    faults = fault_layer.copy().reset_index().drop(columns=["index"])
    adjacency_matrix = numpy.zeros((len(units), faults.shape[0]), dtype=bool)
    for i, u in enumerate(units):
        unit = geology_layer[geology_layer["UNITNAME"] == u]
        intersection = geopandas.sjoin(
            geopandas.GeoDataFrame(geometry=faults["geometry"]),
            geopandas.GeoDataFrame(geometry=unit["geometry"]),
        )
        intersection["index_left"] = intersection.index
        intersection.reset_index(inplace=True)
        adjacency_matrix[i, intersection.loc[:, "index_left"]] = True
    u_idx, f_idx = numpy.where(adjacency_matrix)
    df = pandas.DataFrame({"Unit": units[u_idx].tolist(), "Fault": faults.loc[f_idx, "ID"].to_list()})
    return df
@register_topology("unit_unit_relationships")
@beartype.beartype
def calculate_unit_unit_relationships(
    geology_layer: geopandas.GeoDataFrame,
    contacts: pandas.DataFrame = None,
    map_data: MapData = None,
) -> pandas.DataFrame:
    """Calculate unit to unit relationships."""
    if contacts is None:
        map_data.extract_all_contacts()
    return map_data.contacts.copy().drop(columns=["length", "geometry"])

@beartype.beartype
def run_topology(
    fault_layer: geopandas.GeoDataFrame,
    geology_layer: geopandas.GeoDataFrame,
    topology_name: str = "default",
    **kwargs,
) -> Dict[str, pandas.DataFrame]:
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
    fault_layer: geopandas.GeoDataFrame,
    geology_layer: geopandas.GeoDataFrame,
    contacts: pandas.DataFrame = None,
    map_data: MapData = None,
    buffer_radius: float = 500,
) -> Dict[str, pandas.DataFrame]:
    """Calculate topology relationships using basic geopandas operations."""
    ff_df = calculate_fault_fault_relationships(fault_layer, buffer_radius)
    uf_df = calculate_unit_fault_relationships(fault_layer, geology_layer, buffer_radius)
    uu_df = calculate_unit_unit_relationships(geology_layer, contacts, map_data)

    return {
        "fault_fault_relationships": ff_df,
        "unit_fault_relationships": uf_df,
        "unit_unit_relationships": uu_df,
    }
