import pytest
import os
from map2loop.project import Project
from map2loop.m2l_enums import VerboseLevel, SampleType, StateType, Datatype
from map2loop.sampler import SamplerSpacing, SamplerDecimator
from map2loop.sorter import SorterAlpha
import pandas


"""
============================
Hamersley, Western Australia
============================
"""

####################################################################
# Set the region of interest for the project
# -------------------------------------------
# Define the bounding box for the ROI

bbox_3d = {
    "minx": 515687.31005864,
    "miny": 7493446.76593407,
    "maxx": 562666.860106543,
    "maxy": 7521273.57407786,
    "base": -3200,
    "top": 3000,
}

@pytest.fixture
def sample_supervisor():
    # Specify minimum details (which Australian state, projection and bounding box
    # and output file)
    loop_project_filename = "wa_output.loop3d"
    proj = Project(
        use_australian_state_data="WA",
        working_projection="EPSG:28350",
        bounding_box=bbox_3d,
        verbose_level=VerboseLevel.NONE,
        loop_project_filename=loop_project_filename,
        overwrite_loopprojectfile=True,
    )

    # Set the distance between sample points for arial and linestring geometry
    proj.sample_supervisor.set_sampler(SampleType.GEOLOGY, SamplerSpacing(200.0))
    proj.sample_supervisor.set_sampler(SampleType.FAULT, SamplerSpacing(200.0))

    # Choose which stratigraphic sorter to use or run_all with "take_best" flag to run them all
    proj.set_sorter(SorterAlpha())
    # proj.set_sorter(SorterAgeBased())
    # proj.set_sorter(SorterUseHint())
    # proj.set_sorter(SorterUseNetworkx())
    # proj.set_sorter(SorterMaximiseContacts())
    # proj.set_sorter(SorterObservationProjections())
    proj.run_all(take_best=True)

    return proj.sample_supervisor


def test_type(sample_supervisor):
    assert sample_supervisor.type() == "SampleSupervisor"


def test_set_default_samplers(sample_supervisor):
    sample_supervisor.set_default_samplers()
    assert isinstance(sample_supervisor.samplers[SampleType.GEOLOGY], SamplerSpacing)
    assert isinstance(sample_supervisor.samplers[SampleType.FAULT], SamplerSpacing)
    assert isinstance(sample_supervisor.samplers[SampleType.FOLD], SamplerSpacing)
    assert isinstance(sample_supervisor.samplers[SampleType.FAULT_ORIENTATION], SamplerDecimator)
    assert isinstance(sample_supervisor.samplers[SampleType.DTM], SamplerSpacing)
    assert isinstance(sample_supervisor.samplers[SampleType.CONTACT], SamplerSpacing)
    assert isinstance(sample_supervisor.samplers[SampleType.STRUCTURE], SamplerDecimator)


def test_set_sampler(sample_supervisor):
    sampler = SamplerSpacing(100.0)
    sample_supervisor.set_sampler(SampleType.STRUCTURE, sampler)
    assert sample_supervisor.samplers[SampleType.STRUCTURE] == sampler
    assert sample_supervisor.sampler_dirtyflags[SampleType.STRUCTURE] is True


def test_get_sampler(sample_supervisor):
    sampler = SamplerSpacing(100.0)
    sample_supervisor.set_sampler(SampleType.STRUCTURE, sampler)
    assert sample_supervisor.get_sampler(SampleType.STRUCTURE) == sampler.sampler_label


def test_store(sample_supervisor):
    data = pandas.DataFrame()
    sample_supervisor.store(SampleType.STRUCTURE, data)
    assert isinstance(sample_supervisor.samples[SampleType.STRUCTURE], pandas.DataFrame)
    sample_supervisor.store(SampleType.GEOLOGY, data)
    assert isinstance(sample_supervisor.samples[SampleType.GEOLOGY], pandas.DataFrame)
    sample_supervisor.store(SampleType.FAULT, data)
    assert isinstance(sample_supervisor.samples[SampleType.FAULT], pandas.DataFrame)
    sample_supervisor.store(SampleType.FOLD, data)
    assert isinstance(sample_supervisor.samples[SampleType.FOLD], pandas.DataFrame)
    sample_supervisor.store(SampleType.FAULT_ORIENTATION, data)
    assert isinstance(sample_supervisor.samples[SampleType.FAULT_ORIENTATION], pandas.DataFrame)


def test_check_state(sample_supervisor):
    sample_supervisor.check_state(SampleType.STRUCTURE)
    assert sample_supervisor.dirtyflags[StateType.DATA] is False
    assert sample_supervisor.dirtyflags[StateType.SAMPLER] is False


def test_load(sample_supervisor):
    sample_supervisor.load(SampleType.STRUCTURE)
    sample_supervisor.check_state(SampleType.STRUCTURE)
    assert sample_supervisor.dirtyflags[StateType.DATA] is False
    sample_supervisor.load(SampleType.GEOLOGY)
    sample_supervisor.check_state(SampleType.GEOLOGY)
    assert sample_supervisor.dirtyflags[StateType.DATA] is False
    sample_supervisor.load(SampleType.FAULT)
    sample_supervisor.check_state(SampleType.FAULT)
    assert sample_supervisor.dirtyflags[StateType.DATA] is False
    sample_supervisor.load(SampleType.FOLD)
    sample_supervisor.check_state(SampleType.FOLD)
    assert sample_supervisor.dirtyflags[StateType.DATA] is False
    sample_supervisor.load(SampleType.FAULT_ORIENTATION)
    sample_supervisor.check_state(SampleType.FAULT_ORIENTATION)
    assert sample_supervisor.dirtyflags[StateType.DATA] is False


