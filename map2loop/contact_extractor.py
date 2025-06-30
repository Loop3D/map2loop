"""Utility class for extracting geological contacts."""

from __future__ import annotations

from typing import List, Optional

import geopandas
import pandas
import shapely

from .logging import getLogger

logger = getLogger(__name__)


class ContactExtractor:
    """Encapsulates contact extraction logic."""

    def __init__(self, 
        geology_data: geopandas.GeoDataFrame,
        fault_data: Optional[geopandas.GeoDataFrame] = None) -> None:
        
        self.geology_data = geology_data
        self.fault_data = fault_data
        self.contacts = None

    # ------------------------------------------------------------------
    def extract_all_contacts(self) -> geopandas.GeoDataFrame:
        """Extract all contacts between units in ``geology_data``."""

        logger.info("Extracting contacts")
        if self.fault_data is not None:
            faults = self.fault_data.copy() 
        else:
            faults = None
        geology = self.geology_data.copy()
        geology = geology.dissolve(by="UNITNAME", as_index=False)

        # Remove intrusions
        geology = geology[~geology["INTRUSIVE"]]
        geology = geology[~geology["SILL"]]

        # Remove faults from contact geometry
        if faults is not None:
            faults = faults.copy()
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

        contacts["length"] = [row.length for row in contacts["geometry"]]
        self.contacts = contacts

        return contacts

    # ------------------------------------------------------------------
    def extract_basal_contacts(
        self,
        contacts: geopandas.GeoDataFrame,
        stratigraphic_column: List[str],
    ) -> geopandas.GeoDataFrame:
        """Identify the basal unit of ``contacts`` based on ``stratigraphic_column``."""

        logger.info("Extracting basal contacts")

        units = stratigraphic_column
        basal_contacts = contacts.copy()

        # verify units exist in the geology dataset
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
            lambda row: abs(units.index(row["UNITNAME_1"]) - units.index(row["UNITNAME_2"])),
            axis=1,
        )

        # if the units are more than 1 unit apart, the contact is abnormal
        basal_contacts["type"] = basal_contacts.apply(
            lambda row: "ABNORMAL" if abs(row["stratigraphic_distance"]) > 1 else "BASAL",
            axis=1,
        )

        basal_contacts = basal_contacts[["ID", "basal_unit", "type", "geometry"]]

        basal_contacts["geometry"] = [
            shapely.line_merge(shapely.snap(geo, geo, 1)) for geo in basal_contacts["geometry"]
        ]

        return basal_contacts

