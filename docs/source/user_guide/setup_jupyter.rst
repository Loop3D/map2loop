Setting up your Jupyter Notebook
================================
Now that you’ve created all of the required inputs for map2loop, you can set up a Jupyter notebook to run the code. In order to do this, you’ll need to create an Anaconda (or similar) environment with all the required dependencies. If you need help setting up your virtual environment, please refer to the Installation page. 

Map2loop calling code: 
---------------------
In order to ‘run’ map2loop, you need to pass the program several pieces of information, including:
 *	Shape file paths 
 *	Csv colour file path (optional) 
 *	DEM / DTM path 
 *	hjson config file that maps the attributes from your QGIS project onto the map2loop variables. 

An example code template for processing your QGIS map data using map2loop is provided under the Examples section on the map2loop website. The output from this code is a .loop3d file which can then be passed to LoopStructural to create your 3d model. 

Depending on the sorter algorithm you choose to use with map2loop (as described in the template), you’ll receive different outputs. If you use the take best sorter algorithm, you can expect an output similar to: 

      **Best sorter SorterAgeBased calculated contact length of 29632.67023438857**


Inspecting the .loop3d output file 
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
You can inspect your map2loop output file using the ncdump command via the terminal (e.g. Anaconda Prompt). In order to use this tool, you’ll need to ensure that you have netcdf4 installed in your environment. You can check this by using the command: ''**conda list**'' within your Anaconda environment. This will list all of the installed applications and dependencies. You’ll need to scroll through these to see if netcdf4 is installed. 
If you are able to use this tool, you can run it with the following command, where local_source.loop3d is the name of the output file that you named in the map2loop calling code (see the explanation in the Map2Loop template notebook).
      **ncdump local_source.loop3d**

Note: this command will only work if you are in the correct working directory (i.e wherever you saved the loop3d file). You can change directories using the **cd** command, followed by the directory path that you’d like to change to. 
The expected output of the ncdump command, is a series of text representing the tabulated data generated by map2loop. It will be output directly onto the terminal console. 

LoopStructural calling code 
---------------------------
Once you have run map2loop successfully, you can pass the produced .loop3d file to apt LoopStructural calling code, to produce a 3D model. 
There is an example of this code on the map2loop documentation page. It is also explained in the Loop Structural Calling Code Template. 


