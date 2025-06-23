import beartype
import shapely
from .m2l_enums import Datatype
from typing import Optional
import geopandas
import pandas

from .logging import getLogger
logger = getLogger(__name__)

@beartype.beartype
def extract_all_contacts(
    geology_data: geopandas.GeoDataFrame,
    fault_data: Optional[geopandas.GeoDataFrame] = None,
):
    """
    Extract the contacts between units in the geology GeoDataFrame
    """
    logger.info("Extracting contacts")
    geology = geology_data.copy()
    geology = geology.dissolve(by="UNITNAME", as_index=False)
    # Remove intrusions
    geology = geology[~geology["INTRUSIVE"]]
    geology = geology[~geology["SILL"]]
    # Remove faults from contact geomety
    if fault_data is not None:
        faults = fault_data.copy()
        faults["geometry"] = faults.buffer(50)
        geology = geopandas.overlay(geology, faults, how="difference", keep_geom_type=False)
    units = geology["UNITNAME"].unique()
    column_names = ["UNITNAME_1", "UNITNAME_2", "geometry"]
    contacts = geopandas.GeoDataFrame(crs=geology.crs, columns=column_names, data=None)
    while len(units) > 1:
        unit1 = units[0]
        units = units[1:]
        for unit2 in units:
            if unit1 != unit2:
                # print(f'contact: {unit1} and {unit2}')
                join = geopandas.overlay(
                    geology[geology["UNITNAME"] == unit1],
                    geology[geology["UNITNAME"] == unit2],
                    keep_geom_type=False,
                )[column_names]
                join["geometry"] = join.buffer(1)
                buffered = geology[geology["UNITNAME"] == unit2][["geometry"]].copy()
                buffered["geometry"] = buffered.boundary
                end = geopandas.overlay(buffered, join, keep_geom_type=False)
                if len(end):
                    contacts = pandas.concat([contacts, end], ignore_index=True)
    # contacts["TYPE"] = "UNKNOWN"
    contacts["length"] = [row.length for row in contacts["geometry"]]
    # print('finished extracting contacts')
    return contacts


@beartype.beartype
def extract_basal_contacts(
    contact_data:geopandas.GeoDataFrame, 
    stratigraphic_column: list,
    filter_type:str, 
):
    """
    Identify the basal unit of the contacts based on the stratigraphic column

    Args:
        stratigraphic_column (list):
            The stratigraphic column to use
    """
    logger.info("Extracting basal contacts")
    
    units = stratigraphic_column
    basal_contacts = contact_data.copy()

    # check if the units in the strati colum are in the geology dataset, so that basal contacts can be built
    # if not, stop the project
    if any(unit not in units for unit in basal_contacts["UNITNAME_1"].unique()):
        missing_units = (
            basal_contacts[~basal_contacts["UNITNAME_1"].isin(units)]["UNITNAME_1"]
            .unique()
            .tolist()
        )
        logger.error(
            "There are units in the Geology dataset, but not in the stratigraphic column: "
            + ", ".join(missing_units)
            + ". Please readjust the stratigraphic column if this is a user defined column."
        )
        raise ValueError(
            "There are units in stratigraphic column, but not in the Geology dataset: "
            + ", ".join(missing_units)
            + ". Please readjust the stratigraphic column if this is a user defined column."
        )

    # apply minimum lithological id between the two units
    basal_contacts["ID"] = basal_contacts.apply(
        lambda row: min(units.index(row["UNITNAME_1"]), units.index(row["UNITNAME_2"])), axis=1
    )
    # match the name of the unit with the minimum id
    basal_contacts["basal_unit"] = basal_contacts.apply(lambda row: units[row["ID"]], axis=1)
    # how many units apart are the two units?
    basal_contacts["stratigraphic_distance"] = basal_contacts.apply(
        lambda row: abs(units.index(row["UNITNAME_1"]) - units.index(row["UNITNAME_2"])), axis=1
    )
    # if the units are more than 1 unit apart, the contact is abnormal (meaning that there is one (or more) unit(s) missing in between the two)
    basal_contacts["type"] = basal_contacts.apply(
        lambda row: "ABNORMAL" if abs(row["stratigraphic_distance"]) > 1 else "BASAL", axis=1
    )

    basal_contacts = basal_contacts[["ID", "basal_unit", "type", "geometry"]]

    # added code to make sure that multi-line that touch each other are snapped and merged.
    # necessary for the reconstruction based on featureId
    basal_contacts["geometry"] = [
        shapely.line_merge(shapely.snap(geo, geo, 1)) for geo in basal_contacts["geometry"]
    ]

    if filter_type == 'basal':
        return basal_contacts[basal_contacts["type"] == "BASAL"]
    elif filter_type == 'abnormal':
        return basal_contacts[basal_contacts["type"] == "ABNORMAL"]
    else:
        return basal_contacts
