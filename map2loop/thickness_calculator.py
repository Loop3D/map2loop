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
from shapely import shortest_line, dwithin, length


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


class ThicknessCalculatorBeta(ThicknessCalculator):
    """
    This class is a subclass of the ThicknessCalculator abstract base class. It implements the thickness calculation
    method for a given set of data points. The class is initialized without any arguments.

    Attributes:
        thickness_calculator_label (str): A string that stores the label of the thickness calculator.
        For this class, it is "ThicknessCalculatorBeta".

    Methods:
        compute(units: pandas.DataFrame, stratigraphic_order: list, basal_contacts: pandas.DataFrame, map_data: MapData)
        -> pandas.DataFrame:
        Calculates a thickness map for the overall map area.
    """
    def __init__(self):
        """
        Initialiser for beta version of the thickness calculator
        """
        self.thickness_calculator_label = "ThicknessCalculatorBeta"

    def compute(self,
                units: pandas.DataFrame,
                stratigraphic_order: list,
                basal_contacts: pandas.DataFrame,
                map_data: MapData,
                ) -> pandas.DataFrame:

        # The rest of the code...
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

        Execute thickness calculator method takes unit data, basal_contacts, stratigraphic order, orientation data and
        DTM data to estimate a thickness map.
        # TODO: need to find better approach to calculate thickness for top and bottom units

        Args:
            units (pandas.DataFrame): the data frame of units to add thicknesses to
            stratigraphic_order (list): a list of unit names sorted from youngest to oldest
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            pandas.DataFrame: units dataframe with added thickness column for calculated thickness values
        """
        #TODO: find a way to provide either average thickness for each unit
        no_distance = -1.0
        basal_contacts = basal_contacts[basal_contacts["type"] == "BASAL"]
        thicknesses = units.copy()
        # Set default value
        thicknesses["thickness"] = no_distance
        basal_unit_list = basal_contacts["basal_unit"].to_list()
        # increase buffer around basal contacts to ensure that the points are included as intersections
        basal_contacts['geometry'] = basal_contacts['geometry'].buffer(0.01)
        # TODO: it's better to access the straphigraphyLocations directly from the map_data object
        # get the sampled contacts
        contacts = geopandas.GeoDataFrame(map_data.sampled_contacts)
        # build points from x and y coordinates
        contacts['geometry'] = contacts.apply(lambda row: Point(row.X, row.Y), axis=1)
        # set the crs of the contacts to the crs of the units
        contacts = contacts.set_crs(crs=units.crs)
        # get the elevation Z of the contacts
        contacts = map_data.get_value_from_raster_df(Datatype.DTM, contacts)
        # update the geometry of the contact points to include the Z value
        contacts['geometry'] = contacts.apply(lambda row: Point(row.geometry.x, row.geometry.y, row['Z']), axis=1)
        # spatial join the contact points with the basal contacts to get the unit for each contact point
        contacts = contacts.sjoin(basal_contacts, how='inner', predicate='intersects')
        # interpolate orientation data using bounding box
        interpolator = NormalVectorInterpolator()
        normal_vectors = interpolator.interpolate(map_data)
        # convert interpolated normal vectors to dip and dip direction
        dip, dip_direction = normal_vector_to_dipdirection_dip(normal_vectors[:, 0],
                                                               normal_vectors[:, 1],
                                                               normal_vectors[:, 2])
        # create a GeoDataFrame of the interpolated orientations
        interpolated_orientations = geopandas.GeoDataFrame()
        # add the dip and dip direction to the GeoDataFrame
        interpolated_orientations["dip"] = dip
        interpolated_orientations["dip_direction"] = dip_direction
        # get the x and y coordinates of the interpolated points
        xy = numpy.array([interpolator.xi, interpolator.yi]).T
        # create Point objects from the x and y coordinates
        interpolated_orientations["geometry"] = create_points(xy)
        # set the crs of the interpolated orientations to the crs of the units
        interpolated_orientations = interpolated_orientations.set_crs(crs=units.crs)
        # get the elevation Z of the interpolated points
        interpolated = map_data.get_value_from_raster_df(Datatype.DTM, interpolated_orientations)
        # update the geometry of the interpolated points to include the Z value
        interpolated['geometry'] = interpolated.apply(
            lambda row: Point(row.geometry.x, row.geometry.y, row['Z']), axis=1)
        # for each interpolated point, assign name of unit using spatial join
        interpolated_orientations = interpolated_orientations.sjoin(units, how="inner", op="within")
        interpolated_orientations = interpolated_orientations[
            ["geometry", "dipdir", "dip", "ID_left", "UNITNAME"]].copy()

        if len(stratigraphic_order) < 3:
            print(
                f"Cannot make any thickness calculations with only {len(stratigraphic_order)} units"
            )
            return thicknesses

        thickness_dataframes = []

        for i in range(1, len(stratigraphic_order) - 1):
            # Compare basal contacts of adjacent units
            if (
                    stratigraphic_order[i] in basal_unit_list
                    and stratigraphic_order[i + 1] in basal_unit_list
            ):
                basal_contact = contacts[
                    contacts["basal_unit"] == stratigraphic_order[i]
                    ]["geometry"]
                top_contact = contacts[
                    contacts["basal_unit"] == stratigraphic_order[i + 1]
                    ]["geometry"]

                if basal_contact is not None and top_contact is not None:
                    # distance = contact1.distance(contact2)
                    interp_points = interpolated_orientations.loc[
                        interpolated_orientations["UNITNAME"] == basal_contact["basal_unit"], "geometry"].copy()
                    x = numpy.array([point.x for point in interp_points])
                    y = numpy.array([point.y for point in interp_points])
                    interp_orientations = interpolated_orientations.loc[
                        interpolated_orientations["UNITNAME"] == basal_contact["basal_unit"], ["dip", "dipdir"]].copy()

                    for j, row in basal_contact.iterrows():
                        # Storage dataframe
                        dataframe = pandas.DataFrame()
                        # 6. find the shortest line between the basal contact points and top contact points
                        short_line = shortest_line(row.geometry, top_contact)
                        # calculate the length of the shortest line
                        _length = length(short_line)
                        # find the indices of the points that are within 5% of the length of the shortest line
                        indices = numpy.array(dwithin(short_line, interp_points, _length * 0.05))
                        # store the x and y coordinates of the points that are within
                        # 5% of the length of the shortest line
                        dataframe[i, 'X'] = x[indices]
                        dataframe[i, 'Y'] = y[indices]
                        # get the dip and dip direction of the points that are within
                        # 5% of the length of the shortest line
                        dip = numpy.deg2rad(interp_orientations['dip'].to_numpy()[indices])
                        dipdir = numpy.deg2rad(interp_orientations['dipdir'].to_numpy()[indices])
                        # get the end points of the shortest line
                        end_point = short_line.coords[-1]
                        end_x, end_y, end_z = end_point
                        # calculate the angle ρ
                        p = numpy.arccos(
                            ((row.X - end_x) / _length) * numpy.sin(dipdir) * numpy.sin(dip) +
                            ((row.Y - end_y) / _length) * numpy.cos(dipdir) * numpy.sin(dip) +
                            ((row.Z - end_z) / _length) * numpy.cos(dip)
                        )
                        # calculate the true thickness t = L . cos ρ
                        thickness = numpy.abs(_length * numpy.cos(p))
                        # store the thickness in the dataframe
                        dataframe[i, 'thickness'] = thickness
                        # store the dataframe in a thickness_dataframes list
                        thickness_dataframes.append(dataframe)
                else:
                    print(
                        f"Cannot calculate thickness between {stratigraphic_order[i]} and {stratigraphic_order[i + 1]}"
                    )
                    # distance = no_distance
            else:
                print(
                    f"Cannot calculate thickness between {stratigraphic_order[i]} and {stratigraphic_order[i + 1]}"
                )

        thicknesses = pandas.concat(thickness_dataframes, axis=1)
        return thicknesses
