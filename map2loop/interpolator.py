from abc import ABC, abstractmethod
from typing import Tuple, Any

import beartype
import pandas
import numpy
import math
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
    def setup_interpolation(self, contact_orientations: pandas.DataFrame, map_data: MapData) -> pandas.DataFrame:
        """
        abstract method to setup interpolation (abstract method)

        Args:
            contact_orientations (pandas.DataFrame): structural data with columns: 'X', 'Y', 'Z', 'dipDir/dipdir',
            'dip', 'layer', 'name'
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
    def interpolator(self,x: float, y: float, ni: float, xi: float, yi: float)-> Tuple[numpy.ndarray, list]:
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
    def interpolate(self, contact_orientations: pandas.DataFrame, map_data: MapData) -> list:
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


class IDWInterpolator(Interpolator):
    """
    Inverse Distance Weighting interpolation class

    Args:
        Interpolator(ABC): Derived from Abstract Base Class
    """

    def __init__(self):
        """
        Initialiser of for IDWInterpolator
        """
        self.interpolator_label = "IDWInterpolator"

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.interpolator_label

    @beartype.beartype
    @abstractmethod
    def setup_interpolation(self, contact_orientations: pandas.DataFrame, map_data: MapData) -> pandas.DataFrame:
        """
        Setup the interpolation method (abstract method)

        Args:
            contact_orientations (pandas.DataFrame): structural data with columns: 'X', 'Y', 'Z', 'dipDir/dipdir',
            'dip', 'layer', 'name'
            map_data (map2loop.MapData): a catchall so that access to all map data is available
        """
        # the following code is from LoopStructural
        contact_orientations = contact_orientations.copy()
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
                        "Y" not in contact_orientations.columns
                        and "northing" in contact_orientations.columns
                ):
                    contact_orientations["Y"] = contact_orientations["northing"]
                if (
                        "Z" not in contact_orientations.columns
                        and "altitude" in contact_orientations.columns
                ):
                    contact_orientations["Z"] = contact_orientations["altitude"]
                if (
                        "X" not in contact_orientations.columns
                        or "Y" not in contact_orientations.columns
                        or "Z" not in contact_orientations.columns
                ):
                    raise ValueError(
                        "Contact orientation data must contain either X, Y, Z or easting, northing, altitude"
                    )

        return contact_orientations

    @beartype.beartype
    def setup_grid(self, map_data: MapData) -> numpy.ndarray:
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
        return xi, yi

    @beartype.beartype
    def interpolator(self, x: float, y: float, ni: float, xi: float, yi: float) -> numpy.ndarray:

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
    def interpolate(self, contact_orientations: pandas.DataFrame, map_data: MapData) -> numpy.ndarray:
        """
        Execute interpolation method (abstract method)

        Args:
            contact_orientations (pandas.DataFrame): structural data with columns: 'X', 'Y', 'Z', 'dipDir/dipdir',
            'dip', 'layer', 'name'
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            list: sorted list of unit names

        """

        stratigraphic_orientations = self.setup_interpolation(contact_orientations, map_data)
        x, y = stratigraphic_orientations[["X", "Y"]].to_numpy()
        nx, ny, nz = stratigraphic_orientations[["nx", "ny", "nz"]].to_numpy()
        xi, yi = self.setup_grid(map_data)

        # interpolate each component of the normal vector nx, ny, nz
        nx_interp = self.interpolator(x, y, nx, xi, yi)
        ny_interp = self.interpolator(x, y, ny, xi, yi)
        nz_interp = self.interpolator(x, y, nz, xi, yi)

        return numpy.array([nx_interp, ny_interp, nz_interp]).T