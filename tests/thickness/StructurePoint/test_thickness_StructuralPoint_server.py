from map2loop.thickness_calculator import StructuralPoint
from map2loop.project import Project
from map2loop.m2l_enums import VerboseLevel

config = {
    "structure": {
        "orientation_type": "strike",
        "dipdir_column": "strike2",
        "dip_column": "dip_2",
        "description_column": "DESCRIPTION",
        "bedding_text": "Bed",
        "overturned_column": "structypei",
        "overturned_text": "BEOI",
        "objectid_column": "objectid",
        "desciption_column": "feature",
    },
    "geology": {
        "unitname_column": "UNITNAME",
        "alt_unitname_column": "UNITNAME",
        "group_column": "GROUP",
        "supergroup_column": "supersuite",
        "description_column": "descriptn",
        "minage_column": "min_age_ma",
        "maxage_column": "max_age_ma",
        "rocktype_column": "rocktype1",
        "alt_rocktype_column": "rocktype2",
        "sill_text": "sill",
        "intrusive_text": "intrusive",
        "volcanic_text": "volcanic",
        "objectid_column": "ID",
        "ignore_codes": ["cover"],
    },
    "fault": {
        "structtype_column": "feature",
        "fault_text": "Fault",
        "dip_null_value": "0",
        "dipdir_flag": "num",
        "dipdir_column": "dip_dir",
        "dip_column": "dip",
        "orientation_type": "dip direction",
        "dipestimate_column": "dip_est",
        "dipestimate_text": "gentle,moderate,steep",
        "name_column": "name",
        "objectid_column": "objectid",
    },
    "fold": {
        "structtype_column": "feature",
        "fold_text": "Fold axial trace",
        "description_column": "type",
        "synform_text": "syncline",
        "foldname_column": "NAME",
        "objectid_column": "objectid",
    },
}


def test_from_aus_state():

    bbox_3d = {
        "minx": 515687.31005864,
        "miny": 7493446.76593407,
        "maxx": 562666.860106543,
        "maxy": 7521273.57407786,
        "base": -3200,
        "top": 3000,
    }
    loop_project_filename = "wa_output.loop3d"

    proj = Project(
        use_australian_state_data="WA",
        working_projection="EPSG:28350",
        bounding_box=bbox_3d,
        config_dictionary=config,
        clut_file_legacy=False,
        verbose_level=VerboseLevel.NONE,
        loop_project_filename=loop_project_filename,
    )

    proj.set_thickness_calculator(StructuralPoint())
    proj.run_all()
    assert (
        proj.thickness_calculator.sorter_label == "StructuralPoint"
    ), 'Thickness_calc structural point not being set properly'
    assert (
        "ThicknessMedian" in proj.stratigraphic_column.stratigraphicUnits.columns
    ), 'Thickness not being calculated in StructuralPointCalculator'
    assert (
        "ThicknessStdDev" in proj.stratigraphic_column.stratigraphicUnits.columns
    ), 'Thickness std not being calculated in StructuralPointCalculator'
