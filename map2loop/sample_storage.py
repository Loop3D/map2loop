
from .m2l_enums import Datatype, SampleType, StateType
from .sampler import SamplerDecimator, SamplerSpacing, Sampler
import beartype


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

    def __init__(self, project: "Project"):
        """
        The constructor for the SampleSupervisor class.

        Args:
            project (Project): The Project class associated with the SampleSupervisor.
        """

        self.storage_label = "SampleSupervisor"
        self.samples = [None] * len(SampleType)
        self.samplers = [None] * len(SampleType)
        self.sampler_dirtyflags = [True] * len(SampleType)
        self.dirtyflags = [True] * len(StateType)

    def type(self):
        return self.storage_label

    def set_default_samplers(self):
        """
        Initialisation function to set or reset the point samplers
        """
        self.samplers[SampleType.STRUCTURE] = SamplerDecimator(1)
        self.samplers[SampleType.FAULT_ORIENTATION] = SamplerDecimator(1)
        self.samplers[SampleType.GEOLOGY] = SamplerSpacing(50.0)
        self.samplers[SampleType.FAULT] = SamplerSpacing(50.0)
        self.samplers[SampleType.FOLD] = SamplerSpacing(50.0)
        self.samplers[SampleType.CONTACT] = SamplerSpacing(50.0)
        self.samplers[SampleType.DTM] = SamplerSpacing(50.0)
        # dirty flags to false after initialisation
        self.sampler_dirtyflags = [False] * len(SampleType)

    @beartype.beartype
    def set_sampler(self, sampletype: SampleType, sampler: Sampler):
        """
        Set the point sampler for a specific datatype

        Args:
            sampletype (Datatype):
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
            str: The name of the sampler being used on the specified datatype
        """
        return self.samples[sampletype]

    @beartype.beartype
    def sample(self, sampletype: SampleType):
        """
        sample sample based on the sample type.

        Args:
            sampletype (SampleType): The type of the sample.
        """

        if sampletype == SampleType.CONTACT:
            self.store(
                SampleType.CONTACT,
                self.samplers[SampleType.CONTACT].sample(
                    self.map_data.basal_contacts, self.map_data
                ),
            )

        else:
            datatype = Datatype(sampletype)
            self.store(
                sampletype,
                self.samplers[sampletype].sample(
                    self.map_data.get_map_data(datatype), self.map_data
                ),
            )
