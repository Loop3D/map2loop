# this script intends to generate an updated meta.yml from the dependencies.txt file. 
# This allows us to simply change the dependencies file when they need to change, and the conda build will automatically update the meta.yml file.

import os

# Read dependencies.txt 
with open('dependencies.txt') as f:
    dependencies = f.read().splitlines()

meta_yaml_content = f"""
{{% set name = "map2loop" %}}

package:
  name: "{{{{ name|lower }}}}"
  version: "{{{{ environ.get('GIT_DESCRIBE_TAG', '') }}}}"

source:
  git_url: https://github.com/Loop3D/map2loop

build:
  number: 0
  script: "{{{{ PYTHON }}}} -m pip install ."

requirements:
  host:
    - pip
    - python
"""

# Initialize sections for host and run
host_section = ""
run_section = "  run:\n"

# Loop over dependencies
for dep in dependencies:
    if '==' in dep:  # Check if there's a pinned version
        host_section += f"    - {dep}\n"
    else:
        run_section += f"    - {dep}\n"

# Add the pinned dependencies to the host section
meta_yaml_content += host_section

# Add the unpinned dependencies under the run section
meta_yaml_content += run_section

# Add the channels section
meta_yaml_content += """
channels:
  - loop3d
  - conda-forge

about:
  home: "https://github.com/Loop3D/map2loop"
  license: MIT
  license_family: MIT
  license_file: ../LICENSE
  summary: "Generate 3D model data using 2D maps."
"""

# Save the the meta.yaml file
with open('conda/meta.yaml', 'w') as meta_file:
    meta_file.write(meta_yaml_content)

print("meta.yaml file updated successfully.")