from abc import ABC, abstractmethod
import beartype
import pandas
import numpy as np
import math
from .mapdata import MapData
from typing import Union

from .logging import getLogger

logger = getLogger(__name__)


class Sorter(ABC):
    """
    Base Class of Sorter used to force structure of Sorter

    Args:
        ABC (ABC): Derived from Abstract Base Class
    """

    def __init__(self):
        """
        Initialiser of for Sorter
        """
        self.sorter_label = "SorterBaseClass"

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.sorter_label

    @beartype.beartype
    @abstractmethod
    def sort(
        self,
        units: pandas.DataFrame,
        unit_relationships: pandas.DataFrame,
        contacts: pandas.DataFrame,
        map_data: MapData,
    ) -> list:
        """
        Execute sorter method (abstract method)

        Args:
            units (pandas.DataFrame): the data frame to sort (columns must contain ["layerId", "name", "minAge", "maxAge", "group"])
            unit_relationships (pandas.DataFrame): the relationships between units (columns must contain ["Index1", "Unitname1", "Index2", "Unitname2"])
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            list: sorted list of unit names
        """
        pass


class SorterUseNetworkX(Sorter):
    """
    Sorter class which returns a sorted list of units based on the unit relationships using a topological graph sorting algorithm
    """

    def __init__(self):
        """
        Initialiser for networkx graph sorter
        """
        self.sorter_label = "SorterUseNetworkX"

    @beartype.beartype
    def sort(
        self,
        units: pandas.DataFrame,
        unit_relationships: pandas.DataFrame,
        contacts: pandas.DataFrame,
        map_data: MapData,
    ) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.

        Args:
            units (pandas.DataFrame): the data frame to sort
            unit_relationships (pandas.DataFrame): the relationships between units
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            list: the sorted unit names
        """
        import networkx as nx

        graph = nx.DiGraph()
        name_to_index = {}
        for row in units.iterrows():
            graph.add_node(int(row[1]["layerId"]), name=row[1]["name"])
            name_to_index[row[1]["name"]] = int(row[1]["layerId"])
        for row in unit_relationships.iterrows():
            graph.add_edge(name_to_index[row[1]["UNITNAME_1"]], name_to_index[row[1]["UNITNAME_2"]])

        cycles = list(nx.simple_cycles(graph))
        for i in range(0, len(cycles)):
            if graph.has_edge(cycles[i][0], cycles[i][1]):
                graph.remove_edge(cycles[i][0], cycles[i][1])
                logger.warning(
                    " SorterUseNetworkX: Cycle found and contact edge removed:",
                    units["name"][cycles[i][0]],
                    units["name"][cycles[i][1]],
                )

        indexes = list(nx.topological_sort(graph))
        order = [units["name"][i] for i in list(indexes)]
        logger.info("Stratigraphic order calculated using networkx topological sort")
        logger.info(','.join(order))
        return order


class SorterUseHint(SorterUseNetworkX):
    def __init__(self):
        logger.info("SorterUseHint is deprecated in v3.2. Use SorterUseNetworkX instead")
        super().__init__()


class SorterAgeBased(Sorter):
    """
    Sorter class which returns a sorted list of units based on the min and max ages of the units
    """

    def __init__(self):
        """
        Initialiser for age based sorter
        """
        self.sorter_label = "SorterAgeBased"

    def sort(
        self,
        units: pandas.DataFrame,
        unit_relationships: pandas.DataFrame,
        contacts: pandas.DataFrame,
        map_data: MapData,
    ) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.

        Args:
            units (pandas.DataFrame): the data frame to sort
            unit_relationships (pandas.DataFrame): the relationships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            list: the sorted unit names
        """
        logger.info("Calling age based sorter")
        sorted_units = units.copy()
        # Calculate mean age
        if "minAge" in units.columns and "maxAge" in units.columns:
            sorted_units["meanAge"] = sorted_units.apply(
                lambda row: (row["minAge"] + row["maxAge"]) / 2.0, axis=1
            )
        else:
            sorted_units["meanAge"] = 0

        unique_mean_ages = sorted_units["meanAge"].unique()
        if len(unique_mean_ages) != len(sorted_units["meanAge"]):
            logger.warning(
                "Several mean unit ages are identical, so the calculated stratigraphic order may be incorrect"
            )
        if "group" in units.columns:
            sorted_units = sorted_units.sort_values(by=["group", "meanAge"])
            group_mean_age = sorted_units.groupby("group")["meanAge"].mean()
            group_order = group_mean_age.sort_values().index
            sorted_units["group"] = pandas.Categorical(
                sorted_units["group"], categories=group_order, ordered=True
            )
            sorted_units = sorted_units.sort_values(by=["group", "meanAge"])
        else:
            sorted_units = sorted_units.sort_values(by=["meanAge"])
        logger.info("Stratigraphic order calculated using age based sorting")
        for _i, row in sorted_units.iterrows():
            logger.info(f"{row['name']} - {row['minAge']} - {row['maxAge']} - {row['meanAge']}")

        return list(sorted_units["name"])


