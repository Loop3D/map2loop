import pytest
from map2loop.project import Project
from map2loop.m2l_enums import VerboseLevel, Datatype
from map2loop.sorter import SorterAlpha
from map2loop.sampler import SamplerSpacing
from pyproj.exceptions import CRSError


bbox_3d = {
    "minx": 515687.31005864,
    "miny": 7493446.76593407,
    "maxx": 562666.860106543,
    "maxy": 7521273.57407786,
    "base": -3200,
    "top": 3000,
}
loop_project_filename = "wa_output.loop3d"


def test_run_all_catches_all_errors():
    
    try:
        proj = Project(
            use_australian_state_data="WA",
            working_projection="EPSG:283350",
            bounding_box=bbox_3d,
            clut_file_legacy=False,
            verbose_level=VerboseLevel.NONE,
            loop_project_filename=loop_project_filename)
        proj.set_sampler(Datatype.GEOLOGY, SamplerSpacing(200.0))
        proj.set_sampler(Datatype.FAULT, SamplerSpacing(200.0))
        proj.set_sorter(SorterAlpha())
        proj.run_all(take_best=True)
    except CRSError as crs_error:
        print("Caught CRSError when running project:", crs_error)
    except Exception as e:
        print("Caught an exception:", e)
    else:
        print("No exceptions raised, test passed.")

###################################################################
## test if wrong crs will throw a crs error

def test_expect_crs_error():
    with pytest.raises(CRSError):
        Project(
            use_australian_state_data="WA",
            working_projection="NittyGrittyEPSG",  
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

