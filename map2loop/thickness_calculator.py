# internal imports
from .utils import (
    create_points,
    rebuild_sampled_basal_contacts,
    calculate_endpoints,
    multiline_to_line,
    find_segment_strike_from_pt,
)
from .m2l_enums import Datatype
from .interpolators import DipDipDirectionInterpolator
from .mapdata import MapData

from .logging import getLogger
logger = getLogger(__name__)  

# external imports
from abc import ABC, abstractmethod
import scipy.interpolate
import beartype
import numpy
import scipy
import pandas
import geopandas
import shapely
import math


class ThicknessCalculator(ABC):
    """
    Base Class of Thickness Calculator used to force structure of ThicknessCalculator

    Args:
        ABC (ABC): Derived from Abstract Base Class
    """

    def __init__(self, max_line_length: float = None):
        """
        Initialiser of for ThicknessCalculator
        """
        self.thickness_calculator_label = "ThicknessCalculatorBaseClass"
        self.max_line_length = max_line_length

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

        Note:
        -----
        Geological units' thicknesses are returned in meters. The thickness is calculated based on the stratigraphic order of the units.
        If the thickness is not calculated for a given unit, the assigned thickness is -1.
        For the bottom and top units of the stratigraphic sequence, the assigned thickness is -1.
        """

        if len(stratigraphic_order) < 3:
            logger.warning(
                f"Cannot make any thickness calculations with only {len(stratigraphic_order)} units"
            )
            return units

    def _check_thickness_percentage_calculations(self, thicknesses: pandas.DataFrame):
        units_with_no_thickness = len(thicknesses[thicknesses['ThicknessMean'] == -1])
        total_units = len(thicknesses)

        if total_units > 0 and (units_with_no_thickness / total_units) >= 0.75:
            logger.warning(
                f"More than {int(0.75 * 100)}% of units ({units_with_no_thickness}/{total_units}) "
                f"have a calculated thickness of -1. This may indicate that {self.thickness_calculator_label} "
                f"is not suitable for this dataset."
            )
            
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
        basal_contacts: geopandas.GeoDataFrame,
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

        # Set default values
        thicknesses["ThicknessMean"] = no_distance
        thicknesses["ThicknessMedian"] = no_distance
        thicknesses["ThicknessStdDev"] = no_distance

        basal_unit_list = basal_contacts["basal_unit"].to_list()
        sampled_basal_contacts = rebuild_sampled_basal_contacts(
            basal_contacts=basal_contacts, sampled_contacts=map_data.sampled_contacts
        )

        if len(stratigraphic_order) < 3:
            logger.warning(
                f"ThicknessCalculatorAlpha: Cannot make any thickness calculations with only {len(stratigraphic_order)} units"
            )
            return thicknesses

        for i in range(1, len(stratigraphic_order) - 1):
            # Compare basal contacts of adjacent units
            if (
                stratigraphic_order[i] in basal_unit_list
                and stratigraphic_order[i + 1] in basal_unit_list
            ):
                contact1 = sampled_basal_contacts[
                    sampled_basal_contacts["basal_unit"] == stratigraphic_order[i]
                ]["geometry"].to_list()[0]
                contact2 = sampled_basal_contacts[
                    sampled_basal_contacts["basal_unit"] == stratigraphic_order[i + 1]
                ]["geometry"].to_list()[0]
                if contact1 is not None and contact2 is not None:
                    distance = contact1.distance(contact2)
                else:
                    logger.warning(
                        f"ThicknessCalculatorAlpha: Cannot calculate thickness between {stratigraphic_order[i]} and {stratigraphic_order[i + 1]} \n"
                    )
                    distance = no_distance
            else:
                logger.warning(
                    f"ThicknessCalculatorAlpha: Cannot calculate thickness between {stratigraphic_order[i]} and {stratigraphic_order[i + 1]} \n"
                )

                distance = no_distance

            # Maximum thickness is the horizontal distance between the minimum of these distances
            # Find row in unit_dataframe corresponding to unit and replace thickness value if it is -1 or larger than distance
            idx = thicknesses.index[thicknesses["name"] == stratigraphic_order[i]].tolist()[0]
            if thicknesses.loc[idx, "ThicknessMean"] == -1:
                val = distance
            else:
                val = min(distance, thicknesses.at[idx, "ThicknessMean"])
            thicknesses.loc[idx, "ThicknessMean"] = val

        self._check_thickness_percentage_calculations(thicknesses)
        
        return thicknesses


class InterpolatedStructure(ThicknessCalculator):
    """
    This class is a subclass of the ThicknessCalculator abstract base class. It implements the thickness calculation
    method for a given set of interpolated data points.

    Attributes:
        thickness_calculator_label (str): A string that stores the label of the thickness calculator.
        For this class, it is "InterpolatedStructure".

    Methods:
        compute(units: pandas.DataFrame, stratigraphic_order: list, basal_contacts: pandas.DataFrame, map_data: MapData)
        -> pandas.DataFrame: Calculates a thickness map for the overall map area.
    """

    def __init__(self, max_line_length: float = None):
        """
        Initialiser for interpolated structure version of the thickness calculator
        """
        super().__init__(max_line_length)
        self.thickness_calculator_label = "InterpolatedStructure"
        self.lines = None
        

    @beartype.beartype
    def compute(
        self,
        units: pandas.DataFrame,
        stratigraphic_order: list,
        basal_contacts: geopandas.GeoDataFrame,
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
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of
            the contacts (columns must contain ["ID","basal_unit","type","geometry"])
            structure_data (pandas.DataFrame): sampled structural data
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            pandas.DataFrame: units dataframe with added thickness columns:
            "ThicknessMedian" is the median thickness of the unit,
            "ThicknessStdDev" is the standard deviation of the thickness of the unit
        """

        basal_contacts = basal_contacts[basal_contacts["type"] == "BASAL"].copy()

        thicknesses = units.copy()
        # Set default value
        # thicknesses["ThicknessMedian"] is the median thickness of the unit
        thicknesses["ThicknessMedian"] = -1.0
        thicknesses['ThicknessMean'] = -1.0
        # thicknesses["ThicknessStdDev"] is the standard deviation of the thickness of the unit
        thicknesses["ThicknessStdDev"] = -1.0
        thicknesses['ThicknessStdDev'] = thicknesses['ThicknessStdDev'].astype('float64')
        basal_unit_list = basal_contacts["basal_unit"].to_list()
        # increase buffer around basal contacts to ensure that the points are included as intersections
        basal_contacts["geometry"] = basal_contacts["geometry"].buffer(0.01)
        # get the sampled contacts
        contacts = geopandas.GeoDataFrame(map_data.sampled_contacts)
        # build points from x and y coordinates
        geometry2 = geopandas.points_from_xy(contacts['X'], contacts['Y'])
        contacts.set_geometry(geometry2, inplace=True)

        # set the crs of the contacts to the crs of the units
        contacts = contacts.set_crs(crs=basal_contacts.crs)
        # get the elevation Z of the contacts
        contacts = map_data.get_value_from_raster_df(Datatype.DTM, contacts)
        # update the geometry of the contact points to include the Z value
        contacts["geometry"] = contacts.apply(
            lambda row: shapely.Point(row.geometry.x, row.geometry.y, row["Z"]), axis=1
        )
        # spatial join the contact points with the basal contacts to get the unit for each contact point
        contacts = contacts.sjoin(basal_contacts, how="inner", predicate="intersects")
        contacts = contacts[["X", "Y", "Z", "geometry", "basal_unit"]].copy()
        bounding_box = map_data.get_bounding_box()

        # Interpolate the dip of the contacts
        interpolator = DipDipDirectionInterpolator(data_type="dip")
        # Interpolate the dip of the contacts
        dip = interpolator(bounding_box, structure_data, interpolator=scipy.interpolate.Rbf)
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
        interpolated_orientations.set_geometry(create_points(xy), inplace=True)
        # set the crs of the interpolated orientations to the crs of the units
        interpolated_orientations = interpolated_orientations.set_crs(crs=basal_contacts.crs)
        # get the elevation Z of the interpolated points
        interpolated = map_data.get_value_from_raster_df(Datatype.DTM, interpolated_orientations)
        # update the geometry of the interpolated points to include the Z value
        interpolated["geometry"] = interpolated.apply(
            lambda row: shapely.Point(row.geometry.x, row.geometry.y, row["Z"]), axis=1
        )
        # for each interpolated point, assign name of unit using spatial join
        units = map_data.get_map_data(Datatype.GEOLOGY)
        interpolated_orientations = interpolated_orientations.sjoin(
            units, how="inner", predicate="within"
        )
        interpolated_orientations = interpolated_orientations[
            ["geometry", "dip", "UNITNAME"]
        ].copy()
        
        _lines = []
        _dips = []
        _location_tracking = []
        
        for i in reversed(range(1, len(stratigraphic_order) )):
            if (
                stratigraphic_order[i] in basal_unit_list
                and stratigraphic_order[i - 1] in basal_unit_list
            ):
                basal_contact = contacts.loc[
                    contacts["basal_unit"] == stratigraphic_order[i-1]
                ].copy()
                top_contact = basal_contacts.loc[
                    basal_contacts["basal_unit"] == stratigraphic_order[i]
                ].copy()
                top_contact_geometry = [
                    shapely.geometry.shape(geom.__geo_interface__) for geom in top_contact.geometry
                ]
                if basal_contact is not None and top_contact is not None:
                    interp_points = interpolated_orientations.loc[
                        interpolated_orientations["UNITNAME"] == stratigraphic_order[i], "geometry"
                    ].copy()
                    dip = interpolated_orientations.loc[
                        interpolated_orientations["UNITNAME"] == stratigraphic_order[i], "dip"
                    ].to_numpy()
                    
                    _thickness = []
                
                    for _, row in basal_contact.iterrows():
                        # find the shortest line between the basal contact points and top contact points
                        short_line = shapely.shortest_line(row.geometry, top_contact_geometry)
                        _lines.append(short_line[0])
                        
                        # check if the short line is 
                        if self.max_line_length is not None and short_line.length > self.max_line_length:
                            continue
 
                        # extract the end points of the shortest line
                        p1 = numpy.zeros(3)
                        p1[0] = numpy.asarray(short_line[0].coords[0][0])
                        p1[1] = numpy.asarray(short_line[0].coords[0][1])
                        # get the elevation Z of the end point p1
                        p1[2] = map_data.get_value_from_raster(Datatype.DTM, p1[0], p1[1])
                        # create array to store xyz coordinates of the end point p2
                        p2 = numpy.zeros(3)
                        p2[0] = numpy.asarray(short_line[0].coords[-1][0])
                        p2[1] = numpy.asarray(short_line[0].coords[-1][1])
                        # get the elevation Z of the end point p2
                        p2[2] = map_data.get_value_from_raster(Datatype.DTM, p2[0], p2[1])
                        # calculate the length of the shortest line
                        line_length = scipy.spatial.distance.euclidean(p1, p2)
                        # find the indices of the points that are within 5% of the length of the shortest line
                        indices = shapely.dwithin(short_line, interp_points, line_length * 0.25)
                        # get the dip of the points that are within
                        _dip = numpy.deg2rad(dip[indices])
                        _dips.append(_dip)
                        # calculate the true thickness t = L * sin(dip)
                        thickness = line_length * numpy.sin(_dip)
                        
                        # add location tracking
                        location_tracking = pandas.DataFrame(
                            {
                                "p1_x": [p1[0]], "p1_y": [p1[1]], "p1_z": [p1[2]],
                                "p2_x": [p2[0]], "p2_y": [p2[1]], "p2_z": [p2[2]],
                                "thickness": [thickness],
                                "unit": [stratigraphic_order[i]]
                            }
                        )
                        _location_tracking.append(location_tracking)
                        
                        # Average thickness along the shortest line
                        if all(numpy.isnan(thickness)):
                            pass
                        else:
                            _thickness.append(numpy.nanmean(thickness))

                    # calculate the median thickness and standard deviation for the unit
                    _thickness = numpy.asarray(_thickness, dtype=numpy.float64)

                    median = numpy.nanmedian(_thickness)
                    mean = numpy.nanmean(_thickness)
                    std_dev = numpy.nanstd(_thickness, dtype=numpy.float64)

                    idx = thicknesses.index[
                        thicknesses["name"] == stratigraphic_order[i + 1]
                    ].tolist()[0]
                    thicknesses.loc[idx, "ThicknessMean"] = mean
                    thicknesses.loc[idx, "ThicknessMedian"] = median
                    thicknesses.loc[idx, "ThicknessStdDev"] = std_dev

            else:
                logger.warning(
                    f"Thickness Calculator InterpolatedStructure: Cannot calculate thickness between {stratigraphic_order[i]} and {stratigraphic_order[i - 1]}\n"
                )
        
        # Combine all location_tracking DataFrames into a single DataFrame
        combined_location_tracking = pandas.concat(_location_tracking, ignore_index=True)
        
        # Save the combined DataFrame as an attribute of the class
        self.location_tracking = combined_location_tracking
        
        # Create GeoDataFrame for lines
        self.lines = geopandas.GeoDataFrame(geometry=_lines, crs=basal_contacts.crs)
        self.lines['dip'] = _dips
        
        # Check thickness calculation
        self._check_thickness_percentage_calculations(thicknesses)
        
        return thicknesses

