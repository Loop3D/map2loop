### This file tests the overall behavior of project.py. Runs from LoopServer.

#internal imports
from map2loop.project import Project
from map2loop.m2l_enums import VerboseLevel

#external imports
import pytest
from pyproj.exceptions import CRSError
import os
import requests

bbox_3d = {
    "minx": 515687.31005864,
    "miny": 7493446.76593407,
    "maxx": 562666.860106543,
    "maxy": 7521273.57407786,
    "base": -3200,
    "top": 3000,
}

loop_project_filename = "wa_output.loop3d"


def remove_LPF():
    lpf_exists = os.path.exists(loop_project_filename)
    if lpf_exists:
        os.remove(loop_project_filename)


def test_project_execution():
    try:
        proj = Project(
            use_australian_state_data="WA",
            working_projection="EPSG:28350",
            bounding_box=bbox_3d,
            clut_file_legacy=False,
            verbose_level=VerboseLevel.NONE,
            loop_project_filename=loop_project_filename,
            overwrite_loopprojectfile=True,
        )
    except requests.exceptions.ReadTimeout:
        pytest.skip("Connection to the server timed out, skipping test")
    
    proj.run_all(take_best=True)
    assert proj is not None, "Plot Hamersley Basin failed to execute"

    assert os.path.exists(loop_project_filename), f"Expected file {loop_project_filename} was not created"


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
            overwrite_loopprojectfile=True,
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
            overwrite_loopprojectfile=True,
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
            overwrite_loopprojectfile=True,
        )
    print("FileNotFoundError//Exception by catchall in project.py was raised as expected.")
