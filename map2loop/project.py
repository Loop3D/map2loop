import beartype
from .m2l_enums import VerboseLevel, ErrorState, Datatype
from .mapdata import MapData
from .sampler import Sampler, SamplerDecimator, SamplerSpacing
from .thickness_calculator import ThicknessCalculator, ThicknessCalculatorAlpha
from .sorter import Sorter, SorterUseHint
from .stratigraphic_column import StratigraphicColumn
from .deformation_history import DeformationHistory
from .map2model_wrapper import Map2ModelWrapper
import LoopProjectFile as LPF

import numpy
import pandas
import geopandas
import os
from matplotlib.colors import to_rgba

# TODO: When geopandas gets updated check that this FutureWarning supression
#       is still needed for GeoDataFrame.clip methods
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)


class Project(object):
    """
    The main entry point into using map2loop

    Attiributes
    -----------
    verbose_level: m2l_enums.VerboseLevel
        A selection that defines how much console logging is output
    samplers: Sampler
        A list of samplers used to extract point samples from polyonal or line segments. Indexed by m2l_enum.Dataype
    sorter: Sorter
        The sorting algorithm to use for calculating the stratigraphic column
    thickness_calculator: ThicknessCalulator
        The algorithm to use for making unit thickness estimations
    loop_filename: str
        The name of the loop project file used in this project
    map_data: MapData
        The structure that holds all map and dtm data
    map2model: Map2ModelWrapper
        A wrapper around the map2model module that extracts unit and fault adjacency
    stratigraphic_column: StratigraphicColumn
        The structure that holds the unit information and ordering
    deformation_history: DeformationHistory
        The structura that holds the fault and fold information and interactions
    """

    @beartype.beartype
    def __init__(
        self,
        verbose_level: VerboseLevel = VerboseLevel.ALL,
        tmp_path: str = "m2l_data_tmp",
        working_projection=None,
        bounding_box=None,
        use_australian_state_data: str = "",
        geology_filename: str = "",
        structure_filename: str = "",
        fault_filename: str = "",
        fold_filename: str = "",
        dtm_filename: str = "",
        config_filename: str = "",
        config_dictionary: dict = {},
        clut_filename: str = "",
        save_pre_checked_map_data: bool = False,
        loop_project_filename: str = "",
        **kwargs
    ):
        """
        The initialiser for the map2loop project

        Args:
            verbose_level (VerboseLevel, optional):
                How much console output is sent. Defaults to VerboseLevel.ALL.
            tmp_path (str, optional):
                The directory for storing temporary files. Defaults to "./m2l_data_tmp".
            working_projection (str or int, optional):
                The EPSG projection to use. Defaults to None.
            bounding_box (list or dict, optional):
                The boundary extents of the project (m). Defaults to None.
            use_australian_state_data (str, optional):
                Whether to use default state data and which state to use. Defaults to "".
            geology_filename (str, optional):
                The filename of the geology shapefile. Defaults to "".
            structure_filename (str, optional):
                The filename of the structure shapefile. Defaults to "".
            fault_filename (str, optional):
                The filename of the fault shapefile. Defaults to "".
            fold_filename (str, optional):
                The filename fo the fold shapefile. Defaults to "".
            dtm_filename (str, optional):
                The filename of the digital terrain map to use. Defaults to "".
            config_filename (str, optional):
                The filename of the configuration json file to use (if not using config_dictionary). Defaults to "".
            config_dictionary (dict, optional):
                A dictionary version of the configuration file. Defaults to {}.
            clut_filename (str, optional):
                The filename of the colour look up table to use. Defaults to "".
            save_pre_checked_map_data (bool, optional):
                A flag to save all map data to file before use. Defaults to False.
            loop_project_filename (str, optional):
                The filename of the loop project file. Defaults to "".

        Raises:
            TypeError: Type of working_projection not a str or int
            ValueError: bounding_box not length 4 or 6
            TypeError: Type of bounding_box not a dict or tuple
            ValueError: use_australian_state_data not in state list ['WA', 'SA', 'QLD', 'NSW', 'TAS', 'VIC', 'ACT', 'NT']
        """
        self._error_state = ErrorState.NONE
        self._error_state_msg = ""
        self.verbose_level = verbose_level
        self.samplers = [SamplerDecimator()] * len(Datatype)
        self.set_default_samplers()
        self.sorter = SorterUseHint()
        self.thickness_calculator = ThicknessCalculatorAlpha()
        self.loop_filename = loop_project_filename

        self.map_data = MapData(tmp_path=tmp_path, verbose_level=verbose_level)
        self.map2model = Map2ModelWrapper(self.map_data)
        self.stratigraphic_column = StratigraphicColumn()
        self.deformation_history = DeformationHistory()

        # Sanity check on working projection parameter
        if type(working_projection) == str or type(working_projection) == int:
            self.map_data.set_working_projection(working_projection)
        elif type(working_projection) is None:
            if verbose_level != VerboseLevel.NONE:
                print("No working projection set, will attempt to use the projection of the geology map")
        else:
            raise TypeError(f"Invalid type for working_projection {type(working_projection)}")

        # Sanity check bounding box
        if type(bounding_box) == dict or type(bounding_box) == tuple:
            if len(bounding_box) == 4 or len(bounding_box) == 6:
                self.map_data.set_bounding_box(bounding_box)
            else:
                raise ValueError(f"Length of bounding_box {len(bounding_box)} is neither 4 (map boundary) nor 6 (volumetric boundary)")
        else:
            raise TypeError(f"Invalid type for bounding_box {type(bounding_box)}")

        if config_filename != "":
            self.map_data.set_config_filename(config_filename)
        if config_dictionary != {}:
            self.map_data.config.update_from_dictionary(config_dictionary)

        # Assign filenames
        if use_australian_state_data != "":
            # Sanity check on state string
            if use_australian_state_data in ['WA', 'SA', 'QLD', 'NSW', 'TAS', 'VIC', 'ACT', 'NT']:
                self.map_data.set_filenames_from_australian_state(use_australian_state_data)
            else:
                raise ValueError(f"Australian state {use_australian_state_data} not in state url database")
        if geology_filename != "":
            self.map_data.set_filename(Datatype.GEOLOGY, geology_filename)
        if structure_filename != "":
            self.map_data.set_filename(Datatype.STRUCTURE, structure_filename)
        if fault_filename != "":
            self.map_data.set_filename(Datatype.FAULT, fault_filename)
        if fold_filename != "":
            self.map_data.set_filename(Datatype.FOLD, fold_filename)
        if dtm_filename != "":
            self.map_data.set_filename(Datatype.DTM, dtm_filename)
        if config_filename != "":
            self.map_data.set_config_filename(config_filename)
        if clut_filename != "":
            self.map_data.set_colour_filename(clut_filename)

        # Load all data (both shape and raster)
        self.map_data.load_all_map_data()

        # If flag to save out data is check do so
        if save_pre_checked_map_data:
            self.map_data.save_all_map_data(tmp_path)

        # Populate the stratigraphic column and deformation history from map data
        self.stratigraphic_column.populate(self.map_data.get_map_data(Datatype.GEOLOGY))
        self.deformation_history.populate(self.map_data.get_map_data(Datatype.FAULT))

        # Set default minimum fault length to 5% of the longest bounding box dimension
        bounding_box = self.map_data.get_bounding_box()
        largest_dimension = max(bounding_box["maxx"] - bounding_box["minx"], bounding_box["maxy"] - bounding_box["miny"])
        self.deformation_history.set_minimum_fault_length(largest_dimension * 0.05)

        if len(kwargs):
            print(f"These keywords were not used in initialising the Loop project ({kwargs})")

    # Getters and Setters
    @beartype.beartype
    def set_ignore_codes(self, codes: list):
        """
        Set the ignore codes (a list of unit names to ignore in the geology shapefile)

        Args:
            codes (list): The list of strings to ignore
        """
        self.map_data.set_ignore_codes(codes)

    @beartype.beartype
    def set_sorter(self, sorter: Sorter):
        """
        Set the sorter for determining stratigraphic order of units

        Args:
            sorter (Sorter):
                The sorter to use.  Must be of base class Sorter
        """
        self.sorter = sorter

    def get_sorter(self):
        """
        Get the name of the sorter being used

        Returns:
            str: The name of the sorter used
        """
        return self.sorter.sorter_label

    @beartype.beartype
    def set_thickness_calculator(self, thickness_calculator: ThicknessCalculator):
        """
        Set the thickness calculator that estimates unit thickness of all units

        Args:
            thickness_calculator (ThicknessCalculator):
                The calculator to use. Must be of base class ThicknessCalculator
        """
        self.thickness_calculator = thickness_calculator

    def get_thickness_calculator(self):
        """
        Get the name of the thickness calculator being used

        Returns:
            str: The name of the thickness calculator used
        """
        return self.thickness_calculator.thickness_calculator_label

    def set_default_samplers(self):
        """
        Initialisation function to set or reset the point samplers
        """
        self.samplers[Datatype.STRUCTURE] = SamplerDecimator(1)
        self.samplers[Datatype.GEOLOGY] = SamplerSpacing(50.0)
        self.samplers[Datatype.FAULT] = SamplerSpacing(50.0)
        self.samplers[Datatype.FOLD] = SamplerSpacing(50.0)

    @beartype.beartype
    def set_sampler(self, datatype: Datatype, sampler: Sampler):
        """
        Set the point sampler for a specific datatype

        Args:
            datatype (Datatype):
                The datatype to use this sampler on
            sampler (Sampler):
                The sampler to use
        """
        self.samplers[datatype] = sampler

    @beartype.beartype
    def get_sampler(self, datatype: Datatype):
        """
        Get the sampler name being used for a datatype

        Args:
            datatype (Datatype): The datatype of the sampler

        Returns:
            str: The name of the sampler being used on the specified datatype
        """
        return self.samplers[datatype].sampler_label

    @beartype.beartype
    def set_minimum_fault_length(self, length: float):
        """
        Set the cutoff length for faults to ignore

        Args:
            length (float):
                The cutoff length
        """
        self.deformation_history.set_minimum_fault_length(length)

    @beartype.beartype
    def get_minimum_fault_length(self) -> float:
        """
        Get the cutoff length for faults

        Returns:
            float: The cutoff length
        """
        return self.deformation_history.get_minimum_fault_length()

    # Processing functions
    def sample_map_data(self):
        """
        Use the samplers to extract points along polylines or unit boundaries
        """
        self.geology_samples = self.samplers[Datatype.GEOLOGY].sample(self.map_data.get_map_data(Datatype.GEOLOGY))
        self.structure_samples = self.samplers[Datatype.STRUCTURE].sample(self.map_data.get_map_data(Datatype.STRUCTURE))
        self.fault_samples = self.samplers[Datatype.FAULT].sample(self.map_data.get_map_data(Datatype.FAULT))
        self.fold_samples = self.samplers[Datatype.FOLD].sample(self.map_data.get_map_data(Datatype.FOLD))

    def extract_geology_contacts(self):
        """
        Use the stratigraphic column, and fault and geology data to extract points along contacts
        """
        # Get all contacts (attribute with which units contact each other)
        self.map_data.extract_all_contacts()
        # Use stratigraphic column to determine basal contacts
        self.map_data.extract_basal_contacts(self.stratigraphic_column.column)
        self.sampled_contacts = SamplerSpacing(500.0).sample(self.map_data.basal_contacts)
        self.map_data.get_value_from_raster_df(Datatype.DTM, self.sampled_contacts)

    def calculate_stratigraphic_order(self):
        """
        Use unit relationships, unit ages and the sorter to create a stratigraphic column
        """
        self.stratigraphic_column.column = \
            self.sorter.sort(self.stratigraphic_column.stratigraphicUnits,
                             self.map2model.get_unit_unit_relationships(),
                             self.map2model.get_sorted_units())

    def calculate_unit_thicknesses(self):
        """
        Use the stratigraphic column, and fault and contact data to estimate unit thicknesses
        """
        self.stratigraphic_column.stratigraphicUnits = \
            self.thickness_calculator.compute(self.stratigraphic_column.stratigraphicUnits,
                                              self.stratigraphic_column.column,
                                              self.map_data.basal_contacts)

    def apply_colour_to_units(self):
        """
        Apply the clut file to the units in the stratigraphic column
        """
        self.stratigraphic_column.stratigraphicUnits = \
            self.map_data.colour_units(self.stratigraphic_column.stratigraphicUnits)

    def sort_stratigraphic_column(self):
        """
        Sort the units in the stratigraphic column data structure to match the column order
        """
        self.stratigraphic_column.sort_from_relationship_list(self.stratigraphic_column.column)

    def summarise_fault_data(self):
        """
        Use the fault shapefile to make a summary of each fault by name
        """
        self.map_data.get_value_from_raster_df(Datatype.DTM, self.fault_samples)
        self.fault_samples = self.fault_samples.merge(self.map_data.get_map_data(Datatype.FAULT)[["ID", "DIPDIR", "DIP"]], on="ID", how="left")
        self.fault_samples["DIPDIR"] = self.fault_samples["DIPDIR"].replace(numpy.nan, 0)
        self.fault_samples["DIP"] = self.fault_samples["DIP"].replace(numpy.nan, 90)
        self.deformation_history.summarise_data(self.fault_samples)

    def run_all(self, user_defined_stratigraphic_column=None):
        """
        Runs the full map2loop process

        Args:
            user_defined_stratigraphic_column (None or list, optional):
                A user fed list that overrides the stratigraphic column sorter. Defaults to None.
        """
        if user_defined_stratigraphic_column is None:
            self.calculate_stratigraphic_order()
        elif type(user_defined_stratigraphic_column) is list:
            self.stratigraphic_column.column = user_defined_stratigraphic_column
        else:
            print("user_defined_stratigraphic_column is not of type list. Attempting to calculate column")
            self.calculate_stratigraphic_order()
        self.sort_stratigraphic_column()
        self.extract_geology_contacts()
        self.calculate_unit_thicknesses()
        self.sample_map_data()
        self.summarise_fault_data()
        self.apply_colour_to_units()
        self.save_into_projectfile()

    def save_into_projectfile(self):
        """
        Creates or updates a loop project file with all the data extracted from the map2loop process
        """
        # Open project file
        if self.loop_filename is None or self.loop_filename == "":
            self.loop_filename = os.path.join(self.map_data.tmp_path, os.path.basename(self.map_data.tmp_path) + ".loop3d")

        # Check overwrite of mismatch version
        file_exists = os.path.isfile(self.loop_filename)
        version_mismatch = False
        existing_extents = None
        if file_exists:
            file_version = LPF.Get(self.loop_filename, "version", verbose=False)
            if file_version["errorFlag"] is True:
                print(f"Error: {file_version['errorString']}")
                print(f"       Cannot export loop project file as current file of name {self.loop_filename} is not a loop project file")
                return
            else:
                version_mismatch = file_version["value"] != LPF.LoopVersion()
                if version_mismatch:
                    print(f"Mismatched loop project file versions {LPF.LoopVersion()} and {file_version}, old version will be replaced")
            resp = LPF.Get(self.loop_filename, "extents")
            if not resp["errorFlag"]:
                existing_extents = resp["value"]

        if not file_exists or (version_mismatch):
            LPF.CreateBasic(self.loop_filename)

        # Save extents
        if existing_extents is None:
            LPF.Set(self.loop_filename, "extents", geodesic=[-180, -179, 0, 1],
                    utm=[1,
                         1,
                         self.map_data.bounding_box["minx"],
                         self.map_data.bounding_box["maxx"],
                         self.map_data.bounding_box["miny"],
                         self.map_data.bounding_box["maxy"]
                         ],
                    depth=[
                         self.map_data.bounding_box["top"],
                         self.map_data.bounding_box["base"]
                         ],
                    spacing=[1000, 1000, 500],
                    preference="utm"
                    )
        else:
            # TODO: Check loopfile extents match project extents before continuing
            # if mismatch on extents warn the user and create new file
            LPF.Set(self.loop_filename, "extents", **existing_extents)

        # Save unit information
        stratigraphic_data = numpy.zeros(len(self.stratigraphic_column.stratigraphicUnits), LPF.stratigraphicLayerType)
        stratigraphic_data["layerId"] = self.stratigraphic_column.stratigraphicUnits["layerId"]
        stratigraphic_data["minAge"] = self.stratigraphic_column.stratigraphicUnits["minAge"]
        stratigraphic_data["maxAge"] = self.stratigraphic_column.stratigraphicUnits["maxAge"]
        stratigraphic_data["name"] = self.stratigraphic_column.stratigraphicUnits["name"]
        stratigraphic_data["group"] = self.stratigraphic_column.stratigraphicUnits["group"]
        stratigraphic_data["enabled"] = 1
        stratigraphic_data["rank"] = 0
        stratigraphic_data["thickness"] = self.stratigraphic_column.stratigraphicUnits["thickness"]

        stratigraphic_data["colour1Red"] = [int(a[1:3], 16) for a in self.stratigraphic_column.stratigraphicUnits["colour"]]
        stratigraphic_data["colour1Green"] = [int(a[3:5], 16) for a in self.stratigraphic_column.stratigraphicUnits["colour"]]
        stratigraphic_data["colour1Blue"] = [int(a[5:7], 16) for a in self.stratigraphic_column.stratigraphicUnits["colour"]]
        stratigraphic_data["colour2Red"] = [int(a * 0.95) for a in stratigraphic_data["colour1Red"]]
        stratigraphic_data["colour2Green"] = [int(a * 0.95) for a in stratigraphic_data["colour1Green"]]
        stratigraphic_data["colour2Blue"] = [int(a * 0.95) for a in stratigraphic_data["colour1Blue"]]
        LPF.Set(self.loop_filename, "stratigraphicLog", data=stratigraphic_data, verbose=True)

        # Save contacts
        contacts_data = numpy.zeros(len(self.sampled_contacts), LPF.contactObservationType)
        contacts_data["layerId"] = self.sampled_contacts["ID"]
        contacts_data["easting"] = self.sampled_contacts["X"]
        contacts_data["northing"] = self.sampled_contacts["Y"]
        contacts_data["altitude"] = self.sampled_contacts["Z"]
        LPF.Set(self.loop_filename, "contacts", data=contacts_data, verbose=True)

        # Save fault information
        faults_obs_data = numpy.zeros(len(self.fault_samples), LPF.faultObservationType)
        faults_obs_data["eventId"] = self.fault_samples["ID"]
        faults_obs_data["easting"] = self.fault_samples["X"]
        faults_obs_data["northing"] = self.fault_samples["Y"]
        faults_obs_data["altitude"] = self.fault_samples["Z"]
        faults_obs_data["type"] = 0
        faults_obs_data["dipDir"] = self.fault_samples["DIPDIR"]
        faults_obs_data["dip"] = self.fault_samples["DIP"]
        faults_obs_data["dipPolarity"] = 0  # self.fault_samples["DIPPOLARITY"]
        # faults_obs_data["val"] = self.fault_samples["???"]
        faults_obs_data["displacement"] = 100  # self.fault_samples["DISPLACEMENT"]
        from itertools import cycle, islice
        faults_obs_data["posOnly"] = list(islice(cycle([0, 1]), len(faults_obs_data)))
        LPF.Set(self.loop_filename, "faultObservations", data=faults_obs_data, verbose=True)

        faults = self.deformation_history.get_faults_for_export()
        faults_data = numpy.zeros(len(faults), LPF.faultEventType)
        faults_data["eventId"] = faults["eventId"]
        faults_data["name"] = faults["name"]
        faults_data["minAge"] = faults["minAge"]
        faults_data["maxAge"] = faults["maxAge"]
        faults_data["group"] = faults["group"]
        faults_data["supergroup"] = faults["supergroup"]
        faults_data["avgDisplacement"] = faults["avgDisplacement"]
        faults_data["avgDownthrowDir"] = faults["avgDownthrowDir"]
        faults_data["influenceDistance"] = faults["influenceDistance"]
        faults_data["verticalRadius"] = faults["verticalRadius"]
        faults_data["horizontalRadius"] = faults["horizontalRadius"]
        faults_data["colour"] = faults["colour"]
        faults_data["centreEasting"] = faults["centreX"]
        faults_data["centreNorthing"] = faults["centreY"]
        faults_data["centreAltitude"] = faults["centreZ"]
        faults_data["avgSlipDirEasting"] = faults["avgSlipDirX"]
        faults_data["avgSlipDirNorthing"] = faults["avgSlipDirY"]
        faults_data["avgSlipDirAltitude"] = faults["avgSlipDirZ"]
        faults_data["avgNormalEasting"] = faults["avgNormalX"]
        faults_data["avgNormalNorthing"] = faults["avgNormalY"]
        faults_data["avgNormalAltitude"] = faults["avgNormalZ"]
        LPF.Set(self.loop_filename, "faultLog", data=faults_data, verbose=True)

        # Save structural information
        observations = numpy.zeros(len(self.structure_samples), LPF.stratigraphicObservationType)
        observations["layer"] = "s0"
        observations["layerId"] = self.structure_samples["ID"]
        observations["easting"] = self.structure_samples["X"]
        observations["northing"] = self.structure_samples["Y"]
        # observations["altitude"] = self.structure_samples["Z"]
        observations["dipDir"] = self.structure_samples["DIPDIR"]
        observations["dip"] = self.structure_samples["DIP"]
        observations["dipPolarity"] = self.structure_samples["OVERTURNED"]
        LPF.Set(self.loop_filename, "stratigraphicObservations", data=observations, verbose=True)

    @beartype.beartype
    def draw_geology_map(self, points: pandas.DataFrame = None, overlay: str = ""):
        """
        Plots the geology map with optional points or specific data

        Args:
            points (pandas.DataFrame, optional):
                A dataframe to overlay on the geology map (must contains "X" and "Y" columns). Defaults to None.
            overlay (str, optional):
                Layer of points to overlay (options are "contacts", "basal_contacts", "orientations", "faults"). Defaults to "".
        """
        colour_lookup = self.stratigraphic_column.stratigraphicUnits[["name", "colour"]].set_index("name").to_dict()["colour"]
        geol = self.map_data.get_map_data(Datatype.GEOLOGY).copy()
        geol['colour'] = geol.apply(lambda row: colour_lookup[row.UNITNAME], axis=1)
        geol['colour_rgba'] = geol.apply(lambda row: to_rgba(row['colour'], 1.0), axis=1)
        if points is None and overlay == "":
            geol.plot(color=geol['colour_rgba'])
        else:
            base = geol.plot(color=geol['colour_rgba'])
        if overlay != "":
            if overlay == "contacts":
                points = self.sampled_contacts
            elif overlay == "orientations":
                points = self.structure_samples
            elif overlay == "faults":
                points = self.fault_samples
            else:
                print(f"Invalid overlay option {overlay}")
                return
        gdf = geopandas.GeoDataFrame(points, geometry=geopandas.points_from_xy(points["X"], points["Y"], crs=geol.crs))
        gdf.plot(ax=base, marker="o", color="red", markersize=5)

    @beartype.beartype
    def save_mapdata_to_files(self, save_path: str = ".", extension: str = ".shp.zip"):
        """
        Saves the map data frames to csv files

        Args:
            save_path (str, optional):
                The path to save the file to. Defaults to ".".
            extension (str, optional):
                An alternate extension to save the GeoDataFrame in. Defaults to ".csv".
        """
        if not os.path.exists(save_path):
            os.mkdir(save_path)
        self.map_data.save_all_map_data(save_path, extension)