class SorterAlpha(Sorter):
    """
    Sorter class which returns a sorted list of units based on the adjacency of units
    prioritising the units with lower number of contacting units
    """

    def __init__(self):
        """
        Initialiser for adjacency based sorter
        """
        self.sorter_label = "SorterAlpha"

    def sort(
        self,
        units: pandas.DataFrame,
        unit_relationships: pandas.DataFrame,
        contacts: pandas.DataFrame,
        map_data: MapData,
    ) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.

        Args:
            units (pandas.DataFrame): the data frame to sort
            unit_relationships (pandas.DataFrame): the relationships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            list: the sorted unit names
        """
        import networkx as nx

        contacts = contacts.sort_values(by="length", ascending=False)[
            ["UNITNAME_1", "UNITNAME_2", "length"]
        ]
        units = list(units["name"].unique())
        graph = nx.Graph()
        for unit in units:
            graph.add_node(unit, name=unit)
        max_weight = max(list(contacts["length"])) + 1
        for _, row in contacts.iterrows():
            graph.add_edge(
                row["UNITNAME_1"], row["UNITNAME_2"], weight=int(max_weight - row["length"])
            )

        cnode = None
        new_graph = nx.DiGraph()
        while graph.number_of_nodes() > 0:
            if cnode is None:
                df = pandas.DataFrame(columns=["unit", "num_neighbours"])
                df["unit"] = list(graph.nodes)
                df["num_neighbours"] = df.apply(
                    lambda row: len(list(graph.neighbors(row["unit"]))), axis=1
                )
                df.sort_values(by=["num_neighbours"], inplace=True)
                df.reset_index(inplace=True, drop=True)
                cnode = df["unit"][0]
                new_graph.add_node(cnode)
            neighbour_edge_count = {}
            for neighbour in list(graph.neighbors(cnode)):
                neighbour_edge_count[neighbour] = len(list(graph.neighbors(neighbour)))
            if len(neighbour_edge_count) == 0:
                graph.remove_node(cnode)
                cnode = None
            else:
                node_with_min_edges = min(neighbour_edge_count, key=neighbour_edge_count.get)
                if neighbour_edge_count[node_with_min_edges] < 2:
                    new_graph.add_node(node_with_min_edges)
                    new_graph.add_edge(cnode, node_with_min_edges)
                    graph.remove_node(node_with_min_edges)
                else:
                    new_graph.add_node(node_with_min_edges)
                    new_graph.add_edge(cnode, node_with_min_edges)
                    graph.remove_node(cnode)
                    cnode = node_with_min_edges
        order = list(reversed(list(nx.topological_sort(new_graph))))
        logger.info("Stratigraphic order calculated using adjacency based sorting")
        logger.info(','.join(order))
        return order


class SorterMaximiseContacts(Sorter):
    """
    Sorter class which returns a sorted list of units based on the adjacency of units
    prioritising the maximum length of each contact
    """

    def __init__(self):
        """
        Initialiser for adjacency based sorter

        """
        self.sorter_label = "SorterMaximiseContacts"
        # variables for visualising/interrogating the sorter
        self.graph = None
        self.route = None
        self.directed_graph = None

    def sort(
        self,
        units: pandas.DataFrame,
        unit_relationships: pandas.DataFrame,
        contacts: pandas.DataFrame,
        map_data: MapData,
    ) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.

        Args:
            units (pandas.DataFrame): the data frame to sort
            unit_relationships (pandas.DataFrame): the relationships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            list: the sorted unit names
        """
        import networkx as nx
        import networkx.algorithms.approximation as nx_app

        sorted_contacts = contacts.sort_values(by="length", ascending=False)
        self.graph = nx.Graph()
        units = list(units["name"].unique())
        for unit in units:
            ## some units may not have any contacts e.g. if they are intrusives or sills. If we leave this then the
            ## sorter crashes
            if (
                unit not in sorted_contacts['UNITNAME_1']
                or unit not in sorted_contacts['UNITNAME_2']
            ):
                continue
            self.graph.add_node(unit, name=unit)

        max_weight = max(list(sorted_contacts["length"])) + 1
        sorted_contacts['length'] /= max_weight
        for _, row in sorted_contacts.iterrows():
            self.graph.add_edge(row["UNITNAME_1"], row["UNITNAME_2"], weight=(1 - row["length"]))

        self.route = nx_app.traveling_salesman_problem(self.graph)
        edge_list = list(nx.utils.pairwise(self.route))
        self.directed_graph = nx.DiGraph()
        self.directed_graph.add_node(edge_list[0][0])
        for edge in edge_list:
            if edge[1] not in self.directed_graph.nodes():
                self.directed_graph.add_node(edge[1])
                self.directed_graph.add_edge(edge[0], edge[1])

        # we need to reverse the order of the graph to get the correct order
        order = list(
            reversed(
                list(
                    nx.dfs_preorder_nodes(
                        self.directed_graph, source=list(self.directed_graph.nodes())[0]
                    )
                )
            )
        )
        logger.info("Stratigraphic order calculated using adjacency based sorting")
        logger.info(','.join(order))
        return order


