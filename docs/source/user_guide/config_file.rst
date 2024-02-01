Mapping attributes to variables using an HJSON file
===================================================
Once you’ve completed your map in QGIS, you’ll need to map the attributes (with whatever names you’ve given them) to the variable names used in map2loop. You can map the attributes to the variable names used in version 2 or 3 of map2loop, as specified in the tables in the Setting up your Shapefiles section. 
An example hjson file is shown below, using map2loop-2 variable names (also known as Legacy code. If you decide to use map2loop-2 variable names, you will have to set the legacy flag to true in the map2loop calling code later on. If you use map2loop-3 variable names you'll need to set the legacy flag to false.
          
Feel free to copy the attached template and fill in the required variables with the attribute names specific to your project. 

Config File Template
---------------------
The templates below demonstrate how to setup a config file for map2loop. 
Explanations of the HJSON file elements: 
                                                                       
 * The left most 'term' is the map2loop variable name 
 * The information after the hash on the right is a description of the required field. You can delete this from your own file if you'd like.
 * You'll need to change the attribute name in the second quotation to match your shapefile attribute names (e.g. change "INSERT_DIP" to your attribute name). Ensure that the attribute name is between '' or "".
 * Any lines with a *opt in the description string, means that they are optional. If you don't want to include them, just leave the attribute field blank (e.g. "g": '', )

For more information on the variables and map2loop requirements please see the documentation.
                                                                       
Legacy Variable Names (map2loop-2) Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
Note, there is an inbuilt converter within map2loop so you can use either of the config files with the most recent version of map2loop.
                                                                       
.. codeblock:: JSON
  {
   #ORIENTATION SHAPEFILE ATTRIBUTES
      "d": "INSERT_DIP",                        #attribute containing dip information
      "dd": "INSERT_DIP_DIRECTION",             #attribute containing dip direction information
      "otype": 'dip direction',                 #Set the measurement convention used (either 'strike' or 'dip direction')
      "sf": 'INSERT_STRUCTURE_DESCRIPTION',     #*opt attribute containing type of structure (eg. S0, S1)
      "bedding": 'INSERT_BEDDING_TEXT',         #*opt text defining bedding measurements in the "sf" field (eg "Bedding" or "S0")
      "bo": 'INSERT_FOLIATION_DESCRIPTION',     #*opt attribute containing type of foliation
      "btype": 'OVERTURNED_BEDDING_TEXT',       #*opt text defining overturned bedding measurements in the "bo" field (eg. 'overturned')
   #LITHOLOGY SHAPEFILE ATTRIBUTES
      "c": 'INSERT_UNIT_NAME',                  #attribute containing stratigraphic unit name (most specific)
      "u": 'INSERT_ALT_UNIT_NAME',              #attribute containing alternative stratigraphic unit name (eg unit code). Can be the same as 'c'
      "g": 'INSERT_GROUP',                      #*opt attribute containing stratigraphic group
      "g2": 'INSERT_SUPERGROUP',                #*opt attribute containing stratigraphic supergroup (most coarse classification)
      "ds": 'INSERT_DESCRIPTION',               #*opt general description field
      "r1": 'INSERT_ROCKTYPE',                  #*opt attribute containing extra lithology information (can indicate intrusions)
      "r2": 'INSERT_ROCKTYPE2',                 #*opt attribute containing secondary rocktype information
      "sill": 'INSERT_SILL_TEXT',               #*opt text defining a sill in the "ds" field (eg 'sill')
      "intrusive": 'INSERT_INTRUSIVE_TEXT',     #*opt text defining an intrusion in the "r1" field (eg 'intrusion')
      "volcanic": 'INSERT_VOLCANIC_TEXT',       #*opt text defining volcanics in the "ds" field (eg 'volcanic')
      "min": 'INSERT_MIN_AGE',                  #*opt attribute containing minimum unit age
      "max": 'INSERT_MAX_AGE',                  #*opt attribute containing maximum unit age
    #LINEAR FEATURES SHAPEFILE ATTRIBUTES
      "f": 'INSERT_STRUCT_TYPE',                #attribute containing linear structure type (e.g. fault)
      "fault": 'fault',                         #text defining faults in the "f" field (eg. 'fault')
      "fdip": 'INSERT_FAULT_DIP',               #*opt attribute containing numeric fault dip value (defaults to fdipnull)
      "fdipnull": '0',                          #Default fault dip value, if 'fdip' field is empty
      "fdipdir": 'INSERT_FAULT_DIP_DIRECTION',  #*opt attribute containing the fault dip direction (defaults to -999)
      "fdipdir_flag": 'num',                    #*opt specifies whether fdipdir is "num":numeric or other ("alpha")
      "fdipest": 'INSERT_DIP_EST_TEXT',         #*opt field for text fault dip estimate value (defaults to none)
      "fdipest_vals": 'INSERT_DIP_EST_TERMS',   #*opt text used to estimate dip in increasing steepness, in "fdipest" field
      "n": 'INSERT_FAULT_NAME',                 #*opt attribute containing the fault name
    #GENERAL IDS
      "o": 'INSERT_OBJ_ID',                     #*opt attribute containing unique object id (used in polygon and lineString shapefiles
      "gi": 'INSERT_ORI_ID',                    #*opt attribute containing unique id of structural points
    }
                                                                      
map2loop-3 variable names HJSON File Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`This <../_static/HJSON_TEMPLATE.hjson>`_ This is a template with the most up-to date variable names. 
