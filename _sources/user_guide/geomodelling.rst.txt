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
   * - geopnt_id
     - "objectid_column"
     - ‘gi’
     - Integer / String
     - Optional 
     - Field to specify a unique id of structural measurement 

An example of the QGIS attribute table for simple orientation data is shown in the image below: 

.. image:: _static/images/ori_attributes_table.png
   :width: 400

LineString Shapefile 
......................
This shapefile contains lineStrings that represent fault traces at the surface. Axial traces can also be included in this shape file, however map2loop doesn’t yet have the capability to include fold axes in the 3D model. If you’d like to include fold axes, you will have to do so using LoopStructural.

.. list-table:: **Linear_Features.shp**
   :widths: 20 25 20 20 20 50
   :header-rows: 1

   * - Example Attribute name in QGIS
     - Variable name in map2loop-3
     - Variable name in map2loop-2 (ie Legacy code)
     - Data Type 
     - Required/ optional
     - Description 
   * - Feature
     - "structtype_column"
     - "f"
     - String
     - Required   
     - Field that contains information about the type of structure (eg. ‘fault’)
   * - Plunge
     - "dip_column"
     - "fdip"
     - Integer 
     - Optional 
     - Fault dip value. Note if a fault dip isn’t provided the default value defined by ‘fdipnull’ will be used
   * - Dip Direct
     - "dipdir_column"
     - “fdipdir”
     - Integer 
     - Required 
     - Fault dip direction – calculate this as the strike using the RHR ±90 degrees
   * - Name
     - "name_column"
     - “n”
     - String 
     - Optional
     - Name of the feature 

An example of the QGIS attribute table for a single fault is shown in the image below: 

.. image:: _static/images/fault_attributes_table.png
   :width: 400


Polygon Shapefile 
...................
This contains polygons representing different lithologies and the contacts between them.

.. list-table:: **Lithologies.shp**
   :widths: 20 25 20 20 20 50
   :header-rows: 1

   * - Example Attribute name in QGIS
     - Variable name in map2loop-3
     - Variable name in map2loop-2 (ie Legacy code)
     - Data Type 
     - Required/ optional
     - Description 
   * - supersuite
     - "group_column"
     - “g”
     - String
     - Optional
     - Most coarse stratigraphic unit classification (e.g. supergroup)
   * - group
     - "supergroup_column"
     - "g2"
     - String
     - Optional 
     - Coarser stratigraphic group classification (e.g. group)
   * - Lithology
     - "unitname_column"
     - "c"
     - String
     - Required
     - Most specific stratigraphic unit names (eg. member, formation etc)
   * - Descript
     - "description_column"
     - "ds"
     - String
     - Optional 
     - General description field 
   * - Alt_unit
     - "alt_unitname_column"
     - "u"
     - String
     - Required
     - Field containing alternate stratigraphic unit names
   * - r1
     - "rocktype_column"
     - "r1"
     - String
     - Optional
     - Contains rocktype information (e.g. intrusion)
   * - r2
     - "alt_rocktype_column"
     - "r2"
     - String
     - Optional 
     - Secondary rock type field
   * - min_age
     - "minage_column"
     - "min"
     - Integer
     - Optional 
     - Minimum unit age
   * - max_age
     - "maxage_column"
     - "max"
     - Integer
     - Optional 
     - Maximum unit age

A simple example of the QGIS attribute table for lithology data is shown in the image below: 

.. image:: _static/images/litho_attributes_table.png
   :width: 400

Tips and Trouble Shooting for QGIS map 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* 	Ensure that there are no gaps between your polygons. You may find it helpful to use the ‘snapping tool’ in QGIS. 
*  Map2loop sometimes glitches with white spaces. You may need to replace spaces in names with underscores (for example: Emu Egg Fault becomes Emu_Egg_Fault)
*	If you want to force a stratigraphic sequence but don’t want to but in absolute unit ages, you can number the units with relative ‘age’ values in order (eg, 1, 2, 3, 4). To do this set the min and max ages to the relevant sequence number. This is demonstrated in the image above.

Adding Data 
===========
Once you’ve set up the aforementioned shapefiles, you can start to add your data into the corresponding QGIS layers. 

Tip
~~~

* If you are working in a complex system, or an area with fine geological detail, you may need to upscale your data. It is usually easier to start modelling the large scale structures and then you can try to add in relevant detail once you have a decent model. 
