import numpy
import math
import shapely
import geopandas
import beartype
from beartype.typing import Union, Optional, Dict
import pandas
import re
import json

from .logging import getLogger
logger = getLogger(__name__)


@beartype.beartype
def generate_grid(bounding_box: dict, grid_resolution: Optional[int] = None) -> tuple:
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

    return xi, yi, cell_size


def strike_dip_vector(
    strike: Union[list, numpy.ndarray], dip: Union[list, numpy.ndarray]
) -> numpy.ndarray:
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
def create_points(xy: Union[list, tuple, numpy.ndarray]) -> numpy.ndarray:
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


@beartype.beartype
def find_segment_strike_from_pt(
    line: shapely.LineString, point: shapely.Point, measurement: pandas.Series
) -> float:
    """
    Finds the strike of a line segment (contact) closest to a given point (structural measurement).

    Parameters:
    line (shapely.geometry.LineString): The line segment (from sampled_contacts)
    point (shapely.geometry.Point): The point representing the structural measurement
    measurement (Geoseries): sampled_contacts.iloc[i, :], where i is a given row number.

    Returns:
    float: The strike of the line segment closer to the point
    """

    lines = []
    for c1, c2 in zip(line.coords, line.coords[1:]):
        lines.append(shapely.LineString([c1, c2]))
    distances = [segment.distance(point) for segment in lines]
    nearest_line = lines[distances.index(min(distances))]

    if 0 <= measurement['DIPDIR'] <= 180:
        # 1 is the upper point
        # find the index point in seg a that has highest y value
        idx1 = numpy.argmin(nearest_line.coords.xy[1])
        x1 = nearest_line.coords.xy[0][idx1]
        y1 = nearest_line.coords.xy[1][idx1]
        idx2 = numpy.argmax(nearest_line.coords.xy[1])
        x2 = nearest_line.coords.xy[0][idx2]
        y2 = nearest_line.coords.xy[1][idx2]

    if 180 < measurement['DIPDIR'] <= 360:
        # 1 is the lower point
        idx1 = numpy.argmax(nearest_line.coords.xy[1])
        x1 = nearest_line.coords.xy[0][idx1]
        y1 = nearest_line.coords.xy[1][idx1]
        idx2 = numpy.argmin(nearest_line.coords.xy[1])
        x2 = nearest_line.coords.xy[0][idx2]
        y2 = nearest_line.coords.xy[1][idx2]

    strike = numpy.degrees(math.atan2((x2 - x1), (y2 - y1))) % 360
    return strike


@beartype.beartype
def calculate_endpoints(
    start_point: shapely.Point, azimuth_deg: float, distance: int, bbox: pandas.DataFrame
) -> shapely.geometry.LineString:
    """
    Calculate the endpoints of a line segment given a start point, azimuth angle, distance, and bounding box.

    Parameters:
    start_point (tuple): The coordinates of the start point (x, y).
    azimuth_deg (float): The azimuth angle in degrees.
    distance (float): The distance of the line segment.
    bbox (dict): The bounding box coordinates (minx, miny, maxx, maxy).

    Returns:
    shapely.LineString: A LineString object representing the line segment with endpoints clipped by the bounding box.
    """
    bbox = numpy.array(bbox)[0]
    minx, miny, maxx, maxy = bbox[0], bbox[1], bbox[2], bbox[3]
    x, y = start_point.coords[0]
    azimuth_rad = math.radians(90 - azimuth_deg)

    # Calculate the perpendicular azimuths in radians
    right_azimuth_rad = (azimuth_rad + math.pi / 2) % (2 * math.pi)
    left_azimuth_rad = (azimuth_rad - math.pi / 2) % (2 * math.pi)

    # Calculate offsets for the right-hand perpendicular direction
    dx_right = distance * math.cos(right_azimuth_rad)
    dy_right = distance * math.sin(right_azimuth_rad)
    right_endpoint = (x + dx_right, y + dy_right)

    # Calculate offsets for the left-hand perpendicular direction
    dx_left = distance * math.cos(left_azimuth_rad)
    dy_left = distance * math.sin(left_azimuth_rad)
    left_endpoint = (x + dx_left, y + dy_left)

    line = shapely.LineString([left_endpoint, right_endpoint])

    new_line = shapely.ops.clip_by_rect(line, minx, miny, maxx, maxy)

    return new_line


