import beartype
import pandas

_THROW_CALCULATOR_REGISTRY = {}

@beartype.beartype
def register_throw_calculator(name: str):
    """
    Register a throw calculator function with a given name.

    Args:
        name (str): the name of the throw calculator
    """
    def decorator(func):
        _THROW_CALCULATOR_REGISTRY[name] = func
        return func
    return decorator

@beartype.beartype
def get_throw_calculator(name: str):
    """
    Get a throw calculator function by name.

    Args:
        name (str): the name of the throw calculator to retrieve
    """
    if name not in _THROW_CALCULATOR_REGISTRY:
        raise ValueError(f"Throw calculator {name} not found")
    return _THROW_CALCULATOR_REGISTRY[name]

@beartype.beartype
def calculate_throw(
    faults: pandas.DataFrame,
    stratigraphic_order: list,
    basal_contacts: pandas.DataFrame,
    throw_calculator_name: str,
) -> pandas.DataFrame:
    """
    Calculate fault throw values using the specified calcultor.

    Args:
        faults (pandas.DataFrame): the data frame of the faults to add throw values to
        stratigraphic_order (list): a list of unit names sorted from youngest to oldest
        basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])
        throw_calculator_name (str): the name of the throw calculator to use

    Returns:
        pandas.DataFrame: fault data frame with throw values (avgDisplacement and avgDownthrowDir) filled in
    """
    return get_throw_calculator(throw_calculator_name)(faults, stratigraphic_order, basal_contacts)

@register_throw_calculator("alpha")
@beartype.beartype
def calculate_throw_alpha(
    faults: pandas.DataFrame,
    stratigraphic_order: list,
    basal_contacts: pandas.DataFrame,
) -> pandas.DataFrame:
    """
    Execute throw calculator method takes fault data, basal_contacts and stratigraphic order and attempts to estimate fault throw.

    Args:
        faults (pandas.DataFrame): the data frame of the faults to add throw values to
        stratigraphic_order (list): a list of unit names sorted from youngest to oldest
        basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])

    Returns:
        pandas.DataFrame: fault data frame with throw values (avgDisplacement and avgDownthrowDir) filled in
    """
    # TODO
    # For each fault take the geometric join of all contact lines and that fault line

    # For each contact join take the length of that join as an approximation of the minimum throw of the fault

    # Take all the min throw approximations and set the largest one as the avgDisplacement

    # If a fault has no contact lines the maximum throw should be less than the thickness of the containing
    # unit (if we exclude map height changes and fault angle)

    # Set any remaining displacement values to default value
    faults["avgDisplacement"] = faults.apply(
        lambda row: 100 if row["avgDisplacement"] == -1 else row["avgDisplacement"], axis=1
    )
    return faults