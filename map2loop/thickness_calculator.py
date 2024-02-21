import os
from abc import ABC, abstractmethod
import beartype
import numpy
import pandas
import geopandas
from statistics import mean
from .mapdata import MapData


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
        temporary_path = map_data.tmp_path
        # Load the contact points and interpolated data from the temporary path
        contact_points_file = os.path.join(temporary_path, "raw_contacts.csv")
        interpolated_combo_file = os.path.join(temporary_path, "combo_full.csv")

        # Load the basal contacts as a geopandas dataframe
        basal_contacts = geopandas.read_file(os.path.join(temporary_path, "/basal_contacts.shp.zip"))

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


@beartype.beartype
def calc_thickness_with_grid(config: Config, map_data: MapData):
    contact_points_file = os.path.join(config.temporary_path, "raw_contacts.csv")
    dtm = map_data.get_map_data(Datatype.DTM).open()
    # load basal contacts as geopandas dataframe
    contact_lines = gpd.read_file(
        os.path.join(config.temporary_path, "basal_contacts.shp.zip")
    )
    all_sorts = pd.read_csv(os.path.join(config.temporary_path, "all_sorts.csv"))
    all_sorts["index2"] = all_sorts.index
    # all_sorts.set_index('code',inplace=True)
    geol = map_data.get_map_data(Datatype.GEOLOGY).copy()
    # geol=gpd.read_file(os.path.join(config.temporary_path, 'geol_clip.shp'))
    geol.drop_duplicates(subset="UNIT_NAME", inplace=True)
    # geol.set_index('UNIT_NAME',inplace=True)
    drops = geol[
        geol["DESCRIPTION"].str.contains(config.c_l["sill"])
        & geol["ROCKTYPE1"].str.contains(config.c_l["intrusive"])
        ]
    for ind, drop in drops.iterrows():
        all_sorts.drop(labels=drop.name, inplace=True, errors="ignore")
    all_sorts["code"] = all_sorts.index
    all_sorts["index"] = all_sorts["index2"]
    # all_sorts.set_index('index2',inplace=True)

    contacts = pd.read_csv(contact_points_file)

    clength = len(contacts)
    cx = contacts["X"].to_numpy()
    cy = contacts["Y"].to_numpy()
    cl = contacts["lsx"].to_numpy(dtype=float)
    cm = contacts["lsy"].to_numpy(dtype=float)
    ctextcode = contacts["formation"].to_numpy()

    fth = open(os.path.join(config.output_path, "formation_thicknesses.csv"), "w")
    fth.write(
        "X,Y,formation,appar_th,thickness,cl,cm,p1x,p1y,p2x,p2y,dip,type,slope_dip,slope_length,delz,zbase,zcross\n"
    )

    # np.savetxt(os.path.join(config.temporary_path,'dist.csv'),dist,delimiter = ',')
    # display("ppp",cx.shape,cy.shape,ox.shape,oy.shape,dip.shape,azimuth.shape,dist.shape)
    n_est = 0
    for k in range(0, clength):  # loop through all contact segments
        r = int((cy[k] - config.bbox[1]) / config.run_flags["interpolation_spacing"])
        c = int((cx[k] - config.bbox[0]) / config.run_flags["interpolation_spacing"])

        dip_mean = map_data.dip_grid[r, c]

        dx1 = -cm[k] * config.run_flags["thickness_buffer"]
        dy1 = cl[k] * config.run_flags["thickness_buffer"]
        dx2 = -dx1
        dy2 = -dy1
        p1 = Point((dx1 + cx[k], dy1 + cy[k]))
        p2 = Point((dx2 + cx[k], dy2 + cy[k]))
        ddline = LineString((p1, p2))
        orig = Point((cx[k], cy[k]))

        crossings = np.zeros((1000, 5))

        g = 0
        for indx, apair in all_sorts.iterrows():  # loop through all basal contacts
            if ctextcode[k] == apair["code"]:
                # subset contacts to just those with 'a' code
                is_contacta = (
                        contact_lines["UNIT_NAME"] == all_sorts.iloc[g - 1]["code"]
                )
                acontacts = contact_lines[is_contacta]
                i = 0
                for (
                        ind,
                        acontact,
                ) in (
                        acontacts.iterrows()
                ):  # loop through distinct linestrings for upper contact
                    # if(bboxes_intersect(ddline.bounds,acontact[1].geometry.bounds)):
                    if not str(acontact.geometry) == "None":
                        if ddline.intersects(acontact.geometry):
                            isects = ddline.intersection(acontact.geometry)
                            if isects.geom_type == "MultiPoint":
                                for pt in isects:
                                    if (
                                            pt.distance(orig)
                                            < config.run_flags["thickness_buffer"] * 2
                                    ):
                                        # print(i,",", pt.x, ",",pt.y,",",apair[1]['code'],",",apair[1]['group'])
                                        crossings[i, 0] = i
                                        crossings[i, 1] = int(apair["index"])
                                        crossings[i, 2] = 0
                                        crossings[i, 3] = pt.x
                                        crossings[i, 4] = pt.y
                                        i = i + 1
                            else:
                                if (
                                        isects.distance(orig)
                                        < config.run_flags["thickness_buffer"] * 2
                                ):
                                    # print(i,",", isects.x,",", isects.y,",",apair[1]['code'],",",apair[1]['group'])
                                    crossings[i, 0] = i
                                    crossings[i, 1] = int(apair["index"])
                                    crossings[i, 2] = 0
                                    crossings[i, 3] = isects.x
                                    crossings[i, 4] = isects.y
                                    i = i + 1

                            if (
                                    i > 0
                            ):  # if we found any intersections with base of next higher unit
                                min_dist = 1e8
                                # min_pt = 0
                                for f in range(0, i):  # find closest hit
                                    this_dist = m2l_utils.ptsdist(
                                        crossings[f, 3], crossings[f, 4], cx[k], cy[k]
                                    )
                                    if this_dist < min_dist:
                                        min_dist = this_dist
                                        # min_pt = f
                                        crossx = crossings[f, 3]
                                        crossy = crossings[f, 4]
                                # if not too far, add to output
                                if (
                                        min_dist < config.run_flags["max_thickness_allowed"]
                                        and min_dist > 0
                                ):
                                    locations = [(cx[k], cy[k])]
                                    zbase = float(
                                        m2l_utils.value_from_dtm_dtb(
                                            dtm, "", "", False, locations
                                        )
                                    )
                                    locations = [(crossx, crossy)]
                                    zcross = float(
                                        m2l_utils.value_from_dtm_dtb(
                                            dtm, "", "", False, locations
                                        )
                                    )
                                    delz = fabs(zcross - zbase)
                                    slope_dip = degrees(atan(delz / min_dist))
                                    slope_length = sqrt(
                                        (min_dist * min_dist) + (delz * delz)
                                    )
                                    if slope_dip < dip_mean and zbase > zcross:
                                        surf_dip = dip_mean - slope_dip
                                    elif slope_dip < dip_mean and zbase < zcross:
                                        surf_dip = dip_mean + slope_dip
                                    elif slope_dip > dip_mean and zbase > zcross:
                                        surf_dip = slope_dip - dip_mean
                                    else:
                                        surf_dip = 180 - (dip_mean + slope_dip)

                                    true_thick = slope_length * sin(radians(surf_dip))
                                    if (
                                            not isnan(true_thick)
                                            and true_thick > 0
                                            and true_thick
                                            < config.run_flags["max_thickness_allowed"]
                                    ):
                                        ostr = "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
                                            cx[k],
                                            cy[k],
                                            ctextcode[k],
                                            min_dist,
                                            int(true_thick),
                                            cl[k],
                                            cm[k],
                                            p1.x,
                                            p1.y,
                                            p2.x,
                                            p2.y,
                                            dip_mean,
                                            "full",
                                            slope_dip,
                                            slope_length,
                                            delz,
                                            zbase,
                                            zcross,
                                        )
                                        # ostr = str(cx[k])+','+str(cy[k])+','+ctextcode[k]+','+str(int(true_thick))+\
                                        #    ','+str(cl[k])+','+str(cm[k])+','+str(lm)+','+str(mm)+','+str(nm)+','+\
                                        #    str(p1.x)+','+str(p1.y)+','+str(p2.x)+','+str(p2.y)+','+str(dip_mean)+'\n'
                                        fth.write(ostr)
                                        n_est = n_est + 1

            g = g + 1
    if config.verbose_level != VerboseLevel.NONE:
        print(
            n_est,
            "thickness estimates saved as",
            os.path.join(config.output_path, "formation_thicknesses.csv"),
        )


