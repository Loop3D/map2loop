from abc import ABC, abstractmethod
import beartype
from skspatial.objects import Plane
import numpy


class BaseDipCalculator(ABC):
    """
    Base Class of Sorter used to force structure of Sorter

    Args:
        ABC (ABC): Derived from Abstract Base Class
    """

    def __init__(self):
        """
        Initialiser of for Sorter
        """
        self.dip_calculator_label = "DipCalculatorBaseClass"

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.dip_calculator_label

    @beartype.beartype
    @abstractmethod
    def compute(self, points: list):
        """
        Execute dip calculator method (abstract method)

        Args:
            points (list): list of points to compute dip

        Returns:
            list: dip value
        """
        pass


class DipCalculator(BaseDipCalculator):
    """
    DipCalculator class used to calculate dip of a plane

    Args:
        DipCalculator (BaseDipCalculator): Derived from BaseDipCalculator
    """

    def __init__(self):
        """
        Initialiser of DipCalculator
        """
        super().__init__()
        self.dip_calculator_label = "DipCalculator"
        self.data = None
        self.dip = None

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.dip_calculator_label

    @beartype.beartype
    def compute(self, points: list):
        """
        Execute dip calculator method

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
