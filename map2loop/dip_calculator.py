from abc import ABC, abstractmethod
from typing import Union
import beartype
from skspatial.objects import Plane
import numpy


class DipCalculator(ABC):
    """
    Base Class of Sorter used to force structure of Sorter

    Args:
        ABC (ABC): Derived from Abstract Base Class
    """

    def __init__(self):
        """
        Initialiser of for Sorter
        """
        self.dip_calculator_label = "DipCalculator"

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.dip_calculator_label

    @beartype.beartype
    @abstractmethod
    def compute(self, points: Union[list, numpy.ndarray]):
        """
        Execute dip calculator method (abstract method)

        Args:
            points (list): list of points to compute dip

        Returns:
            list: dip value
        """
        pass


class SvdDipCalculator(DipCalculator):
    """
    SvdDipCalculator class used to calculate dip of a plane

    Args:
        DipCalculator: Dip calculator dip base class
    """

    def __init__(self):
        """
        Initialiser of DipCalculator
        """

        self.dip_calculator_label = "SvdDipCalculator"

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.dip_calculator_label

    @beartype.beartype
    def compute(self, points: Union[list, numpy.ndarray]):
        """
        Execute the Singular Value Decomposition (SVD) dip calculator method

        Args:
            points (list): list of points to compute dip

        Returns:
            list: dip value
        """
        if len(points) != 3:
            raise ValueError("Dip calculation requires 3 points")

        p1 = [points[0].x, points[0].y, points[0].z]
        p2 = [points[1].x, points[1].y, points[1].z]
        p3 = [points[2].x, points[2].y, points[2].z]

        plane = Plane.best_fit([p1, p2, p3])
        normal_vector = plane.normal.round(4)
        dip = numpy.degrees(numpy.arccos(normal_vector[2]))

        return dip


class EigenDipCalculator(DipCalculator):
    """
    EigenDipCalculator class used to calculate dip of a plane

    Args:
        DipCalculator: Dip calculator dip base class
    """

    def __init__(self):
        """
        Initialiser of EigenDipCalculator
        """
        self.dip_calculator_label = "EigenDipCalculator"

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.dip_calculator_label

    @beartype.beartype
    def compute(self, points: Union[list, numpy.ndarray]):
        """
        Execute the dip calculator using EigenAnalysis

        Args:
            points (list): list of points to compute dip

        Returns:
            list: dip value
        """
        if len(points) != 3:
            raise ValueError("Dip calculation requires 3 points")

        # Center the data by subtracting the mean of each column
        centered_data = points - numpy.mean(points, axis=0)

        # Calculate the covariance matrix
        covariance = numpy.dot(centered_data.T, centered_data) / (points.shape[0] - 1)

        # Perform eigenanalysis
        eigenvalues, eigenvectors = numpy.linalg.eig(covariance)

        # Get the normal vector (eigenvector corresponding to smallest eigenvalue)
        normal_vector = eigenvectors[:, numpy.argmin(eigenvalues)]

        # Calculate dip angle from normal vector
        dip = numpy.degrees(numpy.arccos(normal_vector[2] / numpy.linalg.norm(normal_vector)))

        return dip
