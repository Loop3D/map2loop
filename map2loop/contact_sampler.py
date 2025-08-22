from .sampler import SamplerSpacing
from .m2l_enums import Datatype, SampleType
from .contact_extractor import ContactExtractor
from .utils import set_z_values_from_raster_df

class ContactSampler(SamplerSpacing):
    def __init__(self, spacing=50.0,
                    dtm_data=None,
                    geology_data=None,
                    fault_data=None,
                    stratigraphic_column=None,
                ):
        super().__init__(spacing, dtm_data, geology_data)
        self.sampler_label = "ContactSampler"
        self.stratigraphic_column = stratigraphic_column
        self.fault_data = fault_data      
        self.contact_extractor = None

    def get_contact_extractor(self):
        if self.contact_extractor is None:
            self.contact_extractor = ContactExtractor(
                self.geology_data,
                self.fault_data
            )
        return self.contact_extractor
    

    def extract_all_contacts(self):
        extractor = self.get_contact_extractor()
        contacts = extractor.extract_all_contacts()
        return contacts
    

    def extract_basal_contacts(self):
        extractor = self.get_contact_extractor()
        if extractor.contacts is None:
            self.extract_all_contacts()
        
        basal_contacts = extractor.extract_basal_contacts(self.stratigraphic_column)
        
        return basal_contacts
    
    def sample(self, spatial_data=None):
        basal_contacts = self.extract_basal_contacts()
        sampled_contacts = super().sample(basal_contacts)
        
        set_z_values_from_raster_df(self.dtm_data, sampled_contacts)
        
        return sampled_contacts