@beartype.beartype
def multiline_to_line(
    geometry: Union[shapely.geometry.LineString, shapely.geometry.MultiLineString]
) -> shapely.geometry.LineString:
    """
    Converts a multiline geometry to a single line geometry.

    Args:
        geometry (Union[LineString, MultiLineString]): The input geometry to be converted.

    Returns:
        LineString: The converted line geometry.
    """
    if isinstance(geometry, shapely.LineString):
        return geometry
    coords = [list(part.coords) for part in geometry.geoms]
    flat_coords = [shapely.Point(*point) for segment in coords for point in segment]
    return shapely.LineString(flat_coords)


@beartype.beartype
def rebuild_sampled_basal_contacts(
    basal_contacts: geopandas.GeoDataFrame, sampled_contacts: pandas.DataFrame
) -> geopandas.GeoDataFrame:
    """
    Rebuilds the basal contacts as linestrings --> sampled_basal_contacts, based on the existing sampled contact points.
    The rebuild process uses the featureId column in the sampled_contacts DataFrame to find contacts that may be represented as multiline geometries.

    Parameters:
        basal_contacts (geopandas.GeoDataFrame): A GeoDataFrame containing the original basal contacts (based on full contact data).
        sampled_contacts (DataFrame): A DataFrame containing the sampled contact points with columns 'X' and 'Y' for coordinates, 'featureId' for segment number, and 'ID'.

    Returns:
        geopandas.GeoDataFrame: A new GeoDataFrame containing sampled_basal_contacts: unique basal units and their corresponding LineString or
        MultiLineString geometries, rebuilt from the sampled_contacts.
    """

    sampled_geology = geopandas.GeoDataFrame(
        sampled_contacts,
        geometry=geopandas.points_from_xy(sampled_contacts.X, sampled_contacts.Y),
        crs=basal_contacts.crs,
    )

    basal_contacts.loc[:, 'geometry'] = basal_contacts.buffer(1)
    sampled_basal_contacts = sampled_geology.sjoin(
        basal_contacts, how='left', predicate='intersects'
    ).dropna()

    r = []

    for basal_u in sampled_basal_contacts['basal_unit'].unique():

        subset = sampled_basal_contacts[sampled_basal_contacts['basal_unit'] == basal_u]
        unique_segments = subset['featureId'].unique()

        if len(unique_segments) == 1:
            # make a linestring with all the points in subset
            line = shapely.LineString(subset.geometry)
            r.append(line)

        else:
            lines = []
            # Process each segment number
            for featureId in unique_segments:
                seg_subset = subset[subset['featureId'] == featureId]
                if len(seg_subset) > 1:  # Ensure each segment has at least two points
                    line_ = shapely.LineString(seg_subset.geometry.tolist())
                    lines.append(line_)

            # If multiple lines were created, combine them into a MultiLineString
            if lines:
                line = shapely.MultiLineString(lines)
                r.append(line)

    sampled_basal_contacts = geopandas.GeoDataFrame(
        sampled_basal_contacts['basal_unit'].unique(),
        geometry=r,
        crs=basal_contacts.crs,
        columns=['basal_unit'],
    )

    return sampled_basal_contacts


