from abc import ABC, abstractmethod
import beartype
import pandas


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
    def sort(self, units: pandas.DataFrame, unit_relationships: pandas.DataFrame, stratigraphic_order_hint: list, contacts: pandas.DataFrame) -> list:
        """
        Execute sorter method (abstract method)

        Args:
            units (pandas.DataFrame): the data frame to sort (columns must contain ["layerId", "name", "minAge", "maxAge", "group"])
            units_relationships (pandas.DataFrame): the relationships between units (columns must contain ["Index1", "Unitname1", "Index2", "Unitname2"])
            stratigraphic_order_hint (list): a list of unit names to be used as a hint to sorting the units
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres

        Returns:
            list: sorted list of unit names
        """
        pass


class SorterUseHint(Sorter):
    """
    Sorter class which only returns the hint (no algorithm for sorting is done in this class)
    """
    def __init__(self):
        """
        Initialiser for use hint sorter
        """
        self.sorter_label = "SorterUseHint"

    @beartype.beartype
    def sort(self, units: pandas.DataFrame, unit_relationships: pandas.DataFrame, stratigraphic_order_hint: list, contacts: pandas.DataFrame) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.
        In this case it purely returns the hint list

        Args:
            units (pandas.DataFrame): the data frame to sort
            units_relationships (pandas.DataFrame): the relationships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres

        Returns:
            list: the sorted unit names
        """
        return stratigraphic_order_hint


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
    def sort(self, units: pandas.DataFrame, unit_relationships: pandas.DataFrame, stratigraphic_order_hint: list, contacts: pandas.DataFrame) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.

        Args:
            units (pandas.DataFrame): the data frame to sort
            units_relationships (pandas.DataFrame): the relationships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres

        Returns:
            list: the sorted unit names
        """
        try:
            import networkx as nx
        except Exception:
            print("Cannot import networkx module, defaulting to SorterUseHint")
            return stratigraphic_order_hint

        graph = nx.DiGraph()
        for row in units.iterrows():
            graph.add_node(int(row[1]["layerId"]), name=row[1]["name"])
        for row in unit_relationships.iterrows():
            graph.add_edge(row[1]["Index1"], row[1]["Index2"])

        cycles = list(nx.simple_cycles(graph))
        for i in range(0, len(cycles)):
            if graph.has_edge(cycles[i][0], cycles[i][1]):
                graph.remove_edge(cycles[i][0], cycles[i][1])
                print(" SorterUseNetworkX Warning: Cycle found and contact edge removed:", units["name"][cycles[i][0]], units["name"][cycles[i][1]])

        indexes = (list(nx.topological_sort(graph)))
        order = [units["name"][i] for i in list(indexes)]
        return order


