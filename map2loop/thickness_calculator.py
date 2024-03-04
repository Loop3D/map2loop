import os
from abc import ABC, abstractmethod
import beartype
import numpy
import pandas
import geopandas
from statistics import mean
from .mapdata import MapData
from map2loop.sampler import SamplerSpacing
from interpolator import NormalVectorInterpolator, DipInterpolator
from utils import normal_vector_to_dipdirection_dip, create_points
from .m2l_enums import Datatype
from shapely.ops import nearest_points
from shapely.geometry import Point, LineString

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
    def compute(
            self,
            units: pandas.DataFrame,
            stratigraphic_order: list,
            basal_contacts: geopandas.GeoDataFrame,
            map_data: MapData,
    ) -> pandas.DataFrame:
        """
        Execute thickness calculator method (abstract method)

        Args:
            units (pandas.DataFrame): the data frame of units to add thicknesses to
            stratigraphic_order (list): a list of unit names sorted from youngest to oldest
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            pandas.DataFrame: units dataframe with added thickness column for calculated thickness values
        """
        pass


class ThicknessCalculatorAlpha(ThicknessCalculator):
    """
    ThicknessCalculator class which estimates unit thickness based on units, basal_contacts and stratigraphic order
    """

    def __init__(self):
        """
        Initialiser for alpha version of the thickness calculator
        """
        self.thickness_calculator_label = "ThicknessCalculatorAlpha"

    @beartype.beartype
    def compute(
            self,
            units: pandas.DataFrame,
            stratigraphic_order: list,
            basal_contacts: pandas.DataFrame,
            map_data: MapData,
    ) -> pandas.DataFrame:
        """
        Execute thickness calculator method takes unit data, basal_contacts and stratigraphic order and attempts to estimate unit thickness.
        Note: Thicknesses of the top and bottom units are not possible with this data and so are assigned the average of all other calculated unit thicknesses.

        Args:
            units (pandas.DataFrame): the data frame of units to add thicknesses to
            stratigraphic_order (list): a list of unit names sorted from youngest to oldest
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            pandas.DataFrame: units dataframe with added thickness column for calculated thickness values
        """
        # TODO: If we have orientation data near basal contact points we can estimate
        # the actual distance between contacts rather than just using the horizontal distance
        no_distance = -1.0
        basal_contacts = basal_contacts[basal_contacts["type"] == "BASAL"]
        thicknesses = units.copy()
        # Set default value
        thicknesses["thickness"] = no_distance
        basal_unit_list = basal_contacts["basal_unit"].to_list()
        if len(stratigraphic_order) < 3:
            print(
                f"Cannot make any thickness calculations with only {len(stratigraphic_order)} units"
            )
            return thicknesses
        for i in range(1, len(stratigraphic_order) - 1):
            # Compare basal contacts of adjacent units
            if (
                    stratigraphic_order[i] in basal_unit_list
                    and stratigraphic_order[i + 1] in basal_unit_list
            ):
                contact1 = basal_contacts[
                    basal_contacts["basal_unit"] == stratigraphic_order[i]
                    ]["geometry"].to_list()[0]
                contact2 = basal_contacts[
                    basal_contacts["basal_unit"] == stratigraphic_order[i + 1]
                    ]["geometry"].to_list()[0]
                if contact1 is not None and contact2 is not None:
                    distance = contact1.distance(contact2)
                else:
                    print(
                        f"Cannot calculate thickness between {stratigraphic_order[i]} and {stratigraphic_order[i + 1]}"
                    )
                    distance = no_distance
            else:
                print(
                    f"Cannot calculate thickness between {stratigraphic_order[i]} and {stratigraphic_order[i + 1]}"
                )

                distance = no_distance

            # Maximum thickness is the horizontal distance between the minimum of these distances
            # Find row in unit_dataframe corresponding to unit and replace thickness value if it is -1 or larger than distance
            idx = thicknesses.index[
                thicknesses["name"] == stratigraphic_order[i]
                ].tolist()[0]
            if thicknesses.loc[idx, "thickness"] == -1:

                val = distance
            else:
                val = min(distance, thicknesses.at[idx, "thickness"])
            thicknesses.loc[idx, "thickness"] = val

        # If no thickness calculations can be made with current stratigraphic column set all units
        # to a uniform thickness value
        if len(thicknesses[thicknesses["thickness"] > 0]) < 1:
            thicknesses["thickness"] = 100.0
        mean_thickness = mean(thicknesses[thicknesses["thickness"] > 0]["thickness"])

        # For any unit thickness that still hasn't been calculated (i.e. at -1) set to
        # the mean thickness of the other units
        thicknesses["thickness"] = thicknesses.apply(
            lambda row: mean_thickness if row["thickness"] == -1 else row["thickness"],
            axis=1,
        )
        return thicknesses

    # TODO: use S-Tree to find intersections,
    # and K-D tree to find nearest points for efficient computations


