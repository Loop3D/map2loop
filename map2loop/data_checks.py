#internal imports
from .m2l_enums import Datatype

#external imports
import beartype as beartype
from beartype.typing import Tuple, List
import geopandas
import shapely
import pandas

from .logging import getLogger
logger = getLogger(__name__)  

@beartype.beartype
def check_geology_fields_validity(mapdata) -> tuple[bool, str]:
    #TODO (AR) - add check for gaps in geology data (inspo here: https://medium.com/@achm.firmansyah/an-approach-for-checking-overlaps-and-gaps-in-polygons-using-geopandas-ebd6606e7f70 )
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
    
    # 2. Validate geometry
    failed, message = validate_geometry(
        geodata=geology_data,
        expected_geom_types=[shapely.Polygon, shapely.MultiPolygon],
        datatype_name="GEOLOGY"
    )
    if failed:
        return (failed, message)
    
    # # 3. Required Columns & are they str, and then empty or null? 
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
    
    # # 4. check ID column
    if "objectid_column" in config:
        id_validation_failed, id_message = validate_id_column(
            geodata=geology_data,
            config=config,
            id_config_key="objectid_column", 
            geodata_name="GEOLOGY")
        
        if id_validation_failed:
            return (id_validation_failed, id_message)

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

    # 2. Validate geometry
    failed, message = validate_geometry(
        geodata=structure_data,
        expected_geom_types=[shapely.Point, shapely.MultiPoint],
        datatype_name="STRUCTURE"
    )
    if failed:
        return (failed, message)
    
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

    # check ID column 
    if "objectid_column" in config:
        id_validation_failed, id_message = validate_id_column(
            geodata=structure_data,
            config=config,
            id_config_key="objectid_column", 
            geodata_name="STRUCTURE")
        
        if id_validation_failed:
            return (id_validation_failed, id_message)
        
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
    
    # 2. Validate geometry
    failed, message = validate_geometry(
        geodata=fault_data,
        expected_geom_types=[shapely.LineString, shapely.MultiLineString],
        datatype_name="FAULT"
    )
    if failed:
        return (failed, message)
    
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

    
    # # 4. check ID column
    if "objectid_column" in config:
        id_validation_failed, id_message = validate_id_column(
            geodata=fault_data,
            config=config,
            id_config_key="objectid_column", 
            geodata_name="FAULT")
        
        if id_validation_failed:
            return (id_validation_failed, id_message)
    
    return (False, "")

@beartype.beartype
def check_fold_fields_validity(mapdata) -> Tuple[bool, str]:
    # Check type of loaded fold map
    if (
        mapdata.raw_data[Datatype.FOLD] is None
        or type(mapdata.raw_data[Datatype.FOLD]) is not geopandas.GeoDataFrame
    ):
        logger.warning("Fold map is not loaded or valid")
        return (True, "Fold map is not loaded or valid")

    folds = mapdata.raw_data[Datatype.FOLD]
    config = mapdata.config.fold_config

    # Debugging: Print column names in the fold_data
    logger.debug(f"Fold data columns: {folds.columns.tolist()}")

    # 2. Validate geometry
    failed, message = validate_geometry(
        geodata=folds,
        expected_geom_types=[shapely.LineString, shapely.MultiLineString],
        datatype_name="FOLD"
    )
    if failed:
        return (failed, message)
    
    # Check "structtype_column" if it exists
    if "structtype_column" in config:
        structtype_column = config["structtype_column"]

        # Ensure the column exists in the data
        if structtype_column not in folds.columns:
            logger.warning(
                f"Datatype FOLD: '{structtype_column}' (config key: 'structtype_column') is missing from the fold data. Consider removing that key from the config"
            )
            return (True, f"Column '{structtype_column}' is missing from the fold data.")
        else:
            # Check if all entries in the column are strings
            if not folds[structtype_column].apply(lambda x: isinstance(x, str) or pandas.isnull(x)).all():
                logger.error(
                    f"Datatype FOLD: Column '{structtype_column}' (config key: 'structtype_column') contains non-string values. Please ensure all values in this column are strings."
                )
                return (True, f"Datatype FOLD: Column '{structtype_column}' (config key: 'structtype_column') contains non-string values.")

            # Warn about empty or null cells
            if folds[structtype_column].isnull().any() or folds[structtype_column].str.strip().eq("").any():
                logger.warning(
                    f"Datatype FOLD: Column '{structtype_column}' contains NaN, empty, or blank values. Processing might not work as expected."
                )
            
            # Check if "fold_text" is defined and contained in the column
            fold_text = config.get("fold_text", None)
            if fold_text:
                
                # check if fold text is a string
                if not isinstance(fold_text, str):
                    logger.error("Datatype FOLD: 'fold_text' must be a string. Please ensure it is defined correctly in the config.")
                    return (True, "Datatype FOLD: 'fold_text' must be a string.")
                #check if it exists in the column strtype
                if not folds[structtype_column].str.contains(fold_text, na=False).any():
                    logger.error(f"Datatype FOLD: The 'fold_text' value '{fold_text}' is not found in column '{structtype_column}'. This may impact processing.")
                    return (True, f"Datatype FOLD: The 'fold_text' value '{fold_text}' is not found in column '{structtype_column}'.")

            # check synform_text
            synform_text = config.get("synform_text", None)
            if synform_text:
                # Check if synform_text is a string
                if not isinstance(synform_text, str):
                    logger.error("Datatype FOLD: 'synform_text' must be a string. Please ensure it is defined correctly in the config.")
                    return (True, "Datatype FOLD: 'synform_text' must be a string.")
                # Check if it exists in the structtype_column
                if not folds[structtype_column].str.contains(synform_text, na=False).any():
                    logger.warning(
                        f"Datatype FOLD: The 'synform_text' value '{synform_text}' is not found in column '{structtype_column}'. This may impact processing."
                    )
                        
    # check description column
    description_column = config.get("description_column", None)
    if description_column:
        # Ensure the column exists in the data
        if description_column not in folds.columns:
            logger.warning(
                f"Datatype FOLD: Column '{description_column}' (config key: 'description_column') is missing from the fold data. Consider removing that key from the config."
            )
        else:
            # Check if all entries in the column are strings
            if not folds[description_column].apply(lambda x: isinstance(x, str) or pandas.isnull(x)).all():
                logger.error(
                    f"Datatype FOLD: Column '{description_column}' (config key: 'description_column') contains non-string values. Please ensure all values in this column are strings."
                )
                return (True, f"Datatype FOLD: Column '{description_column}' (config key: 'description_column') contains non-string values.")

            # Warn about empty or null cells
            if folds[description_column].isnull().any() or folds[description_column].str.strip().eq("").any():
                logger.warning(
                    f"Datatype FOLD: Column '{description_column}' contains NaN, empty, or blank values. Processing might not work as expected."
                )


    # # 4. check ID column
    if "objectid_column" in config:
        id_validation_failed, id_message = validate_id_column(
            geodata=folds,
            config=config,
            id_config_key="objectid_column", 
            geodata_name="FOLD")
        
        if id_validation_failed:
            return (id_validation_failed, id_message)

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
    
