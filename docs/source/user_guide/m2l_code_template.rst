
Template for Map2Loop
=====================

This is a basic template for the calling code that can be used to run
Map2Loop. The output of the program will be a ‘.loop3d’ file, which can
be passed directly to LoopStructural to produce your 3D model.

.. raw:: html

   <p>

An attempt has been made to explain the code as much as possible. In
your own notebook, you may want to get rid of the explanatory comments
(any lines starting with a ‘#’, and text cells). This won’t affect the
program’s functionality.

Before You Begin
----------------

In order to run map2loop you will need the following files: 1. Polygon
shapefile containing your lithologies 2. LineString shapefile containing
your linear features (e.g. faults) 3. Point data shapefile containing
orientation data 4. hjson file defining the attribute names used in your
shapefiles

.. raw:: html

   <p>

If you need help setting up these files please refer to the map2loop
examples which provide a step-by-step guide.

Setting up your notebook
------------------------

In order for your map2loop code to funtion correctly, you need to import
all of the neccessary python libraries. In simple terms, imports allow
different code modules to speak to eachother.

.. code:: ipython3

    import os
    from map2loop.project import Project
    from map2loop.m2l_enums import VerboseLevel
    from map2loop.m2l_enums import Datatype
    from map2loop.sampler import SamplerSpacing, SamplerDecimator
    from map2loop.sorter import SorterUseHint, SorterUseNetworkX, SorterAgeBased, SorterAlpha
    import time

Naming your .loop3d output file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This format specifies that the output file will be saved in a new folder
within the current directory (where ever you have saved your notebook).
The new folder will be named whatever you specify in line 6 (
“insert_output_folder_name_here”). The generated loop3d file will be
called “local_source.loop3d”. #### CHANGE: (line 6):
“insert_output_folder_name_here” to a project relevant name

.. code:: ipython3

    from datetime import datetime
    nowtime=datetime.now().isoformat(timespec='minutes')   
    model_name=nowtime.replace(":","-").replace("T","-")
    
    #The next line specifies the name of the output file and the folder containing all the data
    loop_project_filename = os.path.join("insert_output_folder_name_here", "local_source.loop3d")
    
    t0 = time.time()

Defining the Model Extents
~~~~~~~~~~~~~~~~~~~~~~~~~~

You’ll need to specify the extent of the area you want to model. This is
defined as minimum and maximum x and y coordinates, where x is the
latitude and y is the longitude. You also need to state the bounds of
the model along the z axis. This is given as the number of meters above
and below the surface that will be modeled. #### CHANGE: The numeric
values assigned to variables accross lines 2 to 7, to match your region
of interest.

.. code:: ipython3

    bounding_box = {
        "minx": 602635,        #minimum latitude
        "miny": 5852551,       #minimum longitude
        "maxx": 642618,        #maximum latitude
        "maxy": 5908499,       #maximum longitude
        "base": -2000,         #meters modeled below the surface
        "top": 1000,           #meters modeled above the surface
    }

Creating a Project Instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is where all of the required files (e.g. shape files) are passed to
map2loop. #### NOTE When passing local files to map2loop you need to
specify the full file path. If you get an error concerning the path, you
may need to use double backslashes in the path specification (e.g
geology_filename = “C:\\Users\\Bob\\Documents\\lithology.shp”, )
alternatively you can use a raw string command and continue to use
single backslashes (e.g geology_filename =
r”C::raw-latex:`\Users`:raw-latex:`\Bob`:raw-latex:`\Documents`:raw-latex:`\lithology`.shp”,)
#### CHANGE: Fill in the appropriate paths described in each string from
lines 2 to 7.

.. raw:: html

   <p>

(line 8): clut_filename is an optional variable. If you would like to
assign colours to each unit using a csv file you’ll need to specify the
full path here, otherwise leave an empty string (i.e clut_filename = ’’,
)

.. raw:: html

   <p>

(line 9): clut_file_legacy =True, if using legacy variable names in your
hjson file (map2loop-2 and prior), clut_file_legacy = False, if you are
using the current map2loop variable names in your hjson file (map2loop-3
onwards)

.. raw:: html

   <p>

(line 11 and 14): This is the folder name you specified in the “Naming
your .loop3d output file” section above

.. raw:: html

   <p>

(line 12): Specify the projection (CRS) that your shapefiles use
(e.g. working_projection = “EPSG:28354”,)

.. code:: ipython3

    proj = Project( 
        geology_filename = 'enter the full path of your lithology polygon shape file here',
        fault_filename = 'enter the full path of your linear features shape file here',
        fold_filename = 'enter the full path of your linear features shape file here',
        structure_filename = 'enter the full path of your orientation point data shape file here',
        dtm_filename = 'au', #if the area is in Australia you can leave this as 'au', otherwise specify full path to DTM
        config_filename = 'enter the full path of your hjson config file here',
        clut_filename = 'OPTIONAL, enter the full path of the csv file specifying unit colours',
        clut_file_legacy = True,
        verbose_level = VerboseLevel.ALL, #can set this to VerboseLevel.NONE if you don't wan't any feedback from the program
        tmp_path = "insert_output_folder_name_here", 
        working_projection = "EPSG:code",
        bounding_box = bounding_box,
        loop_project_filename = os.path.join("insert_output_folder_name_here", "local_source.loop3d")
    )

Setting Sampling Distances
~~~~~~~~~~~~~~~~~~~~~~~~~~

You’ll need to provide samping distances and minimums so that map2loop
knows what resolution you’d like to model in. #### CHANGE: The numeric
values for each of the following lines need to be altered to suit your
case study.

.. raw:: html

   <p>

(line 1): sets the minimum fault length in meters. Map2Loop will ignore
any faults below this numeric value

.. raw:: html

   <p>

(line 2): sets the sample spacing for geological contacts in meters

.. raw:: html

   <p>

(line 3): sets the sample decimator for structural measurements to
sample every nth measurement

.. code:: ipython3

    proj.set_minimum_fault_length(2000.0)
    proj.set_sampler(Datatype.GEOLOGY, SamplerSpacing(100.0))
    proj.set_sampler(Datatype.STRUCTURE, SamplerDecimator(100))

Selecting a Stratigraphic Column Sorter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are several different sorting algorithms that map2loop can use to
calculate the stratigraphic column. Choosing the ‘best’ of these sorters
may take some trial and error. There is also the option to allow
map2loop to choose the best sorter, or to specify the correct
stratigraphic sequence (see below or refer to the map2loop examples for
more information).

.. raw:: html

   <p>

The commands for the different sorters you can choose from are listed
below. Note if you want map2loop to select the best one, skip this step:

.. raw:: html

   </p>

.. raw:: html

   <p>

proj.set_sorter(SorterUseNetworkX()) This sorts units based on their
relationships, using a topological graph sorting algorithm.

.. raw:: html

   </p>

.. raw:: html

   <p>

proj.set_sorter(SorterAgeBased()) This sorts units based on their
minimum and maximum ages (if specified in the attributes table of the
lithology shape file).

.. raw:: html

   </p>

.. raw:: html

   <p>

proj.set_sorter(SorterAlpha()) This sorts units based on their adjacency
(the algorithm uses the number of neighbouring units to do this).

.. raw:: html

   </p>

.. raw:: html

   <p>

proj.set_sorter(SorterBeta()) –NOTE THIS MAY NOT BE WORKING YET This
sorts units based on their adjacency (the algorithm uses egde length to
calculate the order of units).

Running your map2loop program
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you’ve selected a sorter (optional), you will need to run the
program. There are 2 options to do this, depending on whether or not you
have used one of the above sorters.

.. raw:: html

   <p>

(Option 1): proj.run_all(take_best=True) This itterates through the
different sorters and selects the best based on the maximum basal
contact length. Use this option if you want map2loop to calculate the
‘best’ sorter.

.. raw:: html

   <p>

(Option 2): proj.run_all(take_best=False) Use this option if you
implemented any of the above sorters. The False flag ensures that the
specified sorting algorithm is used rather than the calculated ‘best’
option.

.. code:: ipython3

    proj.set_sorter(SorterAlpha())
    proj.run_all(take_best=False)
    
    t1 = time.time()

Alternative: Using a User Defined Stratigraphic Column
------------------------------------------------------

.. raw:: html

   <p>

Alternatively, you can run the program with a user defined stratigraphic
column. If you decide to do this, you’ll need to define the
stratigraphic column with the youngest unit at the top and the oldest at
the bottom as shown in the code below.

.. raw:: html

   <p>

To run the program use the command in line 9 below.

Skip the ‘Selecting a Stratigraphic Column Sorter’ and ‘Running your
map2loop program’ sections above.

.. code:: ipython3

     column = [
        # youngest
        'youngest_unit',
        'middle_unit',
        'oldest_unit',
        # oldest
     ]
        
    proj.run_all(user_defined_stratigraphic_column=column)
    
    t1 = time.time()

Next Steps
----------

The expected output from map2loop is a ‘.loop3d’ file. You can then pass
this file to Loop Structural to produce your 3D model.

Checking the Contents of your .loop3d file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. raw:: html

   <p>

If you’d like to inspect your loop3d output file via terminal
(e.g. Anaconda Prompt) you can do this with the command ncdump
loop3d_file_name.loop3d (e.g. ncdump local_source.loop3d). Ensure that
you’re in the correct working directory (i.e wherever you saved the
loop3d file). You can change directories using the ‘cd’ command. To use
the ncdump tool, you’ll need to ensure that you have netcdf4 installed
in your environment. You can check this by using the command ‘conda
list’ in your Anaconda environment and then scroll through the
applications to see if it is installed.

.. raw:: html

   <p>

Note that the output of ncdump will appear as text within the terminal.