class SorterAgeBased(Sorter):
    """
    Sorter class which returns a sorted list of units based on the min and max ages of the units
    """
    def __init__(self):
        """
        Initialiser for age based sorter
        """
        self.sorter_label = "SorterAgeBased"

    def sort(self, units: pandas.DataFrame, unit_relationships: pandas.DataFrame, stratigraphic_order_hint: list, contacts: pandas.DataFrame) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.

        Args:
            units (pandas.DataFrame): the data frame to sort
            units_relationships (pandas.DataFrame): the relationships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres

        Returns:
            list: the sorted unit names
        """
        sorted_units = units.copy()
        if "minAge" in units.columns and "maxAge" in units.columns:
            sorted_units["meanAge"] = sorted_units.apply(lambda row: (row["minAge"] + row["maxAge"]) / 2.0, axis=1)
        else:
            sorted_units["meanAge"] = 0
        if "group" in units.columns:
            sorted_units = sorted_units.sort_values(by=["group", "meanAge"])
        else:
            sorted_units = sorted_units.sort_values(by=["meanAge"])

        return list(sorted_units["name"])


class SorterAlpha(Sorter):
    """
    Sorter class which returns a sorted list of units based on the adjacency of units
    """
    def __init__(self):
        """
        Initialiser for adjacency based sorter
        """
        self.sorter_label = "SorterAlpha"

    def sort(self, units: pandas.DataFrame, unit_relationships: pandas.DataFrame, stratigraphic_order_hint: list, contacts: pandas.DataFrame) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.

        Args:
            units (pandas.DataFrame): the data frame to sort
            units_relationships (pandas.DataFrame): the relationships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres

        Returns:
            list: the sorted unit names
        """
        try:
            import networkx as nx
        except Exception:
            print("Cannot import networkx module, defaulting to SorterUseHint")
            return stratigraphic_order_hint

        contacts = contacts.sort_values(by="length", ascending=False)[["UNITNAME_1", "UNITNAME_2", "length"]]
        units = list(units["name"].unique())
        graph = nx.Graph()
        for unit in units:
            graph.add_node(unit, name=unit)
        max_weight = max(list(contacts["length"])) + 1
        for _, row in contacts.iterrows():
            graph.add_edge(row["UNITNAME_1"], row["UNITNAME_2"], weight=int(max_weight - row["length"]))

        cnode = None
        new_graph = nx.DiGraph()
        while graph.number_of_nodes() > 0:
            if cnode is None:
                df = pandas.DataFrame(columns=["unit", "num_neighbours"])
                df["unit"] = units
                df["num_neighbours"] = df.apply(lambda row: len(list(graph.neighbors(row["unit"]))), axis=1)
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
        order = (list(nx.topological_sort(new_graph)))
        return order


class SorterBeta(Sorter):
    """
    Sorter class which returns a sorted list of units based on the adjacency of units
    """
    def __init__(self):
        """
        Initialiser for adjacency based sorter
        """
        self.sorter_label = "SorterBeta"

    def sort(self, units: pandas.DataFrame, unit_relationships: pandas.DataFrame, stratigraphic_order_hint: list, contacts: pandas.DataFrame) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.

        Args:
            units (pandas.DataFrame): the data frame to sort
            units_relationships (pandas.DataFrame): the relationships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units
            contacts (pandas.DataFrame): unit contacts with length of the contacts in metres

        Returns:
            list: the sorted unit names
        """
        try:
            import networkx as nx
        except Exception:
            print("Cannot import networkx module, defaulting to SorterUseHint")
            return stratigraphic_order_hint

        contacts = contacts.sort_values(by="length", ascending=False)[["UNITNAME_1", "UNITNAME_2", "length"]]
        units = list(units["name"].unique())
        graph = nx.Graph()
        for unit in units:
            graph.add_node(unit, name=unit)
        max_weight = max(list(contacts["length"])) + 1
        for _, row in contacts.iterrows():
            graph.add_edge(row["UNITNAME_1"], row["UNITNAME_2"], weight=int(max_weight - row["length"]))

        import matplotlib.pyplot as plt
        nx.draw_planar(graph, with_labels=True)
        plt.show()

        changed = True
        while changed is True:
            changed = False
            neighbour_count = {}
            for node in graph.nodes:
                neighbour_count[node] = len(list(graph.neighbors(node)))

            node_with_max_edges = max(neighbour_count, key=neighbour_count.get)
            count = neighbour_count[node_with_max_edges]
            if count > 2:
                for node in list(graph.neighbors(node_with_max_edges)):
                    if count > 2 and len(list(graph.neighbors(node))) > 2:
                        graph.remove_edge(node_with_max_edges, node)
                        changed = True
                        count = count - 1

        nx.draw_planar(graph, with_labels=True)
        plt.show()
        graph = nx.minimum_spanning_tree(graph, weight="weight")
        pos = nx.planar_layout(graph)
        nx.draw_networkx_nodes(graph, pos)
        nx.draw_networkx_edges(graph, pos)
        nx.draw_networkx_labels(graph, pos)
        nx.draw_networkx_edge_labels(graph, pos, nx.get_edge_attributes(graph, "weight"))
        plt.show()

        graph = nx.to_directed(graph)
        nx.draw_planar(graph, with_labels=True)
        plt.show()

        order = (list(nx.topological_sort(graph)))
        print(order)

        return order
