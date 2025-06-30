import pathlib
from map2loop.project import Project

from map2loop.api import Map2LoopAPI


def test_api_list_and_get_class():
    api = Map2LoopAPI()
    classes = api.list_classes()
    assert "MapData" in classes
    mapdata_cls = api.get_class("MapData")
    assert mapdata_cls.__name__ == "MapData"


def test_api_create_instance():
    api = Map2LoopAPI()
    obj = api.create("MapData")
    from map2loop.mapdata import MapData

    assert isinstance(obj, MapData)


def test_api_create_project(tmp_path):
    api = Map2LoopAPI()
    import map2loop

    bbox = {
        "minx": 515687.31005864,
        "miny": 7493446.76593407,
        "maxx": 562666.860106543,
        "maxy": 7521273.57407786,
        "base": -3200,
        "top": 3000,
    }
    geology_file = (
        pathlib.Path(map2loop.__file__).parent
        / "_datasets" / "geodata_files" / "hamersley" / "geology.geojson"
    )
    structure_file = (
        pathlib.Path(map2loop.__file__).parent
        / "_datasets" / "geodata_files" / "hamersley" / "structures.geojson"
    )
    dtm_file = (
        pathlib.Path(map2loop.__file__).parent
        / "_datasets" / "geodata_files" / "hamersley" / "dtm_rp.tif"
    )
    config_dict = {
        "structure": {"dipdir_column": "azimuth2", "dip_column": "dip"},
        "geology": {"unitname_column": "unitname", "alt_unitname_column": "code"},
    }
    project = api.create(
        "Project",
        bounding_box=bbox,
        working_projection="EPSG:28350",
        geology_filename=str(geology_file),
        dtm_filename=str(dtm_file),
        structure_filename=str(structure_file),
        config_dictionary=config_dict,
    )
    assert isinstance(project, Project)
