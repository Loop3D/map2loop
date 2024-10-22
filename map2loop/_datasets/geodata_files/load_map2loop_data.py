import geopandas
import pkg_resources
from osgeo import gdal

def load_hamersley_geology():
    """
    Loads Hamersley geology data from a shapefile

    Args:
        path (str):
            The path to the shapefile

    Returns:
        geopandas.GeoDataFrame: The geology data
    """
    # stream = pkg_resources.resource_filename("../_datasets/geodata_files/hamersley/geology.geojson")
    stream = "map2loop/map2loop/_datasets/geodata_files/hamersley/geology.geojson"
    return geopandas.read_file(stream)


def load_hamersley_structure():
    """
    Loads Hamersley structure data from a shapefile

    Args:
        path (str):
            The path to the shapefile

    Returns:
        geopandas.GeoDataFrame: The structure data
    """
    
    # path = pkg_resources.resource_filename("../_datasets/geodata_files/hamersley/structure.geojson")
    path = "map2loop/map2loop/_datasets/geodata_files/hamersley/structure.geojson"
    return geopandas.read_file(path)

def load_hamersley_dtm():
    """
    Load DTM data from a raster file

    Returns:
        gdal.Dataset: The DTM data
    """
    # path = pkg_resources.resource_filename("../_datasets/geodata_files/hamersley/dtm_rp.tif")
    path = "map2loop/map2loop/_datasets/geodata_files/hamersley/dtm_rp.tif"
    return gdal.Open(path)
