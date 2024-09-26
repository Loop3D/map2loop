# internal imports
from .m2l_enums import VerboseLevel

# external imports
import map2model
import pandas
import numpy
import os
import re
import pathlib


class Map2ModelWrapper:
    """
    A wrapper around map2model functionality

    Attributes
    ----------
    sorted_units: None or list
        map2model's estimate of the stratigraphic column
    fault_fault_relationships: None or pandas.DataFrame
        data frame of fault to fault relationships with columns ["Fault1", "Fault2", "Type", "Angle"]
    unit_fault_relationships: None or pandas.DataFrame
        data frame of unit fault relationships with columns ["Unit", "Fault"]
    unit_unit_relationships: None or pandas.DataFrame
        data frame of unit unit relationships with columns ["Index1", "UnitName1", "Index2", "UnitName2"]
    map_data: MapData
        A pointer to the map data structure in project
    verbose_level: m2l_enum.VerboseLevel
        A selection that defines how much console logging is output
    """

    def __init__(self, map_data, verbose_level: VerboseLevel = VerboseLevel.NONE):
        """
        The initialiser for the map2model wrapper

        Args:
            map_data (MapData):
                The project map data structure to reference
            verbose_level (VerboseLevel, optional):
                How much console output is sent. Defaults to VerboseLevel.ALL.
        """
        self.sorted_units = None
        self.fault_fault_relationships = None
        self.unit_fault_relationships = None
        self.unit_unit_relationships = None
        self.map_data = map_data
        self.verbose_level = verbose_level

    def reset(self):
        """
        Reset the wrapper to before the map2model process
        """
        self.sorted_units = None
        self.fault_fault_relationships = None
        self.unit_fault_relationships = None
        self.unit_unit_relationships = None

    def get_sorted_units(self):
        """
        Getter for the map2model sorted units

        Returns:
            list: The map2model stratigraphic column estimate
        """
        if self.sorted_units is None:
            self.run()
        return self.sorted_units

    def get_fault_fault_relationships(self):
        """
        Getter for the fault fault relationships

        Returns:
            pandas.DataFrame: The fault fault relationships
        """
        if self.fault_fault_relationships is None:
            self.run()
        return self.fault_fault_relationships

    def get_unit_fault_relationships(self):
        """
        Getter for the unit fault relationships

        Returns:
            pandas.DataFrame: The unit fault relationships
        """
        if self.unit_fault_relationships is None:
            self.run()
        return self.unit_fault_relationships

    def get_unit_unit_relationships(self):
        """
        Getter for the unit unit relationships

        Returns:
            pandas.DataFrame: The unit unit relationships
        """
        if self.unit_unit_relationships is None:
            self.run()
        return self.unit_unit_relationships

    def run(self, verbose_level: VerboseLevel = None):
        """
        The main execute function that prepares, runs and parse the output of the map2model process

        Args:
            verbose_level (VerboseLevel, optional):
                How much console output is sent. Defaults to None (which uses the wrapper attribute).
        """
        if verbose_level is None:
            verbose_level = self.verbose_level
        if verbose_level != VerboseLevel.NONE:
            print("Exporting map data for map2model")
        self.map_data.export_wkt_format_files()
        if verbose_level != VerboseLevel.NONE:
            print("Running map2model...")
        map2model_code_map = {
            "o": "ID",  # FIELD_COORDINATES
            "f": "FEATURE",  # FIELD_FAULT_ID
            "u": "CODE",  # FIELD_POLYGON_LEVEL1_NAME
            "g": "GROUP",  # FIELD_POLYGON_LEVEL2_NAME
            "min": "MIN_AGE",  # FIELD_POLYGON_MIN_AGE
            "max": "MAX_AGE",  # FIELD_POLYGON_MAX_AGE
            "c": "UNITNAME",  # FIELD_POLYGON_CODE
            "ds": "DESCRIPTION",  # FIELD_POLYGON_DESCRIPTION
            "r1": "ROCKTYPE1",  # FIELD_POLYGON_ROCKTYPE1
            "r2": "ROCKTYPE2",  # FIELD_POLYGON_ROCKTYPE2
            "msc": "",  # FIELD_SITE_CODE
            "mst": "",  # FIELD_SITE_TYPE
            "mscm": "",  # FIELD_SITE_COMMO
            "fold": self.map_data.config.fold_config["fold_text"],  # FAULT_AXIAL_FEATURE_NAME
            "sill": self.map_data.config.geology_config["sill_text"],  # SILL_STRING
            "intrusive": self.map_data.config.geology_config["intrusive_text"],  # IGNEOUS_STRING
            "volcanic": self.map_data.config.geology_config["volcanic_text"],  # VOLCANIC_STRING
            "deposit_dist": 100,  # deposit_dist
        }
        # TODO: Simplify. Note: this is external so have to match fix to map2model module
        run_log = map2model.run(
            pathlib.Path(self.map_data.map2model_tmp_path),
            pathlib.Path(self.map_data.map2model_tmp_path) / "geology_wkt.csv",
            pathlib.Path(self.map_data.map2model_tmp_path) / "faults_wkt.csv",
            "",
            self.map_data.get_bounding_box(),
            map2model_code_map,
            verbose_level == VerboseLevel.NONE,
            "None",
        )
        if verbose_level == VerboseLevel.ALL:
            print("map2model log:")
            print(run_log)
        if verbose_level != VerboseLevel.NONE:
            print("map2model complete")

        # Parse units sorted
        units_sorted = pandas.read_csv(
            pathlib.Path(self.map_data.map2model_tmp_path) / "units_sorted.txt",
            header=None,
            sep=' ',
        )
        if units_sorted.shape == 0:
            self.sorted_units = []
        else:
            self.sorted_units = list(units_sorted[5])

        # Parse fault intersections
        out = []
        fault_fault_intersection_filename = pathlib.Path(self.map_data.map2model_tmp_path) / "fault-fault-intersection.txt"
        if (
            os.path.isfile(fault_fault_intersection_filename)
            and os.path.getsize(fault_fault_intersection_filename) > 0
        ):
            df = pandas.read_csv(fault_fault_intersection_filename, delimiter="{", header=None)
            df[1] = list(df[1].str.replace("}", "", regex=False))
            df[1] = [re.findall("\(.*?\)", i) for i in df[1]]  # Valid escape for regex
            df[0] = list(df[0].str.replace("^[0-9]*, ", "", regex=True))
            df[0] = list(df[0].str.replace(", ", "", regex=False))
            df[0] = "Fault_" + df[0]
            relations = df[1]
            for j in range(len(relations)):
                relations[j] = [i.strip("()").replace(" ", "").split(",") for i in relations[j]]
            df[1] = relations

            for _, row in df.iterrows():
                for i in numpy.arange(len(row[1])):
                    out += [[row[0], "Fault_" + row[1][i][0], row[1][i][1], float(row[1][i][2])]]

        df_out = pandas.DataFrame(columns=["Fault1", "Fault2", "Type", "Angle"], data=out)
        self.fault_fault_relationships = df_out

        # Parse unit fault relationships
        out = []
        unit_fault_intersection_filename = pathlib.Path(self.map_data.map2model_tmp_path) / "unit-fault-intersection.txt"
        if (
            os.path.isfile(unit_fault_intersection_filename)
            and os.path.getsize(unit_fault_intersection_filename) > 0
        ):
            df = pandas.read_csv(unit_fault_intersection_filename, header=None, sep='{')
            df[1] = list(df[1].str.replace("}", "", regex=False))
            df[1] = df[1].astype(str).str.split(", ")
            df[0] = list(df[0].str.replace("^[0-9]*, ", "", regex=True))
            df[0] = list(df[0].str.replace(", ", "", regex=False))

            for _, row in df.iterrows():
                for i in numpy.arange(len(row[1])):
                    out += [[row[0], "Fault_" + row[1][i]]]

        df_out = pandas.DataFrame(columns=["Unit", "Fault"], data=out)
        self.unit_fault_relationships = df_out

        # Parse unit unit relationships
        units = []
        links = []
        graph_filename = pathlib.Path(self.map_data.map2model_tmp_path) / "graph_all_None.gml.txt"

        if os.path.isfile(graph_filename) and os.path.getsize(graph_filename) > 0:
            with open(
                pathlib.Path(self.map_data.map2model_tmp_path) / "graph_all_None.gml.txt"
            ) as file:
                contents = file.read()
                segments = contents.split("\n\n")
                for line in segments[0].split("\n"):
                    units += [line.split(" ")]
                for line in segments[1].split("\n")[:-1]:
                    links += [line.split(" ")]

        df = pandas.DataFrame(columns=["index", "unit"], data=units)
        df.set_index("index", inplace=True)
        out = []
        for row in links:
            out += [[int(row[0]), df["unit"][row[0]], int(row[1]), df["unit"][row[1]]]]
        df_out = pandas.DataFrame(columns=["Index1", "UnitName1", "Index2", "UnitName2"], data=out)
        self.unit_unit_relationships = df_out
