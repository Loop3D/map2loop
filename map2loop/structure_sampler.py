from .sampler import SamplerDecimator
from .m2l_enums import Datatype
from .utils import set_z_values_from_raster_df
import geopandas
import pandas

class StructureSampler(SamplerDecimator):
    def __init__(self, decimation: int = 1,dtm_data=None, geology_data=None):
        super().__init__(decimation,dtm_data,geology_data)
        self.sampler_label = "StructureSampler"
    
    def sample(self, spatial_data):
        
        data = spatial_data.copy()
        data["X"] = data.geometry.x
        data["Y"] = data.geometry.y
        
        if self.dtm_data is not None:
            result = set_z_values_from_raster_df(self.dtm_data, data)
            if result is not None:
                data["Z"] = result["Z"]
            else:
                data["Z"] = None
        else:
            data["Z"] = None
        
        if self.geology_data is not None:
            data["layerID"] = geopandas.sjoin(
                data, self.geology_data, how='left'
            )['index_right']
        else:
            data["layerID"] = None
            
        data.reset_index(drop=True, inplace=True)
        
        return pandas.DataFrame(data[:: self.decimation].drop(columns="geometry"))