Calculating stratigraphic thicknesses
=====================================

Calculating unit thicknesses in map2loop is both an important and a difficult 
task.  There is no 'best' way to determine thicknesses because it depends on the
stratigraphy of your region of interest and how much data has been collected in
the field.  Because of this map2loop has been written so that a python-capable user
can create their own thickness calculator and use it within the map2loop process.

Below is the structure of a thickness calculator and an example of how to implement
your own and use it within map2loop.

In order to make a plugin thickness calculator map2loop has a template that is 
extendable.  The whole template is shown below:

.. code-block::

    class ThicknessCalculator(ABC):
    """
    Base Class of Thickness Calculator used to force structure of ThicknessCalculator

    Args:
        ABC (ABC): Derived from Abstract Base Class
    """

    def __init__(self):
        """
        Initialiser of for ThicknessCalculator
        """
        self.thickness_calculator_label = "ThicknessCalculatorBaseClass"

    def type(self):
        """
        Getter for subclass type label

        Returns:
            str: Name of subclass
        """
        return self.thickness_calculator_label

    @beartype.beartype
    @abstractmethod
    def compute(
        self,
        units: pandas.DataFrame,
        stratigraphic_order: list,
        basal_contacts: geopandas.GeoDataFrame,
        map_data: MapData,
    ) -> pandas.DataFrame:
        """
        Execute thickness calculator method (abstract method)

        Args:
            units (pandas.DataFrame): the data frame of units to add thicknesses to
            stratigraphic_order (list): a list of unit names sorted from youngest to oldest
            basal_contacts (geopandas.GeoDataFrame): basal contact geo data with locations and unit names of the contacts (columns must contain ["ID","basal_unit","type","geometry"])
            map_data (map2loop.MapData): a catchall so that access to all map data is available

        Returns:
            pandas.DataFrame: units dataframe with added thickness column for calculated thickness values
        """
        pass

Using this abstract base class a new class can be created by taking that base class and
replacing the __init__ and compute functions, the simplest example is shown below:

.. code-block::
from map2loop.thickness_calculator import ThicknessCalculator
from map2loop.mapdata import MapData
import pandas
import geopandas

    class myThicknessCalculator(ThicknessCalculator):
        def __init__(self, thickness=100):
            self.thickness_calculator_label = "myThicknessCalculator"
            self.default_thickness = thickness
        
        def compute(
            self,
            units: pandas.DataFrame,
            stratigraphic_order: list,
            basal_contacts: pandas.DataFrame,
            map_data: MapData,
        ) -> pandas.DataFrame:
            output_units = units.copy()
            output_units['thickness'] = default_thickness
            return output_units

This example will set all unit thicknesses to 100m.

To use this new thickness calculator in the map2loop project one final line needs to
be added after the Project has been initialised:

.. code-block::

    proj = map2loop.Project( ... )

    proj.set_thickness_calculator(myThicknessCalculator(50))

Notes
-----
You need to set the thickness calculator as an instance of myThicknessCalculator
(with the ()s) rather than the definition.  If you want to set the default thickness using
this class you can create the class with the thickness parameter as above
(myThicknessCalculator(50)).

The thickness calculator takes the existing units dataframe, changes the values in the
thickness column and then returns the modified dataframe.  While you have control of
this dataframe you have the power to add or remove units, and change features
of any unit but if you do this there is no longer any guarantee that map2loop will still
process your maps or even finish.

Parameters
----------
As seen in the template and the compute abstract method you have access to other data
from within the map2loop process.  Below is a brief description of each and a potential
use for them in your thickness calculator:

units - while this is the data frame that you need to return it also contains fields
such as group, supergroup and min/max ages.  If you have coarser information about the
thickness of a group this information could be used to ensure that the sum of the unit
thicknesses in your region that are within the same group matches your information.

stratigraphic_order - this is likely the most useful parameter as it tells you which
units are adjacent. In combination with the basal_contacts parameter apparent thicknesses
can be calculated.

basal_contacts - this geometric data frame contains linear data of where adjacent 
contacts are.  By comparing the contacts on both sides of a unit you can calculated the
apparent thickness of a unit

map_data - this catch-all gives you complete access to the shapefiles used in map2loop.
If you need access to the structural orientation data you can use
map_data.get_map_data(Datatype.STRUCTURE) and you have access to the shapefile.  Note 
that changing information or using setter function from map_data is likely to cause 
problems within the map2loop workflow.
