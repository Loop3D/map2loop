import numpy as np


def random_colours_hex(n):
    """
    Generate n random colours in hex format.
    """
    rgb = np.random.rand(n, 3)
    return rgb_to_hex(rgb)


def rgb_to_hex(rgb):
    """
    Convert rgb values in the range [0,1] to hex format.
    """
    return [rgb_to_hex_single(r, g, b) for r, g, b in rgb]


def rgb_to_hex_single(r, g, b):
    """
    Convert rgb values in the range [0,1] to hex format.
    """
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
