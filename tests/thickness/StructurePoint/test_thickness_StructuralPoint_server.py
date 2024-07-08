# # This test runs on a portion of the dataset in https://github.com/Loop3D/m2l3_examples/tree/main/Laurent2016_V2_variable_thicknesses (only for lithologies E, F, and G)
# # structures are confined to litho_F, and the test confirms if the StructuralPoint thickness is calculated, for all lithologies, if the thickness is correct for F (~90 m), and top/bottom units are assigned -1
# # this creates a temp folder in Appdata to store the data to run the proj, checks the thickness, and then deletes the temp folder
# # this was done to avoid overflow of file creation in the tests folder

# # this tests the thickness calculator Structural Point from a server

# #internal imports
# from map2loop.thickness_calculator import StructuralPoint
# from map2loop.project import Project
# from map2loop.m2l_enums import VerboseLevel

# #external imports
# import pathlib
# import pytest
# import requests
# import map2loop


# def test_from_aus_state():

#     bbox_3d = {
#         "minx": 515687.31005864,
#         "miny": 7493446.76593407,
#         "maxx": 562666.860106543,
#         "maxy": 7521273.57407786,
#         "base": -3200,
#         "top": 3000,
#     }
#     loop_project_filename = "wa_output.loop3d"
#     module_path = map2loop.__file__.replace("__init__.py", "")

#     try:
#         proj = Project(
#             use_australian_state_data="WA",
#             working_projection="EPSG:28350",
#             bounding_box=bbox_3d,
#             config_filename=pathlib.Path(module_path)
#             / pathlib.Path('_datasets')
#             / pathlib.Path('config_files')
#             / pathlib.Path('WA.json'),
#             clut_filename=pathlib.Path(module_path)
#             / pathlib.Path('_datasets')
#             / pathlib.Path('clut_files')
#             / pathlib.Path('WA_clut.csv'),
#             # clut_file_legacy=False,
#             verbose_level=VerboseLevel.NONE,
#             loop_project_filename=loop_project_filename,
#             overwrite_loopprojectfile=True,
#         )
        
#     except (requests.exceptions.RequestException, requests.exceptions.ReadTimeout) as e:
#         if "HTTPConnectionPool" in str(e) or isinstance(e, requests.exceptions.ReadTimeout): 
#             pytest.skip("Connection to the server timed out, skipping test")
#         else:
#             raise  # Re-raise the exception if it's not server unavailable

#     proj.set_thickness_calculator(StructuralPoint())
#     proj.run_all()
#     print("from the test", proj.stratigraphic_column.stratigraphicUnits.columns)
#     assert (
#         proj.thickness_calculator.sorter_label == "StructuralPoint"
#     ), 'Thickness_calc structural point not being set properly'
#     assert (
#         "ThicknessMedian" in proj.stratigraphic_column.stratigraphicUnits.columns
#     ), 'Thickness not being calculated in StructuralPointCalculator'
#     assert (
#         "ThicknessStdDev" in proj.stratigraphic_column.stratigraphicUnits.columns
#     ), 'Thickness std not being calculated in StructuralPointCalculator'
