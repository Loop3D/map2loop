from abc import ABC, abstractmethod
from .m2l_enums import Datatype, SampleType, StateType
from .sampler import SamplerDecimator, SamplerSpacing, Sampler
import beartype
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .project import Project


class AccessStorage(ABC):
    def __init__(self):
        self.storage_label = "AccessStorageAbstractClass"

    def type(self):
        return self.storage_label

    @beartype.beartype
    @abstractmethod
    def store(self, sampletype: SampleType, data):
        pass

    @beartype.beartype
    @abstractmethod
    def check_state(self, sampletype: SampleType):
        pass

    @abstractmethod
    def load(self, sampletype: SampleType):
        pass

    @beartype.beartype
    @abstractmethod
    def process(self, sampletype: SampleType):
        pass

    @beartype.beartype
    @abstractmethod
    def reprocess(self, sampletype: SampleType):
        pass

    @beartype.beartype
    @abstractmethod
    def __call__(self, sampletype: SampleType):
        pass


class SampleSupervisor(AccessStorage):
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
        self.set_default_samplers()
        self.project = project
        self.map_data = project.map_data

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
    def store(self, sampletype: SampleType, data):
        """
        Stores the sample data.

        Args:
            sampletype (SampleType): The type of the sample.
            data: The sample data to store.
        """

        # store the sample data
        self.samples[sampletype] = data
        self.sampler_dirtyflags[sampletype] = False

    @beartype.beartype
    def check_state(self, sampletype: SampleType):
        """
        Checks the state of the data, sample and sampler.

        Args:
            sampletype (SampleType): The type of the sample.
        """

        self.dirtyflags[StateType.DATA] = self.map_data.dirtyflags[sampletype]
        self.dirtyflags[StateType.SAMPLER] = self.sampler_dirtyflags[sampletype]

    @beartype.beartype
    def load(self, sampletype: SampleType):
        """
        Loads the map data or raster map data based on the sample type.

        Args:
            sampletype (SampleType): The type of the sample.
        """
        datatype = Datatype(sampletype)

        if datatype == Datatype.DTM:
            self.map_data.load_raster_map_data(datatype)

        else:
            # load map data
            self.map_data.load_map_data(datatype)

    @beartype.beartype
    def process(self, sampletype: SampleType):
        """
        Processes the sample based on the sample type.

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

    @beartype.beartype
    def reprocess(self, sampletype: SampleType):
        """
        Reprocesses the data based on the sample type.

        Args:
            sampletype (SampleType): The type of the sample.
        """

        if sampletype == SampleType.GEOLOGY or sampletype == SampleType.CONTACT:
            self.map_data.extract_all_contacts()

            if self.project.stratigraphic_column.column is None:
                self.project.calculate_stratigraphic_order()

            else:
                self.project.sort_stratigraphic_column()

            self.project.extract_geology_contacts()
            self.process(SampleType.GEOLOGY)

        elif sampletype == SampleType.STRUCTURE:
            self.process(SampleType.STRUCTURE)

        elif sampletype == SampleType.FAULT:
            self.project.calculate_fault_orientations()
            self.project.summarise_fault_data()
            self.process(SampleType.FAULT)

        elif sampletype == SampleType.FOLD:
            self.process(SampleType.FOLD)

    @beartype.beartype
    def __call__(self, sampletype: SampleType):
        """
        Checks the state of the data, sample and sampler, and returns
        the requested sample after reprocessing if necessary.

        Args:
            sampletype (SampleType): The type of the sample.

        Returns:
            The requested sample.
        """

        # check the state of the data, sample and sampler
        self.check_state(sampletype)

        # run the sampler only if no sample was generated before
        if self.samples[sampletype] is None:
            # if the data is changed, load and reprocess the data and generate a new sample
            if self.dirtyflags[StateType.DATA]:
                self.load(sampletype)
                self.reprocess(sampletype)
                return self.samples[sampletype]

            if not self.dirtyflags[StateType.DATA]:
                self.process(sampletype)
                return self.samples[sampletype]

        # return the requested sample after reprocessing if the data is changed
        elif self.samples[sampletype] is not None:
            if not self.dirtyflags[StateType.DATA]:
                if self.dirtyflags[StateType.SAMPLER]:
                    self.reprocess(sampletype)
                    return self.samples[sampletype]

                if not self.dirtyflags[StateType.SAMPLER]:
                    return self.samples[sampletype]

            if self.dirtyflags[StateType.DATA]:
                if not self.dirtyflags[StateType.SAMPLER]:
                    self.load(sampletype)
                    self.reprocess(sampletype)
                    return self.samples[sampletype]
