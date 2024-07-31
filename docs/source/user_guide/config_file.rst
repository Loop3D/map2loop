Mapping attributes to variables using a JSON file
===================================================
Once you’ve completed your map in QGIS, you’ll need to map the attributes (with whatever names you’ve given them) to the variable names used in map2loop. You can map the attributes to the variable names used in version 2 or 3 of map2loop, as specified in the tables in the Setting up your Shapefiles section. 
An example json file is shown below, using map2loop-2 variable names (also known as Legacy code. If you decide to use map2loop-2 variable names, you will have to set the legacy flag to true in the map2loop calling code later on. If you use map2loop-3 variable names you'll need to set the legacy flag to false.
          
Feel free to copy the attached template and fill in the required variables with the attribute names specific to your project. 

Config File Template
---------------------
The templates below demonstrate how to setup a config file for map2loop. 
Explanations of the JSON file elements: 
                                                                       
 * The left most 'term' is the map2loop variable name 
 * The information after the hash on the right is a description of the required field. You can delete this from your own file if you'd like.
 * You'll need to change the attribute name in the second quotation to match your shapefile attribute names (e.g. change "INSERT_DIP" to your attribute name). Ensure that the attribute name is between '' or "".
 * Any lines with a *opt in the description string, means that they are optional. If you don't want to include them, just leave the attribute field blank (e.g. "g": '', )

For more information on the variables and map2loop requirements please see the documentation.
                                                                       
Legacy Variable Names (map2loop-2) Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
Note, there is an inbuilt converter within map2loop so you can use either of the config files with the most recent version of map2loop. 
`This <../_static/HJSON_TEMPLATE.hjson>`_ is an example of the legacy variables.

.. code-block:: python 

    {
  #ORIENTATION SHAPEFILE ATTRIBUTES
      "orientation_type": "dip direction",      #attribute containing dip information
      "dipdir_column": "INSERT_DIP_DIRECTION",  #attribute containing dip direction information
      "dip_column": "INSERT_DIP",               #attribute containing dip information
      "description_column": "INSERT_STRUCTURE_DESCRIPTION",  #*opt attribute containing type of structure (eg. S0, S1)
      "bedding_text": "INSERT_BEDDING_TEXT",    #*opt text defining bedding measurements in the "sf" field (eg "Bedding" or "S0")
      "overturned_column": "INSERT_OVERTURNED", #*opt attribute containing type of foliation
      "overturned_text": "INSERT_OVERTURNED_DESCRIPTION",  #*opt text defining overturned bedding measurements (eg. 'overturned')
      "objectid_column": "INSERT_ID",           #*opt attribute containing unique id of structural points
  #LITHOLOGY SHAPEFILE ATTRIBUTES
      "unitname_column": "INSERT_UNITNAME",     #attribute containing stratigraphic unit name (most specific)
      "alt_unitname_column": "INSERT_ALTERNATIVE_UNITNAME_CODE",  #attribute containing alternative stratigraphic unit name (eg unit code). Can be the same as "unitname_column"
      "group_column": "INSERT_GROUP",           #*opt attribute containing stratigraphic group
      "supergroup_column": "INSERT_SUPERGROUP", #*opt attribute containing stratigraphic supergroup (most coarse classification)
      "description_column": "INSERT_DESCRIPTION",  #*opt general description field
      "minage_column": "INSERT_MIN_AGE",        #*opt attribute containing minimum unit age
      "maxage_column": "INSERT_MAX_AGE",        #*opt attribute containing maximum unit age
      "rocktype_column": "INSERT_ROCKTYPE1",    #*opt attribute containing extra lithology information (can indicate intrusions)
      "alt_rocktype_column": "INSERT_ALTERNATIVE_ROCKTYPE",  #*opt attribute containing secondary rocktype information
      "sill_text": "INSERT_SILL_TEXT",          #*opt text defining a sill in the "ds" field (eg 'sill')
      "intrusive_text": "INSERT_INTRUSIVE_TEXT",  #*opt text defining an intrusion in the "r1" field (eg 'intrusion')
      "volcanic_text": "INSERT_VOLCANIC_TEXT",  #*opt text defining volcanics in the "ds" field (eg 'volcanic')
      "objectid_column": "INSERT_ID",           #*opt attribute containing unique object id (used in polygon and lineString shapefiles)
      "ignore_codes": ["INSERT_COVER_UNIT_CODES_TO_IGNORE"],  #*opt attribute containing codes to ignore
  #LINEAR FEATURES SHAPEFILE ATTRIBUTES
      "structtype_column": "INSERT_FEATURE_TYPE",  #attribute containing linear structure type (e.g. fault)
      "fault_text": "INSERT_FAULT_TEXT",        #text defining faults in the "f" field (eg. 'fault')
      "dip_null_value": "-999",                 #Default fault dip value, if 'fdip' field is empty
      "dipdir_flag": "num",                     #*opt specifies whether fdipdir is "num":numeric or other ("alpha")
      "dipdir_column": "INSERT_DIP_DIRECTION",  #*opt attribute containing the fault dip direction (defaults to -999)
      "dip_column": "INSERT_DIP",               #*opt attribute containing numeric fault dip value (defaults to fdipnull)
      "orientation_type": "dip direction",      #Set the measurement convention used (either 'strike' or 'dip direction')
      "dipestimate_column": "INSERT_DIP_ESTIMATE",  #*opt field for text fault dip estimate value (defaults to none)
      "dipestimate_text": "'NORTH_EAST','NORTH',<rest of cardinals>,'NOT ACCESSED'",  #*opt text used to estimate dip in increasing steepness, in "fdipest" field
      "name_column": "INSERT_FAULT_NAME",       #*opt attribute containing the fault name
      "objectid_column": "INSERT_ID",           #*opt attribute containing unique object id (used in polygon and lineString shapefiles)
  #LINEAR FEATURES SHAPEFILE ATTRIBUTES
      "structtype_column": "INSERT_FEATURE_TYPE",  #attribute containing linear structure type (e.g. fault)
      "fold_text": "INSERT_FOLD_TEXT",          #text defining folds in the "f" field (eg. 'fold')
      "description_column": "INSERT_FOLD_DESCRIPTION",  #*opt attribute containing type of fold
      "synform_text": "INSERT_SYNCLINE_TEXT",   #*opt text defining synclines in the "f" field (eg. 'syncline')
      "foldname_column": "INSERT_FOLD_NAME",    #*opt attribute containing the fold name
      "objectid_column": "INSERT_ID",           #*opt attribute containing unique object id (used in polygon and lineString shapefiles)
  }          

The following is an example filled out of a JSON config file: 
.. code-block:: python 

  {
  "structure" : {
    "orientation_type": "strike",
    "dipdir_column": "strike",
    "dip_column": "dip",
    "description_column": "feature",
    "bedding_text": "Bed",
    "overturned_column": "structypei",
    "overturned_text": "BEOI",
    "objectid_column": "geopnt_id",
  },
  "geology" : {
    "unitname_column": "unitname",
    "alt_unitname_column": "code",
    "group_column": "group_",
    "supergroup_column": "supersuite",
    "description_column": "descriptn",
    "minage_column": "min_age_ma",
    "maxage_column": "max_age_ma",
    "rocktype_column": "rocktype1",
    "alt_rocktype_column": "rocktype2",
    "sill_text": "is a sill",
    "intrusive_text": "intrusive",
    "volcanic_text": "volcanic",
    "objectid_column": "objectid",
    "ignore_codes": ["cover"],
  },
  "fault" : {
    "structtype_column": "feature",
    "fault_text": "Fault",
    "dip_null_value": "0",
    "dipdir_flag": "num",
    "dipdir_column": "dip_dir",
    "dip_column": "dip",
    "orientation_type": "dip direction",
    "dipestimate_column": "dip_est",
    "dipestimate_text": "gentle,moderate,steep",
    "name_column": "name",
    "objectid_column": "objectid",
  },
  "fold" : {
    "structtype_column": "feature",
    "fold_text": "Fold axial trace",
    "description_column": "type",
    "synform_text": "syncline",
    "foldname_column": "name",
    "objectid_column": "objectid",
  }
}

map2loop-3 variable names JSON File Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is a template with the most up-to date variable names. 
