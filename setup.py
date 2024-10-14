"""See pyproject.toml for project metadata."""
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from Cython.Build import cythonize
import logging
import os
from pathlib import Path
import platform
import sys
import subprocess
import shutil
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
        
# MIN_PYTHON_VERSION = (3, 8, 0)
# MIN_GDAL_VERSION = (3, 1, 0)
# ext_options, gdal_version_str = get_gdal_config()
# gdal_version = tuple(int(i) for i in gdal_version_str.strip("dev").split("."))
# if not gdal_version >= MIN_GDAL_VERSION:
#     sys.exit(f"GDAL must be >= {'.'.join(map(str, MIN_GDAL_VERSION))}")
    
# ext_modules = []
# package_data = {}

# # setuptools clean does not cleanup Cython artifacts
# if "clean" in sys.argv:
#     for directory in ["build"]:
#         if os.path.exists(directory):
#             shutil.rmtree(directory)

#     root = Path(".")
#     for ext in ["*.so", "*.pyc", "*.c", "*.cpp"]:
#         for entry in root.rglob(ext):
#             entry.unlink()

# elif "sdist" in sys.argv or "egg_info" in sys.argv:
#     # don't cythonize for the sdist
#     pass

# else:
#     if cythonize is None:
#         raise ImportError("Cython is required to build from source")

ext_options, gdal_version_str = get_gdal_config()

# gdal_version = tuple(int(i) for i in gdal_version_str.strip("dev").split("."))
# if not gdal_version >= MIN_GDAL_VERSION:
#     sys.exit(f"GDAL must be >= {'.'.join(map(str, MIN_GDAL_VERSION))}")

# compile_time_env = {
#     "CTE_GDAL_VERSION": gdal_version,
# }


# # Define the extension module
# ext_modules = [
#     Extension(
#         name="gdal_wrapper",
#         sources=["./map2loop/gdal_wrapper/gdal_wrapper.pyx"],
#         include_dirs=ext_options["include_dirs"],
#         library_dirs=ext_options["library_dirs"],
#         libraries=ext_options["libraries"],
#         extra_compile_args=["-std=c++11"], 
#         compiler_directives={"language_level": "3"},
#         compile_time_env=compile_time_env
#     )
# ]

class BuildGDAL(build_ext):
    def run(self):
        # Build GDAL as a static library
        gdal_dir = os.path.abspath('map2loop/gdal/gdal_sources')
        build_dir = os.path.join(gdal_dir, 'build')
        install_dir = os.path.join(build_dir, 'install')

        # Configure GDAL
        configure_cmd = [
            './configure',
            '--prefix=' + install_dir,
            '--disable-shared',
            '--enable-static',
            '--with-pic',
            '--without-python',
            '--without-libtiff',  # Adjust according to dependencies
            '--without-libjpeg',
            '--without-pg',  # Disable PostgreSQL support if not needed
            # Add other configuration options as needed
        ]

        subprocess.check_call(configure_cmd, cwd=gdal_dir)

        # Build and install GDAL
        subprocess.check_call(['make', '-j4'], cwd=gdal_dir)
        subprocess.check_call(['make', 'install'], cwd=gdal_dir)

        # Build the GDAL Python bindings
        gdal_python_dir = os.path.join(gdal_dir, 'swig', 'python')
        env = os.environ.copy()
        env['CPLUS_INCLUDE_PATH'] = os.path.join(install_dir, 'include')
        env['C_INCLUDE_PATH'] = os.path.join(install_dir, 'include')
        env['LD_LIBRARY_PATH'] = os.path.join(install_dir, 'lib')

        subprocess.check_call(
            ['python', 'setup.py', 'build_ext', '--include-dirs=' + os.path.join(install_dir, 'include'),
             '--library-dirs=' + os.path.join(install_dir, 'lib')],
            cwd=gdal_python_dir,
            env=env
        )

        # Copy built extensions to map2loop package
        # Assuming the built extensions are in gdal_python_dir/build/lib...
        built_lib_dir = os.path.join(gdal_python_dir, 'build', 'lib.*')
        self.copy_extensions_to_source()

        # Continue with the standard build_ext
        build_ext.run(self)

# Define GDAL Extension Module
gdal_module = Extension(
    'map2loop.gdal._gdal',
    sources=[],  # No sources needed since we're linking statically
    include_dirs=[
        os.path.join('map2loop', 'gdal_source', 'build', 'install', 'include'),
    ],
    library_dirs=[
        os.path.join('map2loop', 'gdal_source', 'build', 'install', 'lib'),
    ],
    libraries=['gdal'],
    extra_link_args=['-static'],
)

package_root = os.path.abspath(os.path.dirname(__file__))

version = {}
with open(os.path.join(package_root, "map2loop/version.py")) as fp:
    exec(fp.read(), version)
version = version["__version__"]

setup(
    ext_modules=[gdal_module], 
    cmdclass={
        'build_ext': BuildGDAL,
    },
    )
