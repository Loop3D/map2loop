#internal imports
from .m2l_enums import Datatype

#external imports
import beartype as beartype
from beartype.typing import Tuple
import geopandas
import shapely
import pandas

from .logging import getLogger
logger = getLogger(__name__)  

@beartype.beartype
def check_geology_fields_validity(mapdata) -> tuple[bool, str]:
    #TODO (AR) - add check for gaps in geology data
    """
    Validate the columns in GEOLOGY geodataframe

    Several checks to ensure that the geology data:
    - Is loaded and valid.
    - Contains required columns with appropriate types and no missing or blank values.
    - Has optional columns with valid types, if present.
    - Does not contain duplicate in IDs.
    - Ensures the geometry column has valid geometries.

    Returns:
        Tuple[bool, str]: A tuple indicating success (False) or failure (True)
    """
    # Check if geology data is loaded and valid
    if (
        mapdata.raw_data[Datatype.GEOLOGY] is None
        or type(mapdata.raw_data[Datatype.GEOLOGY]) is not geopandas.GeoDataFrame
    ):
        logger.error("GEOLOGY data is not loaded or is not a valid GeoDataFrame")
        return (True, "GEOLOGY data is not loaded or is not a valid GeoDataFrame")
    
    geology_data = mapdata.raw_data[Datatype.GEOLOGY]
    config = mapdata.config.geology_config
    
    # 1. Check geometry validity - tested & working
    if not geology_data.geometry.is_valid.all():
        logger.error("Invalid geometries found. Please fix those before proceeding with map2loop processing")
        return (True, "Invalid geometries found in datatype GEOLOGY")

    # # 2. Required Columns & are they str, and then empty or null? 
    required_columns = [config["unitname_column"], config["alt_unitname_column"]]
    for col in required_columns:
        if col not in geology_data.columns:
            logger.error(f"Datatype GEOLOGY: Required column with config key: '{[k for k, v in config.items() if v == col][0]}' is missing from geology data.")
            return (True, f"Datatype GEOLOGY: Required column with config key: '{[k for k, v in config.items() if v == col][0]}' is missing from geology data.")
        if not geology_data[col].apply(lambda x: isinstance(x, str)).all():
            config_key = [k for k, v in config.items() if v == col][0]
            logger.error(f"Datatype GEOLOGY: Column '{config_key}' must contain only string values. Please check that the column contains only string values.")
            return (True, f"Datatype GEOLOGY: Column '{config_key}' must contain only string values. Please check that the column contains only string values.")
        if geology_data[col].isnull().any() or geology_data[col].str.strip().eq("").any():
            config_key = [k for k, v in config.items() if v == col][0]
            logger.error(f"Datatype GEOLOGY: NaN or blank values found in required column '{config_key}'. Please double check the column for blank values.")
            return (True, f"Datatype GEOLOGY: NaN or blank values found in required column '{config_key}'. Please double check the column for blank values.")

    # # 3. Optional Columns
    optional_string_columns = [
        "group_column", "supergroup_column", "description_column",
        "rocktype_column", "alt_rocktype_column",
    ]
    
    for key in optional_string_columns:
        if key in config and config[key] in geology_data.columns:
            if not geology_data[config[key]].apply(lambda x: isinstance(x, str)).all():
                logger.warning(
                    f"Datatype GEOLOGY: Optional column '{config[key]}' (config key: '{key}') contains non-string values. "
                    "Map2loop processing might not work as expected."
                )

    optional_numeric_columns = ["minage_column", "maxage_column", "objectid_column"]
    for key in optional_numeric_columns:
        if key in config and config[key] in geology_data.columns:
            if not geology_data[config[key]].apply(lambda x: isinstance(x, (int, float))).all():
                logger.warning(
                    f"Datatype GEOLOGY: Optional column '{config[key]}' (config key: '{key}') contains non-numeric values. "
                    "Map2loop processing might not work as expected."
        )
    
    # # 4. Check for duplicates in ID
    if "objectid_column" in config and config["objectid_column"] in geology_data.columns:
        objectid_values = geology_data[config["objectid_column"]]
        
        # Check for None, NaN, or other null-like values
        if objectid_values.isnull().any():
            logger.error(
                f"Datatype GEOLOGY: Column '{config['objectid_column']}' (config key: 'objectid_column') contains NaN or null values. Ensure all values are valid and non-null."
            )
            return (True, f"Datatype GEOLOGY: Column '{config['objectid_column']}' (config key: 'objectid_column') contains NaN or null values.")
        
        # Check for duplicate values
        if objectid_values.duplicated().any():
            logger.error(
                f"Datatype GEOLOGY: Duplicate values found in column '{config['objectid_column']}' (config key: 'objectid_column'). Please make sure that the column contains unique values."
            )
            return (True, f"Datatype GEOLOGY: Duplicate values found in column '{config['objectid_column']}' (config key: 'objectid_column').")
        
        # Check for uniqueness
        if not objectid_values.is_unique:
            logger.error(
                f"Datatype GEOLOGY: Column '{config['objectid_column']}' (config key: 'objectid_column') contains non-unique values. Ensure all values are unique."
            )
            return (True, f"Datatype GEOLOGY: Column '{config['objectid_column']}' (config key: 'objectid_column') contains non-unique values.")


    # 5. Check for NaNs/blanks in optional fields with warnings
    warning_fields = [
        "group_column", "supergroup_column", "description_column",
        "rocktype_column", "minage_column", "maxage_column",
    ]
    for key in warning_fields:
        col = config.get(key)
        if col and col in geology_data.columns:
            # Check if column contains string values before applying `.str`
            if pandas.api.types.is_string_dtype(geology_data[col]):
                if geology_data[col].isnull().any() or geology_data[col].str.strip().eq("").any():
                    logger.warning(
                        f"Datatype GEOLOGY: NaN or blank values found in optional column '{col}' (config key: '{key}')."
                    )
            else:
                # Non-string columns, check only for NaN values
                if geology_data[col].isnull().any():
                    logger.warning(
                        f"Datatype GEOLOGY: NaN values found in optional column '{col}' (config key: '{key}')."
                    )


    logger.info("Geology fields validation passed.")
    return (False, "")