@beartype.beartype
def calc_min_thickness_with_grid(config: Config, map_data: MapData):
    dtm = map_data.get_map_data(Datatype.DTM).open()
    contact_points_file = os.path.join(config.temporary_path, "raw_contacts.csv")
    # load basal contacts as geopandas dataframe
    contact_lines = gpd.read_file(
        os.path.join(config.temporary_path, "basal_contacts.shp.zip")
    )
    all_sorts = pd.read_csv(os.path.join(config.temporary_path, "all_sorts.csv"))
    contacts = pd.read_csv(contact_points_file)

    sum_thick = pd.read_csv(
        os.path.join(config.output_path, "formation_thicknesses.csv")
    )
    found_codes = sum_thick["formation"].unique()
    if config.verbose_level != VerboseLevel.NONE:
        print(found_codes, "already processed")
    clength = len(contacts)
    cx = contacts["X"].to_numpy()
    cy = contacts["Y"].to_numpy()
    cl = contacts["lsx"].to_numpy(dtype=float)
    cm = contacts["lsy"].to_numpy(dtype=float)
    ctextcode = contacts["formation"].to_numpy()

    fth = open(os.path.join(config.output_path, "formation_thicknesses.csv"), "a+")
    # fth.write('X,Y,formation,appar_th,thickness,cl,cm,p1x,p1y,p2x,p2y,dip\n')

    # np.savetxt(os.path.join(config.temporary_path,'dist.csv'),dist,delimiter = ',')
    # display("ppp",cx.shape,cy.shape,ox.shape,oy.shape,dip.shape,azimuth.shape,dist.shape)
    n_est = 0
    for k in range(0, clength):  # loop through all contact segments
        if not (ctextcode[k] in found_codes):
            # print(ctextcode[k])
            r = int(
                (cy[k] - config.bbox[1]) / config.run_flags["interpolation_spacing"]
            )
            c = int(
                (cx[k] - config.bbox[0]) / config.run_flags["interpolation_spacing"]
            )

            dip_mean = map_data.dip_grid[r, c]

            dx1 = -cm[k] * config.run_flags["thickness_buffer"]
            dy1 = cl[k] * config.run_flags["thickness_buffer"]
            dx2 = -dx1
            dy2 = -dy1
            p1 = Point((dx1 + cx[k], dy1 + cy[k]))
            p2 = Point((dx2 + cx[k], dy2 + cy[k]))
            ddline = LineString((p1, p2))
            orig = Point((cx[k], cy[k]))

            crossings = np.zeros((1000, 5))

            g = 0
            for indx, apair in all_sorts.iterrows():  # loop through all basal contacts
                if ctextcode[k] == apair["code"]:
                    # subset contacts to just those with 'a' code
                    is_contacta = (
                            contact_lines["UNIT_NAME"] != all_sorts.iloc[g - 1]["code"]
                    )
                    acontacts = contact_lines[is_contacta]
                    i = 0
                    for (
                            ind,
                            acontact,
                    ) in (
                            acontacts.iterrows()
                    ):  # loop through distinct linestrings for upper contact
                        # if(bboxes_intersect(ddline.bounds,acontact[1].geometry.bounds)):

                        if not str(acontact.geometry) == "None":
                            if ddline.intersects(acontact.geometry):
                                isects = ddline.intersection(acontact.geometry)
                                if isects.geom_type == "MultiPoint":
                                    for pt in isects.geoms:
                                        if (
                                                pt.distance(orig)
                                                < config.run_flags["thickness_buffer"] * 2
                                        ):
                                            # print(i,",", pt.x, ",",pt.y,",",apair[1]['code'],",",apair[1]['group'])
                                            crossings[i, 0] = i
                                            crossings[i, 1] = int(apair["index"])
                                            crossings[i, 2] = 0
                                            crossings[i, 3] = pt.x
                                            crossings[i, 4] = pt.y
                                            i = i + 1
                                else:
                                    if not isects.geom_type == "GeometryCollection":
                                        if (
                                                isects.distance(orig)
                                                < config.run_flags["thickness_buffer"] * 2
                                        ):
                                            # print(i,",", isects.x,",", isects.y,",",apair[1]['code'],",",apair[1]['group'])
                                            crossings[i, 0] = i
                                            crossings[i, 1] = int(apair["index"])
                                            crossings[i, 2] = 0
                                            crossings[i, 3] = isects.x
                                            crossings[i, 4] = isects.y
                                            i = i + 1

                                if (
                                        i > 0
                                ):  # if we found any intersections with base of next higher unit
                                    min_dist = 1e8
                                    # min_pt = 0
                                    for f in range(0, i):  # find closest hit
                                        this_dist = m2l_utils.ptsdist(
                                            crossings[f, 3],
                                            crossings[f, 4],
                                            cx[k],
                                            cy[k],
                                        )
                                        if this_dist < min_dist:
                                            min_dist = this_dist
                                            # min_pt = f
                                            crossx = crossings[f, 3]
                                            crossy = crossings[f, 4]
                                    # if not too far, add to output
                                    if (
                                            min_dist
                                            < config.run_flags["max_thickness_allowed"]
                                            and min_dist > 1
                                    ):
                                        locations = [(cx[k], cy[k])]
                                        zbase = float(
                                            m2l_utils.value_from_dtm_dtb(
                                                dtm, "", "", False, locations
                                            )
                                        )
                                        locations = [(crossx, crossy)]
                                        zcross = float(
                                            m2l_utils.value_from_dtm_dtb(
                                                dtm, "", "", False, locations
                                            )
                                        )
                                        delz = fabs(zcross - zbase)
                                        slope_dip = degrees(atan(delz / min_dist))
                                        slope_length = sqrt(
                                            (min_dist * min_dist) + (delz * delz)
                                        )
                                        if slope_dip < dip_mean and zbase > zcross:
                                            surf_dip = dip_mean - slope_dip
                                        elif slope_dip < dip_mean and zbase < zcross:
                                            surf_dip = dip_mean + slope_dip
                                        elif slope_dip > dip_mean and zbase > zcross:
                                            surf_dip = slope_dip - dip_mean
                                        else:
                                            surf_dip = 180 - (dip_mean + slope_dip)

                                        true_thick = slope_length * sin(
                                            radians(surf_dip)
                                        )
                                        if (
                                                not isnan(true_thick)
                                                and true_thick > 0
                                                and true_thick
                                                < config.run_flags["max_thickness_allowed"]
                                        ):
                                            ostr = "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
                                                cx[k],
                                                cy[k],
                                                ctextcode[k],
                                                min_dist,
                                                int(true_thick),
                                                cl[k],
                                                cm[k],
                                                p1.x,
                                                p1.y,
                                                p2.x,
                                                p2.y,
                                                dip_mean,
                                                "min",
                                                slope_dip,
                                                slope_length,
                                                delz,
                                                zbase,
                                                zcross,
                                            )
                                            # ostr = str(cx[k])+','+str(cy[k])+','+ctextcode[k]+','+str(int(true_thick))+\
                                            #    ','+str(cl[k])+','+str(cm[k])+','+str(lm)+','+str(mm)+','+str(nm)+','+\
                                            #    str(p1.x)+','+str(p1.y)+','+str(p2.x)+','+str(p2.y)+','+str(dip_mean)+'\n'
                                            fth.write(ostr)
                                            n_est = n_est + 1

            g = g + 1
    if config.verbose_level != VerboseLevel.NONE:
        print(
            n_est,
            "min thickness estimates appended to",
            os.path.join(config.output_path, "formation_thicknesses.csv"),
        )
    fth.close()


