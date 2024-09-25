"""See pyproject.toml for project metadata."""
from setuptools import setup, Extension
from Cython.Build import cythonize
import os


# Get GDAL include path
gdal_config_cmd = os.popen("gdal-config --cflags").read().strip()
gdal_include_dir = gdal_config_cmd.replace("-I", "")

# Get GDAL library path
gdal_lib_cmd = os.popen("gdal-config --libs").read().strip()
gdal_library_dirs = [gdal_lib_cmd.split("-L")[1].split()[0]]

# Define the extension module
extensions = [
    Extension(
        name="gdal_wrapper",
        sources=["./map2loop/gdal_wrapper.pyx"],
        include_dirs=[gdal_include_dir],
        library_dirs=gdal_library_dirs,
        libraries=["gdal"],
        extra_compile_args=["-std=c++11"]
    )
]

package_root = os.path.abspath(os.path.dirname(__file__))

version = {}
with open(os.path.join(package_root, "map2loop/version.py")) as fp:
    exec(fp.read(), version)
version = version["__version__"]

setup(
    ext_modules=cythonize(extensions)
    )
