import beartype
import hjson
import urllib


class Config:
    """
    A data structure containing column name mappings for files and keywords

    Attributes
    ----------
    structure_config: dict
        column names and keywords for structure mappings
    geology_config: dict
        column names and keywords for geology mappings
    fault_config: dict
        column names and keywords for fault mappings
    fold_config: dict
        column names and keywords for fold mappings
    """
    def __init__(self):
        self.structure_config = {
                "orientation_type":    "dip direction",
                "dipdir_column":       "DIPDIR",
                "dip_column":          "DIP",
                "description_column":  "DESCRIPTION",
                "bedding_text":        "bedding",
                "overturned_column":   "DESCRIPTION",
                "overturned_text":     "overturned",
                "objectid_column":     "ID"
            }
        self.geology_config = {
                "unitname_column":     "UNITNAME",
                "alt_unitname_column": "CODE",
                "group_column":        "GROUP",
                "supergroup_column":   "SUPERGROUP",
                "description_column":  "DESCRIPTION",
                "minage_column":       "MIN_AGE",
                "maxage_column":       "MAX_AGE",
                "rocktype_column":     "ROCKTYPE1",
                "alt_rocktype_column": "ROCKTYPE2",
                "sill_text":           "sill",
                "intrusive_text":      "intrusive",
                "volcanic_text":       "volcanic",
                "objectid_column":     "ID",
                "ignore_codes":        ["cover"]
            }
        self.fault_config = {
                "structtype_column":   "FEATURE",
                "fault_text":          "fault",
                "dip_null_value":      "-999",
                "dipdir_flag":         "num",
                "dipdir_column":       "DIPDIR",
                "dip_column":          "DIP",
                "dipestimate_column":  "DIP_ESTIMATE",
                "dipestimate_text":    "'NORTH_EAST','NORTH',<rest of cardinals>,'NOT ACCESSED'",
                "name_column":         "NAME",
                "objectid_column":     "ID"
            }
        self.fold_config = {
                "structtype_column":   "FEATURE",
                "fold_text":           "fold",
                "description_column":  "DESCRIPTION",
                "synform_text":        "syncline",
                "foldname_column":     "NAME",
                "objectid_column":     "ID"
            }

    @beartype.beartype
    def update_from_dictionary(self, dictionary: dict):
        """
        Update the config dictionary from a provided dict

        Args:
            dictionary (dict): The dictionary to update from
        """
        if "structure" in dictionary:
            self.structure_config.update(dictionary["structure"])
            for key in dictionary["structure"].keys():
                if key not in self.structure_config:
                    print(f"Config dictionary structure segment contained {key} which is not used")
            dictionary.pop("structure")
        if "geology" in dictionary:
            self.geology_config.update(dictionary["geology"])
            for key in dictionary["geology"].keys():
                if key not in self.geology_config:
                    print(f"Config dictionary geology segment contained {key} which is not used")
            dictionary.pop("geology")
        if "fault" in dictionary:
            self.fault_config.update(dictionary["fault"])
            for key in dictionary["fault"].keys():
                if key not in self.fault_config:
                    print(f"Config dictionary fault segment contained {key} which is not used")
            dictionary.pop("fault")
        if "fold" in dictionary:
            self.fold_config.update(dictionary["fold"])
            for key in dictionary["fold"].keys():
                if key not in self.fold_config:
                    print(f"Config dictionary fold segment contained {key} which is not used")
            dictionary.pop("fold")
        if len(dictionary):
            print(f"Unused keys from config format {list(dictionary.keys())}")

    @beartype.beartype
    def update_from_legacy_file(self, file_map: dict):
        """
        Update the config dictionary from the provided old version dictionary

        Args:
            file_map (dict): The old version dictionary to update from
        """

        code_mapping = {
            "otype": (self.structure_config, "orientation_type"),
            "dd": (self.structure_config, "dipdir_column"),
            "d": (self.structure_config, "dip_column"),
            "sf": (self.structure_config, "desciption_column"),
            "bedding": (self.structure_config, "bedding_text"),
            "bo": (self.structure_config, "overturned_column"),
            "btype": (self.structure_config, "overturned_text"),
            "gi": (self.structure_config, "objectid_column"),
            "c": (self.geology_config, "unitname_column"),
            "u": (self.geology_config, "alt_unitname_column"),
            "g": (self.geology_config, "group_column"),
            "g2": (self.geology_config, "supergroup_column"),
            "ds": (self.geology_config, "description_column"),
            "min": (self.geology_config, "minage_column"),
            "max": (self.geology_config, "maxage_column"),
            "r1": (self.geology_config, "rocktype_column"),
            "r2": (self.geology_config, "alt_rocktype_column"),
            "sill": (self.geology_config, "sill_text"),
            "intrusive": (self.geology_config, "intrusive_text"),
            "volcanic": (self.geology_config, "volcanic_text"),
            "f": (self.fault_config, "structtype_column"),
            "fault": (self.fault_config, "fault_text"),
            "fdipnull": (self.fault_config, "dip_null_value"),
            "fdipdip_flag": (self.fault_config, "dipdir_flag"),
            "fdipdir": (self.fault_config, "dipdir_column"),
            "fdip": (self.fault_config, "dip_column"),
            "fdipest": (self.fault_config, "dipestimate_column"),
            "fdipest_vals": (self.fault_config, "dipestimate_text"),
            "n": (self.fault_config, "name_column"),
            "ff": (self.fold_config, "structtype_column"),
            "fold": (self.fold_config, "fold_text"),
            "t": (self.fold_config, "description_column"),
            "syn": (self.fold_config, "synform_text"),
        }
        for code in code_mapping:
            if code in file_map:
                code_mapping[code][0][code_mapping[code][1]] = file_map[code]
                file_map.pop(code)

        if "o" in file_map:
            self.structure_config["objectid_column"] = file_map["o"]
            self.fault_config["objectid_column"] = file_map["o"]
            self.fold_config["objectid_column"] = file_map["o"]
            file_map.pop("o")

        if len(file_map) > 0:
            print(f"Unused keys from legacy format {list(file_map.keys())}")

    @beartype.beartype
    def update_from_file(self, filename: str, legacy_format: bool = False):
        """
        Update the config dictionary from the provided json filename or url

        Args:
            filename (str): Filename or URL of the JSON config file
            legacy_format (bool, optional): Whether the JSON is an old version. Defaults to False.
        """
        if legacy_format:
            func = self.update_from_legacy_file
        else:
            func = self.update_from_dictionary

        if filename.startswith("http") or filename.startswith("ftp"):
            with urllib.request.urlopen(filename) as url_data:
                data = hjson.load(url_data)
                func(data)
        else:
            with open(filename) as url_data:
                data = hjson.load(url_data)
                func(data)
