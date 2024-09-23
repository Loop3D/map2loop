"""See pyproject.toml for project metadata."""

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import os
import sys
import pybind11

class get_gdal_include_dirs:
    """Helper class to determine the GDAL include directories from vcpkg."""
    def __str__(self):
        vcpkg_root = os.getenv('VCPKG_ROOT', '/vcpkg/installed/vcpkg/')  # Replace with actual path or set VCPKG_ROOT
        if sys.platform == 'win32':
            return os.path.join(vcpkg_root, 'installed', 'x64-windows', 'include')
        elif sys.platform == 'darwin':
            return os.path.join(vcpkg_root, 'installed', 'x64-osx', 'include')
        else:
            return os.path.join(vcpkg_root, 'installed', 'x64-linux', 'include')

class get_gdal_library_dirs:
    """Helper class to determine the GDAL library directories from vcpkg."""
    def __str__(self):
        vcpkg_root = os.getenv('VCPKG_ROOT', '/vcpkg/installed/vcpkg/')  # Replace with actual path or set VCPKG_ROOT
        if sys.platform == 'win32':
            return os.path.join(vcpkg_root, 'installed', 'x64-windows', 'lib')
        elif sys.platform == 'darwin':
            return os.path.join(vcpkg_root, 'installed', 'x64-osx', 'lib')
        else:
            return os.path.join(vcpkg_root, 'installed', 'x64-linux', 'lib')

ext_modules = [
    Extension(
        'your_module',  # Name of the module
        sources=['map2loop/gdal_extension.cpp'],  # Source file
        include_dirs=[
            pybind11.get_include(),
            get_gdal_include_dirs()
        ],
        library_dirs=[
            get_gdal_library_dirs()
        ],
        libraries=[
            'gdal'  # Link against GDAL
        ],
        language='c++',
        extra_compile_args=['-std=c++14'] if not sys.platform == 'win32' else ['/std:c++14'],
    ),
]

package_root = os.path.abspath(os.path.dirname(__file__))

version = {}
with open(os.path.join(package_root, "map2loop/version.py")) as fp:
    exec(fp.read(), version)
version = version["__version__"]

setup()
