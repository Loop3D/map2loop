import pytest
import pandas as pd
from map2loop.thickness_calculator import InterpolatedStructure
from map2loop.project import Project
import os
from map2loop.m2l_enums import VerboseLevel
from datetime import datetime

os.system('gdown --folder https://drive.google.com/drive/folders/1ZEJvPN4lpGpvoepjGMZgzYPGaY3mT46p')


@pytest.fixture
def project():
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

    return project


@pytest.fixture
def interpolated_structure_thickness():
    return InterpolatedStructure()


@pytest.fixture
def units(project):
    return project.stratigraphic_column.stratigraphicUnits


@pytest.fixture
def stratigraphic_order(project):
    return project.stratigraphic_column.column


@pytest.fixture
def basal_contacts(project):
    return project.map_data.basal_contacts


@pytest.fixture
def samples(project):
    return project.structure_samples


@pytest.fixture
def map_data(project):
    return project.map_data


def test_compute(
    interpolated_structure_thickness,
    units,
    stratigraphic_order,
    basal_contacts,
    samples,
    map_data,
    project,
):
    result = interpolated_structure_thickness.compute(
        units, stratigraphic_order, basal_contacts, samples, map_data
    )
    assert interpolated_structure_thickness.thickness_calculator_label == "InterpolatedStructure"
    assert isinstance(result, pd.DataFrame)
    assert 'Thickness' in result.columns
    assert result['Thickness'].dtypes == float
    assert 'ThicknessStdDev' in result.columns
    assert result['ThicknessStdDev'].dtypes == float
    assert int(result.loc[result['name'] == 'Litho_A', 'Thickness'].to_numpy()[0]) == -1
    assert int(result.loc[result['name'] == 'Litho_B', 'Thickness'].to_numpy()[0]) == 2649
    assert int(result.loc[result['name'] == 'Litho_C', 'Thickness'].to_numpy()[0]) == 950
    assert int(result.loc[result['name'] == 'Litho_D', 'Thickness'].to_numpy()[0]) == -1
