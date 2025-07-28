
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

        self.samplers[SampleType.STRUCTURE] = SamplerDecimator(decimation=1, dtm_data=dtm_data, geology_data=geology_data)
        self.samplers[SampleType.GEOLOGY] = SamplerSpacing(spacing=50.0)
        self.samplers[SampleType.FAULT] = SamplerSpacing(spacing=50.0)
        self.samplers[SampleType.FOLD] = SamplerSpacing(spacing=50.0)
        self.samplers[SampleType.DTM] = SamplerSpacing(spacing=50.0)
        self.samplers[SampleType.CONTACT] = ContactSampler(spacing=50.0,geology_data=geology_data,fault_data=fault_data, stratigraphic_column=self.stratigraphic_column.column)
        self.samplers[SampleType.FAULT_ORIENTATION] = FaultOrientationSampler(dtm_data=dtm_data, geology_data=geology_data, 
        fault_data=fault_data, map_data=self.map_data)
        # dirty flags to false after initialisation
        self.sampler_dirtyflags = [False] * len(SampleType)

    @beartype.beartype
    def set_sampler(self, sampletype: SampleType, sampler: Sampler):
        """
        Set the point sampler for a specific datatype

        Args:
            sampletype (SampleType):
                The sample type (SampleType) to use this sampler on
            sampler (Sampler):
                The sampler to use
        """
        self.samplers[sampletype] = sampler
        # set the dirty flag to True to indicate that the sampler has changed
        self.sampler_dirtyflags[sampletype] = True

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
