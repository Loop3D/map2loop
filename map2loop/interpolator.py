from abc import ABC, abstractmethod
from typing import Tuple, Any

from Cython.Includes.numpy import ndarray
from map2loop.m2l_enums import Datatype
import beartype
import pandas
import geopandas
import numpy
import math

from numpy import ndarray
from scipy.interpolate import Rbf
from pandas import DataFrame

from .mapdata import MapData
from utils import strike_dip_vector


class Interpolator(ABC):
    """
    Base Class of Interpolator used to force structure of Interpolator

    Args:
        ABC (ABC): Derived from Abstract Base Class
    """

    def __init__(self):
        """
        Initialiser of for Interpolator
        """
        self.interpolator_label = "InterpolatorBaseClass"

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.interpolator_label

    @beartype.beartype
    @abstractmethod
    def setup_interpolation(self, map_data: MapData) -> Tuple[pandas.DataFrame, list, numpy.ndarray]:
        """
        abstract method to setup interpolation (abstract method)

        Args:
            map_data (map2loop.MapData): a catchall so that access to all map data is available
        """
        pass

    @beartype.beartype
    @abstractmethod
    def setup_grid(self, map_data: MapData) -> Tuple[numpy.ndarray, list]:
        """
        abstract method to setup an XY grid (abstract method)

        Args:
            map_data (map2loop.MapData): a catchall so that access to all map data is available
        """
        pass

    @beartype.beartype
    @abstractmethod
    def interpolator(self, x: float, y: float, ni: float, xi: float, yi: float) -> Tuple[numpy.ndarray, list]:
        """
        Interpolator method

        Args:
            x (float): x-coordinate of the point
            y (float): y-coordinate of the point
            ni (int): number of points
            xi (float): x-coordinate of the point
            yi (float): z-coordinate of the point

        Returns:
            float: interpolated value
        """

        pass

    @beartype.beartype
    @abstractmethod
    def interpolate(self, map_data: MapData) -> list:
        """
        Execute interpolate method (abstract method)

        Args:
            contact_orientations (pandas.DataFrame): structural data with columns: 'X', 'Y', 'Z', 'dipDir/dipdir',
            'dip', 'layer', 'name'
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            list: sorted list of unit names

        """
        pass


class NormalVectorInterpolator(Interpolator):
    """
    Normal vector interpolation class

    Args:
        NormalVectorInterpolator(Interpolator): Derived from Abstract Base Class
    """

    def __init__(self):
        """
        Initialiser of for NormalVectorInterpolator class
        """
        self.dataframe = None
        self.xi = None
        self.yi = None
        self.interpolator_label = "NormalVectorInterpolator"

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.interpolator_label

    @beartype.beartype
    @abstractmethod
    def setup_interpolation(self, map_data: MapData):
        """
        Setup the interpolation method (abstract method)

        Args:
            contact_orientations (pandas.DataFrame): structural data with columns: 'X', 'Y', 'Z', 'dipDir/dipdir',
            'dip', 'layer', 'name'
            map_data (map2loop.MapData): a catchall so that access to all map data is available
        """
        # the following code is from LoopStructural
        contact_orientations = map_data.get_map_data(Datatype.STRUCTURE).copy()
        if (
                "nx" not in contact_orientations.columns
                or "ny" not in contact_orientations.columns
                or "nz" not in contact_orientations.columns
        ):
            if (
                    "strike" not in contact_orientations.columns
                    and "azimuth" in contact_orientations.columns
            ):
                contact_orientations["strike"] = contact_orientations["azimuth"] - 90
            if (
                    "strike" not in contact_orientations.columns
                    and "dipdir" in contact_orientations.columns
            ):
                contact_orientations["strike"] = contact_orientations["dipdir"] - 90
            if (
                    "strike" not in contact_orientations.columns
                    and "dipDir" in contact_orientations.columns
            ):
                contact_orientations["strike"] = contact_orientations["dipDir"] - 90
            if (
                    "strike" in contact_orientations.columns
                    and "dip" in contact_orientations.columns
            ):
                contact_orientations["nx"] = numpy.nan
                contact_orientations["ny"] = numpy.nan
                contact_orientations["nz"] = numpy.nan
                contact_orientations[["nx", "ny", "nz"]] = strike_dip_vector(
                    contact_orientations["strike"], contact_orientations["dip"]
                )
            if (
                    "nx" not in contact_orientations.columns
                    or "ny" not in contact_orientations.columns
                    or "nz" not in contact_orientations.columns
            ):
                raise ValueError(
                    "Contact orientation data must contain either strike/dipdir, dip, or nx, ny, nz"
                )

            if (
                    "X" not in contact_orientations.columns
                    or "Y" not in contact_orientations.columns
                    or "Z" not in contact_orientations.columns
            ):
                if (
                        "X" not in contact_orientations.columns
                        and "easting" in contact_orientations.columns
                ):
                    contact_orientations["X"] = contact_orientations["easting"]
                if (
                        "X" not in contact_orientations.columns
                        and "easting" not in contact_orientations.columns
                ):
                    contact_orientations["X"] = contact_orientations['geometry'].apply(lambda geom: geom.x)

                if (
                        "Y" not in contact_orientations.columns
                        and "northing" in contact_orientations.columns
                ):
                    contact_orientations["Y"] = contact_orientations["northing"]
                if (
                        "Y" not in contact_orientations.columns
                        and "northing" not in contact_orientations.columns
                ):
                    contact_orientations["Y"] = contact_orientations['geometry'].apply(lambda geom: geom.y)
                if (
                        "Z" not in contact_orientations.columns
                        and "altitude" in contact_orientations.columns
                ):
                    contact_orientations["Z"] = contact_orientations["altitude"]
                if (
                        "Z" not in contact_orientations.columns
                        and "altitude" not in contact_orientations.columns
                ):
                    contact_orientations["Z"] = 0

                if (
                        "X" not in contact_orientations.columns
                        or "Y" not in contact_orientations.columns
                        or "Z" not in contact_orientations.columns
                ):
                    raise ValueError(
                        "Contact orientation data must contain either X, Y, Z or easting, northing, altitude"
                    )

        self.dataframe = contact_orientations

    @beartype.beartype
    def setup_grid(self, map_data: MapData):
        """
        Setup the grid for interpolation

        Args:
            map_data (map2loop.MapData): a catchall so that access to all map data is available
        """
        # Define the desired cell size
        cell_size = 0.05 * (map_data.bounding_box["maxx"] - map_data.bounding_box["minx"])

        # Calculate the grid resolution
        grid_resolution = round((map_data.bounding_box["maxx"] - map_data.bounding_box["minx"]) / cell_size)

        # Generate the grid
        xi = numpy.linspace(
            map_data.bounding_box["minx"], map_data.bounding_box["maxx"], grid_resolution
        )
        yi = numpy.linspace(
            map_data.bounding_box["miny"], map_data.bounding_box["maxy"], grid_resolution
        )

        self.xi = xi
        self.yi = yi

    @beartype.beartype
    def interpolator(self, x: float, y: float, ni: float, xi: float, yi: float) -> numpy.ndarray:
        # TODO: 1. add argument for type of interpolator. 2. add code to process different types of
        #  interpolators from Scipy and use the chosen one
        """
        Inverse Distance Weighting interpolation method

        Args:
            x (float): x-coordinate of the point
            y (float): y-coordinate of the point
            ni (int): value to interpolate
            xi (float): x-coordinate of the point where interpolation of ni is performed (grid point)
            yi (float): y-coordinate of the point where interpolation of ni is performed (grid point)

        Returns:
            Rbf: radial basis function object
        """

        rbf = Rbf(x, y, ni, function="linear")

        return rbf(xi, yi)

    @beartype.beartype
    def interpolate(self, map_data: MapData) -> numpy.ndarray:
        """
        Execute interpolation method

        Args:
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            list: sorted list of unit names

        """

        stratigraphic_orientations = self.setup_interpolation(map_data)
        x, y = stratigraphic_orientations[["X", "Y"]].to_numpy()
        nx, ny, nz = stratigraphic_orientations[["nx", "ny", "nz"]].to_numpy()
        xi, yi = self.setup_grid(map_data)

        # interpolate each component of the normal vector nx, ny, nz
        nx_interp = self.interpolator(x, y, nx, xi, yi)
        ny_interp = self.interpolator(x, y, ny, xi, yi)
        nz_interp = self.interpolator(x, y, nz, xi, yi)

        vecs = numpy.array([nx_interp, ny_interp, nz_interp]).T
        vecs /= numpy.linalg.norm(vecs, axis=1)[:, None]

        return vecs


