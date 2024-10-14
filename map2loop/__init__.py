from .project import Project
from .gdal import _gdal as gdal
__all__ = ['gdal', 'Project']  # Include other public modules
from .version import __version__
s