class SorterObservationProjections(Sorter):
    """
    Sorter class which returns a sorted list of units based on the adjacency of units
    using the direction of observations to predict which unit is adjacent to the current one
    """

    def __init__(self, length: Union[float, int] = 1000):
        """
        Initialiser for adjacency based sorter

        Args:
            length (int): the length of the projection in metres
        """
        self.sorter_label = "SorterObservationProjections"
        self.length = length
        self.lines = []

    def sort(
        self,
        units: pandas.DataFrame,
        unit_relationships: pandas.DataFrame,
        contacts: pandas.DataFrame,
        map_data: MapData,
    ) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.

        Args:
            units (pandas.DataFrame): the data frame to sort
            unit_relationships (pandas.DataFrame): the relationships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            list: the sorted unit names
        """
        import networkx as nx
        import networkx.algorithms.approximation as nx_app
        from shapely.geometry import LineString, Point
        from map2loop.m2l_enums import Datatype

        geol = map_data.get_map_data(Datatype.GEOLOGY).copy()
        geol = geol.drop(geol.index[np.logical_or(geol["INTRUSIVE"], geol["SILL"])])
        orientations = map_data.get_map_data(Datatype.STRUCTURE).copy()

        # Create a map of maps to store younger/older observations
        ordered_unit_observations = []
        for _, row in orientations.iterrows():
            # get containing unit
            containing_unit = geol[geol.contains(row.geometry)]
            if len(containing_unit) > 1:
                logger.info(f"Orientation {row.ID} is within multiple units")
                logger.info(f"Check geology map around coordinates {row.geometry}")

            if len(containing_unit) < 1:
                logger.info(f"Orientation {row.ID} is not in a unit")
                logger.info(f"Check geology map around coordinates {row.geometry}")
            else:
                first_unit_name = containing_unit.iloc[0]["UNITNAME"]
                # Get units that a projected line passes through
                length = self.length
                dipDirRadians = row.DIPDIR * math.pi / 180.0
                dipRadians = row.DIP * math.pi / 180.0
                start = row.geometry
                end = Point(
                    start.x + math.sin(dipDirRadians) * length,
                    start.y + math.cos(dipDirRadians) * length,
                )
                line = LineString([start, end])
                self.lines.append(line)
                inter = geol[line.intersects(geol.geometry)]

                if len(inter) > 1:
                    intersect = line.intersection(inter.geometry.boundary)
                    # # Remove containing unit
                    intersect = intersect.drop(containing_unit.index)

                    # sort by distance from start point
                    sub = geol.loc[intersect.index].copy()
                    sub["distance"] = geol.distance(start)
                    sub = sub.sort_values(by="distance")

                    # Get first unit it hits and the point of intersection
                    second_unit_name = sub.iloc[0].UNITNAME

                    if intersect.loc[sub.index[0]].geom_type == "MultiPoint":
                        second_intersect_point = intersect.loc[sub.index[0]].geoms[0]
                    elif intersect.loc[sub.index[0]].geom_type == "Point":
                        second_intersect_point = intersect.loc[sub.index[0]]
                    else:
                        continue

                    # Get heights for intersection point and start of ray
                    height = map_data.get_value_from_raster(Datatype.DTM, start.x, start.y)
                    first_intersect_point = Point(start.x, start.y, height)
                    height = map_data.get_value_from_raster(
                        Datatype.DTM, second_intersect_point.x, second_intersect_point.y
                    )
                    second_intersect_point = Point(second_intersect_point.x, start.y, height)

                    # Check vertical difference between points and compare to projected dip angle
                    horizontal_dist = (
                        first_intersect_point.x - first_intersect_point.x,
                        second_intersect_point.y - first_intersect_point.y,
                    )
                    horizontal_dist = math.sqrt(horizontal_dist[0] ** 2 + horizontal_dist[1] ** 2)
                    projected_height = first_intersect_point.z + horizontal_dist * math.cos(
                        dipRadians
                    )

                    if second_intersect_point.z < projected_height:
                        ordered_unit_observations += [(first_unit_name, second_unit_name)]
                    else:
                        ordered_unit_observations += [(second_unit_name, first_unit_name)]
        self.ordered_unit_observations = ordered_unit_observations
        # Create a matrix of older versus younger frequency from observations
        unit_names = geol.UNITNAME.unique()
        df = pandas.DataFrame(0, index=unit_names, columns=unit_names)
        for younger, older in ordered_unit_observations:
            df.loc[younger, older] += 1
        max_value = max(df.max())

        # Using the older/younger matrix create a directed graph
        g = nx.DiGraph()
        remaining_units = unit_names
        for unit1 in unit_names:
            g.add_node(unit1)
        for unit1 in unit_names:
            remaining_units = remaining_units[1:]
            for unit2 in remaining_units:
                if unit1 != unit2:
                    weight = df.loc[unit1, unit2] - df.loc[unit2, unit1]
                    if weight < 0:
                        g.add_edge(unit1, unit2, weight=max_value + weight)
                    elif weight > 0:
                        g.add_edge(unit2, unit1, weight=max_value - weight)
                    if df.loc[unit1, unit2] > 0 and df.loc[unit2, unit1] > 0 and weight == 0:
                        # if both units have the same weight add a bidirectional edge
                        pass
                        print('')
                        g.add_edge(unit2, unit1, weight=max_value)
                        g.add_edge(unit1, unit2, weight=max_value)
        self.G = g
        # Link in unlinked units from contacts with max weight
        g_undirected = g.to_undirected()
        for unit in unit_names:
            if len(list(g_undirected.neighbors(unit))) < 1:
                mask1 = contacts["UNITNAME_1"] == unit
                mask2 = contacts["UNITNAME_2"] == unit
                for _, row in contacts[mask1 | mask2].iterrows():
                    if unit == row["UNITNAME_1"]:
                        g.add_edge(row["UNITNAME_2"], unit, weight=max_value * 10)
                    else:
                        g.add_edge(row["UNITNAME_1"], unit, weight=max_value * 10)

        # Run travelling salesman using the observation evidence as weighting
        route = nx_app.traveling_salesman_problem(g.to_undirected())
        self.route = route
        edge_list = list(nx.utils.pairwise(route))
        self.edge_list = edge_list
        dd = nx.DiGraph()
        dd.add_node(edge_list[0][0])
        for edge in edge_list:
            if edge[1] not in dd.nodes():
                dd.add_node(edge[1])
                dd.add_edge(edge[0], edge[1])
        self.directed = dd
        logger.info("Stratigraphic order calculated using observation based sorting")
        order = list(nx.dfs_preorder_nodes(dd, source=list(dd.nodes())[0]))
        logger.info(','.join(order))
        return order