class DipDipDirectionInterpolator(Interpolator):
    """


    Args:
        Interpolator(ABC): Derived from Abstract Base Class
    """

    def __init__(self):
        """
        Initialiser of for IDWInterpolator
        """
        self.x = None
        self.y = None
        self.xi = None
        self.yi = None
        self.dip = None
        self.dipdir = None
        self.interpolator_label = "DipDipDirectionInterpolator"

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.interpolator_label

    @beartype.beartype
    @abstractmethod
    def setup_interpolation(self, map_data: MapData):
        """
        Setup the interpolation method
        """
        contact_orientations = map_data.get_map_data(Datatype.STRUCTURE).copy()
        contact_orientations['x'] = contact_orientations['geometry'].apply(lambda geom: geom.x)
        contact_orientations['y'] = contact_orientations['geometry'].apply(lambda geom: geom.y)
        self.x, self.y = contact_orientations[['x', 'y']].to_list()
        self.dip = contact_orientations["dip"].to_list()
        self.dipdir = contact_orientations["dipdir"].to_list()

    @beartype.beartype
    def setup_grid(self, map_data: MapData):
        """
        Setup the grid for interpolation

        Args:
            map_data (map2loop.MapData): a catchall so that access to all map data is available
        """
        # Define the desired cell size
        cell_size = 0.05 * (map_data.bounding_box["maxx"] - map_data.bounding_box["minx"])

        # Calculate the grid resolution
        grid_resolution = round((map_data.bounding_box["maxx"] - map_data.bounding_box["minx"]) / cell_size)

        # Generate the grid
        self.xi = numpy.linspace(
            map_data.bounding_box["minx"], map_data.bounding_box["maxx"], grid_resolution
        )
        self.yi = numpy.linspace(
            map_data.bounding_box["miny"], map_data.bounding_box["maxy"], grid_resolution
        )

    @beartype.beartype
    def interpolator(self, ni: Any) -> numpy.ndarray:
        """
        Inverse Distance Weighting interpolation method

        Args:
            ni (Any): list or numpy.ndarray of values to interpolate


        Returns:
            Rbf: radial basis function object
        """

        rbf = Rbf(self.x, self.y, ni, function="linear")

        return rbf(self.xi, self.yi)

    @beartype.beartype
    def interpolate(self, map_data: MapData) -> tuple[ndarray | ndarray, ndarray | ndarray]:
        """
        Execute interpolation method (abstract method)

        Args:
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            list: sorted list of unit names

        """

        self.setup_interpolation(map_data)
        self.setup_grid(map_data)

        # interpolate each component of the normal vector nx, ny, nz
        interpolated_dip = self.interpolator(self.dip)
        interpolated_dipdir = self.interpolator(self.dipdir)
        interpolated = numpy.array([interpolated_dip, interpolated_dipdir]).T

        return interpolated
