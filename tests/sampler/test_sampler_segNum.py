import pandas
from map2loop.sampler import SamplerSpacing
import shapely
import geopandas

geology_original = pandas.read_csv("./tests/sampler/geo_test.csv")
geology_original['geometry'] = geology_original['geometry'].apply(shapely.wkt.loads)
geology_original = geopandas.GeoDataFrame(geology_original, crs='epsg:7854')

sampler_space = 700.0

sampler = SamplerSpacing(spacing=sampler_space)
geology_samples = sampler.sample(geology_original)


# the actual test:
for _, poly in geology_original.iterrows():
    # check if one polygon, only 0 in segNum
    multipolygon = poly['geometry']
    corresponding_rows = geology_samples[geology_samples['ID'] == poly['ID']]

    if poly['geometry'].geom_type == 'Polygon':
        if poly.geometry.area < sampler_space:
            continue
        # check if zero segNum
        assert corresponding_rows['segNum'].unique() == '0', "Polygon with segNum 0 is not sampled."

        # check if in the right place
        for _, sample in corresponding_rows.iterrows():
            point = shapely.Point(sample['X'], sample['Y']).buffer(1)
            assert point.intersects(
                poly.geometry
            ), f"Point from SegNum 0 is not in the correct polygon segment of ID {poly['ID']}."

    if poly['geometry'].geom_type == 'MultiPolygon':
        if any(geom.area < sampler_space for geom in multipolygon.geoms):
            continue  # skip tiny little polys

        # # is the number of segs the same as the geology polygon?
        assert len(multipolygon.geoms) == len(
            corresponding_rows.segNum.unique()
        ), "Mismatch in the number of geo_polygons and segNum"

        for i, polygon in enumerate(poly.geometry.geoms):
            polygon_samples = corresponding_rows[corresponding_rows['segNum'] == str(i)]
            print(polygon_samples)
            for _, sample in polygon_samples.iterrows():
                point = shapely.Point(sample['X'], sample['Y']).buffer(
                    1
                )  # buffer just to make sure
                assert point.intersects(
                    polygon
                ), f"Point from SegNum {i} is not in the correct polygon segment of ID {poly['ID']}."