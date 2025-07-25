from map2loop.fault_orientation import FaultOrientationNearest
from .m2l_enums import Datatype, SampleType
from .sampler import Sampler
from .utils import set_z_values_from_raster_df

class FaultOrientationSampler(Sampler):
    def __init__(self, dtm_data=None, geology_data=None, fault_data=None,map_data=None):
        super().__init__(dtm_data,geology_data)
        self.sampler_label = "FaultOrientationSampler"
        self.fault_data = fault_data
        self.fault_orientation = FaultOrientationNearest()
    
    def sample(self, spatial_data):
        
        fault_orientations = self.fault_orientation.calculate(
            self.fault_data,
            spatial_data,
            self.map_data
        )
        
        set_z_values_from_raster_df(self.dtm_data, fault_orientations)
        
        return fault_orientations