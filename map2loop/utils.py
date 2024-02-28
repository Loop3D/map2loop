import numpy
from math import radians, degrees, atan2, asin


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
    nx (float): The x-component of the normal vector.
    ny (float): The y-component of the normal vector.
    nz (float): The z-component of the normal vector.

    Returns:
    dip (float): The dip angle in degrees, ranging from 0 to 90.
    dipdir (float): The dip direction in degrees, ranging from 0 to 360.

    """

    # Calculate the dip direction in degrees, ranging from 0 to 360
    dipdir = degrees(atan2(nx, ny)) % 360

    # Calculate the dip angle in degrees, ranging from 0 to 90
    dip = 90 - degrees(asin(nz))

    # If the dip angle is greater than 90 degrees, adjust the dip and dip direction
    if dip > 90:
        dip = 180 - dip
        dipdir = dipdir + 180

    # Ensure the dip direction is within the range of 0 to 360 degrees
    dipdir = dipdir % 360

    return dip, dipdir
