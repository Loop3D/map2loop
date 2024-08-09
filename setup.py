"""See pyproject.toml for project metadata."""

from setuptools import setup
import os

package_root = os.path.abspath(os.path.dirname(__file__))

version = {}
with open(os.path.join(package_root, "map2loop/version.py")) as fp:
    exec(fp.read(), version)
version = version["__version__"]
setup()
