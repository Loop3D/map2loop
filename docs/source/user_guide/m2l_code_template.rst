Map2loop calling code Template
------------------------------
This is a basic template for the calling code that can be used to run Map2Loop. The output of the program will be a '.loop3d' file, which can be passed directly to LoopStructural to produce your 3D model.

An attempt has been made to explain the code as much as possible. In your own notebook, you may want to get rid of the explanatory comments (any lines starting with a '#', and text cells). This won't affect the program's functionality.

Before You Begin
,,,,,,,,,,,,,,,,
In order to run map2loop you will need the following files:
  #. Polygon shapefile containing your lithologies
  #. LineString shapefile containing your linear features (e.g. faults)
  #. Point data shapefile containing orientation data
  #. hjson file defining the attribute names used in your shapefiles

If you need help setting up these files please refer to the map2loop examples which provide a step-by-step guide.

Setting up your notebook
,,,,,,,,,,,,,,,,,,,,,,,,
In order for your map2loop code to funtion correctly, you need to import all of the neccessary python libraries. In simple terms, imports allow different code modules to speak to eachother.

  ..code-block:: python
    import os
    from map2loop.project import Project
    from map2loop.m2l_enums import VerboseLevel
    from map2loop.m2l_enums import Datatype
    from map2loop.sampler import SamplerSpacing, SamplerDecimator
    from map2loop.sorter import SorterUseHint, SorterUseNetworkX, SorterAgeBased, SorterAlpha
    import time
