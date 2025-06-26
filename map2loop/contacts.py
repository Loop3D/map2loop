import beartype
import shapely
from typing import Optional
import geopandas
import pandas

from .logging import getLogger

logger = getLogger(__name__)


class ContactExtractor:
    """Utility class to extract geological contacts."""

    @beartype.beartype
    def __init__(
        self,
        geology_data: geopandas.GeoDataFrame,
        fault_data: Optional[geopandas.GeoDataFrame] = None,
    ) -> None:
        """Store geology and fault data for contact extraction."""

        self.geology_data = geology_data
        self.fault_data = fault_data
        self.contacts: Optional[geopandas.GeoDataFrame] = None

    @beartype.beartype
    def extract_all_contacts(self) -> geopandas.GeoDataFrame:
        """Extract the contacts between units in the geology data."""

        logger.info("Extracting contacts")
        geology = self.geology_data.copy()
        geology = geology.dissolve(by="UNITNAME", as_index=False)
        geology = geology[~geology["INTRUSIVE"]]
        geology = geology[~geology["SILL"]]

        if self.fault_data is not None:
            faults = self.fault_data.copy()
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

    @beartype.beartype
    def extract_basal_contacts(
        self,
        stratigraphic_column: list,
        contact_data: Optional[geopandas.GeoDataFrame] = None,
    ) -> tuple[geopandas.GeoDataFrame, geopandas.GeoDataFrame]:
        """Identify basal contacts using the stratigraphic column."""

        logger.info("Extracting basal contacts")

        if contact_data is None:
            if self.contacts is None:
                raise ValueError(
                    "No contact data available. Run 'extract_all_contacts' first or provide contact_data."
                )
            contact_data = self.contacts

        units = stratigraphic_column
        all_contacts = contact_data.copy()

        if any(unit not in units for unit in all_contacts["UNITNAME_1"].unique()):
            missing_units = (
                all_contacts[~all_contacts["UNITNAME_1"].isin(units)]["UNITNAME_1"]
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

        all_contacts["ID"] = all_contacts.apply(
            lambda row: min(units.index(row["UNITNAME_1"]), units.index(row["UNITNAME_2"])),
            axis=1,
        )
        all_contacts["basal_unit"] = all_contacts.apply(lambda row: units[row["ID"]], axis=1)
        all_contacts["stratigraphic_distance"] = all_contacts.apply(
            lambda row: abs(units.index(row["UNITNAME_1"]) - units.index(row["UNITNAME_2"])),
            axis=1,
        )
        all_contacts["type"] = all_contacts.apply(
            lambda row: "ABNORMAL" if abs(row["stratigraphic_distance"]) > 1 else "BASAL",
            axis=1,
        )

        all_contacts = all_contacts[["ID", "basal_unit", "type", "geometry"]]

        all_contacts["geometry"] = [
            shapely.line_merge(shapely.snap(geo, geo, 1)) for geo in all_contacts["geometry"]
        ]

        self.contacts = all_contacts
        basal_contacts = all_contacts[all_contacts["type"] == "BASAL"]

        return all_contacts, basal_contacts
