import pytest

from map2loop.mapdata import MapData


@pytest.mark.parametrize(
    "projection, expected_projection, bounding_box, expected_warning",
    [
        (4326, "EPSG:4326", None, None),  # happy path with int projection
        ("EPSG:3857", "EPSG:3857", None, None),  # happy path with str projection
        (9999, "EPSG:9999", None, None),  # edge case with high int projection
        ("EPSG:9999", "EPSG:9999", None, None),  # edge case with high str projection
        (
            None,
            None,
            None,
            "Warning: Unknown projection set None. Leaving all map data in original projection\n",
        ),  # error case with None
        (
            [],
            None,
            None,
            "Warning: Unknown projection set []. Leaving all map data in original projection\n",
        ),  # error case with list
        (
            {},
            None,
            None,
            "Warning: Unknown projection set {}. Leaving all map data in original projection\n",
        ),  # error case with dict
    ],
    ids=[
        "int_projection",
        "str_projection",
        "high_int_projection",
        "high_str_projection",
        "none_projection",
        "list_projection",
        "dict_projection",
    ],
)
def test_set_working_projection(
    projection, expected_projection, bounding_box, expected_warning, capsys
):

    map_data = MapData()
    map_data.bounding_box = bounding_box

    map_data.set_working_projection(projection)

    assert (
        map_data.working_projection == expected_projection
    ), "Map.data set_working_projection() not attributing the correct projection"

    if expected_warning:
        captured = capsys.readouterr()
        assert expected_warning in captured.out
    else:
        captured = capsys.readouterr()
        assert captured.out == ""
