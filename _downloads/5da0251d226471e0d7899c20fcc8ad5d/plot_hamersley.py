"""
============================
Hamersley, Western Australia
============================
"""
import time
import os
from map2loop.project import Project
from map2loop.m2l_enums import VerboseLevel, Datatype
from map2loop.sorter import (
    SorterAlpha,
    SorterAgeBased,
    SorterUseHint,
    SorterUseNetworkX,
    SorterMaximiseContacts,
    SorterObservationProjections,
)
from map2loop.sampler import SamplerSpacing
from datetime import datetime

####################################################################
# Set the region of interest for the project
# -------------------------------------------
# Define the bounding box for the ROI

bbox_3d = {
    "minx": 515687.31005864,
    "miny": 7493446.76593407,
    "maxx": 562666.860106543,
    "maxy": 7521273.57407786,
    "base": -3200,
    "top": 3000,
}

# Specify minimum details (which Australian state, projection and bounding box
# and output file)
loop_project_filename = "wa_output.loop3d"
proj = Project(
    use_australian_state_data="WA",
    working_projection="EPSG:28350",
    bounding_box=bbox_3d,
    verbose_level=VerboseLevel.NONE,
    loop_project_filename=loop_project_filename,
)

# Set the distance between sample points for arial and linestring geometry
proj.set_sampler(Datatype.GEOLOGY, SamplerSpacing(200.0))
proj.set_sampler(Datatype.FAULT, SamplerSpacing(200.0))

# Choose which stratigraphic sorter to use or run_all with "take_best" flag to run them all
proj.set_sorter(SorterAlpha())
# proj.set_sorter(SorterAgeBased())
# proj.set_sorter(SorterUseHint())
# proj.set_sorter(SorterUseNetworkx())
# proj.set_sorter(SorterMaximiseContacts())
# proj.set_sorter(SorterObservationProjections())
proj.run_all(take_best=True)

####################################################################
# Visualise the map2loop results
# -------------------------------------------

proj.map_data.basal_contacts.plot()