####################################
# Normalise thickness for each estimate to median for that formation
#
# normalise_thickness(output_path)
# Args:
# output_path path to m2l output directory
#
# Normalises previously calculated formation thickness by dviding by median value for that formation
####################################
def normalise_thickness(output_path):
    thickness = pd.read_csv(
        os.path.join(output_path, "formation_thicknesses.csv"), sep=","
    )

    codes = thickness.formation.unique()
    f = open(os.path.join(output_path, "formation_thicknesses_norm.csv"), "w")
    f.write("x,y,formation,app_th,thickness,norm_th\n")
    fs = open(os.path.join(output_path, "formation_summary_thicknesses.csv"), "w")
    fs.write("formation,thickness median,thickness std,method\n")
    for code in codes:
        is_code = thickness.formation.str.contains(code, regex=False)
        all_thick = thickness[is_code]
        all_thick2 = all_thick[all_thick["thickness"] != 0]
        thicknesses = np.asarray(all_thick2.loc[:, "thickness"], dtype=float)

        if len(all_thick2) > 2:
            med = np.median(thicknesses)
            std = np.std(thicknesses)
            # print(code, med, std)
            ostr = "{},{},{},{}\n".format(code, med, std, all_thick2.iloc[0]["type"])
            # ostr = str(code)+","+str(all_thick2.loc[:,"thickness"].median())+","+str(all_thick2.loc[:,"thickness"].std())+"\n"
            fs.write(ostr)

            thick = all_thick2.to_numpy()

            for i in range(len(thick)):
                if med > 0:
                    ostr = "{},{},{},{},{},{}\n".format(
                        thick[i, 0],
                        thick[i, 1],
                        thick[i, 2],
                        thick[i, 3],
                        thick[i, 4],
                        thicknesses[i] / med,
                    )
                    # ostr = str(thick[i,0])+","+str(thick[i,1])+","+str(thick[i,2])+","+str(thick[i,3])+","+str(thick[i,3]/med)+"\n"
                    f.write(ostr)
    f.close()
    fs.close()