@beartype.beartype
def validate_geometry(
    geodata: geopandas.GeoDataFrame,
    expected_geom_types: List[type],
    datatype_name: str
) -> Tuple[bool, str]:
    """
    Validates the geometry column of a GeoDataFrame.

    Parameters:
        geodata (gpd.GeoDataFrame): The GeoDataFrame to validate.
        expected_geom_types (List[type]): A list of expected Shapely geometry types.
        datatype_name (str): A string representing the datatype being validated (e.g., "GEOLOGY").

    Returns:
        Tuple[bool, str]: A tuple where the first element is a boolean indicating if validation failed,
                          and the second element is an error message if failed.
    """
    # 1. Check if all geometries are valid
    if not geodata.geometry.is_valid.all():
        logger.error(f"Invalid geometries found in datatype {datatype_name}. Please fix them before proceeding.")
        return True, f"Invalid geometries found in datatype {datatype_name}"
    
    # 2. Check if all geometries are of the expected types
    if not geodata.geometry.apply(lambda geom: isinstance(geom, tuple(expected_geom_types))).all():
        invalid_types = geodata[~geodata.geometry.apply(lambda geom: isinstance(geom, tuple(expected_geom_types)))]
        invalid_indices = invalid_types.index.tolist()
        expected_types_names = ', '.join([geom_type.__name__ for geom_type in expected_geom_types])
        logger.error(
            f"Datatype {datatype_name}: Invalid geometry types found. Expected types: {expected_types_names}. "
            f"Rows with invalid types: {invalid_indices}"
        )
        return True, (
            f"Invalid geometry types found in datatype {datatype_name}. "
            f"All geometries must be {expected_types_names}."
        )
    
    # If all checks pass
    logger.debug(f"Geometry validation passed for datatype {datatype_name}")
    return False, ""


@beartype.beartype
def validate_id_column(
    geodata: geopandas.GeoDataFrame,
    config: dict,
    id_config_key: str, 
    geodata_name: str
) -> Tuple[bool, str]:

    # Retrieve the ID column name from the configuration
    id_column = config.get(id_config_key)
    
    if not id_column:
        error_msg = f"Configuration key '{id_config_key}' is missing."
        logger.error(error_msg)
        return (True, error_msg)
    
    if id_column in geodata.columns:
        geodata[id_column] = pandas.to_numeric(geodata[id_column], errors='coerce')
    
        # Check for non-numeric values (which are now NaN after coercion)
        if geodata[id_column].isnull().any():
            error_msg = (
                f"Datatype {geodata_name}: Column '{id_column}' "
                f"(config key: '{id_config_key}') contains non-numeric or NaN values. "
                "Please rectify the values, or remove this key from the config dictionary to let map2loop assign IDs."
            )
            logger.error(error_msg)
            return (True, error_msg)
        
        if not (geodata[id_column] == geodata[id_column].astype(int)).all():
            error_msg = (
                f"Datatype {geodata_name}: Column '{id_column}' "
                f"(config key: '{id_config_key}') contains non-integer values."
            )
            logger.error(error_msg)
            return (True, error_msg)

        if geodata[id_column].duplicated().any():
            error_msg = (
                f"Datatype {geodata_name}: Column '{id_column}' "
                f"(config key: '{id_config_key}') contains duplicate values."
            )
            logger.error(error_msg)
            return (True, error_msg)
    
    
    elif id_column not in geodata.columns:
        msg = (
            f"Datatype {geodata_name}: Column '{id_column}' "
            f"(config key: '{id_config_key}') is missing from the data. "
            "Map2loop will automatically generate IDs."
        )
        logger.warning(msg)

    return (False, "")