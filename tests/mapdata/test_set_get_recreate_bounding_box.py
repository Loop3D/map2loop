import pytest
from map2loop import MapData # Replace with the actual module and class name
import geopandas
import shapely

@pytest.fixture
md = MapData()

def test_set_bounding_box_with_tuple(md):
    bounding_box = (0, 10, 0, 10)
    md.set_bounding_box(bounding_box)
    
    assert md.bounding_box == {
        "minx": 0,
        "maxx": 10,
        "miny": 0,
        "maxy": 10,
        "top": 0,
        "base": 2000
    }

def test_set_bounding_box_with_dict(your_class_instance):
    bounding_box = {
        "minx": 0,
        "maxx": 10,
        "miny": 0,
        "maxy": 10,
        "top": 5,
        "base": 15
    }
    your_class_instance.set_bounding_box(bounding_box)
    
    assert your_class_instance.bounding_box == bounding_box

def test_set_bounding_box_with_invalid_type(your_class_instance):
    with pytest.raises(TypeError):
        your_class_instance.set_bounding_box([0, 10, 0, 10])  # List instead of tuple or dict

def test_bounding_box_keys(your_class_instance):
    bounding_box = (0, 10, 0, 10)
    your_class_instance.set_bounding_box(bounding_box)
    
    for key in ["minx", "maxx", "miny", "maxy", "top", "base"]:
        assert key in your_class_instance.bounding_box

def test_bounding_box_polygon(your_class_instance):
    bounding_box = (0, 10, 0, 10)
    your_class_instance.set_bounding_box(bounding_box)
    
    minx, miny, maxx, maxy = 0, 0, 10, 10
    lat_point_list = [miny, miny, maxy, maxy, miny]
    lon_point_list = [minx, maxx, maxx, minx, minx]
    expected_polygon = geopandas.GeoDataFrame(
        index=[0],
        crs=your_class_instance.working_projection,
        geometry=[shapely.Polygon(zip(lon_point_list, lat_point_list))]
    )
    
    assert your_class_instance.bounding_box_polygon.equals(expected_polygon)

if __name__ == "__main__":
    pytest.main()
