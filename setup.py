"""See pyproject.toml for project metadata."""

import os
from setuptools import setup

package_root = os.path.abspath(os.path.dirname(__file__))

# Get the version from the version.py file
version = {}
with open(os.path.join(package_root, "map2loop/version.py")) as fp:
    exec(fp.read(), version)
version = version["__version__"]

# Read dependencies from dependencies.txt
requirements_file = os.path.join(package_root, "dependencies.txt")
with open(requirements_file, 'r') as f:
    install_requires = [line.strip() for line in f if line.strip()]

setup(
    name="map2loop",
    install_requires=install_requires,
    version=version,
    license="MIT",
    package_data={
        # Include test files:
        '': ['tests/*.py'],
    },
)