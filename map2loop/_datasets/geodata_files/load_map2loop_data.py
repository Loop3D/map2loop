import geopandas
from importlib.resources import files
from osgeo import gdal
gdal.UseExceptions()

def load_hamersley_geology():
    """
    Loads Hamersley geology data from a shapefile

    Args:
        path (str):
            The path to the shapefile

    Returns:
        geopandas.GeoDataFrame: The geology data
    """
    stream = files("map2loop._datasets.geodata_files.hamersley").joinpath("geology.geojson")
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

    path = files("map2loop._datasets.geodata_files.hamersley").joinpath("structure.geojson")
    return geopandas.read_file(path)


def load_hamersley_dtm():
    """
    Load DTM data from a raster file

    Returns:
        gdal.Dataset: The DTM data
    """
    path = files("map2loop._datasets.geodata_files.hamersley").joinpath("dtm_rp.tif")
    return gdal.Open(str(path))
