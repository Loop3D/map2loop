"""See pyproject.toml for project metadata."""
from setuptools import setup, Extension
from Cython.Build import cythonize
import logging
import os
from pathlib import Path
import platform
import sys
logger = logging.getLogger(__name__)

def copy_data_tree(datadir, destdir):
    if os.path.exists(destdir):
        shutil.rmtree(destdir)
    shutil.copytree(datadir, destdir)



def read_response(cmd):
    return subprocess.check_output(cmd).decode("utf").strip()

# Get GDAL config from gdal-config command
def get_gdal_config():
    """
    Obtain the paths and version for compiling and linking with the GDAL C-API.

    GDAL_INCLUDE_PATH, GDAL_LIBRARY_PATH, and GDAL_VERSION environment variables
    are used if all are present.

    If those variables are not present, gdal-config is called (it should be
    on the PATH variable). gdal-config provides all the paths and version.

    If no environment variables were specified or gdal-config was not found,
    no additional paths are provided to the extension. It is still possible
    to compile in this case using custom arguments to setup.py.
    """
    include_dir = os.environ.get("GDAL_INCLUDE_PATH")
    library_dir = os.environ.get("GDAL_LIBRARY_PATH")
    gdal_version_str = os.environ.get("GDAL_VERSION")

    if include_dir and library_dir and gdal_version_str:
        gdal_libs = ["gdal"]

        if platform.system() == "Windows":
            # NOTE: if libgdal is built for Windows using CMake, it is now "gdal",
            # but older Windows builds still use "gdal_i"
            if (Path(library_dir) / "gdal_i.lib").exists():
                gdal_libs = ["gdal_i"]

        return {
            "include_dirs": [include_dir],
            "library_dirs": [library_dir],
            "libraries": gdal_libs,
        }, gdal_version_str

    if include_dir or library_dir or gdal_version_str:
        logger.warning(
            "If specifying the GDAL_INCLUDE_PATH, GDAL_LIBRARY_PATH, or GDAL_VERSION "
            "environment variables, you need to specify all of them."
        )

    try:
        # Get libraries, etc from gdal-config (not available on Windows)
        flags = ["cflags", "libs", "version"]
        gdal_config = os.environ.get("GDAL_CONFIG", "gdal-config")
        config = {flag: read_response([gdal_config, f"--{flag}"]) for flag in flags}

        gdal_version_str = config["version"]
        include_dirs = [entry[2:] for entry in config["cflags"].split(" ")]
        library_dirs = []
        libraries = []
        extra_link_args = []

        for entry in config["libs"].split(" "):
            if entry.startswith("-L"):
                library_dirs.append(entry[2:])
            elif entry.startswith("-l"):
                libraries.append(entry[2:])
            else:
                extra_link_args.append(entry)

        return {
            "include_dirs": include_dirs,
            "library_dirs": library_dirs,
            "libraries": libraries,
            "extra_link_args": extra_link_args,
        }, gdal_version_str

    except Exception as e:
        if platform.system() == "Windows":
            # Get GDAL API version from the command line if specified there.
            if "--gdalversion" in sys.argv:
                index = sys.argv.index("--gdalversion")
                sys.argv.pop(index)
                gdal_version_str = sys.argv.pop(index)
            else:
                print(
                    "GDAL_VERSION must be provided as an environment variable "
                    "or as --gdalversion command line argument"
                )
                sys.exit(1)

            logger.info(
                "Building on Windows requires extra options to setup.py to locate "
                "GDAL files. See the installation documentation."
            )
            return {}, gdal_version_str

        else:
            raise e
        
MIN_PYTHON_VERSION = (3, 8, 0)
MIN_GDAL_VERSION = (3, 7, 0)
ext_options, gdal_version_str = get_gdal_config()
gdal_version = tuple(int(i) for i in gdal_version_str.strip("dev").split("."))
if not gdal_version >= MIN_GDAL_VERSION:
    sys.exit(f"GDAL must be >= {'.'.join(map(str, MIN_GDAL_VERSION))}")
# Define the extension module
extensions = [
    Extension(
        name="gdal_wrapper",
        sources=["./map2loop/gdal_wrapper/gdal_wrapper.pyx"],
        include_dirs=[ext_options["include_dirs"]],
        library_dirs=[ext_options["library_dirs"]],
        libraries=[ext_options["libraries"]],
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