@beartype.beartype
def generate_random_hex_colors(n: int, seed: int = None) -> list:
    """
    Generate a list of unique random hex color codes.

    Args:
        n (int): The number of random hex color codes to generate.

    Returns:
        list: A list of randomly generated hex color codes as strings.

    Example:
        >>> generate_random_hex_colors(3)
        ['#1a2b3c', '#4d5e6f', '#7f8e9d']
    """
    if not isinstance(n, int):
        raise TypeError(
            "n of colours must be an integer"
        )  ## not sure if necessary as beartype should handle this

    if seed is not None:
        rng = numpy.random.default_rng(seed)
    else:
        rng = numpy.random.default_rng(123456)

    colors = set()  # set prevents duplicates

    while len(colors) < n:
        color = "#{:06x}".format(rng.integers(0, 0xFFFFFF))
        colors.add(color)
    return list(colors)


@beartype.beartype
def hex_to_rgb(hex_color: str) -> tuple:
    """
    Convert a hex color code to an RGBA tuple.
    Args:
        hex_color (str): The hex color code (e.g., "#RRGGBB" or "#RGB").
        alpha (float, optional): The alpha value (opacity) for the color. Defaults to 1.0.
    Returns:
        tuple: A tuple (r, g, b, a) where r, g, b are in the range 0-1 and a is in the range 0-1.
    """
    # if input not string or starts with '#', raise error
    if not isinstance(hex_color, str) or not hex_color.startswith('#'):
        raise ValueError("Invalid hex color code. Must start with '#'.")

    # Remove '#' from the hex color code
    hex_color = hex_color.lstrip('#')

    # check if hex color code is the right length
    if len(hex_color) not in [3, 6]:
        raise ValueError("Invalid hex color code. Must be 3 or 6 characters long after '#'.")

    # Handle short hex code (e.g., "#RGB")
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])

    alpha = 1.0
    # Convert the hex color code to an RGBA tuple// if it fails, return error
    try:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0

    except ValueError as e:
        raise ValueError("Invalid hex color code. Contains non-hexadecimal characters.") from e

    return (r, g, b, alpha)


@beartype.beartype
def calculate_minimum_fault_length(
    bbox: dict[str, int | float], area_percentage: float
) -> float:

    """
    Calculate the minimum fault length based on the map bounding box and a given area percentage.

    Args:
        bbox (dict): A dictionary with keys 'minx', 'miny', 'maxx', 'maxy' representing the bounding box in meters.
        area_percentage (float): The percentage of the bounding box area to use for calculating the threshold length.

    Returns:
        float: The calculated minimum fault length as the square root of the threshold area.
    """

    # Calculate the width and height of the bounding box in meters
    width = bbox['maxx'] - bbox['minx']
    height = bbox['maxy'] - bbox['miny']

    # Calculate the total bounding box area
    bbox_area = width * height

    # Calculate the threshold area based on the given percentage
    threshold_area = area_percentage * bbox_area

    # Return the square root of the threshold area as the minimum fault length
    return threshold_area**0.5


def preprocess_hjson_to_json(hjson_content):
    # Remove comments
    hjson_content = re.sub(r'#.*', '', hjson_content)
    hjson_content = re.sub(r'//.*', '', hjson_content)
    # Replace single quotes with double quotes
    hjson_content = re.sub(r"(?<!\\)'", '"', hjson_content)
    # Ensure keys are enclosed in double quotes
    hjson_content = re.sub(r'(?<!")([a-zA-Z0-9_]+)\s*:', r'"\1":', hjson_content)
    # Fix trailing commas
    hjson_content = re.sub(r',\s*([\]}])', r'\1', hjson_content)
    # Remove unnecessary whitespace
    hjson_content = re.sub(r'\s+', ' ', hjson_content.strip())
    return hjson_content


@beartype.beartype
def read_hjson_with_json(file_path: str) -> dict:
    try:
        # Read the file
        with open(file_path, "r", encoding="utf-8") as file:
            hjson_content = file.read()
        if not hjson_content.strip():
            raise ValueError("The HJSON file is empty.")
        # Preprocess HJSON to JSON
        preprocessed_content = preprocess_hjson_to_json(hjson_content)
        # Parse JSON
        return json.loads(preprocessed_content)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"HJSON file not found: {file_path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode preprocessed HJSON as JSON: {e}") from e
    
