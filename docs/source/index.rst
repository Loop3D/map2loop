.. map2loop documentation master file, created by
   sphinx-quickstart on Wed Jan 17 15:48:56 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Map2loop 3.0.x
====================================

Generate 3D geological model inputs from geographical maps — a high-level implementation and extension of the original map2loop code developed by Prof. Mark Jessell at UWA. To see an example interactive model built with map2loop and LoopStructural, follow this link:

.. raw:: html
   :file: http://tectonique.net/models/brockman_syncline.html

Install
-------------

You will need some flavour of conda (a python package manager, `see here <https://docs.anaconda.com/anaconda/install/index.html>`_), as well as Python ≥ 3.8

To just install map2loop run the following command

.. code-block::

   conda install -c conda-forge -c loop3d map2loop -y



Development
~~~~~~~~~~~~

If you want to tinker yourself/contribute, clone the source code with

.. code-block::

   git clone https://github.com/Loop3D/map2loop.git

Or get the source + example notebooks with

.. code-block::

   git clone https://github.com/Loop3D/map2loop.git


Navigate into map2loop, and issue the following to install map2loop and its dependencies.

.. code-block::

   conda install -c loop3d --file dependencies.txt
   pip install .

To install map2loop in an editable environment run the following command:

.. code-block::

   pip install -e .


Building with Docker
---------------------

Fair warning, we recommend conda to almost everyone. With great software development power comes great environment setup inconvenience. 
You'll need to download and install the `docker containerisation software <https://docs.docker.com/get-docker/>`_, and the docker and docker-compose CLI.

Development
~~~~~~~~~~~~~

1. Clone this repo and navigate inside as per above
2. Run the following and click on the Jupyter server forwarded link to access and edit the notebooks

.. code-block::

   docker-compose up --build
   

3. To hop into a bash shell in a running container, open a terminal and issue

.. code-block::

      docker ps
   

Find the container name or ID and then run

.. code-block::

      docker exec -it <container_NAMEorID> bash
      # Probably -> docker exec -it  map2loop_dev_1 bash

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

   getting_started/index
   _auto_examples/index
   user_guide/index

.. autosummary::
   :caption: API
   :toctree: _autosummary
   :template: custom-module-template.rst
   :recursive:

   map2loop
