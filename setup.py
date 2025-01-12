from setuptools.command.sdist import sdist as _sdist
import shutil
from setuptools import setup, find_packages
from pathlib import Path

<<<<<<< HEAD
<<<<<<< HEAD
# Resolve the absolute path to the directory containing this file:
package_root = Path(__file__).resolve().parent
=======
import os
from setuptools import setup

package_root = os.path.abspath(os.path.dirname(__file__))
>>>>>>> 7978841 (feat: v3.2 (#153))
=======
# Resolve the absolute path to the directory containing this file:
package_root = Path(__file__).resolve().parent
>>>>>>> b33532b (fix: include dependencies in site-packages  - issue #169 (#170))

# Get the version from the version.py file
version = {}
version_file = package_root / "map2loop" / "version.py"
with version_file.open() as fp:
    exec(fp.read(), version)

# Read dependencies from dependencies.txt
<<<<<<< HEAD
<<<<<<< HEAD
requirements_file = package_root / "dependencies.txt"
with requirements_file.open("r") as f:
    install_requires = [line.strip() for line in f if line.strip()]


class CustomSDist(_sdist):

    def make_release_tree(self, base_dir, files):
        # 1) Let the normal sdist process run first.
        super().make_release_tree(base_dir, files)
        map2loop_dir = Path(base_dir) / "map2loop"

        # 2) Specify which files to move from the root to map2loop/.
        top_level_files = ["dependencies.txt", "LICENSE", "README.md"]

        for filename in top_level_files:
            src = Path(base_dir) / filename
            dst = map2loop_dir / filename

            # If the source file exists in base_dir, move it to map2loop/.
            if src.exists():
                shutil.copy(str(src), str(dst))

setup(
    name="map2loop",
    install_requires=install_requires,        
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"": ['dependencies.txt']},
    include_package_data=True,
    license="MIT",
    cmdclass={
        "sdist": CustomSDist,
    },
)
=======
requirements_file = os.path.join(package_root, "dependencies.txt")
with open(requirements_file, 'r') as f:
=======
requirements_file = package_root / "dependencies.txt"
with requirements_file.open("r") as f:
>>>>>>> b33532b (fix: include dependencies in site-packages  - issue #169 (#170))
    install_requires = [line.strip() for line in f if line.strip()]


class CustomSDist(_sdist):

    def make_release_tree(self, base_dir, files):
        # 1) Let the normal sdist process run first.
        super().make_release_tree(base_dir, files)
        map2loop_dir = Path(base_dir) / "map2loop"

        # 2) Specify which files to move from the root to map2loop/.
        top_level_files = ["dependencies.txt", "LICENSE", "README.md"]

        for filename in top_level_files:
            src = Path(base_dir) / filename
            dst = map2loop_dir / filename

            # If the source file exists in base_dir, move it to map2loop/.
            if src.exists():
                shutil.copy(str(src), str(dst))

setup(
    name="map2loop",
    install_requires=install_requires,        
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"": ['dependencies.txt']},
    include_package_data=True,
    license="MIT",
    cmdclass={
        "sdist": CustomSDist,
    },
)
<<<<<<< HEAD
>>>>>>> 7978841 (feat: v3.2 (#153))
=======
>>>>>>> b33532b (fix: include dependencies in site-packages  - issue #169 (#170))
