import toml
import re
import argparse
import logging
import sys

def parse_dependency(dep):
    """Parses a dependency string into package name and version specifier."""
    version_specifiers = ['==', '>=', '<=', '~=', '!=', '<', '>', '===', '~=', '^', '*']
    dep = dep.strip()
    for spec in version_specifiers:
        index = dep.find(spec)
        if index != -1:
            pkg_name = dep[:index].strip()
            version = dep[index:].strip()
            # Normalize spacing in version specifier
            version = re.sub(r'\s+', '', version)
            return pkg_name, version
    return dep, ""

def read_dependencies(dependencies_file):
    """Reads dependencies from a dependencies.txt file."""
    try:
        with open(dependencies_file, 'r') as f:
            dependencies = f.readlines()
        # Strip whitespace and remove empty lines
        dependencies = [dep.strip() for dep in dependencies if dep.strip()]
        return dependencies
    except FileNotFoundError:
        logging.error(f"Dependencies file '{dependencies_file}' not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred while reading dependencies: {e}")
        sys.exit(1)

def update_pyproject_toml(dependencies, pyproject_file):
    """Update the dependencies section in pyproject.toml."""
    try:
        with open(pyproject_file, 'r') as f:
            pyproject_data = toml.load(f)
    except FileNotFoundError:
        logging.error(f"pyproject.toml file '{pyproject_file}' not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred while reading pyproject.toml: {e}")
        sys.exit(1)

    try:
        # Get the [build-system] section
        build_deps = pyproject_data['build-system']['requires']

        # Initialize dependencies dictionary
        existing_deps = {}
        setuptools_list = []

        # Parse existing dependencies
        for dep in build_deps:
            dep = dep.strip()
            if 'setuptools' in dep:
                setuptools_list.append(dep)
                continue
            pkg_name, version = parse_dependency(dep)
            existing_deps[pkg_name] = version

        # Process new dependencies
        for dep in dependencies:
            pkg_name, version = parse_dependency(dep)
            existing_deps[pkg_name] = version  # Update or add

        # Reconstruct the dependencies list
        # Keep 'setuptools' at the start
        new_build_deps = setuptools_list
        for pkg_name in sorted(existing_deps.keys()):
            version = existing_deps[pkg_name]
            if version:
                dep_str = f"{pkg_name}{version}"
            else:
                dep_str = pkg_name
            new_build_deps.append(dep_str)

        pyproject_data['build-system']['requires'] = new_build_deps

        # Write back the updated pyproject.toml
        with open(pyproject_file, 'w') as f:
            toml.dump(pyproject_data, f)

        logging.info(f"Updated '{pyproject_file}' with dependencies from '{args.dependencies_file}'.")
    except Exception as e:
        logging.error(f"An error occurred while updating pyproject.toml: {e}")
        sys.exit(1)

def update_meta_yaml(dependencies, meta_yaml_file):
    """Replace the dependencies in the 'run' section of meta.yaml with those from dependencies.txt."""
    try:
        with open(meta_yaml_file, 'r') as f:
            meta_yaml_content = f.read()
    except FileNotFoundError:
        logging.error(f"meta.yaml file '{meta_yaml_file}' not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred while reading meta.yaml: {e}")
        sys.exit(1)

    try:
        # Find the 'requirements:' section
        requirements_match = re.search(
            r'(requirements:\s+host:.*?\n)(\s+run:\s*\n)((?:\s*-\s*.*?\n)*)',
            meta_yaml_content, re.DOTALL)

        if requirements_match:
            # Extract the parts of the requirements section
            requirements_start = requirements_match.group(1)
            run_indent = re.match(r'(\s+)run:', requirements_match.group(2)).group(1)

            # Build the new run section
            new_run_section = f"{run_indent}run:\n"
            for dep in dependencies:
                dep = dep.strip()
                new_run_section += f"{run_indent}  - {dep}\n"

            # Reconstruct the entire requirements section
            updated_requirements_section = requirements_start + new_run_section

            # Replace the old requirements section with the updated one
            updated_meta_yaml_content = meta_yaml_content.replace(
                requirements_match.group(0), updated_requirements_section)

            # Save the updated meta.yaml file
            with open(meta_yaml_file, 'w') as meta_file:
                meta_file.write(updated_meta_yaml_content)

            logging.info(f"Updated '{meta_yaml_file}' with dependencies from '{args.dependencies_file}'.")
        else:
            logging.error(f"Error: 'requirements' section not found in '{meta_yaml_file}'.")
            sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred while updating meta.yaml: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update dependencies in pyproject.toml and meta.yaml")
    parser.add_argument('--dependencies-file', default='map2loop/dependencies.txt',
                        help='Path to the dependencies.txt file')
    parser.add_argument('--pyproject-file', default='map2loop/pyproject.toml',
                        help='Path to the pyproject.toml file')
    parser.add_argument('--meta-yaml-file', default='map2loop/conda/meta.yaml',
                        help='Path to the meta.yaml file')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level')

    args = parser.parse_args()

    # Set up logging
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        logging.error(f"Invalid log level: {args.log_level}")
        sys.exit(1)
    logging.basicConfig(level=numeric_level, format='%(levelname)s: %(message)s')

    dependencies = read_dependencies(args.dependencies_file)
    update_pyproject_toml(dependencies, args.pyproject_file)
    update_meta_yaml(dependencies, args.meta_yaml_file)
