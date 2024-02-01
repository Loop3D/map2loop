Getting Started
===============
map2loop is a python library that improves the ease and accessibility of 3D modelling with Loop. It enables you to create 3D geological models from digital maps produced in programs such as GIS. map2loop's role within the Loop3D ecosystem is to automatically convert digital map data into a useable format. The generated ‘.loop3d’ output file can then be transformed into a 3D geological model using the LoopStructural library.

map2loop Requirements
......................
In order to run map2loop you will need the following input files:

#.  Polygon shapefile containing your lithologies
#.  LineString shapefile containing your linear features (e.g. faults)
#.  Point data shapefile containing orientation data
#.  hjson config file, used to map the attribute names used in your shapefiles to map2loop's variables

Additional useful inputs: 

* DEM or DTM file for your map region 
* Optional CSV file specifying unit colours

If you need help setting up these files please refer to the relevant map2loop user pages or to the examples which provide a step-by-step guide. 