def test_process(sample_supervisor):
    sample_supervisor.process(SampleType.STRUCTURE)
    sample_supervisor.check_state(SampleType.STRUCTURE)
    assert sample_supervisor.samples[SampleType.STRUCTURE] is not None
    sample_supervisor.process(SampleType.GEOLOGY)
    sample_supervisor.check_state(SampleType.GEOLOGY)
    assert sample_supervisor.samples[SampleType.GEOLOGY] is not None
    sample_supervisor.process(SampleType.FAULT)
    sample_supervisor.check_state(SampleType.FAULT)
    assert sample_supervisor.samples[SampleType.FAULT] is not None
    sample_supervisor.process(SampleType.FOLD)
    sample_supervisor.check_state(SampleType.FOLD)
    assert sample_supervisor.samples[SampleType.FOLD] is not None
    sample_supervisor.process(SampleType.CONTACT)
    sample_supervisor.check_state(SampleType.CONTACT)
    assert sample_supervisor.samples[SampleType.CONTACT] is not None


def test_reprocess(sample_supervisor):

    sample_supervisor.sampler_dirtyflags[SampleType.STRUCTURE] = True
    sample_supervisor.reprocess(SampleType.STRUCTURE)
    assert sample_supervisor.samples[SampleType.STRUCTURE] is not None
    assert isinstance(sample_supervisor.samples[SampleType.STRUCTURE], pandas.DataFrame)
    assert sample_supervisor.sampler_dirtyflags[SampleType.STRUCTURE] is False

    sample_supervisor.sampler_dirtyflags[SampleType.GEOLOGY] = True
    sample_supervisor.reprocess(SampleType.GEOLOGY)
    assert sample_supervisor.samples[SampleType.GEOLOGY] is not None
    assert isinstance(sample_supervisor.samples[SampleType.GEOLOGY], pandas.DataFrame)
    assert sample_supervisor.sampler_dirtyflags[SampleType.GEOLOGY] is False

    sample_supervisor.sampler_dirtyflags[SampleType.FOLD] = True
    sample_supervisor.reprocess(SampleType.FOLD)
    assert sample_supervisor.samples[SampleType.FOLD] is not None
    assert isinstance(sample_supervisor.samples[SampleType.FOLD], pandas.DataFrame)
    assert sample_supervisor.sampler_dirtyflags[SampleType.FOLD] is False

    sample_supervisor.sampler_dirtyflags[SampleType.CONTACT] = True
    sample_supervisor.reprocess(SampleType.CONTACT)
    assert sample_supervisor.samples[SampleType.CONTACT] is not None
    assert isinstance(sample_supervisor.samples[SampleType.CONTACT], pandas.DataFrame)
    assert sample_supervisor.sampler_dirtyflags[SampleType.CONTACT] is False


def test_call(sample_supervisor):

    sample_supervisor(SampleType.STRUCTURE)
    assert sample_supervisor.samples[SampleType.STRUCTURE] is not None
    assert isinstance(sample_supervisor.samples[SampleType.STRUCTURE], pandas.DataFrame)

    sample_supervisor.samples[SampleType.STRUCTURE] = None
    sample_supervisor(SampleType.STRUCTURE)
    assert sample_supervisor.samples[SampleType.STRUCTURE] is not None
    assert isinstance(sample_supervisor.samples[SampleType.STRUCTURE], pandas.DataFrame)

    sample_supervisor.set_sampler(SampleType.STRUCTURE, SamplerDecimator(1))
    sample_supervisor(SampleType.STRUCTURE)
    assert sample_supervisor.samples[SampleType.STRUCTURE] is not None
    assert isinstance(sample_supervisor.samples[SampleType.STRUCTURE], pandas.DataFrame)

    sample_supervisor.samples[SampleType.GEOLOGY] = None
    sample_supervisor.map_data.dirtyflags[SampleType.GEOLOGY] = True
    sample_supervisor(SampleType.GEOLOGY)
    assert sample_supervisor.samples[SampleType.GEOLOGY] is not None
    assert isinstance(sample_supervisor.samples[SampleType.GEOLOGY], pandas.DataFrame)

    sample_supervisor(SampleType.FAULT)
    assert sample_supervisor.samples[SampleType.FAULT] is not None
    assert isinstance(sample_supervisor.samples[SampleType.FAULT], pandas.DataFrame)

    sample_supervisor(SampleType.FOLD)
    assert sample_supervisor.samples[SampleType.FOLD] is not None
    assert isinstance(sample_supervisor.samples[SampleType.FOLD], pandas.DataFrame)

    sample_supervisor(SampleType.CONTACT)
    assert sample_supervisor.samples[SampleType.CONTACT] is not None
    assert isinstance(sample_supervisor.samples[SampleType.CONTACT], pandas.DataFrame)