.. map2loop documentation master file, created by
   sphinx-quickstart on Wed Jan 17 15:48:56 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Map2loop 3.0.x
====================================

Generate 3D geological model inputs from geolocial maps — a high-level implementation and extension of the original map2loop code developed by Prof. Mark Jessell at UWA. To see an example interactive model built with map2loop and LoopStructural, follow this link:

.. raw:: html
   :file: http://tectonique.net/models/brockman_syncline.html



Usage
------

Our notebooks cover use cases in more detail, but here is an example of processing Loop's South Australia remote geospatial data in just 20 lines of Python.

First, lets import map2loop and define a bounding box. You can use GIS software to find one. Remember what projection your coordinates are in!

.. code-block::

   from map2loop.project import Project
   from map2loop.m2l_enums import VerboseLevel

   # Note that this region is defined in the EPSG 28354 projection and
   # x and y represent easting and northing respectively
   bbox_3d = {
      'minx': 250805.1529856466,
      'miny': 6405084.328058686,
      'maxx': 336682.921539395,
      'maxy': 6458336.085975628,
      'base': -3200,
      'top': 1200
   }



Then, specify: the state, directory for the output, the bounding box and projection from above - and hit go! That's it.

.. code-block::

   proj = Project(use_australian_state_data = "SA",
                  working_projection = 'EPSG:28354',
                  bounding_box = bbox_3d,
                  loop_project_filename = "output.loop3d"
                  )

   proj.run_all()


This is a minimal example and a small part of Loop.

Our *documentation and other resources outline how to extend map2loop and port to the LoopStructural modelling engine. We are working to incorporate geophysical tools and best provide visualisation and workflow consolidation in the GUI.*

*Loop is led by Laurent Ailleres (Monash University) with a team of Work Package leaders from:*

- *Monash University: Roy Thomson, Lachlan Grose and Robin Armit*
- *University of Western Australia: Mark Jessell, Jeremie Giraud, Mark Lindsay and Guillaume Pirot*
- *Geological Survey of Canada: Boyan Brodaric and Eric de Kemp*



Known Issues and FAQs
~~~~~~~~~~~~~~~~~~~~~~~
- Developing with docker on Windows means you won't have GPU passthrough and can’t use a discrete graphics card in the container even if you have one.
- If Jupyter links require a token or password, it may mean port 8888 is already in use. To fix, either make docker map to another port on the host ie -p 8889:8888 or stop any other instances on 8888.

Links
~~~~~~

`https://loop3d.github.io/ <https://loop3d.github.io/>`_

`https://github.com/Loop3D/LoopStructural <https://github.com/Loop3D/LoopStructural>`_



.. toctree::
   :hidden:

   user_guide/index
   _auto_examples/index
   CHANGLOG.md

.. autosummary::
   :caption: API
   :toctree: _autosummary
   :template: custom-module-template.rst
   :recursive:

   map2loop