@beartype.beartype
def update_from_legacy_file(
    filename: str,
    json_save_path: Optional[str] = None,
    lower: bool = False
) -> Optional[Dict[str, Dict]]:
    """
    Update the config dictionary from the provided old version dictionary
    Args:
        filename (str): the path to the legacy file
        json_save_path (str, optional): the path to save the updated json file. Defaults to None.
        lower (bool, optional): whether to convert all strings to lowercase. Defaults to False.
        
    Returns:
        Dict[Dict]: the updated config dictionary
    
    Example:
        from map2loop.utils import update_from_legacy_file
        update_from_legacy_file(filename=r"./source_data/example.hjson")
    """
    # only import config if needed
    from .config import Config
    file_map = Config()
    
    code_mapping = {
        "otype": (file_map.structure_config, "orientation_type"),
        "dd": (file_map.structure_config, "dipdir_column"),
        "d": (file_map.structure_config, "dip_column"),
        "sf": (file_map.structure_config, "description_column"),
        "bedding": (file_map.structure_config, "bedding_text"),
        "bo": (file_map.structure_config, "overturned_column"),
        "btype": (file_map.structure_config, "overturned_text"),
        "gi": (file_map.structure_config, "objectid_column"),
        "c": (file_map.geology_config, "unitname_column"),
        "u": (file_map.geology_config, "alt_unitname_column"),
        "g": (file_map.geology_config, "group_column"),
        "g2": (file_map.geology_config, "supergroup_column"),
        "ds": (file_map.geology_config, "description_column"),
        "min": (file_map.geology_config, "minage_column"),
        "max": (file_map.geology_config, "maxage_column"),
        "r1": (file_map.geology_config, "rocktype_column"),
        "r2": (file_map.geology_config, "alt_rocktype_column"),
        "sill": (file_map.geology_config, "sill_text"),
        "intrusive": (file_map.geology_config, "intrusive_text"),
        "volcanic": (file_map.geology_config, "volcanic_text"),
        "f": (file_map.fault_config, "structtype_column"),
        "fault": (file_map.fault_config, "fault_text"),
        "fdipnull": (file_map.fault_config, "dip_null_value"),
        "fdipdip_flag": (file_map.fault_config, "dipdir_flag"),
        "fdipdir": (file_map.fault_config, "dipdir_column"),
        "fdip": (file_map.fault_config, "dip_column"),
        "fdipest": (file_map.fault_config, "dipestimate_column"),
        "fdipest_vals": (file_map.fault_config, "dipestimate_text"),
        "n": (file_map.fault_config, "name_column"),
        "ff": (file_map.fold_config, "structtype_column"),
        "fold": (file_map.fold_config, "fold_text"),
        "t": (file_map.fold_config, "description_column"),
        "syn": (file_map.fold_config, "synform_text"),
    }
    # try and ready the file:
    try:
        parsed_data = read_hjson_with_json(filename)
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        return
    #map the keys 
    file_map = file_map.to_dict()
    for legacy_key, new_mapping in code_mapping.items():
        if legacy_key in parsed_data:
            section, new_key = new_mapping
            value = parsed_data[legacy_key]
            if lower and isinstance(value, str):
                value = value.lower()
            section[new_key] = value
    
    if "o" in parsed_data:
        object_id_value = parsed_data["o"]
        if lower and isinstance(object_id_value, str):
            object_id_value = object_id_value.lower()
        file_map['structure']["objectid_column"] = object_id_value
        file_map['geology']["objectid_column"] = object_id_value
        file_map['fold']["objectid_column"] = object_id_value 
        
    if json_save_path is not None:
        with open(json_save_path, "w") as f:
            json.dump(parsed_data, f, indent=4)
    
    return file_map
