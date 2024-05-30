# internal imports
from .m2l_enums import Datatype, Datastate, VerboseLevel
from .config import Config
from .aus_state_urls import AustraliaStateUrls
from .utils import generate_random_hex_colors

# external imports
import geopandas
import pandas
import numpy
import pathlib
import shapely
from osgeo import gdal, osr
from owslib.wcs import WebCoverageService
import urllib
from gzip import GzipFile
from uuid import uuid4
import beartype
import os
from io import BytesIO
from typing import Union
import requests
import requests


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
    tmp_path: str
        The path to the directory holding the temporary files
    verbose_level: m2l_enums.VerboseLevel
        A selection that defines how much console logging is output
    config: Config
        A link to the config structure which is defined in config.py
    """

    def __init__(self, tmp_path: str = "", verbose_level: VerboseLevel = VerboseLevel.ALL):
        """
        The initialiser for the map data

        Args:
            tmp_path (str, optional):
                The directory for storing temporary files. Defaults to "".
            verbose_level (VerboseLevel, optional):
                How much console output is sent. Defaults to VerboseLevel.ALL.
        """
        self.raw_data = [None] * len(Datatype)
        self.data = [None] * len(Datatype)
        self.contacts = None
        self.basal_contacts = None
        self.sampled_contacts = None
        self.filenames = [None] * len(Datatype)
        # self.output_filenames = [None] * len(Datatype)
        self.dirtyflags = [True] * len(Datatype)
        self.data_states = [Datastate.UNNAMED] * len(Datatype)
        self.working_projection = None
        self.bounding_box = None
        self.bounding_box_polygon = None
        self.bounding_box_str = None
        self.config_filename = None
        self.colour_filename = None
        self.tmp_path = tmp_path
        self.verbose_level = verbose_level

        self.config = Config()

    def set_working_projection(self, projection):
        """
        Set the working projection for the map data

        Args:
            projection (int or str):
                The projection to use for map reprojection
        """
        if issubclass(type(projection), int):
            projection = "EPSG:" + str(projection)
            self.working_projection = projection
        elif issubclass(type(projection), str):
            self.working_projection = projection
        else:
            print(
                f"Warning: Unknown projection set {projection}. Leaving all map data in original projection\n"
            )
        if self.bounding_box is not None:
            self.recreate_bounding_box_str()

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
        self.bounding_box_str = f"{minx},{miny},{maxx},{maxy},{self.working_projection}"

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
            print(f"Requested filename for {str(type(datatype))} is not set\n")
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
        self.config_filename = filename
        self.config.update_from_file(filename, legacy_format=legacy_format, lower=lower)

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
        self.colour_filename = filename

    def get_colour_filename(self):
        """
        Get the colour lookup table filename

        Returns:
            str: The colour lookup table filename
        """
        return self.colour_filename

    @beartype.beartype
    def set_ignore_codes(self, codes: list):
        """
        Set the codes to ignore in the geology shapefile

        Args:
            codes (list):
                The list of codes to ignore
        """
        self.config.geology_config["ignore_codes"] = codes
        self.data_states[Datatype.GEOLOGY] = Datastate.CLIPPED
        self.dirtyflags[Datatype.GEOLOGY] = True

    @beartype.beartype
    def get_ignore_codes(self) -> list:
        """
        Get the list of codes to ignore

        Returns:
            list: The list of strings to ignore
        """
        return self.config.geology_config["ignore_codes"]

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
        if state in ["WA", "SA", "QLD", "NSW", "TAS", "VIC", "ACT", "NT"]:
            self.set_filename(Datatype.GEOLOGY, AustraliaStateUrls.aus_geology_urls[state])
            self.set_filename(Datatype.STRUCTURE, AustraliaStateUrls.aus_structure_urls[state])
            self.set_filename(Datatype.FAULT, AustraliaStateUrls.aus_fault_urls[state])
            self.set_filename(Datatype.FOLD, AustraliaStateUrls.aus_fold_urls[state])
            self.set_filename(Datatype.DTM, "au")
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
            print(f"Warning: Filename for {str(datatype)} is not set")
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
        for i in [
            Datatype.GEOLOGY,
            Datatype.STRUCTURE,
            Datatype.FAULT,
            Datatype.FOLD,
            Datatype.FAULT_ORIENTATION,
        ]:

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
            print(f"Datatype {datatype.name} is not set and so cannot be loaded\n")
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
                    print(
                        f"Failed to open {datatype.name} file called '{self.filenames[datatype]}'\n"
                    )
                    print(f"Cannot continue as {datatype.name} was not loaded\n")
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
    def __check_and_create_tmp_path(self):
        """
        Create the temporary files directory if it is not valid
        """
        if not os.path.isdir(self.tmp_path):
            os.mkdir(self.tmp_path)


 
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
        self.__check_and_create_tmp_path()
        
        # For gdal debugging use exceptions
        gdal.UseExceptions()
        bb_ll = tuple(self.bounding_box_polygon.to_crs("EPSG:4326").geometry.total_bounds)
    
        if filename.lower() == "aus" or filename.lower() == "au":

            url = "http://services.ga.gov.au/gis/services/DEM_SRTM_1Second_over_Bathymetry_Topography/MapServer/WCSServer?"
            wcs = WebCoverageService(url, version="1.0.0")

            coverage = wcs.getCoverage(
                identifier="1", bbox=bb_ll, format="GeoTIFF", crs=4326, width=2048, height=2048
            )
            # This is stupid that gdal cannot read a byte stream and has to have a
            # file on the local system to open or otherwise create a gdal file
            # from scratch with Create

            tmp_file = os.path.join(self.tmp_path, "StupidGDALLocalFile.tif")

            with open(tmp_file, "wb") as fh:
                fh.write(coverage.read())
            tif = gdal.Open(tmp_file)
        
        elif filename == "hawaii":
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
            image_data = self.open_http_query(filename)
            mmap_name = f"/vsimem/{str(uuid4())}"
            gdal.FileFromMemBuffer(mmap_name, image_data.read())
            tif = gdal.Open(mmap_name)
        else:
            tif = gdal.Open(filename, gdal.GA_ReadOnly)
        # except Exception:
        #     print(
        #         f"Failed to open geoTIFF file from '{filename}'\n"
        #     )
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
            print(f"Datatype {datatype.name} is not set and so cannot be loaded\n")
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
                    print(f"Warp failed for {datatype.name}\n")
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
        if datatype == Datatype.GEOLOGY:
            func = self.parse_geology_map
        elif datatype == Datatype.STRUCTURE:
            func = self.parse_structure_map
        elif datatype == Datatype.FAULT:
            func = self.parse_fault_map
        elif datatype == Datatype.FOLD:
            func = self.parse_fold_map
        elif datatype == Datatype.FAULT_ORIENTATION:
            func = self.parse_fault_orientations
        if func:
            error, message = func()
            if error:
                print(message)

    @beartype.beartype
    def parse_fault_orientations(self) -> tuple:
        """
        Parse the fault orientations shapefile data into a consistent format

        Returns:
            tuple: A tuple of (bool: success/fail, str: failure message)
        """
        # Check type and size of loaded structure map
        if (
            self.raw_data[Datatype.FAULT_ORIENTATION] is None
            or type(self.raw_data[Datatype.FAULT_ORIENTATION]) is not geopandas.GeoDataFrame
        ):
            return (True, "Fault orientation shapefile is not loaded or valid")

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
    def parse_structure_map(self) -> tuple:
        """
        Parse the structure shapefile data into a consistent format

        Returns:
            tuple: A tuple of (bool: success/fail, str: failure message)
        """
        # Check type and size of loaded structure map
        if (
            self.raw_data[Datatype.STRUCTURE] is None
            or type(self.raw_data[Datatype.STRUCTURE]) is not geopandas.GeoDataFrame
        ):
            return (True, "Structure map is not loaded or valid")

        if len(self.raw_data[Datatype.STRUCTURE]) < 2:
            print(
                "Stucture map does not enough orientations to complete calculations (need at least 2), projection may be inconsistent"
            )

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
        else:
            print(f"Structure map does not contain dipdir_column '{config['dipdir_column']}'")
                    
        # Ensure all DIPDIR values are within [0, 360]
        structure["DIPDIR"] = structure["DIPDIR"] % 360.0
        
        if config["dip_column"] in self.raw_data[Datatype.STRUCTURE]:
            structure["DIP"] = self.raw_data[Datatype.STRUCTURE][config["dip_column"]]
        else:
            print(f"Structure map does not contain dip_column '{config['dip_column']}'")

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

    @beartype.beartype
    def parse_geology_map(self) -> tuple:
        """
        Parse the geology shapefile data into a consistent format

        Returns:
            tuple: A tuple of (bool: success/fail, str: failure message)
        """
        # Check type of loaded geology map
        if (
            self.raw_data[Datatype.GEOLOGY] is None
            or type(self.raw_data[Datatype.GEOLOGY]) is not geopandas.GeoDataFrame
        ):
            return (True, "Geology map is not loaded or valid")

        # Create new geodataframe
        geology = geopandas.GeoDataFrame(self.raw_data[Datatype.GEOLOGY]["geometry"])
        config = self.config.geology_config

        # Parse unit names and codes
        if config["unitname_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["UNITNAME"] = self.raw_data[Datatype.GEOLOGY][config["unitname_column"]].astype(
                str
            )
        else:
            msg = f"Geology map does not contain unitname_column {config['unitname_column']}"
            print(msg)
            return (True, msg)
        if config["alt_unitname_column"] in self.raw_data[Datatype.GEOLOGY]:
            geology["CODE"] = self.raw_data[Datatype.GEOLOGY][config["alt_unitname_column"]].astype(
                str
            )
        else:
            msg = (
                f"Geology map does not contain alt_unitname_column {config['alt_unitname_column']}"
            )
            print(msg)
            return (True, msg)

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

        # TODO: Check for duplicates in "ID"
        # TODO: Check that the exploded geology has more than 1 unit
        #       Do we need to explode the geometry at this stage for geology/faults/folds???
        #       If not subsequent classes will need to be able to deal with them
        # TODO: Check for Nans or blanks in "UNITNAME", "GROUP", "SUPERGROUP", "DESCRIPTION", "CODE", "ROCKTYPE"
        # Strip out whitespace (/n <space> /t) and '-', ',', '?' from "UNITNAME", "CODE" "GROUP" "SUPERGROUP"
        geology["UNITNAME"] = geology["UNITNAME"].str.replace("[ -/?]", "_", regex=True)
        geology["CODE"] = geology["CODE"].str.replace("[ -/?]", "_", regex=True)
        geology["GROUP"] = geology["GROUP"].str.replace("[ -/?]", "_", regex=True)
        geology["SUPERGROUP"] = geology["SUPERGROUP"].str.replace("[ -/?]", "_", regex=True)

        # Mask out ignored unit_names/codes (ie. for cover)
        for code in self.config.geology_config["ignore_codes"]:
            geology = geology[~geology["CODE"].astype(str).str.contains(code)]
            geology = geology[~geology["UNITNAME"].astype(str).str.contains(code)]

        geology = geology.dissolve(by="UNITNAME", as_index=False)

        # Note: alt_rocktype_column and volcanic_text columns not used
        self.data[Datatype.GEOLOGY] = geology
        return (False, "")

    @beartype.beartype
    def parse_fault_map(self) -> tuple:
        """
        Parse the fault shapefile data into a consistent format

        Returns:
            tuple: A tuple of (bool: success/fail, str: failure message)
        """
        # Check type of loaded fault map
        if (
            self.raw_data[Datatype.FAULT] is None
            or type(self.raw_data[Datatype.FAULT]) is not geopandas.GeoDataFrame
        ):
            return (True, "Fault map is not loaded or valid")

        # Create new geodataframe
        faults = geopandas.GeoDataFrame(self.raw_data[Datatype.FAULT]["geometry"])
        config = self.config.fault_config

        if config["structtype_column"] in self.raw_data[Datatype.FAULT]:
            faults["FEATURE"] = self.raw_data[Datatype.FAULT][config["structtype_column"]]
            faults = faults[faults["FEATURE"].astype(str).str.contains(config["fault_text"])]
            if self.verbose_level > VerboseLevel.NONE:
                if len(faults) < len(self.raw_data[Datatype.GEOLOGY]) and len(faults) == 0:
                    msg = f"Fault map reduced to 0 faults as structtype_column ({config['structtype_column']}) does not contains as row with fault_text \"{config['fault_text']}\""
                    print(msg)

        if config["name_column"] in self.raw_data[Datatype.FAULT]:
            faults["NAME"] = self.raw_data[Datatype.FAULT][config["name_column"]].astype(str)
        else:
            faults["NAME"] = "Fault_" + faults.index.astype(str)

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
                    print(
                        f"No projection on original map data, assigning to working_projection {self.working_projection}"
                    )
                    self.raw_data[datatype].crs = self.working_projection
                else:
                    self.raw_data[datatype].to_crs(crs=self.working_projection, inplace=True)
        else:
            print(
                f"Type of {datatype.name} map not a GeoDataFrame so cannot change map crs projection"
            )

    @beartype.beartype
    def save_all_map_data(self, output_dir: str, extension: str = ".csv"):
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
    def save_raw_map_data(self, output_dir: str, datatype: Datatype, extension: str = ".shp.zip"):
        """
        Save the map data from datatype to file

        Args:
            output_dir (str):
                The directory to save to
            datatype (Datatype):
                The datatype of the geopanda to save
            extension (str, optional):
                The extension to use for the data. Defaults to ".csv".
        """
        try:
            filename = os.path.join(output_dir, datatype.name + extension)
            if extension == ".csv":
                # TODO: Add geopandas to pandas converter and then write csv
                # self.raw_data[datatype].write_csv(filename)
                print("GeoDataFrame to CSV conversion not implimented")
            else:
                self.raw_data[datatype].to_file(filename)
        except Exception:
            print(f"Failed to save {datatype.name} to file named {filename}\n")

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
            raise ValueError(f"Filename {filename} is invalid")
        return filename.replace("{PROJ_STR}", self.working_projection)

    def calculate_bounding_box_and_projection(self):
        """
        Calculate the bounding box and projection from the geology file

        Returns:
            dict, str: The bounding box and projection of the geology shapefile
        """
        if self.filenames[Datatype.GEOLOGY] is None:
            print(
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
            print(
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

        self.__check_and_create_tmp_path()
        if not os.path.isdir(os.path.join(self.tmp_path, "map2model_data")):
            os.mkdir(os.path.join(self.tmp_path, "map2model_data"))

        # Check geology data status and export to a WKT format file
        self.load_map_data(Datatype.GEOLOGY)
        if type(self.data[Datatype.GEOLOGY]) is not geopandas.GeoDataFrame:
            print("Cannot export geology data as it is not a GeoDataFrame")
        elif self.data_states[Datatype.GEOLOGY] != Datastate.COMPLETE:
            print(
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
                os.path.join(self.tmp_path, "map2model_data", "geology_wkt.csv"),
                sep="\t",
                index=False,
            )

        # Check faults data status and export to a WKT format file
        self.load_map_data(Datatype.FAULT)
        if type(self.data[Datatype.FAULT]) is not geopandas.GeoDataFrame:
            print("Cannot export fault data as it is not a GeoDataFrame")
        elif self.data_states[Datatype.FAULT] != Datastate.COMPLETE:
            print(
                f"Cannot export fault data as it only loaded to {self.data_states[Datatype.FAULT].name} status"
            )
        else:
            faults = self.get_map_data(Datatype.FAULT).copy()
            faults.rename(columns={"geometry": "WKT"}, inplace=True)
            faults.to_csv(
                os.path.join(self.tmp_path, "map2model_data", "faults_wkt.csv"),
                sep="\t",
                index=False,
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
            print(f"Cannot get value from {datatype.name} data as data is not loaded")
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
            print("Cannot get value from data as data is not loaded")
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
        units = stratigraphic_column
        basal_contacts = self.contacts.copy()
        basal_contacts["ID"] = basal_contacts.apply(
            lambda row: min(units.index(row["UNITNAME_1"]), units.index(row["UNITNAME_2"])), axis=1
        )
        basal_contacts["basal_unit"] = basal_contacts.apply(lambda row: units[row["ID"]], axis=1)
        basal_contacts["distance"] = basal_contacts.apply(
            lambda row: abs(units.index(row["UNITNAME_1"]) - units.index(row["UNITNAME_2"])), axis=1
        )
        basal_contacts["type"] = basal_contacts.apply(
            lambda row: "ABNORMAL" if abs(row["distance"]) > 1 else "BASAL", axis=1
        )
        basal_contacts = basal_contacts[["ID", "basal_unit", "type", "geometry"]]
        if save_contacts:
            self.basal_contacts = basal_contacts
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
                print(
                    f"Colour Lookup file {self.colour_filename} not found. Assigning random colors to units"
                )
                self.colour_filename = None

        if self.colour_filename is None:
            print("No colour configuration file found. Assigning random colors to units")
            missing_colour_n = len(stratigraphic_units["colour"])
            stratigraphic_units.loc[stratigraphic_units["colour"].isna(), ["colour"]] = (
                generate_random_hex_colors(missing_colour_n)
            )

        colour_lookup["colour"] = colour_lookup["colour"].str.upper()
        if "UNITNAME" in colour_lookup.columns and "colour" in colour_lookup.columns:
            stratigraphic_units = stratigraphic_units.merge(
                colour_lookup,
                left_on="name",
                right_on="UNITNAME",
                suffixes=("_old", ""),
                how="left",
            )
            stratigraphic_units.loc[stratigraphic_units["colour"].isna(), ["colour"]] = (
                generate_random_hex_colors(int(stratigraphic_units["colour"].isna().sum()))
            )
            stratigraphic_units.drop(columns=["UNITNAME", "colour_old"], inplace=True)
        else:
            print(
                f"Colour Lookup file {self.colour_filename} does not contain 'UNITNAME' or 'colour' field"
            )
        return stratigraphic_units
