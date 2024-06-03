import pytest
import os
from map2loop.project import Project
from map2loop.m2l_enums import VerboseLevel, SampleType, StateType
from map2loop.sampler import SamplerSpacing, SamplerDecimator
from datetime import datetime
import pandas

os.system('gdown --folder https://drive.google.com/drive/folders/1ZEJvPN4lpGpvoepjGMZgzYPGaY3mT46p')


@pytest.fixture
def sample_supervisor():
    bounding_box = {"minx": 0, "miny": 0, "maxx": 10000, "maxy": 10000, "base": 0, "top": -5000}

    nowtime = datetime.now().isoformat(timespec='minutes')
    model_name = nowtime.replace(":", "-").replace("T", "-")
    loop_project_filename = os.path.join(model_name, "local_source.loop3d")
    project = Project(
        geology_filename='./data/lithologies.shp',
        fault_filename="./data/faults.shp",
        fold_filename="./data/faults.shp",
        structure_filename="./data/measurements.shp",
        dtm_filename='./data/DEM.tif',
        config_filename='./data/example.hjson',
        clut_filename='./data/500kibg_colours.csv',
        clut_file_legacy=True,
        verbose_level=VerboseLevel.NONE,
        tmp_path=model_name,
        working_projection="EPSG:7854",
        bounding_box=bounding_box,
        loop_project_filename=loop_project_filename,
    )
    
    # Or you can run map2loop and pre-specify the stratigraphic column
    column = [
        # youngest
        'Litho_A',
        'Litho_B',
        'Litho_C',
        'Litho_D',
        # oldest
    ]

    project.run_all(user_defined_stratigraphic_column=column)

    return project.sample_supervisor


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


# TODO: test_store to be completed
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