@beartype.beartype
def check_structure_fields_validity(mapdata) -> Tuple[bool, str]:
    """
    Validate the structure data for required and optional fields.

    Performs the following checks:
    - Ensures the structure map is loaded, valid, and contains at least two structures.
    - Validates the geometry column
    - Checks required numeric columns (`dip_column`, `dipdir_column`) for existence, dtype, range, and null values.
    - Checks optional string columns (`description_column`, `overturned_column`) for type and null/empty values.
    - Validates the optional numeric `objectid_column` for type, null values, and duplicates.

    Returns:
        Tuple[bool, str]: A tuple where the first value indicates if validation failed (True = failed),
                        and the second value provides a message describing the issue.
    """
    
    # Check type and size of loaded structure map
    if (
        mapdata.raw_data[Datatype.STRUCTURE] is None
        or type(mapdata.raw_data[Datatype.STRUCTURE]) is not geopandas.GeoDataFrame
    ):
        logger.warning("Structure map is not loaded or valid")
        return (True, "Structure map is not loaded or valid")

    if len(mapdata.raw_data[Datatype.STRUCTURE]) < 2:
        logger.warning(
            "Datatype STRUCTURE: map does with not enough orientations to complete calculations (need at least 2), projection may be inconsistent"
        )
    
    structure_data = mapdata.raw_data[Datatype.STRUCTURE]
    config = mapdata.config.structure_config

    # 1. Check geometry validity
    if not structure_data.geometry.is_valid.all():
        logger.error("datatype STRUCTURE: Invalid geometries found. Please fix those before proceeding with map2loop processing")
        return (True, "Invalid geometries found in datatype STRUCTURE")

    # 2. Check mandatory numeric columns
    required_columns = [config["dipdir_column"], config["dip_column"]]
    for col in required_columns:
        if col not in structure_data.columns:
            logger.error(f"DDatatype STRUCTURE: Required column with config key: '{[k for k, v in config.items() if v == col][0]}' is missing from structure data.")
            return (True, f"Datatype STRUCTURE: Required column with config key: '{[k for k, v in config.items() if v == col][0]}' is missing from structure data.")
        if not structure_data[col].apply(lambda x: isinstance(x, (int, float))).all():
            config_key = [k for k, v in config.items() if v == col][0]
            logger.error(f"Datatype STRUCTURE: Column '{config_key}' must contain only numeric values. Please check that the column contains only numeric values.")
            return (True, f"Datatype STRUCTURE: Column '{config_key}' must contain only numeric values. Please check that the column contains only numeric values.")
        if structure_data[col].isnull().any():
            config_key = [k for k, v in config.items() if v == col][0]
            logger.error(f"Datatype STRUCTURE: NaN or blank values found in required column '{config_key}'. Please double check the column for blank values.")
            return (True, f"Datatype STRUCTURE: NaN or blank values found in required column '{config_key}'. Please double check the column for blank values.")

    if config["dip_column"] in structure_data.columns:
        invalid_dip = ~((structure_data[config["dip_column"]] >= 0) & (structure_data[config["dip_column"]] <= 90))
        if invalid_dip.any():
            logger.warning(
                f"Datatype STRUCTURE: Column '{config['dip_column']}' has values that are not between 0 and 90 degrees. Is this intentional?"
            )

    if config["dipdir_column"] in structure_data.columns:
        invalid_dipdir = ~((structure_data[config["dipdir_column"]] >= 0) & (structure_data[config["dipdir_column"]] <= 360))
        if invalid_dipdir.any():
            logger.warning(
                f"Datatype STRUCTURE: Column '{config['dipdir_column']}' has values that are not between 0 and 360 degrees. Is this intentional?"
            )
    
    # check validity of optional string columns
    optional_string_columns = ["description_column", "overturned_column"]
    for key in optional_string_columns:
        if key in config and config[key] in structure_data.columns:
            column_name = config[key]
            if not structure_data[column_name].apply(lambda x: isinstance(x, str) or pandas.isnull(x)).all():
                logger.warning(
                    f"Datatype STRUCTURE: Optional column with config key: '{key}' contains non-string values. "
                    "Map2loop processing might not work as expected."
                )
            if structure_data[column_name].isnull().any() or structure_data[column_name].str.strip().eq("").any():
                logger.warning(
                    f"Datatype STRUCTURE: Optional column config key: '{key}' contains NaN, empty, or null values. "
                    "Map2loop processing might not work as expected."
        )

    # check ID column for type, null values, and duplicates
    optional_numeric_column_key = "objectid_column"
    optional_numeric_column = config.get(optional_numeric_column_key)

    if optional_numeric_column:
        if optional_numeric_column in structure_data.columns:
            # Check for non-integer values
            if not structure_data[optional_numeric_column].apply(lambda x: isinstance(x, int) or pandas.isnull(x)).all():
                logger.error(
                    f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains non-integer values. Rectify this, or remove this column from the config - map2loop will generate a new ID."
                )
                return (True, f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains non-integer values.")
            # Check for NaN
            if structure_data[optional_numeric_column].isnull().any():
                logger.error(
                    f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains NaN values. Rectify this, or remove this column from the config - map2loop will generate a new ID."
                )
                return (True, f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains NaN values.")
            # Check for duplicates
            if structure_data[optional_numeric_column].duplicated().any():
                logger.error(
                    f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains duplicate values. Rectify this, or remove this column from the config - map2loop will generate a new ID."
                )
                return (True, f"Datatype STRUCTURE: ID column '{optional_numeric_column}' (config key: '{optional_numeric_column_key}') contains duplicate values.")

    return (False, "")

@beartype.beartype
def check_fault_fields_validity(mapdata) -> Tuple[bool, str]:
    
    # Check type of loaded fault map
    if (
        mapdata.raw_data[Datatype.FAULT] is None
        or type(mapdata.raw_data[Datatype.FAULT]) is not geopandas.GeoDataFrame
    ):
        logger.warning("Fault map is not loaded or valid")
        return (True, "Fault map is not loaded or valid")
    
    fault_data = mapdata.raw_data[Datatype.FAULT]
    config = mapdata.config.fault_config
    
    # Check geometry
    if not fault_data.geometry.is_valid.all():
        logger.error("datatype FAULT: Invalid geometries found. Please fix those before proceeding with map2loop processing")
        return (True, "Invalid geometries found in FAULT data.")

    # Check for LineString or MultiLineString geometries
    if not fault_data.geometry.apply(lambda geom: isinstance(geom, (shapely.LineString, shapely.MultiLineString))).all():
        invalid_types = fault_data[~fault_data.geometry.apply(lambda geom: isinstance(geom, (shapely.LineString, shapely.MultiLineString)))]
        logger.error(
            f"FAULT data contains invalid geometry types. Rows with invalid geometry types: {invalid_types.index.tolist()}"
        )
        return (True, "FAULT data contains geometries that are not LineString or MultiLineString.")
    
    # Check "structtype_column" if it exists
    if "structtype_column" in config:
        structtype_column = config["structtype_column"]

        # Ensure the column exists in the data
        if structtype_column not in fault_data.columns:
            logger.warning(
                f"Datatype FAULT: '{structtype_column}' (config key: 'structtype_column') is missing from the fault data. Consider removing that key from the config"
            )
        else:
        # Check if all entries in the column are strings
            if not fault_data[structtype_column].apply(lambda x: isinstance(x, str) or pandas.isnull(x)).all():
                logger.error(
                    f"Datatype FAULT: Column '{structtype_column}' (config key: 'structtype_column') contains non-string values. Please ensure all values in this column are strings."
                )
                return (True, f"Datatype FAULT: Column '{structtype_column}' (config key: 'structtype_column') contains non-string values.")

            # Warn about empty or null cells
            if fault_data[structtype_column].isnull().any() or fault_data[structtype_column].str.strip().eq("").any():
                logger.warning(
                    f"Datatype FAULT: Column '{structtype_column}' contains NaN, empty, or blank values. Processing might not work as expected."
                )

    # Check if "fault_text" is defined and contained in the column
    fault_text = config.get("fault_text", None)

    # Check if the structtype_column exists in the fault_data
    if structtype_column not in fault_data.columns:
        logger.warning(
            f"Datatype FAULT: The column '{structtype_column}' is not present in the fault data."
        )

    else:
        if not fault_data[structtype_column].str.contains(fault_text).any():
            logger.error(
                f"Datatype FAULT: The 'fault_text' value '{fault_text}' is not found in column '{structtype_column}'. Project might end up with no faults"
            )
    
    #checks on name column
    name_column = config.get("name_column")
    if name_column not in fault_data.columns:
        logger.warning(
            f"Datatype FAULT: Column '{name_column}' (config key 'name_column') is missing from the fault data."
            "Please ensure it is present, or remove that key from the config."
        )
    
    if name_column and name_column in fault_data.columns:
        # Check if the column contains non-string values
        if not fault_data[name_column].apply(lambda x: isinstance(x, str) or pandas.isnull(x)).all():
            logger.error(
                f"Datatype FAULT: Column '{name_column}' (config key 'name_column') contains non-string values. Ensure all values are valid strings."
            )
            return (True, f"Datatype FAULT: Column '{name_column}' (config key 'name_column') contains non-string values.")
        
        # Check for NaN values
        if fault_data[name_column].isnull().any():
            logger.warning(
                f"Datatype FAULT: Column '{name_column}' (config key 'name_column') contains NaN or empty values. This may affect processing."
            )
        
        # Check for duplicate values
        if fault_data[name_column].duplicated().any():
            logger.warning(
                f"Datatype FAULT: Column '{name_column}' contains duplicate values. This may affect processing."
            )

    # dips & strikes
    # Check for dips and dip directions
    strike_dips_columns = ["dip_column", "dipdir_column"]

    for key in strike_dips_columns:
        column_name = config.get(key)
        if column_name:  # Only proceed if the config has this key
            if column_name in fault_data.columns:
                
                #coerce to numeric
                fault_data[column_name] = pandas.to_numeric(fault_data[column_name], errors='coerce')
                
                # Check if the column contains only numeric values                    
                if not fault_data[column_name].apply(lambda x: isinstance(x, (int, float)) or pandas.isnull(x)).all():
                    logger.warning(
                        f"Datatype FAULT: Column '{column_name}' (config key {key}) must contain only numeric values. Please ensure the column is numeric."
                    )

                # Check for NaN or empty values
                if fault_data[column_name].isnull().any():
                    logger.warning(
                        f"Datatype FAULT: Column '{column_name}' (config key {key}) contains NaN or empty values. This may affect processing."
                    )

                # Check range constraints
                if key == "dip_column":
                    # Dips must be between 0 and 90
                    invalid_values = ~((fault_data[column_name] >= 0) & (fault_data[column_name] <= 90))
                    if invalid_values.any():
                        logger.warning(
                            f"Datatype FAULT: Column '{column_name}' (config key {key}) contains values outside the range [0, 90]. Was this intentional?"
                        )
                elif key == "dipdir_column":
                    # Dip directions must be between 0 and 360
                    invalid_values = ~((fault_data[column_name] >= 0) & (fault_data[column_name] <= 360))
                    if invalid_values.any():
                        logger.warning(
                            f"Datatype FAULT: Column '{column_name}' (config key {key}) contains values outside the range [0, 360]. Was this intentional?"
                        )
            else:
                logger.warning(
                    f"Datatype FAULT: Column '{column_name}' (config key {key}) is missing from the fault data. Please ensure the column name is correct, or otherwise remove that key from the config."
                )
                
    
    # dip estimates
    dip_estimate_column = config.get("dip_estimate_column")
    valid_directions = [
        "north_east", "south_east", "south_west", "north_west",
        "north", "east", "south", "west"
    ]

    if dip_estimate_column:  
        if dip_estimate_column in fault_data.columns:
            # Ensure all values are in the set of valid directions or are NaN
            invalid_values = fault_data[dip_estimate_column][
                ~fault_data[dip_estimate_column].apply(lambda x: x in valid_directions or pandas.isnull(x))
            ]

            if not invalid_values.empty:
                logger.error(
                    f"Datatype FAULT: Column '{dip_estimate_column}' contains invalid values not in the set of allowed dip estimates: {valid_directions}."
                )
                return (
                    True,
                    f"Datatype FAULT: Column '{dip_estimate_column}' contains invalid values. Allowed values: {valid_directions}.",
                )

            # Warn if there are NaN or empty values
            if fault_data[dip_estimate_column].isnull().any():
                logger.warning(
                    f"Datatype FAULT: Column '{dip_estimate_column}' contains NaN or empty values. This may affect processing."
                )
        else:
            logger.error(
                f"Datatype FAULT: Column '{dip_estimate_column}' is missing from the fault data. Please ensure the column name is correct or remove that key from the config."
            )
            return (True, f"Datatype FAULT: Column '{dip_estimate_column}' is missing from the fault data.")

    # Check ID column
    id_column = config.get("objectid_column")
    
    if id_column:  
        if id_column in fault_data.columns:
            # Check for non-integer values
            # Attempt to coerce the ID column to integers because WA data says so (ARodrigues)
            fault_data[id_column] = pandas.to_numeric(fault_data[id_column], errors='coerce')

            # Check if all values are integers or null after coercion
            if not fault_data[id_column].apply(lambda x: pandas.isnull(x) or isinstance(x, int)).all():
                logger.warning(
                    f"Datatype FAULT: ID column '{id_column}' must contain only integer values. Rectify this or remove the key from the config to auto-generate IDs."
                )
            
            # Check for NaN values
            if fault_data[id_column].isnull().any():
                logger.warning(
                    f"Datatype FAULT: ID column '{id_column}' contains NaN or null values. Rectify this or remove the key from the config to auto-generate IDs."
                )

            # Check for duplicates
            if fault_data[id_column].duplicated().any():
                logger.error(
                    f"Datatype FAULT: ID column '{id_column}' contains duplicate values. Rectify this or remove the key from the config to auto-generate IDs."
                )
    
    return (False, "")


@beartype.beartype
def validate_config_dictionary(config_dict: dict) -> None:
    
    # 1)  check mandatory keys for "structure" and "geology"
    required_keys = {
        "structure": {"dipdir_column", "dip_column"},
        "geology": {"unitname_column", "alt_unitname_column"},
    }

    # Loop over "structure" and "geology"
    for section, keys in required_keys.items():

        # 1) Check that "section" exists
        if section not in config_dict:
            logger.error(f"Missing required section '{section}' in config dictionary.")
            raise ValueError(f"Missing required section '{section}' in config dictionary.")

        # 2) Check that each required key is in config_dict[section]
        for key in keys:
            if key not in config_dict[section]:
                logger.error(f"Missing required key '{key}' for '{section}' section of the config dictionary.")
                raise ValueError(f"Missing required key '{key}' for '{section}' section of the config dictionary.")
    
    # 2) check for legacy keys first:
    legacy_keys = {
        "otype", "dd", "d", "sf", "bedding", "bo", "btype", "gi", "c", "u",
        "g", "g2", "ds", "min", "max", "r1", "r2", "sill", "intrusive", "volcanic",
        "f", "fdipnull", "fdipdip_flag", "fdipdir", "fdip", "fdipest",
        "fdipest_vals", "n", "ff", "t", "syn"
    }

    def check_keys(d: dict, parent_key=""):
        for key, value in d.items():
            if key in legacy_keys:
                logger.error(
                    f"Legacy key found in config - '{key}' at '{parent_key}'. Please use the new config format. Use map2loop.utils.update_from_legacy_file to convert between the formats if needed"
                )
                raise ValueError(
                    f"Legacy key found in config - '{key}' at '{parent_key}'. Please use the new config format. Use map2loop.utils.update_from_legacy_file to convert between the formats if needed"
                )
            if isinstance(value, dict):
                check_keys(value, parent_key=f"{parent_key}{key}.")
    
    check_keys(config_dict)

    # 3) check if all keys are valid:
    allowed_keys_by_section = {
        "structure": {
            "orientation_type", "dipdir_column", "dip_column",
            "description_column", "bedding_text", "overturned_column", "overturned_text",
            "objectid_column", "desciption_column",
        },
        "geology": {
            "unitname_column", "alt_unitname_column", "group_column",
            "supergroup_column", "description_column", "minage_column",
            "maxage_column", "rocktype_column",  "alt_rocktype_column",
            "sill_text", "intrusive_text",  "volcanic_text",   "objectid_column", "ignore_lithology_codes",
        },
        "fault": {
            "structtype_column",  "fault_text",  "dip_null_value",
            "dipdir_flag", "dipdir_column",  "dip_column",  "orientation_type",
            "dipestimate_column",  "dipestimate_text",  "name_column",
            "objectid_column", "minimum_fault_length", "ignore_fault_codes",
        },
        "fold": {
            "structtype_column", "fold_text", "description_column",
            "synform_text", "foldname_column","objectid_column",
        },
    }
    
    for section_name, section_dict in config_dict.items():
        # check section
        if section_name not in allowed_keys_by_section:
            logger.error(f"Unrecognized section '{section_name}' in config dictionary.")
            raise ValueError(f"Unrecognized section '{section_name}' in config dictionary.")

        # check keys
        allowed_keys = allowed_keys_by_section[section_name]
        for key in section_dict.keys():
            if key not in allowed_keys:
                logger.error(f"Key '{key}' is not an allowed key in the '{section_name}' section.")
                raise ValueError(f"Key '{key}' is not an allowed key in the '{section_name}' section.")
    
    # 4) check if minimum fault length is a number
    mfl = config_dict.get("fault", {}).get("minimum_fault_length", None)
    if mfl is not None and not isinstance(mfl, (int, float)):
        logger.error("minimum_fault_length must be a number.")
        raise ValueError(f"minimum_fault_length must be a number, instead got: {type(mfl)}")