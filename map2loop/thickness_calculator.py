import os
from abc import ABC, abstractmethod
import beartype
import numpy
import pandas
import geopandas
from statistics import mean
from .mapdata import MapData
from map2loop.sampler import SamplerSpacing


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
        Initialiser for beta version of the thickness calculator
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

        # def calc_thickness(temporary_path, output_path, buffer, max_thickness_allowed, c_l):
        """
        This function calculates the thickness of geological units based on various data inputs.

        Parameters:
        temporary_path (str): The temporary path where the data files are located.
        output_path (str): The path where the output file will be saved.
        buffer (float): The buffer distance for identifying close points.
        max_thickness_allowed (float): The maximum allowed thickness for a geological unit.
        c_l (dict): A dictionary containing configuration parameters.

        Returns:
        None: The function writes the results to an output file and does not return anything.
        """
        # TODO: find a way to use sampled contacts - stratigraphyLocations?
        # Load the contact points and interpolated data from the temporary path
        # contact_points_file = os.path.join(temporary_path, "raw_contacts.csv")
        contact_points_file = map_data.contacts
        # TODO: implement interpolation code
        # interpolated_combo_file = os.path.join(temporary_path, "combo_full.csv")

        # Load the basal contacts as a geopandas dataframe
        # basal_contacts = geopandas.read_file(os.path.join(temporary_path, "/basal_contacts.shp.zip"))

        # Load the sorted data
        all_sorts = pandas.read_csv(os.path.join(temporary_path, "all_sorts.csv"))

        # Load the contacts and orientations data
        contacts = pandas.read_csv(contact_points_file)
        orientations = pandas.read_csv(interpolated_combo_file)

        # Get the length of the orientations and contacts data
        olength = len(orientations)
        clength = len(contacts)

        # Convert the X and Y coordinates, the slope of the line segment, and the formation name to numpy arrays
        cx = contacts["X"].to_numpy()
        cy = contacts["Y"].to_numpy()
        cl = contacts["lsx"].to_numpy(dtype=float)
        cm = contacts["lsy"].to_numpy(dtype=float)
        ctextcode = contacts["formation"].to_numpy()

        # Convert the X and Y coordinates, the dip and azimuth to numpy arrays
        ox = orientations["X"].to_numpy()
        oy = orientations["Y"].to_numpy()
        dip = orientations["dip"].to_numpy().reshape(olength, 1)
        azimuth = orientations["azimuth"].to_numpy().reshape(olength, 1)

        # Initialize arrays for the direction cosines
        l = numpy.zeros(len(ox))
        m = numpy.zeros(len(ox))
        n = numpy.zeros(len(ox))

        # Open the output file and write the header
        file = open(os.path.join(output_path, "formation_thicknesses.csv"), "w")
        file.write(
            "X,Y,formation,appar_th,thickness,cl,cm,meanl,meanm,meann,p1x,p1y,p2x,p2y,dip\n"
        )

        # Calculate the distance matrix
        dist = m2l_interpolation.distance_matrix(ox, oy, cx, cy)

        # Initialize the counter for the number of thickness estimates
        n_est = 0

        # Loop through all contact segments
        for k in range(0, clength):
            # Calculate the distance to all other points and identify those within the buffer distance
            a_dist = dist[:, k: k + 1]
            is_close = a_dist < buffer
            close_dip = dip[is_close]
            close_azimuth = azimuth[is_close]

            # Initialize the counter for the number of good candidates
            n_good = 0

            # Find the averaged dips within the buffer
            for j in range(0, len(close_dip)):
                l[n_good], m[n_good], n[n_good] = m2l_utils.ddd2dircos(
                    float(close_dip[j]), float(close_azimuth[j]) + 90.0
                )
                n_good = n_good + 1

            # If we found any candidates, calculate the average direction cosine of points within the buffer range
            if n_good > 0:
                lm = numpy.mean(l[:n_good])
                mm = numpy.mean(m[:n_good])
                nm = numpy.mean(n[:n_good])
                dip_mean, dipdirection_mean = m2l_utils.dircos2ddd(lm, mm, nm)

                # Create a line segment perpendicular to the contact point
                dx1 = -cm[k] * buffer
                dy1 = cl[k] * buffer
                dx2 = -dx1
                dy2 = -dy1
                p1 = Point((dx1 + cx[k], dy1 + cy[k]))
                p2 = Point((dx2 + cx[k], dy2 + cy[k]))
                ddline = LineString((p1, p2))
                orig = Point((cx[k], cy[k]))

                # Initialize the crossings array
                crossings = numpy.zeros((1000, 5))

                # Loop through all basal contacts
                g = 0
                for indx, apair in all_sorts.iterrows():
                    if ctextcode[k] == apair["code"]:
                        # Subset contacts to just those with 'a' code
                        is_contacta = (
                                basal_contacts["UNIT_NAME"] == all_sorts.iloc[g - 1]["code"]
                        )
                        acontacts = basal_contacts[is_contacta]
                        i = 0

                        # Loop through distinct linestrings for upper contact
                        for ind, acontact in acontacts.iterrows():
                            if not str(acontact.geometry) == "None":
                                if ddline.intersects(acontact.geometry):
                                    isects = ddline.intersection(acontact.geometry)

                                    # If the intersection is a MultiPoint, loop through all points
                                    if isects.geom_type == "MultiPoint":
                                        for pt in isects:
                                            if pt.distance(orig) < buffer * 2:
                                                crossings[i, 0] = i
                                                crossings[i, 1] = int(apair["index"])
                                                crossings[i, 2] = 0
                                                crossings[i, 3] = pt.x
                                                crossings[i, 4] = pt.y
                                                i = i + 1
                                    else:
                                        if isects.distance(orig) < buffer * 2:
                                            crossings[i, 0] = i
                                            crossings[i, 1] = int(apair["index"])
                                            crossings[i, 2] = 0
                                            crossings[i, 3] = isects.x
                                            crossings[i, 4] = isects.y
                                            i = i + 1

                                    # If we found any intersections with the base of the next higher unit
                                    if i > 0:
                                        min_dist = 1e8
                                        for f in range(0, i):  # find closest hit
                                            this_dist = m2l_utils.ptsdist(
                                                crossings[f, 3],
                                                crossings[f, 4],
                                                cx[k],
                                                cy[k],
                                            )
                                            if this_dist < min_dist:
                                                min_dist = this_dist

                                        # If the minimum distance is not too far, add to output
                                        if min_dist < max_thickness_allowed:
                                            true_thick = sin(radians(dip_mean)) * min_dist
                                            ostr = "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
                                                cx[k],
                                                cy[k],
                                                ctextcode[k],
                                                min_dist,
                                                int(true_thick),
                                                cl[k],
                                                cm[k],
                                                lm,
                                                mm,
                                                nm,
                                                p1.x,
                                                p1.y,
                                                p2.x,
                                                p2.y,
                                                dip_mean,
                                            )
                                            file.write(ostr)
                                            n_est = n_est + 1

                    g = g + 1

        # Print the number of thickness estimates that were saved to the output file
        print(
            n_est,
            "thickness estimates saved as",
            os.path.join(output_path, "formation_thicknesses.csv"),
        )


class ThicknessCalculatorTheta(ThicknessCalculator):

        def __init__(self):
            """
            Initialiser for theta version of the thickness calculator
            """
            self.thickness_calculator_label = "ThicknessCalculatorTheta"

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
            bounding_box = map_data.bounding_box
            side_length = bounding_box['maxx'] - bounding_box['minx']
            # define the spacing of the sampler automatically to 4% of the side length of the bounding box
            spacing = side_length * 0.04
            # sample the contacts
            sampler = SamplerSpacing(spacing)
            sampled_contacts = sampler.sample(basal_contacts)
            
