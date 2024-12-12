# internal imports
from .m2l_enums import Datatype, Datastate, VerboseLevel
from .config import Config
from .aus_state_urls import AustraliaStateUrls
from .utils import generate_random_hex_colors, calculate_minimum_fault_length

# external imports
import geopandas
import pandas
import numpy
import pathlib
import shapely
from osgeo import gdal, osr
gdal.UseExceptions()
from owslib.wcs import WebCoverageService
import urllib
from gzip import GzipFile
from uuid import uuid4
import beartype
import os
from io import BytesIO
from typing import Union, Tuple
import tempfile


from .logging import getLogger
logger = getLogger(__name__)  



class MapData:
    """
    A data structure containing all the map data loaded from map files

    Attributes
    ----------
    raw_data: list of geopandas.DataFrames
        A list containing the raw geopanda data frames before any modification
    data: list of geopandas.DataFrames
        A list containing the geopanda data frames or raster image of all the different map data
    contacts: geopandas.DataFrame
        A dataframe containing the contacts between units in polylines
    basal_contacts: geopandas.DataFrame
        A dataframe containing the contacts between units labelled with whether it is basal or not
    filenames: list of data source filenames
        A list of the filenames/urls of where to find the data to be loaded
    dirtyflags: list of booleans
        A list of flags indicating whether the data has been loaded or dirtied
    data_states: intEnum
        Enums representing the state of each of the data sets
    working_projection: str
        A string containing the projection e.g. "EPSG:28350"
    bounding_box: dict
        The bounding box in cartesian coordinates with 6 elements
    bounding_box_polygon: shapely.Polygon
        The bounding box in polygonal form
    bounding_box_str: str
        The bounding box in string form (used for url requests)
    config_filename: str
        The filename of the json config file
    colour_filename: str
        The filename of the csv colour table file (columns are unit name and colour in #000000 form)
    verbose_level: m2l_enums.VerboseLevel
        A selection that defines how much console logging is output
    config: Config
        A link to the config structure which is defined in config.py
    """

    def __init__(self, verbose_level: VerboseLevel = VerboseLevel.ALL):
        """
        The initialiser for the map data

        Args:
            verbose_level (VerboseLevel, optional):
                How much console output is sent. Defaults to VerboseLevel.ALL.
        """
        self.raw_data = [None] * len(Datatype)
        self.data = [None] * len(Datatype)
        self.contacts = None
        self.basal_contacts = None
        self.sampled_contacts = None
        self.filenames = [None] * len(Datatype)
        self.dirtyflags = [True] * len(Datatype)
        self.data_states = [Datastate.UNNAMED] * len(Datatype)
        self.working_projection = None
        self.bounding_box = None
        self.bounding_box_polygon = None
        self.bounding_box_str = None
        self.config_filename = None
        self.colour_filename = None
        self.verbose_level = verbose_level
        self.config = Config()

    @property
    @beartype.beartype
    def minimum_fault_length(self) -> Union[int,float]:
        return self.config.fault_config["minimum_fault_length"]

    @minimum_fault_length.setter
    @beartype.beartype
    def minimum_fault_length(self, length: float):
        self.config.fault_config["minimum_fault_length"] = length

    def set_working_projection(self, projection):
        """
        Set the working projection for the map data

        Args:
            projection (int or str):
                The projection to use for map reprojection
        """

        if issubclass(type(projection), int):
            projection = f"EPSG:{str(projection)}"
            self.working_projection = projection
        elif issubclass(type(projection), str):
            self.working_projection = projection
        else:
            logger.warning(
                f"Warning: Unknown projection set {projection}. Leaving all map data in original projection\n"
            )
        if self.bounding_box is not None:
            self.recreate_bounding_box_str()
        logger.info(f"Setting working projection to {self.working_projection}")
        
    def get_working_projection(self):
        """
        Get the working projection

        Returns:
            str: The working projection in "EPSG:<int>" form
        """
        return self.working_projection

    def set_bounding_box(self, bounding_box):
        """
        Set the bounding box of the map data

        Args:
            bounding_box (tuple or dict):
                The bounding box to use for maps
        """
        # Convert tuple bounding_box to dict else assign directly
        if issubclass(type(bounding_box), tuple):
            self.bounding_box = {
                "minx": bounding_box[0],
                "maxx": bounding_box[1],
                "miny": bounding_box[2],
                "maxy": bounding_box[3],
            }
            if len(bounding_box) == 6:
                self.bounding_box["top"] = bounding_box[4]
                self.bounding_box["base"] = bounding_box[5]
        elif issubclass(type(bounding_box), dict):
            self.bounding_box = bounding_box
        else:
            raise TypeError(f"Invalid type for bounding_box {type(bounding_box)}")

        # Check for map based bounding_box and add depth boundaries
        if len(self.bounding_box) == 4:
            logger.warning(
                "Bounding box does not contain top and base values, setting to 0 and 2000"
            )
            self.bounding_box["top"] = 0
            self.bounding_box["base"] = 2000

        # Check that bounding_box has all the right keys
        for i in ["minx", "maxx", "miny", "maxy", "top", "base"]:
            if i not in self.bounding_box:
                raise KeyError(f"bounding_box dictionary does not contain {i} key")
        # Create geodataframe boundary for clipping
        minx = self.bounding_box["minx"]
        miny = self.bounding_box["miny"]
        maxx = self.bounding_box["maxx"]
        maxy = self.bounding_box["maxy"]
        top = self.bounding_box["top"]
        base = self.bounding_box["base"]
        logger.info(f'Setting bounding box to {minx}, {miny}, {maxx}, {maxy},{base},{top}')

        lat_point_list = [miny, miny, maxy, maxy, miny]
        lon_point_list = [minx, maxx, maxx, minx, minx]
        self.bounding_box_polygon = geopandas.GeoDataFrame(
            index=[0],
            crs=self.working_projection,
            geometry=[shapely.Polygon(zip(lon_point_list, lat_point_list))],
        )
        self.recreate_bounding_box_str()

    def recreate_bounding_box_str(self):
        """
        Creates the bounding box string from the bounding box dict
        """
        minx = self.bounding_box["minx"]
        miny = self.bounding_box["miny"]
        maxx = self.bounding_box["maxx"]
        maxy = self.bounding_box["maxy"]
        logger.info(
            'Creating bounding box string from: {minx}, {miny}, {maxx}, {maxy}, {self.working_projection}'
        )
        self.bounding_box_str = f"{minx},{miny},{maxx},{maxy},{self.working_projection}"
        logger.info(f'Bounding box string is {self.bounding_box_str}')

    @beartype.beartype
    def get_bounding_box(self, polygon: bool = False):
        """
        Get the bounding box in dict or polygon form

        Args:
            polygon (bool, optional): Flag to get the bounding box in polygon form. Defaults to False.

        Returns:
            dict or shapely.Polygon: The bounding box in the requested form
        """
        if polygon:
            return self.bounding_box_polygon
        else:
            return self.bounding_box

    @beartype.beartype
    def set_filename(self, datatype: Datatype, filename: str):
        """
        Set the filename for a specific datatype

        Args:
            datatype (Datatype):
                The datatype for the filename specified
            filename (str):
                The filename to store
        """
        logger.info(f"Setting filename for {datatype} to {filename}")
        if self.filenames[datatype] != filename:
            self.filenames[datatype] = filename
            self.data_states[datatype] = Datastate.UNLOADED
            if filename == "":
                self.dirtyflags[datatype] = False
            else:
                self.dirtyflags[datatype] = True

    @beartype.beartype
    def get_filename(self, datatype: Datatype):
        """
        Get a filename of a specified datatype

        Args:
            datatype (Datatype):
                The datatype of the filename wanted

        Returns:
            string: The filename of the datatype specified
        """
        if self.data_states != Datastate.UNNAMED:
            return self.filenames[datatype]
        else:
            logger.warning(f"Requested filename for {str(type(datatype))} is not set\n")
            return None

    @beartype.beartype
    def set_config_filename(
        self, filename: Union[pathlib.Path, str], legacy_format: bool = False, lower: bool = False
    ):
        """
        Set the config filename and update the config structure

        Args:
            filename (str):
                The filename of the config file
            legacy_format (bool, optional):
                Whether the file is in m2lv2 form. Defaults to False.
        """
        logger.info('Setting config filename to {filename}')
        self.config_filename = filename
        self.config.update_from_file(filename, legacy_format=legacy_format, lower=lower)
        logger.info(f"Config is: {self.config.to_dict()}")

    def get_config_filename(self):
        """
        Get the config filename

        Returns:
            str: The config filename
        """
        return self.config_filename

    @beartype.beartype
    def set_colour_filename(self, filename: Union[pathlib.Path, str]):
        """
        Set the filename of the colour csv file

        Args:
            filename (str):
                The csv colour look up table filename
        """
        logger.info(f'Colour filename is: {filename}')
        self.colour_filename = filename

    def get_colour_filename(self):
        """
        Get the colour lookup table filename

        Returns:
            str: The colour lookup table filename
        """
        return self.colour_filename

    @beartype.beartype
    def set_ignore_lithology_codes(self, codes: list):
        """
        Set the lithology codes (names) to be ignored in the geology shapefile.

        This method updates the `ignore_lithology_codes` entry in the geology configuration
        and marks the geology data as "clipped" to indicate that certain lithologies have been
        excluded. Additionally, it sets a dirty flag for the geology data to signal that it
        requires reprocessing.

        Args:
            codes (list):
                A list of lithology names to ignore in the geology shapefile. These
                entries will be excluded from further processing.
        """
        self.config.geology_config["ignore_lithology_codes"] = codes
        self.data_states[Datatype.GEOLOGY] = Datastate.CLIPPED
        self.dirtyflags[Datatype.GEOLOGY] = True

    @beartype.beartype
    def get_ignore_lithology_codes(self) -> list:
        """
        Retrieve the list of lithology names to be ignored in the geology shapefile.

        This method fetches the current list of lithology names or codes from the geology
        configuration that have been marked for exclusion during processing.

        Returns:
            list: A list of lithology names currently set to be ignored in the
            geology shapefile.
        """
        return self.config.geology_config["ignore_lithology_codes"]

    @beartype.beartype
    def set_ignore_fault_codes(self, codes: list):
        """
        Set the list of fault codes to be ignored during processing.

        This method updates the `ignore_fault_codes` entry in the fault configuration and
        marks the fault data as "clipped" to indicate that it has been filtered. Additionally,
        it sets a dirty flag for the fault data to signal that it requires reprocessing.

        Args:
            codes (list): A list of fault codes to ignore during further processing.
        """
        self.config.fault_config["ignore_fault_codes"] = codes
        self.data_states[Datatype.FAULT] = Datastate.CLIPPED
        self.dirtyflags[Datatype.FAULT] = True

    @beartype.beartype
    def get_ignore_fault_codes(self) -> list:
        """
        Retrieve the list of fault codes that are set to be ignored.

        This method fetches the current list of fault codes from the fault configuration
        that have been marked for exclusion during processing.

        Returns:
            list: A list of fault codes that are currently marked for exclusion.
        """
        return self.config.fault_config["ignore_fault_codes"]
    
    @beartype.beartype
    def get_minimum_fault_length(self) -> Union[float, int, None]:
        """
        Get the minimum fault length
        """

        return self.minimum_fault_length
    
    @beartype.beartype
    def set_filenames_from_australian_state(self, state: str):
        """
        Set the shape/dtm filenames appropriate to the Australian state

        Args:
            state (str):
                The abbreviated Australian state name

        Raises:
            ValueError: state string not in state list ['WA', 'SA', 'QLD', 'NSW', 'TAS', 'VIC', 'ACT', 'NT']
        """
        logger.info(f"Setting filenames for Australian state {state}")
        if state in ["WA", "SA", "QLD", "NSW", "TAS", "VIC", "ACT", "NT"]:
            self.set_filename(Datatype.GEOLOGY, AustraliaStateUrls.aus_geology_urls[state])
            self.set_filename(Datatype.STRUCTURE, AustraliaStateUrls.aus_structure_urls[state])
            self.set_filename(Datatype.FAULT, AustraliaStateUrls.aus_fault_urls[state])
            self.set_filename(Datatype.FOLD, AustraliaStateUrls.aus_fold_urls[state])
            self.set_filename(Datatype.DTM, "hawaii")
            lower = state == "SA"

            # Check if this is running a documentation test and use local datasets if so
            if os.environ.get("DOCUMENTATION_TEST", False):
                import map2loop

                # because doc tests runs on docker from within the m2l folder
                module_path = map2loop.__file__.replace("__init__.py", "")

                config_path_str = '_datasets/config_files/{}.json'.format(state)
                self.set_config_filename(pathlib.Path(module_path) / pathlib.Path(config_path_str))

                colour_file_str = '_datasets/clut_files/{}_clut.csv'.format(state)
                self.set_colour_filename(pathlib.Path(module_path) / pathlib.Path(colour_file_str))

            else:
                self.set_config_filename(
                    AustraliaStateUrls.aus_config_urls[state], legacy_format=False, lower=lower
                )
                self.set_colour_filename(AustraliaStateUrls.aus_clut_urls[state])
        else:
            raise ValueError(f"Australian state {state} not in state url database")

    @beartype.beartype
    def check_filename(self, datatype: Datatype) -> bool:
        """
        Check the filename for datatype is set

        Args:
            datatype (Datatype):
                The datatype of the filename to check

        Returns:
            bool: true if the filename is set, false otherwise
        """
        if self.filenames[datatype] is None or self.filenames[datatype] == "":
            logger.warning(f"Warning: Filename for {str(datatype)} is not set")
            return False
        return True

    def check_filenames(self) -> bool:
        """
        Check all filenames to see if they are valid

        Returns:
            bool: true if the filenames are set, false otherwise
        """
        ret: bool = True
        for datatype in Datatype:
            ret = ret and self.check_filename(datatype)
        return ret

    @beartype.beartype
    def load_all_map_data(self):
        """
        Load all the map data for each datatype.  Cycles through each type and loads it
        """
        logger.info('Loading all map data')
        for i in [
            Datatype.GEOLOGY,
            Datatype.STRUCTURE,
            Datatype.FAULT,
            Datatype.FOLD,
            Datatype.FAULT_ORIENTATION,
        ]:
            logger.info(f'Loading map data for {i}')
            self.load_map_data(i)
        self.load_raster_map_data(Datatype.DTM)

    @beartype.beartype
    def load_map_data(self, datatype: Datatype):
        """
        Load map data from file, reproject and clip it and then check data is valid

        Args:
            datatype (Datatype):
                The datatype to load
        """
        if self.filenames[datatype] is None or self.data_states[datatype] == Datastate.UNNAMED:
            logger.warning(f"Datatype {datatype.name} is not set and so cannot be loaded\n")
            self.data[datatype] = self.get_empty_dataframe(datatype)
            self.dirtyflags[datatype] = False
            self.data_states[datatype] = Datastate.COMPLETE
        elif self.dirtyflags[datatype] is True:
            if self.data_states[datatype] == Datastate.UNLOADED:
                # Load data from file
                try:
                    map_filename = self.filenames[datatype]
                    map_filename = self.update_filename_with_bounding_box(map_filename)
                    map_filename = self.update_filename_with_projection(map_filename)
                    self.raw_data[datatype] = geopandas.read_file(map_filename)
                    self.data_states[datatype] = Datastate.LOADED
                except Exception:
                    logger.error(
                        f"Failed to open {datatype.name} file called '{self.filenames[datatype]}'\n"
                    )
                    logger.error(f"Cannot continue as {datatype.name} was not loaded\n")
                    return
            if self.data_states[datatype] == Datastate.LOADED:
                # Reproject geopanda to required CRS
                self.set_working_projection_on_map_data(datatype)
                self.data_states[datatype] = Datastate.REPROJECTED
            if self.data_states[datatype] == Datastate.REPROJECTED:
                # Clip geopanda to bounding polygon
                self.raw_data[datatype] = geopandas.clip(
                    self.raw_data[datatype], self.bounding_box_polygon
                )
                self.data_states[datatype] = Datastate.CLIPPED
            if self.data_states[datatype] == Datastate.CLIPPED:
                # Convert column names using codes_and_labels dictionary
                self.check_map(datatype)
                self.data_states[datatype] = Datastate.COMPLETE
            self.dirtyflags[datatype] = False

    @beartype.beartype
    def get_empty_dataframe(self, datatype: Datatype):
        """
        Create a basic empty geodataframe for a specified datatype

        Args:
            datatype (Datatype):
                The datatype of the empty dataset

        Returns:
            geopandas.GeoDataFrame or None: The created geodataframe
        """
        data = None
        if datatype == Datatype.FAULT:
            data = geopandas.GeoDataFrame(
                columns=["geometry", "ID", "NAME", "DIPDIR", "DIP"], crs=self.working_projection
            )
        elif datatype == Datatype.FOLD:
            data = geopandas.GeoDataFrame(
                columns=["geometry", "ID", "NAME", "SYNCLINE"], crs=self.working_projection
            )
        return data

    @beartype.beartype
    def open_http_query(url: str):
        """
        Attempt to open the http url and unzip the file if required
        Note: This is specific to opening remotely hosted dtm data in geotiff format

        Args:
            url (str):
                The url to open

        Returns:
            _type_: The geotiff file
        """
        logger.info(f"Opening http query to {url}")
        try:
            request = urllib.Request(url, headers={"Accept-Encoding": "gzip"})
            response = urllib.request.urlopen(request, timeout=30)
            if response.info().get("Content-Encoding") == "gzip":
                return GzipFile(fileobj=BytesIO(response.read()))
            else:
                return response
        except urllib.URLError:
            return None

    @beartype.beartype
    def __retrieve_tif(self, filename: str):
        """
        Load geoTIFF files from Geoscience Australia or NOAA hawaii or https sources

        Args:
            filename (str):
                The filename or url or "au"/"hawaii" source to load from

        Returns:
            _type_: The open geotiff in a gdal handler
        """

        # For gdal debugging use exceptions
        gdal.UseExceptions()
        bb_ll = tuple(
            float(coord)
            for coord in self.bounding_box_polygon.to_crs("EPSG:4326").geometry.total_bounds
        )

        if filename.lower() == "aus" or filename.lower() == "au":
            logger.info('Using Geoscience Australia DEM')
            url = "http://services.ga.gov.au/gis/services/DEM_SRTM_1Second_over_Bathymetry_Topography/MapServer/WCSServer?"
            wcs = WebCoverageService(url, version="1.0.0")

            coverage = wcs.getCoverage(
                identifier="1", bbox=bb_ll, format="GeoTIFF", crs=4326, width=2048, height=2048
            )

            # This is stupid that gdal cannot read a byte stream and has to have a
            # file on the local system to open or otherwise create a gdal file
            # from scratch with Create
            import pathlib

            tmp_file = pathlib.Path(tempfile.mkdtemp()) / pathlib.Path("temp.tif")

            with open(tmp_file, "wb") as fh:
                fh.write(coverage.read())

            tif = gdal.Open(str(tmp_file))

        elif filename == "hawaii":
            logger.info('Using Hawaii DEM')
            import netCDF4

            bbox_str = (
                f"[({str(bb_ll[1])}):1:({str(bb_ll[3])})][({str(bb_ll[0])}):1:({str(bb_ll[2])})]"
            )

            filename = f"https://pae-paha.pacioos.hawaii.edu/erddap/griddap/srtm30plus_v11_land.nc?elev{bbox_str}"
            f = urllib.request.urlopen(filename)
            ds = netCDF4.Dataset("in-mem-file", mode="r", memory=f.read())
            spatial = [
                ds.geospatial_lon_min,
                ds.geospatial_lon_resolution,
                0,
                ds.geospatial_lat_min,
                0,
                ds.geospatial_lat_resolution,
            ]
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)
            driver = gdal.GetDriverByName("GTiff")
            tif = driver.Create(
                f"/vsimem/{str(uuid4())}",
                xsize=ds.dimensions["longitude"].size,
                ysize=ds.dimensions["latitude"].size,
                bands=1,
                eType=gdal.GDT_Float32,
            )
            tif.SetGeoTransform(spatial)
            tif.SetProjection(srs.ExportToWkt())
            tif.GetRasterBand(1).WriteArray(numpy.flipud(ds.variables["elev"][:][:]))
        elif filename.startswith("http"):
            logger.info(f'Opening remote file {filename}')
            image_data = self.open_http_query(filename)
            mmap_name = f"/vsimem/{str(uuid4())}"
            gdal.FileFromMemBuffer(mmap_name, image_data.read())
            tif = gdal.Open(mmap_name)
        else:
            logger.info(f'Opening local file {filename}')
            tif = gdal.Open(str(filename), gdal.GA_ReadOnly)
        return tif

    @beartype.beartype
    def load_raster_map_data(self, datatype: Datatype):
        """
        Load raster map data from file, reproject and clip it and then check data is valid

        Args:
            datatype (Datatype):
                The raster datatype to load
        """
        if self.filenames[datatype] is None or self.data_states[datatype] == Datastate.UNNAMED:
            logger.warning(f"Datatype {datatype.name} is not set and so cannot be loaded\n")
        elif self.dirtyflags[datatype] is True:
            if self.data_states[datatype] == Datastate.UNLOADED:
                # Load data from file
                self.data[datatype] = self.__retrieve_tif(self.filenames[datatype])
                self.data_states[datatype] = Datastate.LOADED
            if self.data_states[datatype] == Datastate.LOADED:
                # Reproject raster to required CRS
                try:
                    self.data[datatype] = gdal.Warp(
                        "",
                        self.data[datatype],
                        srcSRS=self.data[datatype].GetProjection(),
                        dstSRS=self.working_projection,
                        format="VRT",
                        outputType=gdal.GDT_Float32,
                    )
                except Exception:
                    logger.error(f"Warp failed for {datatype.name}\n")
                self.data_states[datatype] = Datastate.REPROJECTED
            if self.data_states[datatype] == Datastate.REPROJECTED:
                # Clip raster image to bounding polygon
                bounds = [
                    self.bounding_box["minx"],
                    self.bounding_box["maxy"],
                    self.bounding_box["maxx"],
                    self.bounding_box["miny"],
                ]
                self.data[datatype] = gdal.Translate(
                    "",
                    self.data[datatype],
                    format="VRT",
                    outputType=gdal.GDT_Float32,
                    outputSRS=self.working_projection,
                    projWin=bounds,
                    projWinSRS=self.working_projection,
                )
                self.data_states[datatype] = Datastate.COMPLETE
            self.dirtyflags[datatype] = False

    @beartype.beartype
    def check_map(self, datatype: Datatype):
        """
        Check the validity of a map data from file

        Args:
            datatype (Datatype):
                The datatype to check
        """
        func = None
        #check and parse geology data
        if datatype == Datatype.GEOLOGY:
            validity_check, message = self.check_geology_fields_validity()
            if validity_check:
                logger.error(f"Datatype GEOLOGY data validation failed: {message}")
                return
            func = self.parse_geology_map
            
        #check and parse structure data
        elif datatype == Datatype.STRUCTURE:
            validity_check, message = self.check_structure_fields_validity()
            if validity_check:
                logger.error(f"Datatype STRUCTURE data validation failed: {message}")
                return
            func = self.parse_structure_map
        
        #check and parse fault data
        elif datatype == Datatype.FAULT:
            validity_check, message = self.check_fault_fields_validity()
            if validity_check:
                logger.error(f"Datatype FAULT data validation failed: {message}")
                return
            func = self.parse_fault_map
        
        elif datatype == Datatype.FAULT_ORIENTATION:
            func = self.parse_fault_orientations
            
        #check and parse fold data
        elif datatype == Datatype.FOLD:
            func = self.parse_fold_map

        if func:
            error, message = func()
            if error:
                logger.error(message)

    @beartype.beartype
    def check_geology_fields_validity(self) -> tuple[bool, str]:
        #TODO (AR) - add check for gaps in geology data
        """
        Validate the columns in GEOLOGY geodataframe

        Several checks to ensure that the geology data:
        - Is loaded and valid.
        - Contains required columns with appropriate types and no missing or blank values.
        - Has optional columns with valid types, if present.
        - Does not contain duplicate in IDs.
        - Ensures the geometry column has valid geometries.

        Returns:
            Tuple[bool, str]: A tuple indicating success (False) or failure (True)
        """
        # Check if geology data is loaded and valid
        if (
            self.raw_data[Datatype.GEOLOGY] is None
            or type(self.raw_data[Datatype.GEOLOGY]) is not geopandas.GeoDataFrame
        ):
            logger.error("GEOLOGY data is not loaded or is not a valid GeoDataFrame")
            return (True, "GEOLOGY data is not loaded or is not a valid GeoDataFrame")
        
        geology_data = self.raw_data[Datatype.GEOLOGY]
        config = self.config.geology_config
        
        # 1. Check geometry validity - tested & working
        if not geology_data.geometry.is_valid.all():
            logger.error("Invalid geometries found. Please fix those before proceeding with map2loop processing")
            return (True, "Invalid geometries found in datatype GEOLOGY")
    
        # # 2. Required Columns & are they str, and then empty or null? 
        required_columns = [config["unitname_column"], config["alt_unitname_column"]]
        for col in required_columns:
            if col not in geology_data.columns:
                logger.error(f"Datatype GEOLOGY: Required column with config key: '{[k for k, v in config.items() if v == col][0]}' is missing from geology data.")
                return (True, f"Datatype GEOLOGY: Required column with config key: '{[k for k, v in config.items() if v == col][0]}' is missing from geology data.")
            if not geology_data[col].apply(lambda x: isinstance(x, str)).all():
                config_key = [k for k, v in config.items() if v == col][0]
                logger.error(f"Datatype GEOLOGY: Column '{config_key}' must contain only string values. Please check that the column contains only string values.")
                return (True, f"Datatype GEOLOGY: Column '{config_key}' must contain only string values. Please check that the column contains only string values.")
            if geology_data[col].isnull().any() or geology_data[col].str.strip().eq("").any():
                config_key = [k for k, v in config.items() if v == col][0]
                logger.error(f"Datatype GEOLOGY: NaN or blank values found in required column '{config_key}'. Please double check the column for blank values.")
                return (True, f"Datatype GEOLOGY: NaN or blank values found in required column '{config_key}'. Please double check the column for blank values.")

        # # 3. Optional Columns
        optional_string_columns = [
            "group_column", "supergroup_column", "description_column",
            "rocktype_column", "alt_rocktype_column",
        ]
        
        for key in optional_string_columns:
            if key in config and config[key] in geology_data.columns:
                if not geology_data[config[key]].apply(lambda x: isinstance(x, str)).all():
                    logger.warning(
                        f"Datatype GEOLOGY: Optional column '{config[key]}' (config key: '{key}') contains non-string values. "
                        "Map2loop processing might not work as expected."
                    )

        optional_numeric_columns = ["minage_column", "maxage_column", "objectid_column"]
        for key in optional_numeric_columns:
            if key in config and config[key] in geology_data.columns:
                if not geology_data[config[key]].apply(lambda x: isinstance(x, (int, float))).all():
                    logger.warning(
                        f"Datatype GEOLOGY: Optional column '{config[key]}' (config key: '{key}') contains non-numeric values. "
                        "Map2loop processing might not work as expected."
            )
        
        # # 4. Check for duplicates in ID
        if "objectid_column" in config and config["objectid_column"] in geology_data.columns:
            objectid_values = geology_data[config["objectid_column"]]
            
            # Check for None, NaN, or other null-like values
            if objectid_values.isnull().any():
                logger.error(
                    f"Datatype GEOLOGY: Column '{config['objectid_column']}' (config key: 'objectid_column') contains NaN or null values. Ensure all values are valid and non-null."
                )
                return (True, f"Datatype GEOLOGY: Column '{config['objectid_column']}' (config key: 'objectid_column') contains NaN or null values.")
            
            # Check for duplicate values
            if objectid_values.duplicated().any():
                logger.error(
                    f"Datatype GEOLOGY: Duplicate values found in column '{config['objectid_column']}' (config key: 'objectid_column'). Please make sure that the column contains unique values."
                )
                return (True, f"Datatype GEOLOGY: Duplicate values found in column '{config['objectid_column']}' (config key: 'objectid_column').")
            
            # Check for uniqueness
            if not objectid_values.is_unique:
                logger.error(
                    f"Datatype GEOLOGY: Column '{config['objectid_column']}' (config key: 'objectid_column') contains non-unique values. Ensure all values are unique."
                )
                return (True, f"Datatype GEOLOGY: Column '{config['objectid_column']}' (config key: 'objectid_column') contains non-unique values.")

    
        # 5. Check for NaNs/blanks in optional fields with warnings
        warning_fields = [
            "group_column", "supergroup_column", "description_column",
            "rocktype_column", "minage_column", "maxage_column",
        ]
        for key in warning_fields:
            col = config.get(key)
            if col and col in geology_data.columns:
                # Check if column contains string values before applying `.str`
                if pandas.api.types.is_string_dtype(geology_data[col]):
                    if geology_data[col].isnull().any() or geology_data[col].str.strip().eq("").any():
                        logger.warning(
                            f"Datatype GEOLOGY: NaN or blank values found in optional column '{col}' (config key: '{key}')."
                        )
                else:
                    # Non-string columns, check only for NaN values
                    if geology_data[col].isnull().any():
                        logger.warning(
                            f"Datatype GEOLOGY: NaN values found in optional column '{col}' (config key: '{key}')."
                        )


        logger.info("Geology fields validation passed.")
        return (False, "")

    @beartype.beartype
    def parse_geology_map(self) -> tuple:
        """
        Parse the geology shapefile data into a consistent format

        Returns:
            tuple: A tuple of (bool: success/fail, str: failure message)
        """

        # Create new geodataframe
        geology = geopandas.GeoDataFrame(self.raw_data[Datatype.GEOLOGY]["geometry"])
        config = self.config.geology_config

        # Parse unit names and codes
        if config["unitname_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["UNITNAME"] = self.raw_data[Datatype.GEOLOGY][config["unitname_column"]].astype(
                str
            )

        if config["alt_unitname_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["CODE"] = self.raw_data[Datatype.GEOLOGY][config["alt_unitname_column"]].astype(
                str
            )

        # Parse group and supergroup columns
        if config["group_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["GROUP"] = self.raw_data[Datatype.GEOLOGY][config["group_column"]].astype(str)
        else:
            geology["GROUP"] = ""
        if config["supergroup_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["SUPERGROUP"] = self.raw_data[Datatype.GEOLOGY][
                config["supergroup_column"]
            ].astype(str)
        else:
            geology["SUPERGROUP"] = ""

        # Parse description and rocktype columns for sill and intrusive flags
        if config["description_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["SILL"] = (
                self.raw_data[Datatype.GEOLOGY][config["description_column"]]
                .astype(str)
                .str.contains(config["sill_text"])
            )
            geology["DESCRIPTION"] = self.raw_data[Datatype.GEOLOGY][
                config["description_column"]
            ].astype(str)
        else:
            geology["SILL"] = False
            geology["DESCRIPTION"] = ""

        if config["rocktype_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["INTRUSIVE"] = (
                self.raw_data[Datatype.GEOLOGY][config["rocktype_column"]]
                .astype(str)
                .str.contains(config["intrusive_text"])
            )
            geology["ROCKTYPE1"] = self.raw_data[Datatype.GEOLOGY][
                config["rocktype_column"]
            ].astype(str)
        else:
            geology["INTRUSIVE"] = False
            geology["ROCKTYPE1"] = ""

        if config["alt_rocktype_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["ROCKTYPE2"] = self.raw_data[Datatype.GEOLOGY][
                config["alt_rocktype_column"]
            ].astype(str)
        else:
            geology["ROCKTYPE2"] = ""

        # TODO: Explode intrusion multipart geology

        # Parse age columns
        if config["minage_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["MIN_AGE"] = self.raw_data[Datatype.GEOLOGY][config["minage_column"]].astype(
                numpy.float64
            )
        else:
            geology["MIN_AGE"] = 0.0
        if config["maxage_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["MAX_AGE"] = self.raw_data[Datatype.GEOLOGY][config["maxage_column"]].astype(
                numpy.float64
            )
        else:
            geology["MAX_AGE"] = 100000.0

        # Add object id
        if config["objectid_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["ID"] = self.raw_data[Datatype.GEOLOGY][config["objectid_column"]]
        else:
            geology["ID"] = numpy.arange(len(geology))

        # TODO: Check that the exploded geology has more than 1 unit
        #       Do we need to explode the geometry at this stage for geology/faults/folds???
        #       If not subsequent classes will need to be able to deal with them
        # Strip out whitespace (/n <space> /t) and '-', ',', '?' from "UNITNAME", "CODE" "GROUP" "SUPERGROUP"
        geology["UNITNAME"] = geology["UNITNAME"].str.replace("[ -/?]", "_", regex=True)
        geology["CODE"] = geology["CODE"].str.replace("[ -/?]", "_", regex=True)
        geology["GROUP"] = geology["GROUP"].str.replace("[ -/?]", "_", regex=True)
        geology["SUPERGROUP"] = geology["SUPERGROUP"].str.replace("[ -/?]", "_", regex=True)

        # Mask out ignored unit_names/codes (ie. for cover)
        for code in self.config.geology_config["ignore_lithology_codes"]:
            geology = geology[~geology["CODE"].astype(str).str.contains(code)]
            geology = geology[~geology["UNITNAME"].astype(str).str.contains(code)]

        geology = geology.dissolve(by="UNITNAME", as_index=False)

        # Note: alt_rocktype_column and volcanic_text columns not used
        self.data[Datatype.GEOLOGY] = geology
        return (False, "")

    @beartype.beartype
    def check_structure_fields_validity(self) -> Tuple[bool, str]:
        """
        Validate the structure data for required and optional fields.

        Performs the following checks:
        - Ensures the structure map is loaded, valid, and contains at least two structures.
        - Validates the geometry column
        - Checks required numeric columns (`dip_column`, `dipdir_column`) for existence, dtype, range, and null values.
        - Checks optional string columns (`description_column`, `overturned_column`) for type and null/empty values.
        - Validates the optional numeric `objectid_column` for type, null values, and duplicates.

        Returns:
            Tuple[bool, str]: A tuple where the first value indicates if validation failed (True = failed),
                            and the second value provides a message describing the issue.
        """
        
        # Check type and size of loaded structure map
        if (
            self.raw_data[Datatype.STRUCTURE] is None
            or type(self.raw_data[Datatype.STRUCTURE]) is not geopandas.GeoDataFrame
        ):
            logger.warning("Structure map is not loaded or valid")
            return (True, "Structure map is not loaded or valid")

        if len(self.raw_data[Datatype.STRUCTURE]) < 2:
            logger.warning(
                "Datatype STRUCTURE: map does with not enough orientations to complete calculations (need at least 2), projection may be inconsistent"
            )
        
        structure_data = self.raw_data[Datatype.STRUCTURE]
        config = self.config.structure_config

        # 1. Check geometry validity
        if not structure_data.geometry.is_valid.all():
            logger.error("datatype STRUCTURE: Invalid geometries found. Please fix those before proceeding with map2loop processing")
            return (True, "Invalid geometries found in datatype STRUCTURE")

        # 2. Check mandatory numeric columns
        required_columns = [config["dipdir_column"], config["dip_column"]]
        for col in required_columns:
            if col not in structure_data.columns:
                logger.error(f"DDatatype STRUCTURE: Required column with config key: '{[k for k, v in config.items() if v == col][0]}' is missing from structure data.")
                return (True, f"Datatype STRUCTURE: Required column with config key: '{[k for k, v in config.items() if v == col][0]}' is missing from structure data.")
            if not structure_data[col].apply(lambda x: isinstance(x, (int, float))).all():
                config_key = [k for k, v in config.items() if v == col][0]
                logger.error(f"Datatype STRUCTURE: Column '{config_key}' must contain only numeric values. Please check that the column contains only numeric values.")
                return (True, f"Datatype STRUCTURE: Column '{config_key}' must contain only numeric values. Please check that the column contains only numeric values.")
            if structure_data[col].isnull().any():
                config_key = [k for k, v in config.items() if v == col][0]
                logger.error(f"Datatype STRUCTURE: NaN or blank values found in required column '{config_key}'. Please double check the column for blank values.")
                return (True, f"Datatype STRUCTURE: NaN or blank values found in required column '{config_key}'. Please double check the column for blank values.")

        if config["dip_column"] in structure_data.columns:
            invalid_dip = ~((structure_data[config["dip_column"]] >= 0) & (structure_data[config["dip_column"]] <= 90))
            if invalid_dip.any():
                logger.warning(
                    f"Datatype STRUCTURE: Column '{config['dip_column']}' has values that are not between 0 and 90 degrees. Is this intentional?"
                )

        if config["dipdir_column"] in structure_data.columns:
            invalid_dipdir = ~((structure_data[config["dipdir_column"]] >= 0) & (structure_data[config["dipdir_column"]] <= 360))
            if invalid_dipdir.any():
                logger.warning(
                    f"Datatype STRUCTURE: Column '{config['dipdir_column']}' has values that are not between 0 and 360 degrees. Is this intentional?"
                )
        
        # check validity of optional string columns
        optional_string_columns = ["description_column", "overturned_column"]
        for key in optional_string_columns:
            if key in config and config[key] in structure_data.columns:
                column_name = config[key]
                if not structure_data[column_name].apply(lambda x: isinstance(x, str) or pandas.isnull(x)).all():
                    logger.warning(
                        f"Datatype STRUCTURE: Optional column with config key: '{key}' contains non-string values. "
                        "Map2loop processing might not work as expected."
                    )
                if structure_data[column_name].isnull().any() or structure_data[column_name].str.strip().eq("").any():
                    logger.warning(
                        f"Datatype STRUCTURE: Optional column config key: '{key}' contains NaN, empty, or null values. "
                        "Map2loop processing might not work as expected."
            )

        # check ID column for type, null values, and duplicates
        optional_numeric_column_key = "objectid_column"
        optional_numeric_column = config.get(optional_numeric_column_key)

        if optional_numeric_column:
            if optional_numeric_column in structure_data.columns:
                # Check for non-integer values
                if not structure_data[optional_numeric_column].apply(lambda x: isinstance(x, int) or pandas.isnull(x)).all():
                    logger.error(
                        f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains non-integer values. Rectify this, or remove this column from the config - map2loop will generate a new ID."
                    )
                    return (True, f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains non-integer values.")
                # Check for NaN
                if structure_data[optional_numeric_column].isnull().any():
                    logger.error(
                        f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains NaN values. Rectify this, or remove this column from the config - map2loop will generate a new ID."
                    )
                    return (True, f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains NaN values.")
                # Check for duplicates
                if structure_data[optional_numeric_column].duplicated().any():
                    logger.error(
                        f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains duplicate values. Rectify this, or remove this column from the config - map2loop will generate a new ID."
                    )
                    return (True, f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains duplicate values.")

        return (False, "")


    @beartype.beartype
    def parse_structure_map(self) -> tuple:
        """
        Parse the structure shapefile data into a consistent format

        Returns:
            tuple: A tuple of (bool: success/fail, str: failure message)
        """

        # Create new geodataframe
        structure = geopandas.GeoDataFrame(self.raw_data[Datatype.STRUCTURE]["geometry"])
        config = self.config.structure_config

        # Parse dip direction and dip columns
        if config["dipdir_column"] in self.raw_data[Datatype.STRUCTURE]:
            if config["orientation_type"] == "strike":
                structure["DIPDIR"] = self.raw_data[Datatype.STRUCTURE].apply(
                    lambda row: (row[config["dipdir_column"]] + 90.0) % 360.0, axis=1
                )
            else:
                structure["DIPDIR"] = self.raw_data[Datatype.STRUCTURE][config["dipdir_column"]]


        # Ensure all DIPDIR values are within [0, 360]
        structure["DIPDIR"] = structure["DIPDIR"] % 360.0

        if config["dip_column"] in self.raw_data[Datatype.STRUCTURE]:
            structure["DIP"] = self.raw_data[Datatype.STRUCTURE][config["dip_column"]]


        # Add bedding and overturned booleans
        if config["overturned_column"] in self.raw_data[Datatype.STRUCTURE]:
            structure["OVERTURNED"] = (
                self.raw_data[Datatype.STRUCTURE][config["overturned_column"]]
                .astype(str)
                .str.contains(config["overturned_text"])
            )
        else:
            structure["OVERTURNED"] = False

        if config["description_column"] in self.raw_data[Datatype.STRUCTURE]:
            structure["BEDDING"] = (
                self.raw_data[Datatype.STRUCTURE][config["description_column"]]
                .astype(str)
                .str.contains(config["bedding_text"])
            )
        else:
            structure["BEDDING"] = False

        # Add object id
        if config["objectid_column"] in self.raw_data[Datatype.STRUCTURE]:
            structure["ID"] = self.raw_data[Datatype.STRUCTURE][config["objectid_column"]]
        else:
            structure["ID"] = numpy.arange(len(structure))

        self.data[Datatype.STRUCTURE] = structure
        return (False, "")

    def check_fault_fields_validity(self) -> Tuple[bool, str]:
        
        # Check type of loaded fault map
        if (
            self.raw_data[Datatype.FAULT] is None
            or type(self.raw_data[Datatype.FAULT]) is not geopandas.GeoDataFrame
        ):
            logger.warning("Fault map is not loaded or valid")
            return (True, "Fault map is not loaded or valid")
        
        fault_data = self.raw_data[Datatype.FAULT]
        config = self.config.fault_config
        
        # Check geometry
        if not fault_data.geometry.is_valid.all():
            logger.error("datatype FAULT: Invalid geometries found. Please fix those before proceeding with map2loop processing")
            return (True, "Invalid geometries found in FAULT data.")

        # Check for LineString or MultiLineString geometries
        if not fault_data.geometry.apply(lambda geom: isinstance(geom, (shapely.LineString, shapely.MultiLineString))).all():
            invalid_types = fault_data[~fault_data.geometry.apply(lambda geom: isinstance(geom, (shapely.LineString, shapely.MultiLineString)))]
            logger.error(
                f"FAULT data contains invalid geometry types. Rows with invalid geometry types: {invalid_types.index.tolist()}"
            )
            return (True, "FAULT data contains geometries that are not LineString or MultiLineString.")
        
        # Check "structtype_column" if it exists
        # if "structtype_column" in config:
        #     structtype_column = config["structtype_column"]

        #     # Ensure the column exists in the data
        #     if structtype_column not in fault_data.columns:
        #         logger.warning(
        #             f"Datatype FAULT: '{structtype_column}' (config key: 'structtype_column') is missing from the fault data. Consider removing that key from the config"
        #         )
        #     else:
        #     # Check if all entries in the column are strings
        #         if not fault_data[structtype_column].apply(lambda x: isinstance(x, str) or pandas.isnull(x)).all():
        #             logger.error(
        #                 f"Datatype FAULT: Column '{structtype_column}' (config key: 'structtype_column') contains non-string values. Please ensure all values in this column are strings."
        #             )
        #             return (True, f"Datatype FAULT: Column '{structtype_column}' (config key: 'structtype_column') contains non-string values.")

        #         # Warn about empty or null cells
        #         if fault_data[structtype_column].isnull().any() or fault_data[structtype_column].str.strip().eq("").any():
        #             logger.warning(
        #                 f"Datatype FAULT: Column '{structtype_column}' contains NaN, empty, or blank values. Processing might not work as expected."
        #             )

            # Check if "fault_text" is defined and contained in the column
            # fault_text = config.get("fault_text", None)
            # if not fault_text:
            #     logger.error(
            #         "Datatype FAULT: 'fault_text' is not defined in the configuration, but it is required to filter faults."
            #     )
            #     return (True, "Datatype FAULT: 'fault_text' is not defined in the configuration.")

            # if not fault_data[structtype_column].str.contains(fault_text).any():
            #     logger.error(
            #         f"Datatype FAULT: The 'fault_text' value '{fault_text}' is not found in column '{structtype_column}'. Ensure it is correctly defined at least for one row"
            #     )
            #     return (True, f"Datatype FAULT: The 'fault_text' value '{fault_text}' is not found in column '{structtype_column}'.")
        
        #checks on name column
        name_column = config.get("name_column")
        if name_column not in fault_data.columns:
            logger.warning(
                f"Datatype FAULT: Column '{name_column}' (config key 'name_column') is missing from the fault data."
                "Please ensure it is present, or remove that key from the config."
            )
        
        if name_column and name_column in fault_data.columns:
            # Check if the column contains non-string values
            if not fault_data[name_column].apply(lambda x: isinstance(x, str) or pandas.isnull(x)).all():
                logger.error(
                    f"Datatype FAULT: Column '{name_column}' (config key 'name_column') contains non-string values. Ensure all values are valid strings."
                )
                return (True, f"Datatype FAULT: Column '{name_column}' (config key 'name_column') contains non-string values.")
            
            # Check for NaN values
            if fault_data[name_column].isnull().any():
                logger.warning(
                    f"Datatype FAULT: Column '{name_column}' (config key 'name_column') contains NaN or empty values. This may affect processing."
                )
            
            # Check for duplicate values
            if fault_data[name_column].duplicated().any():
                logger.warning(
                    f"Datatype FAULT: Column '{name_column}' contains duplicate values. This may affect processing."
                )

        # dips & strikes
        # Check for dips and dip directions
        strike_dips_columns = ["dip_column", "dipdir_column"]

        for key in strike_dips_columns:
            column_name = config.get(key)
            if column_name:  # Only proceed if the config has this key
                if column_name in fault_data.columns:
                    
                    #coerce to numeric
                    fault_data[column_name] = pandas.to_numeric(fault_data[column_name], errors='coerce')
                    
                    # Check if the column contains only numeric values                    
                    if not fault_data[column_name].apply(lambda x: isinstance(x, (int, float)) or pandas.isnull(x)).all():
                        logger.warning(
                            f"Datatype FAULT: Column '{column_name}' (config key {key}) must contain only numeric values. Please ensure the column is numeric."
                        )

                    # Check for NaN or empty values
                    if fault_data[column_name].isnull().any():
                        logger.warning(
                            f"Datatype FAULT: Column '{column_name}' (config key {key}) contains NaN or empty values. This may affect processing."
                        )

                    # Check range constraints
                    if key == "dip_column":
                        # Dips must be between 0 and 90
                        invalid_values = ~((fault_data[column_name] >= 0) & (fault_data[column_name] <= 90))
                        if invalid_values.any():
                            logger.warning(
                                f"Datatype FAULT: Column '{column_name}' (config key {key}) contains values outside the range [0, 90]. Was this intentional?"
                            )
                    elif key == "dipdir_column":
                        # Dip directions must be between 0 and 360
                        invalid_values = ~((fault_data[column_name] >= 0) & (fault_data[column_name] <= 360))
                        if invalid_values.any():
                            logger.warning(
                                f"Datatype FAULT: Column '{column_name}' (config key {key}) contains values outside the range [0, 360]. Was this intentional?"
                            )
                else:
                    logger.warning(
                        f"Datatype FAULT: Column '{column_name}' (config key {key}) is missing from the fault data. Please ensure the column name is correct, or otherwise remove that key from the config."
                    )
                    
        
        # dip estimates
        dip_estimate_column = config.get("dip_estimate_column")
        valid_directions = [
            "north_east", "south_east", "south_west", "north_west",
            "north", "east", "south", "west"
        ]

        if dip_estimate_column:  
            if dip_estimate_column in fault_data.columns:
                # Ensure all values are in the set of valid directions or are NaN
                invalid_values = fault_data[dip_estimate_column][
                    ~fault_data[dip_estimate_column].apply(lambda x: x in valid_directions or pandas.isnull(x))
                ]

                if not invalid_values.empty:
                    logger.error(
                        f"Datatype FAULT: Column '{dip_estimate_column}' contains invalid values not in the set of allowed dip estimates: {valid_directions}."
                    )
                    return (
                        True,
                        f"Datatype FAULT: Column '{dip_estimate_column}' contains invalid values. Allowed values: {valid_directions}.",
                    )

                # Warn if there are NaN or empty values
                if fault_data[dip_estimate_column].isnull().any():
                    logger.warning(
                        f"Datatype FAULT: Column '{dip_estimate_column}' contains NaN or empty values. This may affect processing."
                    )
            else:
                logger.error(
                    f"Datatype FAULT: Column '{dip_estimate_column}' is missing from the fault data. Please ensure the column name is correct or remove that key from the config."
                )
                return (True, f"Datatype FAULT: Column '{dip_estimate_column}' is missing from the fault data.")

        # Check ID column
        id_column = config.get("objectid_column")
        
        if id_column:  
            if id_column in fault_data.columns:
                # Check for non-integer values
                # Attempt to coerce the ID column to integers because WA data says so (ARodrigues)
                fault_data[id_column] = pandas.to_numeric(fault_data[id_column], errors='coerce')

                # Check if all values are integers or null after coercion
                if not fault_data[id_column].apply(lambda x: pandas.isnull(x) or isinstance(x, int)).all():
                    logger.warning(
                        f"Datatype FAULT: ID column '{id_column}' must contain only integer values. Rectify this or remove the key from the config to auto-generate IDs."
                    )
                
                # Check for NaN values
                if fault_data[id_column].isnull().any():
                    logger.warning(
                        f"Datatype FAULT: ID column '{id_column}' contains NaN or null values. Rectify this or remove the key from the config to auto-generate IDs."
                    )

                # Check for duplicates
                if fault_data[id_column].duplicated().any():
                    logger.error(
                        f"Datatype FAULT: ID column '{id_column}' contains duplicate values. Rectify this or remove the key from the config to auto-generate IDs."
                    )

        
        return (False, "")


    @beartype.beartype
    def parse_fault_map(self) -> tuple:
        """
        Parse the fault shapefile data into a consistent format.

        Returns:
            tuple: A tuple of (bool: success/fail, str: failure message)
        """

        # Create a new geodataframe
        faults = geopandas.GeoDataFrame(self.raw_data[Datatype.FAULT]["geometry"])

        # Get fault configuration
        config = self.config.fault_config

        # update minimum fault length either with the value from the config or calculate it
        if self.minimum_fault_length < 0:
            self.minimum_fault_length = calculate_minimum_fault_length(
                bbox=self.bounding_box, area_percentage=0.05
            )
        logger.info(f"Calculated minimum fault length - {self.minimum_fault_length}")
        
        # crop
        faults = faults.loc[faults.geometry.length >= self.minimum_fault_length]
        
        if config["structtype_column"] in self.raw_data[Datatype.FAULT]:
            faults["FEATURE"] = self.raw_data[Datatype.FAULT][config["structtype_column"]]
            faults = faults[faults["FEATURE"].astype(str).str.contains(config["fault_text"])]
            if self.verbose_level > VerboseLevel.NONE:
                if len(faults) < len(self.raw_data[Datatype.GEOLOGY]) and len(faults) == 0:
                    msg = f"Fault map reduced to 0 faults as structtype_column ({config['structtype_column']}) does not contains as row with fault_text \"{config['fault_text']}\""
                    print(msg)
                    logger.warning(msg)

        if config["name_column"] in self.raw_data[Datatype.FAULT]:
            faults["NAME"] = self.raw_data[Datatype.FAULT][config["name_column"]].astype(str)
        else:
            faults["NAME"] = "Fault_" + faults.index.astype(str)

        # crop by the ignore fault codes
        ignore_codes = config["ignore_fault_codes"]

        # Find the intersection of ignore_codes and the 'NAME' column values
        existing_codes = set(ignore_codes).intersection(set(faults["NAME"].values))

        # Find the codes that do not exist in the DataFrame
        non_existing_codes = set(ignore_codes) - existing_codes

        # Issue a warning if there are any non-existing codes
        if non_existing_codes:
            logger.info(f"Warning: {non_existing_codes} set to fault ignore codes are not in the provided data. Skipping")

        # Filter the DataFrame to remove rows where 'NAME' is in the existing_codes
        if existing_codes:
            faults = faults[~faults["NAME"].isin(existing_codes)]
            logger.info(f"The following faults were found and removed as per the config: {existing_codes}")
        else:
            logger.info("None of the fault ignore codes exist in the original fault data.")
            pass

        # parse dip column
        if config["dip_column"] in self.raw_data[Datatype.FAULT]:
            faults["DIP"] = self.raw_data[Datatype.FAULT][config["dip_column"]].astype(
                numpy.float64
            )
        else:
            faults["DIP"] = numpy.nan  # config["dip_null_value"]

        # Replace dip 0 with nan as dip 0 means unknown
        faults["DIP"] = [numpy.nan if dip == 0 else dip for dip in faults["DIP"]]

        # Parse the dip direction for the fault
        if config["dipdir_flag"] != "alpha":
            if config["dipdir_column"] in self.raw_data[Datatype.FAULT]:
                faults["DIPDIR"] = self.raw_data[Datatype.FAULT][config["dipdir_column"]].astype(
                    numpy.float64
                )
            else:
                faults["DIPDIR"] = numpy.nan
        else:
            # Take the geoDataSeries of the dipdir estimates (assume it's a string description)
            if config["dip_estimate_column"] in self.raw_data[Datatype.FAULT]:
                dipdir_text_estimates = self.raw_data[Datatype.FAULT][
                    config["dip_estimate_column"]
                ].astype(str)
            elif config["dipdir_column"] in self.raw_data[Datatype.FAULT]:
                dipdir_text_estimates = self.raw_data[Datatype.FAULT][
                    config["dipdir_column"]
                ].astype(str)
            else:
                dipdir_text_estimates = None
                faults["DIPDIR"] = numpy.nan

            # Map dipdir_estimates in text form to cardinal direction
            if dipdir_text_estimates:
                direction_map = {
                    "north_east": 45.0,
                    "south_east": 135.0,
                    "south_west": 225.0,
                    "north_west": 315.0,
                    "north": 0.0,
                    "east": 90.0,
                    "south": 180.0,
                    "west": 270.0,
                }
                for direction in direction_map:
                    dipdir_text_estimates = dipdir_text_estimates.astype(str).str.replace(
                        f".*{direction}.*", direction_map[direction], regex=True
                    )
                # Catch all for any field that still contains anything that isn't a number
                dipdir_text_estimates = dipdir_text_estimates.astype(str).str.replace(
                    ".*[^0-9.].*", numpy.nan, regex=True
                )
                faults["DIPDIR"] = dipdir_text_estimates.astype(numpy.float64)

        # Add object id
        if config["objectid_column"] in self.raw_data[Datatype.FAULT]:
            faults["ID"] = self.raw_data[Datatype.FAULT][config["objectid_column"]].astype(int)
        else:
            faults["ID"] = faults.index

        if len(faults):
            faults["NAME"] = faults.apply(
                lambda fault: (
                    "Fault_" + str(fault["ID"]) if fault["NAME"].lower() == "nan" else fault["NAME"]
                ),
                axis=1,
            )
            faults["NAME"] = faults.apply(
                lambda fault: (
                    "Fault_" + str(fault["ID"])
                    if fault["NAME"].lower() == "none"
                    else fault["NAME"]
                ),
                axis=1,
            )
            faults["NAME"] = faults["NAME"].str.replace(" -/?", "_", regex=True)
        self.data[Datatype.FAULT] = faults

        return (False, "")

    @beartype.beartype
    def parse_fault_orientations(self) -> tuple:
        """
        Parse the fault orientations shapefile data into a consistent format

        Returns:
            tuple: A tuple of (bool: success/fail, str: failure message)
        """
        # Check type and size of loaded structure map


        # Create new geodataframe
        fault_orientations = geopandas.GeoDataFrame(
            self.raw_data[Datatype.FAULT_ORIENTATION]["geometry"]
        )

        config = self.config.fault_config

        # Parse dip direction and dip columns
        if config["dipdir_column"] in self.raw_data[Datatype.FAULT_ORIENTATION]:
            if config["orientation_type"] == "strike":
                fault_orientations["DIPDIR"] = self.raw_data[Datatype.STRUCTURE].apply(
                    lambda row: (row[config["dipdir_column"]] + 90.0) % 360.0, axis=1
                )
            else:
                fault_orientations["DIPDIR"] = self.raw_data[Datatype.FAULT_ORIENTATION][
                    config["dipdir_column"]
                ]
        else:
            print(
                f"Fault orientation shapefile does not contain dipdir_column '{config['dipdir_column']}'"
            )

        if config["dip_column"] in self.raw_data[Datatype.FAULT_ORIENTATION]:
            fault_orientations["DIP"] = self.raw_data[Datatype.FAULT_ORIENTATION][
                config["dip_column"]
            ]
        else:
            print(
                f"Fault orientation shapefile does not contain dip_column '{config['dip_column']}'"
            )

        # TODO LG would it be worthwhile adding a description column for faults?
        # it would be possible to parse out the fault displacement, type, slip direction
        # if this was stored in the descriptions?

        # Add object id
        if config["objectid_column"] in self.raw_data[Datatype.FAULT_ORIENTATION]:
            fault_orientations["ID"] = self.raw_data[Datatype.FAULT_ORIENTATION][
                config["objectid_column"]
            ]
        else:
            fault_orientations["ID"] = numpy.arange(len(fault_orientations))
        self.data[Datatype.FAULT_ORIENTATION] = fault_orientations
        return (False, "")


    @beartype.beartype
    def parse_fold_map(self) -> tuple:
        """
        Parse the fold shapefile data into a consistent format

        Returns:
            tuple: A tuple of (bool: success/fail, str: failure message)
        """
        # Check type of loaded fold map
        if (
            self.raw_data[Datatype.FOLD] is None
            or type(self.raw_data[Datatype.FOLD]) is not geopandas.GeoDataFrame
        ):
            return (True, "Fold map is not loaded or valid")

        # Create new geodataframe
        folds = geopandas.GeoDataFrame(self.raw_data[Datatype.FOLD]["geometry"])
        config = self.config.fold_config

        if config["structtype_column"] in self.raw_data[Datatype.FOLD]:
            folds[config["structtype_column"]] = self.raw_data[Datatype.FOLD][
                config["structtype_column"]
            ]
            folds = folds[
                folds[config["structtype_column"]].astype(str).str.contains(config["fold_text"])
            ]
            if self.verbose_level > VerboseLevel.NONE:
                if len(folds) < len(self.raw_data[Datatype.GEOLOGY]) and len(folds) == 0:
                    msg = f"Fold map reduced to 0 folds as structtype_column ({config['structtype_column']}) does not contains any row with fold_text \"{config['fold_text']}\""
                    logger.warning(msg)
                    print(msg)

        if config["foldname_column"] in self.raw_data[Datatype.FOLD]:
            folds["NAME"] = self.raw_data[Datatype.FOLD][config["foldname_column"]].astype(str)
        else:
            folds["NAME"] = numpy.arange(len(folds))
            folds["NAME"] = "Fold_" + folds["NAME"].astype(str)

        # Extract syncline from description field
        if config["description_column"] in self.raw_data[Datatype.FOLD]:
            folds["SYNCLINE"] = (
                self.raw_data[Datatype.FOLD][config["description_column"]]
                .astype(str)
                .str.contains(config["synform_text"])
            )
        else:
            folds["SYNCLINE"] = False

        # Add object id
        if config["objectid_column"] in self.raw_data[Datatype.FOLD]:
            folds["ID"] = self.raw_data[Datatype.FOLD][config["objectid_column"]]
        else:
            folds["ID"] = numpy.arange(len(folds))

        self.data[Datatype.FOLD] = folds
        return (False, "")

    @beartype.beartype
    def set_working_projection_on_map_data(self, datatype: Datatype):
        """
        Set the working projection on the GeoDataFrame structure or if already set reproject the data

        Args:
            datatype (Datatype):
                The datatype to set or reproject
        """
        if self.working_projection is None:
            print("No working projection set leaving map data in original projection")
        elif type(self.raw_data[datatype]) is geopandas.GeoDataFrame:
            if self.data_states[datatype] >= Datastate.LOADED:
                if self.raw_data[datatype].crs is None:
                    logger.info(
                        f"No projection on original map data, assigning to working_projection {self.working_projection}"
                    )
                    self.raw_data[datatype].crs = self.working_projection
                else:
                    self.raw_data[datatype].to_crs(crs=self.working_projection, inplace=True)
        else:
            logger.warning(
                f"Type of {datatype.name} map not a GeoDataFrame so cannot change map crs projection"
            )

    @beartype.beartype
    def save_all_map_data(self, output_dir: pathlib.Path, extension: str = ".csv"):
        """
        Save all the map data to file

        Args:
            output_dir (str):
                The directory to save to
            extension (str, optional):
                The extension to use for the data. Defaults to ".csv".
        """
        for i in [Datatype.GEOLOGY, Datatype.STRUCTURE, Datatype.FAULT, Datatype.FOLD]:
            self.save_raw_map_data(output_dir, i, extension)

    @beartype.beartype
    def save_raw_map_data(
        self, output_dir: pathlib.Path, datatype: Datatype, extension: str = ".shp.zip"
    ):
        """
        Save the map data from datatype to file

        Args:
            output_dir (pathlib.Path):
                The directory to save to
            datatype (Datatype):
                The datatype of the geopanda to save
            extension (str, optional):
                The extension to use for the data. Defaults to ".csv".
        """
        try:
            filename = pathlib.Path(output_dir) / f"{datatype.name}{extension}"
            raw_data = self.raw_data[datatype]

            if raw_data is None:
                logger.info(f"No data available for {datatype.name}. Skipping saving to file {filename}.")
                return

            if extension == ".csv":
                raw_data.to_csv(filename, index=False)  # Save as CSV
            else:
                self.raw_data[datatype].to_file(filename)

        except Exception as e:
            logger.error(f"Failed to save {datatype.name} to file named {filename}\nError: {str(e)}")
            print(f"Failed to save {datatype.name} to file named {filename}\nError: {str(e)}")

    @beartype.beartype
    def get_raw_map_data(self, datatype: Datatype):
        """
        Get the raw data geopanda of the specified datatype

        Args:
            datatype (Datatype):
                The datatype to retrieve

        Returns:
            geopandas.GeoDataFrame: The raw data
        """
        if self.data_states[datatype] != Datastate.COMPLETE or self.dirtyflags[datatype] is True:
            self.load_map_data(datatype)
        return self.raw_data[datatype]

    @beartype.beartype
    def get_map_data(self, datatype: Datatype):
        """
        Get the data geopanda of the specified datatype

        Args:
            datatype (Datatype):
                The datatype to retrieve

        Returns:
            geopandas.GeoDataFrame: The dataframe
        """
        if self.data_states[datatype] != Datastate.COMPLETE or self.dirtyflags[datatype] is True:
            self.load_map_data(datatype)
        return self.data[datatype]

    @beartype.beartype
    def update_filename_with_bounding_box(self, filename: str):
        """
        Update the filename/url with the bounding box
        This replace all instances of {BBOX_STR} with the bounding_box_str

        Args:
            filename (str):
                The original filename

        Raises:
            ValueError: Filename is blank

        Returns:
            str: The modified filename
        """
        if filename is None:
            logger.error(f"Filename {filename} is invalid")
            raise ValueError(f"Filename {filename} is invalid")
        return filename.replace("{BBOX_STR}", self.bounding_box_str)

    @beartype.beartype
    def update_filename_with_projection(self, filename: str):
        """
        Update the filename/url with the projection
        This replace all instances of {PROJ_STR} with the projection string

        Args:
            filename (str):
                The original filename

        Raises:
            ValueError: Filename is blank

        Returns:
            str: The modified filename
        """
        if filename is None:
            logger.error(f"Filename {filename} is invalid")
            raise ValueError(f"Filename {filename} is invalid")
        return filename.replace("{PROJ_STR}", self.working_projection)

    def calculate_bounding_box_and_projection(self):
        """
        Calculate the bounding box and projection from the geology file

        Returns:
            dict, str: The bounding box and projection of the geology shapefile
        """
        if self.filenames[Datatype.GEOLOGY] is None:
            logger.info(
                "Could not open geology file as none set, no bounding box or projection available"
            )
            return None, None
        temp_geology_filename = self.filenames[Datatype.GEOLOGY]
        temp_geology_filename = temp_geology_filename.replace("{BBOX_STR}", "")
        temp_geology_filename = temp_geology_filename.replace("{PROJ_STR}", "")
        try:
            geology_data = geopandas.read_file(temp_geology_filename)
            bounds = geology_data.total_bounds
            return {
                "minx": bounds[0],
                "maxx": bounds[1],
                "miny": bounds[2],
                "maxy": bounds[3],
            }, geology_data.crs
        except Exception:
            logger.error(
                f"Could not open geology file {temp_geology_filename} so no bounding box or projection found"
            )
            return None, None

    @beartype.beartype
    def export_wkt_format_files(self):
        """
        Save out the geology and fault GeoDataFrames in WKT format
        This is used by map2model
        """
        # TODO: - Move away from tab seperators entirely (topology and map2model)

        self.map2model_tmp_path = pathlib.Path(tempfile.mkdtemp())

        # Check geology data status and export to a WKT format file
        self.load_map_data(Datatype.GEOLOGY)
        if type(self.data[Datatype.GEOLOGY]) is not geopandas.GeoDataFrame:
            logger.warning("Cannot export geology data as it is not a GeoDataFrame")
        elif self.data_states[Datatype.GEOLOGY] != Datastate.COMPLETE:
            logger.warning(
                f"Cannot export geology data as it only loaded to {self.data_states[Datatype.GEOLOGY].name} status"
            )
        else:
            columns = [
                "geometry",
                "ID",
                "UNITNAME",
                "GROUP",
                "MIN_AGE",
                "MAX_AGE",
                "CODE",
                "ROCKTYPE1",
                "ROCKTYPE2",
                "DESCRIPTION",
            ]
            geology = self.get_map_data(Datatype.GEOLOGY)[columns].copy()
            geology.reset_index(inplace=True, drop=True)
            geology.rename(
                columns={"geometry": "WKT", "CODE": "UNITNAME", "UNITNAME": "CODE"}, inplace=True
            )
            geology["MIN_AGE"] = geology["MIN_AGE"].replace("None", 0)
            geology["MAX_AGE"] = geology["MAX_AGE"].replace("None", 4500000000)
            geology["GROUP"] = geology["GROUP"].replace("None", "")
            geology["ROCKTYPE1"] = geology["ROCKTYPE1"].replace("", "None")
            geology["ROCKTYPE2"] = geology["ROCKTYPE2"].replace("", "None")
            geology.to_csv(
                pathlib.Path(self.map2model_tmp_path) / "geology_wkt.csv", sep="\t", index=False
            )

        # Check faults data status and export to a WKT format file
        self.load_map_data(Datatype.FAULT)
        if type(self.data[Datatype.FAULT]) is not geopandas.GeoDataFrame:
            logger.warning("Cannot export fault data as it is not a GeoDataFrame")
        elif self.data_states[Datatype.FAULT] != Datastate.COMPLETE:
            logger.warning(
                f"Cannot export fault data as it only loaded to {self.data_states[Datatype.FAULT].name} status"
            )
        else:
            faults = self.get_map_data(Datatype.FAULT).copy()
            faults.rename(columns={"geometry": "WKT"}, inplace=True)
            faults.to_csv(
                pathlib.Path(self.map2model_tmp_path) / "faults_wkt.csv", sep="\t", index=False
            )

    @beartype.beartype
    def get_value_from_raster(self, datatype: Datatype, x, y):
        """
        Get the value from a raster map at the specified point

        Args:
            datatype (Datatype):
                The datatype of the raster map to retrieve from
            x (float or int):
                The easting coordinate of the value
            y (float or int):
                The northing coordinate of the value

        Returns:
            float or int: The value at the point specified
        """
        data = self.get_map_data(datatype)
        if data is None:
            logger.warning(f"Cannot get value from {datatype.name} data as data is not loaded")
            return None
        inv_geotransform = gdal.InvGeoTransform(data.GetGeoTransform())

        px = int(inv_geotransform[0] + inv_geotransform[1] * x + inv_geotransform[2] * y)
        py = int(inv_geotransform[3] + inv_geotransform[4] * x + inv_geotransform[5] * y)
        # Clamp values to the edges of raster if past boundary, similiar to GL_CLIP
        px = max(px, 0)
        px = min(px, data.RasterXSize - 1)
        py = max(py, 0)
        py = min(py, data.RasterYSize - 1)
        val = data.ReadAsArray(px, py, 1, 1)[0][0]
        return val

    @beartype.beartype
    def __value_from_raster(self, inv_geotransform, data, x: float, y: float):
        """
        Get the value from a raster dataset at the specified point

        Args:
            inv_geotransform (gdal.GeoTransform):
                The inverse of the data's geotransform
            data (numpy.array):
                The raster data
            x (float):
                The easting coordinate of the value
            y (float):
                The northing coordinate of the value

        Returns:
            float or int: The value at the point specified
        """
        px = int(inv_geotransform[0] + inv_geotransform[1] * x + inv_geotransform[2] * y)
        py = int(inv_geotransform[3] + inv_geotransform[4] * x + inv_geotransform[5] * y)
        # Clamp values to the edges of raster if past boundary, similiar to GL_CLIP
        px = max(px, 0)
        px = min(px, data.shape[0] - 1)
        py = max(py, 0)
        py = min(py, data.shape[1] - 1)
        return data[px][py]

    @beartype.beartype
    def get_value_from_raster_df(self, datatype: Datatype, df: pandas.DataFrame):
        """
        Add a 'Z' column to a dataframe with the heights from the 'X' and 'Y' coordinates

        Args:
            datatype (Datatype):
                The datatype of the raster map to retrieve from
            df (pandas.DataFrame):
                The original dataframe with 'X' and 'Y' columns

        Returns:
            pandas.DataFrame: The modified dataframe
        """
        if len(df) <= 0:
            df["Z"] = []
            return df
        data = self.get_map_data(datatype)
        if data is None:
            logger.warning("Cannot get value from data as data is not loaded")
            return None

        inv_geotransform = gdal.InvGeoTransform(data.GetGeoTransform())
        data_array = numpy.array(data.GetRasterBand(1).ReadAsArray().T)

        df["Z"] = df.apply(
            lambda row: self.__value_from_raster(inv_geotransform, data_array, row["X"], row["Y"]),
            axis=1,
        )
        return df

    @beartype.beartype
    def extract_all_contacts(self, save_contacts=True):
        """
        Extract the contacts between units in the geology GeoDataFrame
        """
        logger.info("Extracting contacts")
        geology = self.get_map_data(Datatype.GEOLOGY).copy()
        geology = geology.dissolve(by="UNITNAME", as_index=False)
        # Remove intrusions
        geology = geology[~geology["INTRUSIVE"]]
        geology = geology[~geology["SILL"]]
        # Remove faults from contact geomety
        if self.get_map_data(Datatype.FAULT) is not None:
            faults = self.get_map_data(Datatype.FAULT).copy()
            faults["geometry"] = faults.buffer(50)
            geology = geopandas.overlay(geology, faults, how="difference", keep_geom_type=False)
        units = geology["UNITNAME"].unique()
        column_names = ["UNITNAME_1", "UNITNAME_2", "geometry"]
        contacts = geopandas.GeoDataFrame(crs=geology.crs, columns=column_names, data=None)
        while len(units) > 1:
            unit1 = units[0]
            units = units[1:]
            for unit2 in units:
                if unit1 != unit2:
                    # print(f'contact: {unit1} and {unit2}')
                    join = geopandas.overlay(
                        geology[geology["UNITNAME"] == unit1],
                        geology[geology["UNITNAME"] == unit2],
                        keep_geom_type=False,
                    )[column_names]
                    join["geometry"] = join.buffer(1)
                    buffered = geology[geology["UNITNAME"] == unit2][["geometry"]].copy()
                    buffered["geometry"] = buffered.boundary
                    end = geopandas.overlay(buffered, join, keep_geom_type=False)
                    if len(end):
                        contacts = pandas.concat([contacts, end], ignore_index=True)
        # contacts["TYPE"] = "UNKNOWN"
        contacts["length"] = [row.length for row in contacts["geometry"]]
        # print('finished extracting contacts')
        if save_contacts:
            self.contacts = contacts
        return contacts

    @beartype.beartype
    def extract_basal_contacts(self, stratigraphic_column: list, save_contacts=True):
        """
        Identify the basal unit of the contacts based on the stratigraphic column

        Args:
            stratigraphic_column (list):
                The stratigraphic column to use
        """
        logger.info("Extracting basal contacts")
        
        units = stratigraphic_column
        basal_contacts = self.contacts.copy()

        # check if the units in the strati colum are in the geology dataset, so that basal contacts can be built
        # if not, stop the project
        if any(unit not in units for unit in basal_contacts["UNITNAME_1"].unique()):
            missing_units = (
                basal_contacts[~basal_contacts["UNITNAME_1"].isin(units)]["UNITNAME_1"]
                .unique()
                .tolist()
            )
            logger.error(
                "There are units in the Geology dataset, but not in the stratigraphic column: "
                + ", ".join(missing_units)
                + ". Please readjust the stratigraphic column if this is a user defined column."
            )
            raise ValueError(
                "There are units in stratigraphic column, but not in the Geology dataset: "
                + ", ".join(missing_units)
                + ". Please readjust the stratigraphic column if this is a user defined column."
            )

        # apply minimum lithological id between the two units
        basal_contacts["ID"] = basal_contacts.apply(
            lambda row: min(units.index(row["UNITNAME_1"]), units.index(row["UNITNAME_2"])), axis=1
        )
        # match the name of the unit with the minimum id
        basal_contacts["basal_unit"] = basal_contacts.apply(lambda row: units[row["ID"]], axis=1)
        # how many units apart are the two units?
        basal_contacts["stratigraphic_distance"] = basal_contacts.apply(
            lambda row: abs(units.index(row["UNITNAME_1"]) - units.index(row["UNITNAME_2"])), axis=1
        )
        # if the units are more than 1 unit apart, the contact is abnormal (meaning that there is one (or more) unit(s) missing in between the two)
        basal_contacts["type"] = basal_contacts.apply(
            lambda row: "ABNORMAL" if abs(row["stratigraphic_distance"]) > 1 else "BASAL", axis=1
        )

        basal_contacts = basal_contacts[["ID", "basal_unit", "type", "geometry"]]

        # added code to make sure that multi-line that touch each other are snapped and merged.
        # necessary for the reconstruction based on featureId
        basal_contacts["geometry"] = [
            shapely.line_merge(shapely.snap(geo, geo, 1)) for geo in basal_contacts["geometry"]
        ]

        if save_contacts:
            # keep abnormal contacts as all_basal_contacts
            self.all_basal_contacts = basal_contacts
            # remove the abnormal contacts from basal contacts
            self.basal_contacts = basal_contacts[basal_contacts["type"] == "BASAL"]

        return basal_contacts

    @beartype.beartype
    def colour_units(
        self, stratigraphic_units: pandas.DataFrame, random: bool = False
    ) -> pandas.DataFrame:
        """
        Add a colour column to the units in the stratigraphic units structure

        Args:
            stratigraphic_units (pandas.DataFrame):
                The stratigraphic units data
            random (bool, optional):
                Flag of whether to add random colours to missing entries in the colour lookup table. Defaults to False.

        Returns:
            pandas.DataFrame: The modified units
        """

        colour_lookup = pandas.DataFrame(columns=["UNITNAME", "colour"])

        if self.colour_filename is not None:
            try:
                colour_lookup = pandas.read_csv(self.colour_filename, sep=",")
            except FileNotFoundError:
                logger.info(
                    f"Colour Lookup file {self.colour_filename} not found. Assigning random colors to units"
                )
                self.colour_filename = None

        if self.colour_filename is None:
            logger.info("\nNo colour configuration file found. Assigning random colors to units")
            missing_colour_n = len(stratigraphic_units["colour"])
            stratigraphic_units.loc[
                stratigraphic_units["colour"].isna(), "colour"
            ] = generate_random_hex_colors(missing_colour_n)

        colour_lookup["colour"] = colour_lookup["colour"].str.upper()
        # if there are duplicates in the clut file, drop.
        colour_lookup = colour_lookup.drop_duplicates(subset=["UNITNAME"])

        if "UNITNAME" in colour_lookup.columns and "colour" in colour_lookup.columns:
            stratigraphic_units = stratigraphic_units.merge(
                colour_lookup,
                left_on="name",
                right_on="UNITNAME",
                suffixes=("_old", ""),
                how="left",
            )
            stratigraphic_units.loc[
                stratigraphic_units["colour"].isna(), "colour"
            ] = generate_random_hex_colors(int(stratigraphic_units["colour"].isna().sum()))
            stratigraphic_units.drop(columns=["UNITNAME", "colour_old"], inplace=True)
        else:
            logger.warning(
                f"Colour Lookup file {self.colour_filename} does not contain 'UNITNAME' or 'colour' field"
            )
        return stratigraphic_units

    @property
    def GEOLOGY(self):
        return self.get_map_data(Datatype.GEOLOGY)

    @property
    def STRUCTURE(self):
        return self.get_map_data(Datatype.STRUCTURE)

    @property
    def FAULT(self):
        return self.get_map_data(Datatype.FAULT)