class ThicknessCalculatorBeta(ThicknessCalculator):

    def __init__(self):
        """
        Initialiser for theta version of the thickness calculator
        """
        self.thickness_calculator_label = "ThicknessCalculatorBeta"

    def compute(self,
                units: pandas.DataFrame,
                stratigraphic_order: list,
                basal_contacts: pandas.DataFrame,
                map_data: MapData,
                ) -> pandas.DataFrame:
        """
        Args:
            units (pandas.DataFrame): the data frame of units to add thicknesses to
            stratigraphic_order (list): a list of unit names sorted from youngest to oldest
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            pandas.DataFrame: units dataframe with added thickness column for calculated thickness values
        """
        no_distance = -1.0
        basal_contacts = basal_contacts[basal_contacts["type"] == "BASAL"]
        thicknesses = units.copy()
        # Set default value
        thicknesses["thickness"] = no_distance
        basal_unit_list = basal_contacts["basal_unit"].to_list()
        # 1. calculate $spacing using bounding box
        # bounding_box = map_data.bounding_box
        # side_length = bounding_box['maxx'] - bounding_box['minx']
        # # define the spacing of the sampler automatically to 4% of the side length of the bounding box
        # spacing = side_length * 0.04
        # # # 2. Sample $basal_contacts using $spacing
        # sampler = SamplerSpacing(spacing)
        # sampled_contacts = map_data.sampled_contacts
        # 4. interpolate orientation data using bounding box
        interpolator = NormalVectorInterpolator()
        normal_vectors = interpolator.interpolate(map_data)
        # convert normal vectors to dip and dip direction
        dip, dip_direction = normal_vector_to_dipdirection_dip(normal_vectors[:, 0],
                                                               normal_vectors[:, 1],
                                                               normal_vectors[:, 2])
        interp_dataframe = geopandas.GeoDataFrame()
        interp_dataframe["dip"] = dip
        interp_dataframe["dip_direction"] = dip_direction
        xy = numpy.array([interpolator.xi, interpolator.yi]).T
        interp_dataframe["geometry"] = create_points(xy)
        # 5. For each interpolated point, assign name of unit using spatial join
        units = map_data.get_map_data(Datatype.GEOLOGY)
        interp_dataframe = interp_dataframe.sjoin(units, how="inner", op="within")
        interp_dataframe = interp_dataframe[["geometry", "DIPDIR", "DIP", "ID_left", "UNITNAME"]].copy()
        interp_dataframe['nearest_point'] = None

        if len(stratigraphic_order) < 3:
            print(
                f"Cannot make any thickness calculations with only {len(stratigraphic_order)} units"
            )
            return thicknesses
        for i in range(1, len(stratigraphic_order) - 1):
            # Compare basal contacts of adjacent units
            if (
                    stratigraphic_order[i] in basal_unit_list
                    and stratigraphic_order[i + 1] in basal_unit_list
            ):
                basal_contact = interp_dataframe[
                    interp_dataframe["basal_unit"] == stratigraphic_order[i]
                    ]["geometry"]
                top_contact = interp_dataframe[
                    interp_dataframe["basal_unit"] == stratigraphic_order[i + 1]
                    ]["geometry"]

                if basal_contact is not None and top_contact is not None:
                    # distance = contact1.distance(contact2)
                    for j, row in basal_contact.iterrows():
                        # Create unary union
                        unary_union = top_contact.unary_union
                        nearest = nearest_points(row.geometry, unary_union)
                        interp_dataframe.loc[j, 'nearest_point'] = nearest[1]
                        interp_dataframe.loc[j, 'line'] = LineString([row.geometry, nearest[1]])
                else:
                    print(
                        f"Cannot calculate thickness between {stratigraphic_order[i]} and {stratigraphic_order[i + 1]}"
                    )
                    distance = no_distance
            else:
                print(
                    f"Cannot calculate thickness between {stratigraphic_order[i]} and {stratigraphic_order[i + 1]}"
                )

        # 6. calculate the nearest neighbours between base and top of unit in the stratigraphic order
        # 7. select the nearest neighbour of each basal point and their distance to the top point
        # 8. calculate the nearest neighbour between orientation data and basal points and top points
        # 9. calculate angle ρ = cos–1 {[(x1 – x2) / L] sinθb sinδb + [(y1 – y2) / L] cosθb sinδb + [(z2 – z1) / L] cosδb} / L : is the distance between basal and top points
        # 10. Calculate true thickness t = L . cos ρ
