
from .m2l_enums import Datatype, SampleType
from .sampler import SamplerDecimator, SamplerSpacing, Sampler
import beartype
from .mapdata import MapData
from .stratigraphic_column import StratigraphicColumn
from .fault_orientation_sampler import FaultOrientationSampler
from .contact_sampler import ContactSampler

from .logging import getLogger

logger = getLogger(__name__)


class SampleSupervisor:
    """
    The SampleSupervisor class is responsible for managing the samples and samplers in the project.
    It extends the AccessStorage abstract base class.

    Attributes:
        storage_label (str): The label of the storage.
        samples (list): A list of samples.
        samplers (list): A list of samplers.
        sampler_dirtyflags (list): A list of flags indicating if the sampler has changed.
        dirtyflags (list): A list of flags indicating the state of the data, sample or sampler.
        project (Project): The project associated with the SampleSupervisor.
        map_data (MapData): The map data associated with the project.
    """

    def __init__(self, project: "Project", map_data: MapData, stratigraphic_column: StratigraphicColumn ):
        """
        The constructor for the SampleSupervisor class.

        Args:
            project (Project): The Project class associated with the SampleSupervisor.
        """

        self.storage_label = "SampleSupervisor"
        self.map_data = map_data
        self.stratigraphic_column = stratigraphic_column
        self.samples = [None] * len(SampleType)
        self.samplers = [None] * len(SampleType)
        self.sampler_dirtyflags = [True] * len(SampleType)
        self.set_default_samplers()

    def type(self):
        return self.storage_label

    def set_default_samplers(self):
        """
        Initialisation function to set or reset the point samplers
        """

        geology_data = self.map_data.get_map_data(Datatype.GEOLOGY)
        dtm_data = self.map_data.get_map_data(Datatype.DTM)
        fault_data = self.map_data.get_map_data(Datatype.FAULT)

        self._set_decimator_sampler(SampleType.STRUCTURE, decimation=1)
        self._set_spacing_sampler(SampleType.GEOLOGY, spacing=50.0)
        self._set_spacing_sampler(SampleType.FAULT, spacing=50.0)
        self._set_spacing_sampler(SampleType.FOLD, spacing=50.0)
        self._set_spacing_sampler(SampleType.DTM, spacing=50.0)
        self._set_contact_sampler(SampleType.CONTACT, spacing=50.0)
        self._set_fault_orientation_sampler(SampleType.FAULT_ORIENTATION)

        # dirty flags to false after initialisation
        self.sampler_dirtyflags = [False] * len(SampleType)

    def _verify_sampler_type(self, sampletype: SampleType, sampler_type: str):
        allowed_samplers = {
            SampleType.STRUCTURE: ["SamplerDecimator"],
            SampleType.GEOLOGY: ["SamplerSpacing"],
            SampleType.FAULT: ["SamplerSpacing"],
            SampleType.FOLD: ["SamplerSpacing"],
            SampleType.DTM: ["SamplerSpacing"],
            SampleType.CONTACT: ["ContactSampler"],
            SampleType.FAULT_ORIENTATION: ["FaultOrientationSampler"]
        }
        
        if sampletype in allowed_samplers and sampler_type not in allowed_samplers[sampletype]:
            allowed = ", ".join(allowed_samplers[sampletype])
            raise ValueError(f"Invalid sampler type '{sampler_type}' for sample '{sampletype}', please use {allowed}")

    @beartype.beartype
    def set_sampler(self, sampletype: SampleType, sampler_type: str, **kwargs):
        """
        Set the point sampler for a specific datatype

        Args:
            sampletype (SampleType):
                The sample type (SampleType) to use this sampler on
            samplertype (str):
                The sampler to use
        """
        self._verify_sampler_type(sampletype, sampler_type)

        if sampler_type == "SamplerDecimator":
            self._set_decimator_sampler(sampletype, **kwargs)
        elif sampler_type == "SamplerSpacing":
            self._set_spacing_sampler(sampletype, **kwargs)
        elif sampler_type == "ContactSampler":
            self._set_contact_sampler(sampletype, **kwargs)
        elif sampler_type == "FaultOrientationSampler":
            self._set_fault_orientation_sampler(sampletype, **kwargs)
        else:
            raise ValueError('incorrect sampler type')

        # set the dirty flag to True to indicate that the sampler has changed
        self.sampler_dirtyflags[sampletype] = True

    @beartype.beartype
    def _set_decimator_sampler(self, sampletype, decimation=1):
        geology_data = self.map_data.get_map_data(Datatype.GEOLOGY)
        dtm_data = self.map_data.get_map_data(Datatype.DTM)
        self.samplers[sampletype] = SamplerDecimator(decimation=decimation, dtm_data=dtm_data, geology_data=geology_data)

    @beartype.beartype
    def _set_spacing_sampler(self, sampletype, spacing=50.0):
        self.samplers[sampletype] = SamplerSpacing(spacing=spacing)
    
    @beartype.beartype
    def _set_contact_sampler(self, sampletype, spacing=50.0):
        geology_data = self.map_data.get_map_data(Datatype.GEOLOGY)
        fault_data = self.map_data.get_map_data(Datatype.FAULT)
        self.samplers[sampletype] = ContactSampler(spacing=spacing,geology_data=geology_data,fault_data=fault_data, stratigraphic_column=self.stratigraphic_column.column)

    @beartype.beartype
    def _set_fault_orientation_sampler(self, sampletype):
        geology_data = self.map_data.get_map_data(Datatype.GEOLOGY)
        dtm_data = self.map_data.get_map_data(Datatype.DTM)
        fault_data = self.map_data.get_map_data(Datatype.FAULT)
        self.samplers[sampletype] = FaultOrientationSampler(dtm_data=dtm_data, geology_data=geology_data, fault_data=fault_data, map_data=self.map_data)
    
    @beartype.beartype
    def get_sampler(self, sampletype: SampleType):
        """
        Get the sampler name being used for a datatype

        Args:
            sampletype: The sample type of the sampler

        Returns:
            str: The name of the sampler being used on the specified datatype
        """
        return self.samplers[sampletype].sampler_label
    
    @beartype.beartype
    def get_samples(self, sampletype: SampleType):
        """
        Get a sample given a sample type

        Args:
            sampletype: The sample type of the sampler

        Returns:
            The sample data associated with the specified sample type
        """
        return self.samples[sampletype]
    
    @beartype.beartype
    def store(self, sampletype: SampleType, sample_data):
        self.samples[sampletype] = sample_data
        self.sampler_dirtyflags[sampletype] = False

    @beartype.beartype
    def sample(self, sampletype: SampleType):
        """
        sample sample based on the sample type.

        Args:
            sampletype (SampleType): The type of the sample.
        
        Returns:
            The sample data for the specified sample type
        """
        if self.samples[sampletype] is not None and not self.sampler_dirtyflags[sampletype]:
            return self.samples[sampletype]
        if sampletype == SampleType.BASAL_CONTACT:
            self._sample_basal_contact()
        elif sampletype == SampleType.CONTACT:
            self._sample_contact()
        else:
            self._sample_other_types(sampletype)

        return self.samples[sampletype]
    
    @beartype.beartype
    def _sample_basal_contact(self):
        contact_sampler = self.samplers[SampleType.CONTACT]
        basal_contacts = contact_sampler.extract_basal_contacts()
        self.store(SampleType.BASAL_CONTACT, basal_contacts)
    
    @beartype.beartype
    def _sample_contact(self):
        contact_sampler = self.samplers[SampleType.CONTACT]
        sampled_contacts = contact_sampler.sample()
        self.store(SampleType.CONTACT, sampled_contacts)
    
    @beartype.beartype
    def _sample_other_types(self, sampletype: SampleType):
        datatype = Datatype(sampletype)
        spatial_data = self.map_data.get_map_data(datatype)
        sampled_data = self.samplers[sampletype].sample(spatial_data)
        self.store(sampletype, sampled_data)
