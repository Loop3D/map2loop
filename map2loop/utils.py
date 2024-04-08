import numpy
import shapely
import beartype
from typing import Union


@beartype.beartype
def generate_grid(bounding_box: dict, grid_resolution: int = None) -> tuple:
    """
    Setup the grid for interpolation

    Args:
        bounding_box (dict): a dictionary containing the bounding box of the map data.
            The bounding box dictionary should comply with the following format: {
                "minx": value,
                "maxx": value,
                "miny": value,
                "maxy": value,
            }
        grid_resolution (int, optional): The number of grid points in the x and y directions. Defaults to None.

    Returns:
        xi, yi (numpy.ndarray, numpy.ndarray): The x and y coordinates of the grid points.
        grid_resolution (int): The number of grid points in the x and y directions.
    """

    # Define the desired cell size
    cell_size = 0.01 * (bounding_box["maxx"] - bounding_box["minx"])

    if grid_resolution is None:
        # Calculate the grid resolution
        grid_resolution = round((bounding_box["maxx"] - bounding_box["minx"]) / cell_size)

    # Generate the grid
    x = numpy.linspace(bounding_box["minx"], bounding_box["maxx"], grid_resolution)
    y = numpy.linspace(bounding_box["miny"], bounding_box["maxy"], grid_resolution)
    xi, yi = numpy.meshgrid(x, y)
    xi = xi.flatten()
    yi = yi.flatten()

    return xi, yi


def strike_dip_vector(strike: Union[float, list, numpy.ndarray],
                      dip: Union[float, list, numpy.ndarray]) -> numpy.ndarray:
    """
    Calculates the strike-dip vector from the given strike and dip angles.

    Args:
        strike (Union[float, list, numpy.ndarray]): The strike angle(s) in degrees. Can be a single value or an array of values.
        dip (Union[float, list, numpy.ndarray]): The dip angle(s) in degrees. Can be a single value or an array of values.

    Returns:
        numpy.ndarray: The calculated strike-dip vector(s). Each row corresponds to a vector,
        and the columns correspond to the x, y, and z components of the vector.

    Note:
        This code is adapted from LoopStructural.
    """

    # Initialize a zero vector with the same length as the input strike and dip angles
    vec = numpy.zeros((len(strike), 3))

    # Convert the strike and dip angles from degrees to radians
    s_r = numpy.deg2rad(strike)
    d_r = numpy.deg2rad(dip)

    # Calculate the x, y, and z components of the strike-dip vector
    vec[:, 0] = numpy.sin(d_r) * numpy.cos(s_r)
    vec[:, 1] = -numpy.sin(d_r) * numpy.sin(s_r)
    vec[:, 2] = numpy.cos(d_r)

    # Normalize the strike-dip vector
    vec /= numpy.linalg.norm(vec, axis=1)[:, None]

    return vec


@beartype.beartype
def normal_vector_to_dipdirection_dip(normal_vector: numpy.ndarray) -> numpy.ndarray:
    """
    Calculates the dip and dip direction from a normal vector.

    Args:
        normal_vector (numpy.ndarray): The normal vector(s) for which to calculate the dip and dip direction.
            Each row corresponds to a vector, and the columns correspond to the x, y, and z components of the vector.

    Returns:
        numpy.ndarray: The calculated dip and dip direction(s). Each row corresponds to a set of dip and dip direction,
        and the columns correspond to the dip and dip direction, respectively.

    Note:
        This code is adapted from LoopStructural.
    """

    # Calculate the dip direction in degrees, ranging from 0 to 360
    dipdir = numpy.degrees(numpy.arctan2(normal_vector[:, 0], normal_vector[:, 1])) % 360

    # Calculate the dip angle in degrees, ranging from 0 to 90
    dip = 90 - numpy.degrees(numpy.arcsin(normal_vector[:, 2]))

    # If the dip angle is greater than 90 degrees, adjust the dip and dip direction
    mask = dip > 90
    dip[mask] = 180 - dip[mask]
    dipdir[mask] = (dipdir[mask] + 180) % 360

    # Ensure the dip direction is within the range of 0 to 360 degrees
    dipdir = dipdir % 360
    dip_dipdir = numpy.array([dip, dipdir]).T

    return dip_dipdir


@beartype.beartype
def create_points(xy: Union[list, tuple, numpy.ndarray]) -> shapely.points:
    """
    Creates a list of shapely Point objects from a list, tuple, or numpy array of coordinates.

    Args:
        xy (Union[list, tuple, numpy.ndarray]): A list, tuple, or numpy array of coordinates,
        where each coordinate contains two elements representing the x and y coordinates of a point.

    Returns:
        shapely.points: A list of Point objects created from the input list of coordinates.
    """
    points = shapely.points(xy)
    return points
