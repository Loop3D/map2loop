Installing map2loop
===================

Install
-------------

You will need some flavour of conda (a python package manager, `see here <https://docs.anaconda.com/anaconda/install/index.html>`_), as well as Python ≥ 3.8

In addition, map2loop installation may run smoother if ```conda-forge``` is added to the channels. 
To check for that, run:

.. code-block::

   conda config --show channels


if conda-forge is not in the output, the channel can be added with:

.. code-block::

   conda config --add channels conda-forge



Express install:
~~~~~~~~~~~~~~~~

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
   git clone https://github.com/Loop3D/map2loop-3-notebooks


Navigate into the map2loop folder, and issue the following to install map2loop and its dependencies.

.. code-block::
   
   conda install -conda-forge -c loop3d --file dependencies.txt

To install map2loop in an editable environment run the following command:

.. code-block::

   pip install -e .


Building with Docker
---------------------

Fair warning, we recommend conda to almost everyone. With great software development power comes great environment setup inconvenience. 
You'll need to download and install the `docker containerisation software <https://docs.docker.com/get-docker/>`_, and the docker and docker-compose CLI.

Development with docker
~~~~~~~~~~~~~~~~~~~~~~~

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