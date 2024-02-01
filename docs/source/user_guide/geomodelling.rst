Creating a 3D geological model
------------------------------
This is a step-by-step tutorial designed to help you get started with using Loop’s python libraries to create a 3D geological model. 
This piece covers how to use map2loop to convert a QGIS map into a loop3d file, which can in turn be used by LoopStructural to create a 3D geological model. 

Getting Started
===============
map2loop takes 3 shapefile inputs and generates a ‘.loop3d’ output file, which can be transformed into a 3D geological model using the LoopStructural library. 
Please note that the names used for shapefiles and attributes throughout this tutorial are examples. You can name these as you see fit, provided you refer to your names within the calling code as explained towards the end of this guide.

Required Shape Files 
....................
In order to use map2loop, you will first need to create a digital QGIS map containing three shapefiles as specified in the table below:

.. list-table:: 
   :widths: 25 100 25
   :header-rows: 1

   * - Shape file example name
     - Shape file description 
     - QGIS Geometry Type 
   * - Lithologies.shp
     - Represents contacts (eg. lithologies) as different polygons on your QGIS map
     - Polygon
   * - Linear_Features.shp
     - Represents linear features (eg faults and axial traces), as lines on your QGIS map
     - LineString
   * - Orientation_data.shp
     - Represents orientation data (eg. bedding measurements, foliations etc) as points on your QGIS map
     - Point 
Notes:
~~~~~
* If your map doesn’t have any faults in it, you will need to create a blank lineString shapefile to pass map2loop as an input. 
* Axial trace data is not yet used by map2loop, so irrespective of whether you include it in the line shape file, you will have to manually add axial traces using LoopStructural. 
* Faults are currently modelled using a single orientation measurement (dip and dip direction). This makes it difficult to model faults with changing dip using map2loop. This issue is currently being worked on, but in the meantime if you would like to model complex fault systems it may be best to use LoopStructural to generate these. 

Shape File Attribute Table Requirements 
=======================================
This section covers the required attributes that each shape file should contain, within the QGIS attributes table. Please note that you can name attributes whatever you’d like, as long as they contain the information specified below. 

Point Shapefile
...............

This file contains point data that is used to represent orientation data (e.g. bedding and foliation measurements).

.. list-table:: **Orientation_data.shp**
   :widths: 20 25 20 20 20 50
   :header-rows: 1

   * - Example Attribute name in QGIS
     - Variable name in map2loop-3
     - Variable name in map2loop-2 (ie Legacy code)
     - Data Type 
     - Required/ optional
     - Description 
   * - Strike
     - “dipdir_column”
     - “dd”
     - Integer
     - Required
     - Strike (using the right hand rule)
   * - Dip 
     - "dip_column"
     - “d”
     - Integer
     - Required
     - Dip 
   * - Desc
     - "desciption_column"
     - “sf”
     - String
     - Optional
     - Description field about structural measurements. This could be a specification about deformation event or foliation type (eg. ‘s0’).
   * - bo
     - "overturned_column"
     - 'bo'
     - String 
     - Optional 
     - Text field indicating if bedding measurements are overturned (eg. ‘overturned’)
   * - 
     - 
     - 
     - 
     - 
     - 
   * - 
     - 
     - 
     - 
     - 
     - 







