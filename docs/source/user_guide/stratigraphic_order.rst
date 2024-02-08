Identifying stratigraphic order
===============================

Calculating stratigraphic order in map2loop can be difficult depending on the
stratigraphy of your region of interest and how much data has been collected in
the field.  Because of this map2loop has been written so that a python-capable user
can create their own stratigraphic column sorter and use it within the map2loop process.

Below is the structure of a stratigraphic column sorter and an example of how to implement
your own and use it within map2loop.

In order to make a plugin sorter map2loop has a template that is extendable.  The whole
template is shown below:

.. code-block::

    class Sorter(ABC):
        """
        Base Class of Sorter used to force structure of Sorter

        Args:
            ABC (ABC): Derived from Abstract Base Class
        """
        def __init__(self):
            """
            Initialiser of for Sorter
            """
            self.sorter_label = "SorterBaseClass"

        def type(self):
            """
            Getter for subclass type label

            Returns:
                str: Name of subclass
            """
            return self.sorter_label

        @beartype.beartype
        @abstractmethod
        def sort(self, units: pandas.DataFrame, unit_relationships: pandas.DataFrame, stratigraphic_order_hint: list, contacts: pandas.DataFrame, map_data: MapData) -> list:
            """
            Execute sorter method (abstract method)

            Args:
                units (pandas.DataFrame): the data frame to sort (columns must contain ["layerId", "name", "minAge", "maxAge", "group"])
                units_relationships (pandas.DataFrame): the relationships between units (columns must contain ["Index1", "Unitname1", "Index2", "Unitname2"])
                stratigraphic_order_hint (list): a list of unit names to be used as a hint to sorting the units
                contacts (geopandas.GeoDataFrame): unit contacts with length of the contacts in metres
                map_data (map2loop.MapData): a catchall so that access to all map data is available

            Returns:
                list: sorted list of unit names
            """
            pass

Using this abstract base class a new class can be created by taking that base class and
replacing the __init__ and sort functions, the simplest example is shown below:

.. code-block::
from map2loop.sorter import Sorter
from map2loop.mapdata import MapData
import pandas
import geopandas

    class mySorter(Sorter):
        def __init__(self):
            self.sorter_label = "mySorter"

        def sort(self,
            units: pandas.DataFrame,
            unit_relationships: pandas.DataFrame,
            stratigraphic_order_hint: list,
            contacts: geopandas.GeoDataFrame,
            map_data: MapData
        ) -> list:
            unitnames = sorted(units['name'])
            return unitnames

This example will sort the units into alphabetical order based on name and return the
stratigraphic column order in a list of unit names.

To use this new sorter in the map2loop project one final line needs to
be added after the Project has been initialised:

.. code-block::

    proj = map2loop.Project( ... )

    proj.set_sorter(mySorter())

Notes
-----
You need to set the sorter as an instance of mySorter (with the ()s) rather than the definition.

The sorter takes the existing units dataframe and must return a list containing all the
unitnames present in that dataframe.  If some are added or missing map2loop with raise an
exception.  Also while you have control of this dataframe you have the power to add or
remove units, and change features of any unit but if you do this there is no longer any
guarantee that map2loop will still process your maps or even finish.

As the base class Sorter contains abstract methods and is parsed through beartype the
structure of the sort function must remain the same.  If there is reason to access more
map2loop data that isn't in the map_data structure raise an issue with in the map2loop
github repo and we can address that.

Parameters
----------
As seen in the template and the sort abstract method you have access to other data
from within the map2loop process. Below is a brief description of each and a potential
use for them in your thickness calculator:

units - this is the data frame that contains the units and fields such as group, supergroup and
min/max ages.  If the age data is present it can be useful in sorting the units. Also
group and supergroup information could be used to ensure that all units within the
same group/supergroup are contiguous.

unit_relationships - this data frame contains a list of adjacent units within the shapefile.
The format is ['Index1', 'Unitname1', 'Index2', 'Unitname2'] and each row is a single
adjacency that was found.  Note that some of these contacts might have been across a fault
so take that into account when using this data.

stratigraphic_order_hint - this is a first pass attempt at the stratigraphic column
calculated by map2model which looks at unit adjacency in the shapefile.

contacts - this geometric data frame contains linear data of where adjacent
units are and the length of that contact. Using this data you might prioritise
longer contacts as more likely to be adjacent in the stratigraphic column.

map_data - this catch-all gives you complete access to the shapefiles used in map2loop.
If you need access to the structural orientation data you can use
map_data.get_map_data(Datatype.STRUCTURE) or if you want the geology map 
map_data.get_map_data(Datatype.GEOLOGY) and you have access to those shapefiles.  Note
that changing information or using setter function from map_data is likely to cause
problems within the map2loop workflow.

