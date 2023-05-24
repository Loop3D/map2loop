from abc import ABC, abstractmethod
import beartype
import pandas
import geopandas
from statistics import mean


class ThicknessCalculator(ABC):
    """
    Base Class of Thickness Calculator used to force structure of ThicknessCalculator

    Args:
        ABC (ABC): Derived from Abstract Base Class
    """
    def __init__(self):
        """
        Initialiser of for ThicknessCalculator
        """
        self.thickness_calculator_label = "ThicknessCalculatorBaseClass"

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.thickness_calculator_label

    @beartype.beartype
    @abstractmethod
    def compute(self, units: pandas.DataFrame, stratigraphic_order: list, basal_contacts: geopandas.GeoDataFrame) -> pandas.DataFrame:
        """
        Execute thickness calculator method (abstract method)

        Args:
            units (pandas.DataFrame): the data frame to sort (columns must contain ["layerId", "name", "minAge", "maxAge", "group"])
            stratigraphic_order (list): a list of unit names sorted from youngest to oldest
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])

        Returns:
            pandas.DataFrame: sorted list of unit names
        """
        pass


class ThicknessCalculatorAlpha(ThicknessCalculator):
    """
    ThiknessCalculator class which estimates unit thickness based on units, basal_contacts and stratigraphic order
    """
    def __init__(self):
        """
        Initialiser for alpha version of the thickness calculator
        """
        self.thickness_calculator_label = "ThicknessCalculatorAlpha"

    @beartype.beartype
    def compute(self, units: pandas.DataFrame, stratigraphic_order: list, basal_contacts: pandas.DataFrame) -> pandas.DataFrame:
        """
        Execute thickness calculator method takes unit data, basal_contacts and stratigraphic order and attempts to estimate unit thickness.
        Note: Thicknesses of the top and bottom units are not possible with this data and so are assigned the average of all other calculated unit thicknesses.

        Args:
            units (pandas.DataFrame): the data frame to sort (columns must contain ["layerId", "name", "minAge", "maxAge", "group"])
            stratigraphic_order (list): a list of unit names sorted from youngest to oldest
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])

        Returns:
            pandas.DataFrame: sorted list of unit names
        """
        # TODO: If we have orientation data near basal contact points we can estimate the actual distance between contacts
        # rather than just using the horizontal distance
        no_distance = -1
        basal_contacts = basal_contacts[basal_contacts["type"] == "BASAL"]
        thicknesses = units.copy()
        # Set default value
        thicknesses["thickness"] = no_distance
        basal_unit_list = basal_contacts["basal_unit"].to_list()
        if len(stratigraphic_order) < 3:
            print(f"Cannot make any thickness calculations with only {len(stratigraphic_order)} units")
            return thicknesses
        for i in range(1, len(stratigraphic_order)-1):
            # Compare basal contacts of adjacent units
            if stratigraphic_order[i] in basal_unit_list and stratigraphic_order[i+1] in basal_unit_list:
                contact1 = basal_contacts[basal_contacts["basal_unit"] == stratigraphic_order[i]]["geometry"].to_list()[0]
                contact2 = basal_contacts[basal_contacts["basal_unit"] == stratigraphic_order[i+1]]["geometry"].to_list()[0]
                if contact1 is not None and contact2 is not None:
                    distance = contact1.distance(contact2)
                else:
                    distance = no_distance
            else:
                distance = no_distance

            # Maximum thickness is the horizontal distance between the minimum of these distances
            # Find row in unit_dataframe corresponding to unit and replace thickness value if it is -1 or larger than distance
            idx = thicknesses.index[thicknesses["name"] == stratigraphic_order[i]].tolist()[0]
            if thicknesses.loc[idx, "thickness"] == -1:
                val = distance
            else:
                val = min(distance, thicknesses.at[idx, "thickness"])
            thicknesses.loc[idx, "thickness"] = val

        # If no thickness calculations can be made with current stratigraphic column set all untis
        # to a uniform thickness value
        if len(thicknesses[thicknesses["thickness"] > 0]) < 1:
            thicknesses["thickness"] = 100.0
        mean_thickness = mean(thicknesses[thicknesses["thickness"] > 0]["thickness"])
        thicknesses["thickness"] = thicknesses.apply(lambda row: mean_thickness if row["thickness"] == -1 else row["thickness"], axis=1)
        return thicknesses
