import os
import sys
import setuptools

version = {}
package_root = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(package_root, "map2loop/version.py")) as fp:
    exec(fp.read(), version)
version = version["__version__"]

head, tail = os.path.split(sys.argv[0])


def get_description():
    long_description = ""
    readme_file = os.path.join(head, "README.md")
    with open(readme_file, "r") as fh:
        long_description = fh.read()
    return long_description


setuptools.setup(
    name="map2loop",
    version=version,
    author="The Loop Organisation",
    author_email="roy.thomson@monash.edu",
    description="Generate 3D model data from 2D maps.",
    long_description=get_description(),
    long_description_content_type="text/markdown",
    install_requires=[
        "numpy",
        # "gdal",
        "pandas",
        "geopandas",
        "shapely",
        "tqdm",
        "networkx",
        "owslib",
        "hjson",
        "loopprojectfile",
        "map2model",
        "beartype",
    ],
    url="https://github.com/Loop3D/map2loop",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    python_requires=">=3.8",
)
