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
    def sort(self, units: pandas.DataFrame, unit_relationships: pandas.DataFrame, stratigraphic_order_hint: list) -> list:
        """
        Execute sorter method (abstract method)

        Args:
            units (pandas.DataFrame): the data frame to sort (columns must contain ["layerId", "name", "minAge", "maxAge", "group"])
            units_relationships (pandas.DataFrame): the relatinoships between units (columns must contain ["Index1", "Unitname1", "Index2", "Unitname2"])
            stratigraphic_order_hint (list): a list of unit names to be used as a hint to sorting the units

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
    def sort(self, units: pandas.DataFrame, unit_relationships: pandas.DataFrame, stratigraphic_order_hint: list) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.
        In this case it purely returns the hint list

        Args:
            units (pandas.DataFrame): the data frame to sort
            units_relationships (pandas.DataFrame): the relationships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units

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
    def sort(self, units: pandas.DataFrame, unit_relationships: pandas.DataFrame, stratigraphic_order_hint: list) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.

        Args:
            units (pandas.DataFrame): the data frame to sort
            units_relationships (pandas.DataFrame): the relatinoships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units

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

    def sort(self, units: pandas.DataFrame, unit_relationships: pandas.DataFrame, stratigraphic_order_hint: list) -> list:
        """
        Execute sorter method takes unit data, relationships and a hint and returns the sorted unit names based on this algorithm.

        Args:
            units (pandas.DataFrame): the data frame to sort
            units_relationships (pandas.DataFrame): the relatinoships between units
            stratigraphic_order_hint (list): a list of unit names to use as a hint to sorting the units

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
