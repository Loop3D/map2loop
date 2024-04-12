# import map2loop
import pandas
import geopandas
import shapely
from map2loop.sampler import SamplerSpacing

test_geology_shapefile = pandas.read_csv("geology_test.csv")
test_geology_shapefile['geometry'] = test_geology_shapefile['geometry'].apply(shapely.wkt.loads)

test_geology_shapefile = geopandas.GeoDataFrame(
    test_geology_shapefile, crs = 'epsg:7854',
)

sampler = SamplerSpacing(spacing=50.0)

sampled_data = sampler.sample(test_geology_shapefile)

assert 'segNum' in sampled_data.columns, "SegNum column is not found in the sampled data."