class StructuralPoint(ThicknessCalculator):
    '''
    This class is a subclass of the ThicknessCalculator abstract base class. It implements the thickness calculation using a deterministic workflow based on stratigraphic measurements.

    Attributes:
        thickness_calculator_label (str): A string that stores the label of the thickness calculator.
        For this class, it is "StrucuturalPoint".

    Methods:
        compute(units: pandas.DataFrame, stratigraphic_order: list, basal_contacts: pandas.DataFrame, map_data: MapData)
        -> pandas.DataFrame: Calculates the thickness in meters for each unit in the stratigraphic column.

    '''

    def __init__(self, max_line_length: float = None):
        super().__init__(max_line_length)
        self.thickness_calculator_label = "StructuralPoint"
        self.strike_allowance = 30
        self.lines = None
        

    @beartype.beartype
    def compute(
        self,
        units: pandas.DataFrame,
        stratigraphic_order: list,
        basal_contacts: geopandas.GeoDataFrame,
        structure_data: pandas.DataFrame,
        map_data: MapData,
    ) -> pandas.DataFrame:
        """
        Method overview:
        - define perpendicular line, with strike perpendicular to the stratigraphic measurement's strike
        - find intersection points between the perpendicular line and the geological contacts
        - Perform the following checks:
            1) is there more than one intersection?
            2) are the intersections between two different lithologies, and if so, grab the neighboring lithologies only.
            3) is the distance between the two intersections less than half the map dimensions? (avoids incorrect intersections to be picked)
            4) is the stratigraphic measurement strike within 30 degrees of the strike of the geological contacts?

        - once the intersections pass the checks, calculate the thickness of the unit at the intersection points, using the general formula L*sin(dip)

        Attributes:
        -----------
            units (pandas.DataFrame): the data frame of units to add thicknesses to
            stratigraphic_order (list): a list of unit names sorted from youngest to oldest
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of
            the contacts (columns must contain ["ID","basal_unit","type","geometry"])
            structure_data (pandas.DataFrame): sampled structural data
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
        --------
            pandas.DataFrame: units dataframe with added thickness columns:
            "ThicknessMedian" is the median thickness of the unit,
            "ThicknessStdDev" is the standard deviation of the thickness of the unit

        Note:
        -----
            This method is highly dependent on the existence of stratigraphic measurements that follow the strike of the geological contacts.
            If an unit does not contain a stratigraphic measurement, the thickness will not be calculated. Interpolated Structure may be used for such situations and future versions of map2loop will attempt to solve for this.
            If the thickness is not calculated for a given unit, the assigned thickness will be -1.
            For the bottom and top units of the stratigraphic sequence, the assigned thickness will also be -1.
        """
        # input sampled data
        sampled_structures = structure_data
        basal_contacts = basal_contacts.copy()

        # grab geology polygons and calculate bounding boxes for each lithology
        geology = map_data.get_map_data(datatype=Datatype.GEOLOGY)
        geology[['minx', 'miny', 'maxx', 'maxy']] = geology.bounds

        # create a GeoDataFrame of the sampled structures
        sampled_structures = geopandas.GeoDataFrame(
            sampled_structures,
            geometry=geopandas.points_from_xy(sampled_structures.X, sampled_structures.Y),
            crs=basal_contacts.crs,
        )
        # add unitname to the sampled structures
        sampled_structures['unit_name'] = geopandas.sjoin(sampled_structures, geology)['UNITNAME']

        # remove nans from sampled structures
        # this happens when there are strati measurements within intrusions. If intrusions are removed from the geology map, unit_name will then return a nan
        logger.info(
            f"skipping row(s) {sampled_structures[sampled_structures['unit_name'].isnull()].index.to_numpy()} in sampled structures dataset, as they do not spatially coincide with a valid geology polygon \n"
        )
        sampled_structures = sampled_structures.dropna(subset=['unit_name'])

        # rebuild basal contacts lines based on sampled dataset
        sampled_basal_contacts = rebuild_sampled_basal_contacts(
            basal_contacts, map_data.sampled_contacts
        )

        # calculate map dimensions
        map_dx = geology.total_bounds[2] - geology.total_bounds[0]
        map_dy = geology.total_bounds[3] - geology.total_bounds[1]

        # create empty lists to store thicknesses and lithologies
        thicknesses = []
        lis = []
        _lines = []
        _dip = []

        # loop over each sampled structural measurement
        for s in range(0, len(sampled_structures)):

            # make a shapely point from the measurement
            measurement = sampled_structures.iloc[s]
            measurement_pt = shapely.Point(measurement.X, measurement.Y)

            # find unit and strike
            litho_in = measurement['unit_name']
            strike = (measurement['DIPDIR'] - 90) % 360

            # find bounding box of the lithology
            bbox_poly = geology[geology['UNITNAME'] == litho_in][['minx', 'miny', 'maxx', 'maxy']]

            # check if litho_in is in geology
            # for a special case when the litho_in is not in the geology
            if len(geology[geology['UNITNAME'] == litho_in]) == 0:
                logger.info(
                    f"There are structural measurements in unit - {litho_in} - that are not in the geology shapefile. Skipping this structural measurement"
                )
                continue
            else:
                # make a subset of the geology polygon & find neighbour units
                GEO_SUB = geology[geology['UNITNAME'] == litho_in]['geometry'].values[0]

            neighbor_list = list(
                basal_contacts[GEO_SUB.intersects(basal_contacts.geometry)]['basal_unit']
            )

            # draw orthogonal line to the strike (default value 10Km), and clip it by the bounding box of the lithology
            if self.max_line_length is None:
                self.max_line_length = 10000
            B = calculate_endpoints(measurement_pt, strike, self.max_line_length, bbox_poly)
            b = geopandas.GeoDataFrame({'geometry': [B]}).set_crs(basal_contacts.crs)

            # find all intersections
            all_intersections = sampled_basal_contacts.overlay(
                b, how='intersection', keep_geom_type=False
            )
            all_intersections = all_intersections[
                all_intersections['geometry'].geom_type == 'Point'
            ]

            # clip intersections by the neighbouring geology polygons
            final_intersections = all_intersections[
                all_intersections['basal_unit'].isin(neighbor_list)
            ]

            # sometimes the intersections will return as MultiPoint, so we need to convert them to nearest point
            if 'MultiPoint' in final_intersections['geometry'].geom_type.values:
                multi = final_intersections[
                    final_intersections['geometry'].geom_type == 'MultiPoint'
                ].index
                for m in multi:
                    nearest_ = shapely.ops.nearest_points(
                        final_intersections.loc[m, :].geometry, measurement_pt
                    )[0]
                    final_intersections.at[m, 'geometry'] = nearest_
                    final_intersections.at[m, 'geometry'] = nearest_

            # check to see if there's less than 2 intersections
            if len(final_intersections) < 2:
                continue

            # check to see if the intersections cross two lithologies"
            if len(final_intersections['basal_unit'].unique()) == 1:
                continue

            # declare the two intersection points
            int_pt1 = final_intersections.iloc[0].geometry
            int_pt2 = final_intersections.iloc[1].geometry

            # if the intersections are too far apart, skip
            if (
                math.sqrt(((int_pt1.x - int_pt2.x) ** 2) + ((int_pt1.y - int_pt2.y) ** 2))
                > map_dx / 2
                or math.sqrt(((int_pt1.x - int_pt2.x) ** 2) + ((int_pt1.y - int_pt2.y) ** 2))
                > map_dy / 2
            ):
                continue

            # find the segments that the intersections belong to
            seg1 = sampled_basal_contacts[
                sampled_basal_contacts['basal_unit'] == final_intersections.iloc[0]['basal_unit']
            ].geometry.iloc[0]
            seg2 = sampled_basal_contacts[
                sampled_basal_contacts['basal_unit'] == final_intersections.iloc[1]['basal_unit']
            ].geometry.iloc[0]

            # simplify the geometries to LineString
            if seg1.geom_type == 'MultiLineString':
                seg1 = multiline_to_line(seg1)
            if seg2.geom_type == 'MultiLineString':
                seg2 = multiline_to_line(seg2)

            # find the strike of the segments
            strike1 = find_segment_strike_from_pt(seg1, int_pt1, measurement)
            strike2 = find_segment_strike_from_pt(seg2, int_pt2, measurement)

            # check to see if the strike of the stratigraphic measurement is within the strike allowance of the strike of the geological contact
            b_s = strike - self.strike_allowance, strike + self.strike_allowance
            if not (b_s[0] < strike1 < b_s[1] and b_s[0] < strike2 < b_s[1]):
                continue

            #build the debug info
            line = shapely.geometry.LineString([int_pt1, int_pt2])
            _lines.append(line)
            _dip.append(measurement['DIP'])  

            # find the lenght of the segment
            L = math.sqrt(((int_pt1.x - int_pt2.x) ** 2) + ((int_pt1.y - int_pt2.y) ** 2))

            # if length is higher than max_line_length, skip
            if self.max_line_length is not None and L > self.max_line_length:
                continue
            
            # calculate thickness
            thickness = L * math.sin(math.radians(measurement['DIP']))

            thicknesses.append(thickness)
            lis.append(litho_in)
        
        # create the debug gdf
        self.lines = geopandas.GeoDataFrame(geometry=_lines, crs=basal_contacts.crs)
        self.lines["DIP"] = _dip
        
        # create a DataFrame of the thicknesses median and standard deviation by lithology
        result = pandas.DataFrame({'unit': lis, 'thickness': thicknesses})
        result = result.groupby('unit')['thickness'].agg(['median', 'mean', 'std']).reset_index()
        result.rename(columns={'thickness': 'ThicknessMedian'}, inplace=True)

        output_units = units.copy()
        # remove the old thickness column
        output_units['ThicknessMedian'] = numpy.full(len(output_units), numpy.nan)
        output_units['ThicknessMean'] = numpy.full(len(output_units), numpy.nan)
        output_units['ThicknessStdDev'] = numpy.full(len(output_units), numpy.nan)
        
        # find which units have no thickness calculated
        names_not_in_result = units[~units['name'].isin(result['unit'])]['name'].to_list()
        # assign the thicknesses to the each unit
        for _, unit in result.iterrows():
            idx = units.index[units['name'] == unit['unit']].tolist()[0]
            output_units.loc[idx, 'ThicknessMedian'] = unit['median']
            output_units.loc[idx, 'ThicknessMean'] = unit['mean']
            output_units.loc[idx, 'ThicknessStdDev'] = unit['std']
       
        output_units["ThicknessMean"] = output_units["ThicknessMean"].fillna(-1)
        output_units["ThicknessMedian"] = output_units["ThicknessMedian"].fillna(-1)
        output_units["ThicknessStdDev"] = output_units["ThicknessStdDev"].fillna(-1)
        
        
        # handle the units that have no thickness
        for unit in names_not_in_result:
            # if no thickness has been calculated for the unit
            if (
                # not a top//bottom unit
                (output_units[output_units['name'] == unit]['ThicknessMedian'].all() == 0)
                and (unit != stratigraphic_order[-1])
                and (unit != stratigraphic_order[0])
            ):
                idx = stratigraphic_order.index(unit)
                # throw warning to user
                logger.warning(
                    'Thickness Calculator StructuralPoint: Cannot calculate thickness between',
                    unit,
                    "and ",
                    stratigraphic_order[idx + 1],
                    "\n",
                )
                # assign -1 as thickness
                output_units.loc[output_units["name"] == unit, "ThicknessMedian"] = -1
                output_units.loc[output_units["name"] == unit, "ThicknessMean"] = -1
                output_units.loc[output_units["name"] == unit, "ThicknessStdDev"] = -1

            # if top//bottom unit assign -1
            if unit in [stratigraphic_order[-1], stratigraphic_order[0]]:
                output_units.loc[output_units["name"] == unit, "ThicknessMedian"] = -1
                output_units.loc[output_units["name"] == unit, "ThicknessMean"] = -1
                output_units.loc[output_units["name"] == unit, "ThicknessStdDev"] = -1

        self._check_thickness_percentage_calculations(output_units)
        
        return output_units
