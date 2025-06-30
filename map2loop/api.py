"""Public API for map2loop
==========================

This module provides a stable interface to dynamically access classes within the
``map2loop`` package.  It exposes a :class:`Map2LoopAPI` facade which can be used
by external applications, e.g. a QGIS plugin, to instantiate map2loop classes
without relying on the internal module layout.  Classes are discovered using
Python's introspection facilities the first time the API is used.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import pathlib
from types import ModuleType
from typing import Any, Dict, List, Type


class Map2LoopAPI:
    """Facade exposing map2loop classes.

    The API implements a dynamic factory that discovers classes from the
    ``map2loop`` package.  It allows creating instances of classes by name and
    retrieving class objects directly.  Because discovery happens at runtime,
    external clients remain agnostic to refactoring inside the package.
    """

    def __init__(self) -> None:
        self._class_map: Dict[str, Type[Any]] = {}
        self._discover_classes()

    # ------------------------------------------------------------------
    def _discover_classes(self) -> None:
        """Populate ``_class_map`` with classes found in ``map2loop``."""
        package_dir = pathlib.Path(__file__).parent
        for module_info in pkgutil.iter_modules([str(package_dir)]):
            name = module_info.name
            if name.startswith("_") or name == "api":
                continue  # skip private modules and this file
            module = importlib.import_module(f"map2loop.{name}")
            self._register_classes(module)

    def _register_classes(self, module: ModuleType) -> None:
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if inspect.isclass(attr) and attr.__module__ == module.__name__:
                self._class_map[attr.__name__] = attr

    # ------------------------------------------------------------------
    def list_classes(self) -> List[str]:
        """Return names of available classes."""
        return sorted(self._class_map.keys())

    # ------------------------------------------------------------------
    def get_class(self, class_name: str) -> Type[Any]:
        """Return class object by name.

        Parameters
        ----------
        class_name:
            Name of the class as exposed by the API.
        """
        cls = self._class_map.get(class_name)
        if cls is None:
            # If a new class was added after initialisation, attempt to reload.
            self._discover_classes()
            cls = self._class_map.get(class_name)
        if cls is None:
            raise ValueError(f"Class '{class_name}' not found in map2loop package")
        return cls

    # ------------------------------------------------------------------
    def create(self, class_name: str, *args: Any, **kwargs: Any) -> Any:
        """Instantiate a class by name."""
        cls = self.get_class(class_name)
        return cls(*args, **kwargs)


__all__ = ["Map2LoopAPI"]
