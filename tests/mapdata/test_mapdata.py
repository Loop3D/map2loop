import pytest
import geopandas
import shapely
from map2loop.mapdata import MapData 
from map2loop.m2l_enums import Datatype

def test_structures_less_than_360():
    md = MapData()

    md.config.structure_config = {
            "dipdir_column": "DIPDIR",
            "dip_column": "DIP",
            "description_column": "DESCRIPTION",
            "bedding_text": "Bedding",
            "objectid_column": "ID",
            "overturned_column": "facing",
            "overturned_text": "DOWN",
            "orientation_type": "strike"  
        }

    data = {
        'geometry': [shapely.Point(1, 1), shapely.Point(2, 2), shapely.Point(3, 3),],
        'DIPDIR': [45.0, 370.0, 420.0], 
        'DIP': [30.0, 60.0, 50],
        'OVERTURNED': ["False", "True", "True"],
        'DESCRIPTION': ["Bedding", "Bedding", "Bedidng"],
        'ID': [1, 2, 3]
    }

    data = geopandas.GeoDataFrame(data)

    md.raw_data[Datatype.STRUCTURE] = data
    md.parse_structure_map()

    assert md.data[Datatype.STRUCTURE]['DIPDIR'].all() < 360, "MapData.STRUCTURE is producing DIPDIRs > 360 degrees"