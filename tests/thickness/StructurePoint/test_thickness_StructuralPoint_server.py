from map2loop.thickness_calculator import StructuralPoint

from map2loop.project import Project
from map2loop.m2l_enums import VerboseLevel


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
