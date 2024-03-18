import numpy
from shapely.geometry import Point
import beartype


@beartype.beartype
def setup_grid(bounding_box: dict):
    """
    Setup the grid for interpolation

    Args:
        bounding_box

    Returns:
        xi, yi (numpy.ndarray, numpy.ndarray): The x and y coordinates of the grid points.
    """
    # Define the desired cell size
    cell_size = 0.01 * (bounding_box["maxx"] - bounding_box["minx"])

    # Calculate the grid resolution
    grid_resolution = round((bounding_box["maxx"] - bounding_box["minx"]) / cell_size)

    # Generate the grid
    x = numpy.linspace(
        bounding_box["minx"],
        bounding_box["maxx"],
        grid_resolution,
    )
    y = numpy.linspace(
        bounding_box["miny"],
        bounding_box["maxy"],
        grid_resolution,
    )
    xi, yi = numpy.meshgrid(x, y)
    xi = xi.flatten()
    yi = yi.flatten()

    return xi, yi


def strike_dip_vector(strike, dip):
    """
    This function calculates the strike-dip vector from the given strike and dip angles.

    Parameters:
    strike (float or array-like): The strike angle(s) in degrees. Can be a single value or an array of values.
    dip (float or array-like): The dip angle(s) in degrees. Can be a single value or an array of values.

    Returns:
    vec (numpy.ndarray): The calculated strike-dip vector(s). Each row corresponds to a vector,
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


def normal_vector_to_dipdirection_dip(nx, ny, nz):
    """
    This function calculates the dip and dip direction from a normal vector.

    Parameters:
    nx: The x-component of the normal vector.
    ny: The y-component of the normal vector.
    nz: The z-component of the normal vector.

    Returns:
    dip (float): The dip angle in degrees, ranging from 0 to 90.
    dipdir (float): The dip direction in degrees, ranging from 0 to 360.

    """

    # Calculate the dip direction in degrees, ranging from 0 to 360
    dipdir = numpy.degrees(numpy.arctan2(nx, ny)) % 360

    # Calculate the dip angle in degrees, ranging from 0 to 90
    dip = 90 - numpy.degrees(numpy.arcsin(nz))

    # If the dip angle is greater than 90 degrees, adjust the dip and dip direction
    mask = dip > 90
    dip[mask] = 180 - dip[mask]
    dipdir[mask] = (dipdir[mask] + 180) % 360

    # Ensure the dip direction is within the range of 0 to 360 degrees
    dipdir = dipdir % 360

    return dip, dipdir


def create_points(xy):
    points = []
    for x, y in xy:
        point = Point(x, y)
        points.append(point)
    return points
