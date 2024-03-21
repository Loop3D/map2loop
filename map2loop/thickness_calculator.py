from abc import ABC, abstractmethod
import beartype
import numpy
from scipy.spatial.distance import euclidean
import pandas
import geopandas
from statistics import mean
from .mapdata import MapData
from scipy.interpolate import Rbf
from .interpolators import DipDipDirectionInterpolator
from .utils import create_points
from .m2l_enums import Datatype
from shapely.geometry import Point, shape
from shapely import dwithin, shortest_line


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
        structure_data: pandas.DataFrame,
        map_data: MapData,
    ) -> pandas.DataFrame:
        """
        Execute thickness calculator method (abstract method)

        Args:
            units (pandas.DataFrame): the data frame of units to add thicknesses to
            stratigraphic_order (list): a list of unit names sorted from youngest to oldest
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])
            structure_data (pandas.DataFrame): sampled structural data
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
        structure_data: pandas.DataFrame,
        map_data: MapData,
    ) -> pandas.DataFrame:
        """
        Execute thickness calculator method takes unit data, basal_contacts and stratigraphic order and attempts to estimate unit thickness.
        Note: Thicknesses of the top and bottom units are not possible with this data and so are assigned the average of all other calculated unit thicknesses.

        Args:
            units (pandas.DataFrame): the data frame of units to add thicknesses to
            stratigraphic_order (list): a list of unit names sorted from youngest to oldest
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])
            structure_data (pandas.DataFrame): sampled structural data
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
    method for a given set of interpolated data points.

    Attributes:
        thickness_calculator_label (str): A string that stores the label of the thickness calculator.
        For this class, it is "ThicknessCalculatorBeta".

    Methods:
        compute(units: pandas.DataFrame, stratigraphic_order: list, basal_contacts: pandas.DataFrame, map_data: MapData)
        -> pandas.DataFrame: Calculates a thickness map for the overall map area.
    """

    def __init__(self):
        """
        Initialiser for beta version of the thickness calculator
        """
        self.thickness_calculator_label = "ThicknessCalculatorBeta"
        self.lines = []


    @beartype.beartype
    def compute(
        self,
        units: pandas.DataFrame,
        stratigraphic_order: list,
        basal_contacts: pandas.DataFrame,
        structure_data: pandas.DataFrame,
        map_data: MapData,
    ) -> pandas.DataFrame:
        """
        Execute thickness calculator method takes unit data, basal_contacts, stratigraphic order, orientation data and
        DTM data to estimate unit thickness.

        The method works by iterating over the stratigraphic order of units. For each unit, it finds the basal contact
        points and the top contact line. It then calculates the shortest line between these points. For each basal
        contact point, it finds the interpolated points that are within 10% of the length of the shortest line. It then
        calculates the true thickness of the unit at these points using the formula t = L . sin dip, where L is the
        length of the line orthogonal to both contacts and dip is the dip of the interpolated points.
        The method then calculates the median thickness and standard deviation for the unit.

        Args:
            units (pandas.DataFrame): the data frame of units to add thicknesses to
            stratigraphic_order (list): a list of unit names sorted from youngest to oldest
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])
            structure_data (pandas.DataFrame): sampled structural data
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            pandas.DataFrame: units dataframe with added thickness column
        """
        basal_contacts = basal_contacts[basal_contacts["type"] == "BASAL"].copy()
        thicknesses = units.copy()
        # Set default value
        thicknesses["betaThickness"] = -1.0
        thicknesses["betaStdDev"] = 0
        basal_unit_list = basal_contacts["basal_unit"].to_list()
        # increase buffer around basal contacts to ensure that the points are included as intersections
        basal_contacts["geometry"] = basal_contacts["geometry"].buffer(0.01)
        # get the sampled contacts
        contacts = geopandas.GeoDataFrame(map_data.sampled_contacts)
        # build points from x and y coordinates
        contacts["geometry"] = contacts.apply(lambda row: Point(row.X, row.Y), axis=1)
        # set the crs of the contacts to the crs of the units
        contacts = contacts.set_crs(crs=basal_contacts.crs)
        # get the elevation Z of the contacts
        contacts = map_data.get_value_from_raster_df(Datatype.DTM, contacts)
        # update the geometry of the contact points to include the Z value
        contacts["geometry"] = contacts.apply(
            lambda row: Point(row.geometry.x, row.geometry.y, row["Z"]), axis=1
        )
        # spatial join the contact points with the basal contacts to get the unit for each contact point
        contacts = contacts.sjoin(basal_contacts, how="inner", predicate="intersects")
        contacts = contacts[["X", "Y", "Z", "geometry", "basal_unit"]].copy()
        bounding_box = map_data.get_bounding_box()
        # Interpolate the dip of the contacts
        interpolator = DipDipDirectionInterpolator(data_type="dip")
        dip = interpolator.interpolate(bounding_box, structure_data, interpolator=Rbf)
        # create a GeoDataFrame of the interpolated orientations
        interpolated_orientations = geopandas.GeoDataFrame()
        # add the dip and dip direction to the GeoDataFrame
        interpolated_orientations["dip"] = dip
        # interpolated_orientations["dip_direction"] = dip_direction
        # get the x and y coordinates of the interpolated points
        interpolated_orientations["X"] = interpolator.xi
        interpolated_orientations["Y"] = interpolator.yi
        xy = numpy.array([interpolator.xi, interpolator.yi]).T
        # create Point objects from the x and y coordinates
        interpolated_orientations["geometry"] = create_points(xy)
        # set the crs of the interpolated orientations to the crs of the units
        interpolated_orientations = interpolated_orientations.set_crs(
            crs=basal_contacts.crs
        )
        # get the elevation Z of the interpolated points
        interpolated = map_data.get_value_from_raster_df(
            Datatype.DTM, interpolated_orientations
        )
        # update the geometry of the interpolated points to include the Z value
        interpolated["geometry"] = interpolated.apply(
            lambda row: Point(row.geometry.x, row.geometry.y, row["Z"]), axis=1
        )
        # for each interpolated point, assign name of unit using spatial join
        units = map_data.get_map_data(Datatype.GEOLOGY)
        interpolated_orientations = interpolated_orientations.sjoin(
            units, how="inner", predicate="within"
        )
        interpolated_orientations = interpolated_orientations[
            ["geometry", "dip", "UNITNAME"]
        ].copy()

        if len(stratigraphic_order) < 3:
            print(
                f"Cannot make any thickness calculations with only {len(stratigraphic_order)} units"
            )
            return thicknesses

        for i in range(0, len(stratigraphic_order) - 1):
            if (
                stratigraphic_order[i] in basal_unit_list
                and stratigraphic_order[i + 1] in basal_unit_list
            ):
                basal_contact = contacts.loc[
                    contacts["basal_unit"] == stratigraphic_order[i]
                ].copy()
                top_contact = basal_contacts.loc[
                    basal_contacts["basal_unit"] == stratigraphic_order[i + 1]
                ].copy()
                top_contact_geometry = [
                    shape(geom.__geo_interface__) for geom in top_contact.geometry
                ]
                if basal_contact is not None and top_contact is not None:
                    interp_points = interpolated_orientations.loc[
                        interpolated_orientations["UNITNAME"] == stratigraphic_order[i],
                        "geometry",
                    ].copy()
                    dip = interpolated_orientations.loc[
                        interpolated_orientations["UNITNAME"] == stratigraphic_order[i],
                        "dip",
                    ].to_numpy()
                    _thickness = []
                    for j, row in basal_contact.iterrows():
                        # find the shortest line between the basal contact points and top contact points
                        short_line = shortest_line(row.geometry, top_contact_geometry)
                        self.lines.append(short_line)
                        # extract the end points of the shortest line
                        p1 = numpy.asarray(short_line[0].coords[0])
                        p2 = numpy.asarray(short_line[0].coords[-1])
                        # get the elevation Z of the end point p2
                        p2[2] = map_data.get_value_from_raster(
                            Datatype.DTM, p2[0], p2[1]
                        )
                        # calculate the length of the shortest line
                        line_length = euclidean(p1, p2)
                        # find the indices of the points that are within 5% of the length of the shortest line
                        indices = dwithin(short_line, interp_points, line_length * 0.1)
                        # get the dip of the points that are within
                        # 10% of the length of the shortest line
                        _dip = numpy.deg2rad(dip[indices])
                        # get the end points of the shortest line
                        # calculate the true thickness t = L . sin dip
                        thickness = line_length * numpy.sin(_dip)
                        # Average thickness along the shortest line
                        _thickness.append(numpy.nanmean(thickness))

                    # calculate the median thickness and standard deviation for the unit
                    _thickness = numpy.asarray(_thickness, dtype=numpy.float64)
                    median = numpy.nanmedian(_thickness)
                    std_dev = numpy.nanstd(_thickness)

                    idx = thicknesses.index[
                        thicknesses["name"] == stratigraphic_order[i + 1]
                    ].tolist()[0]
                    thicknesses.loc[idx, "betaThickness"] = median
                    thicknesses.loc[idx, "betaStdDev"] = std_dev
            else:
                print(
                    f"Cannot calculate thickness between {stratigraphic_order[i]} and {stratigraphic_order[i + 1]}"
                )

        return thicknesses
