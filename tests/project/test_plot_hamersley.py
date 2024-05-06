import pytest
from map2loop.project import Project
from map2loop.m2l_enums import VerboseLevel, Datatype
from map2loop.sorter import SorterAlpha
from map2loop.sampler import SamplerSpacing
from pyproj.exceptions import CRSError
import os

bbox_3d = {
    "minx": 515687.31005864,
    "miny": 7493446.76593407,
    "maxx": 562666.860106543,
    "maxy": 7521273.57407786,
    "base": -3200,
    "top": 3000,
}
loop_project_filename = "wa_output.loop3d"

def test_project_execution():
    proj = Project(
        use_australian_state_data="WA",
        working_projection="EPSG:28350",
        bounding_box=bbox_3d,
        clut_file_legacy=False,
        verbose_level=VerboseLevel.NONE,
        loop_project_filename=loop_project_filename,
    )
    proj.run_all(take_best=True)
    assert proj is not None, "Plot Hamersley Basin failed to execute"

def test_file_creation():
    expected_file = loop_project_filename
    assert os.path.exists(expected_file), f"Expected file {expected_file} was not created"

###################################################################
## test if wrong crs will throw a crs error


def test_expect_crs_error():
    with pytest.raises(CRSError):
        Project(
            use_australian_state_data="WA",
            working_projection="NittyGrittyCRS",
            bounding_box=bbox_3d,
            clut_file_legacy=False,
            verbose_level=VerboseLevel.NONE,
            loop_project_filename=loop_project_filename,
        )
    print("CRSError was raised as expected.")


###################################################################
## test if wrong state throws an error


def test_expect_state_error():

    with pytest.raises(ValueError):
        Project(
            use_australian_state_data="NittyGrittyState",
            working_projection="EPSG:28350",
            bounding_box=bbox_3d,
            clut_file_legacy=False,
            verbose_level=VerboseLevel.NONE,
            loop_project_filename=loop_project_filename,
        )

    print("ValueError was raised as expected.")


###################################################################
# test if it catches wrong config file
def test_expect_config_error():
    with pytest.raises(Exception):
        Project(
            use_australian_state_data="WA",
            working_projection="EPSG:28350",
            bounding_box=bbox_3d,
            clut_file_legacy=False,
            config_filename='NittyGrittyConfig.csv',
            verbose_level=VerboseLevel.NONE,
            loop_project_filename=loop_project_filename,
        )
    print("FileNotFoundError//Exception by catchall in project.py was raised as expected.")
