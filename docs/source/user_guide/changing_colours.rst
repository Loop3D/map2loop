Changing Colours 
================
Using a CSV file
----------------
The easiest way to set the colour of different units in your model is to create a csv file that contains the lithological unit names in one column and the hex colour code in another, as shown below: 


Changing colours via your Jupyter notebook
------------------------------------------
You can also change unit and fault colours manually in your Jupyter notebook. There are examples of the code you can use to achieve this below. Importantly, if you decide to use this method, you’ll need to call this code after the creation of ‘model’ in your Jupyter notebook. 
The stratigraphy data is stored in a python dictionary, so to change the colour of specific elements you need to use the associated key. In the below cases you need to navigate through the nested dictionaries to find the colour value. To view the contents of the stratigraphic column dictionary in your own notebook you can just use the command:

.. code-block:: python 
model. stratigraphic_column

To view a dictionary nested within the stratigraphic_column dictionary you will need to specify the key, for example: 

.. code-block:: python 
model.stratigraphic_column['sg']

If you run this command, you’ll get an output showing the sg dictionary (which contains all of the rock units) as well as any dictionaries nested within it. 


Unit Colours
.............
Following on from the above explanation, to access the unit colour you will need to navigate from the stratigraphic_column dictionary through the dictionaries nested within it. In the example below you’ll navigate to ‘sg’ then ‘unit_name’ then ‘colour’ where you can finally edit the hex colour value. 

Make sure to replace ‘unit_name’ with the name of the unit you want to change and the ‘#f71945’ with the hex colour code you desire. Remember you can check these values by running and inspecting the output of: model. stratigraphic_column

.. code-block:: python
model.stratigraphic_column['sg']['unit_name']['colour'] = '#f71945' 

Fault Colours
..............
The code to change the colour of faults is very similar, where ‘fault_name’ is the name of the fault you’re editing. 

.. code-block:: python
model.stratigraphic_column['faults']['fault_name’]['colour'] = '#f25d27'

Please see the examples for further clarification. 


