from importlib.metadata import version
from spatialdata_db.parsing import load_10x_metadata
from django.core.exceptions import ImproperlyConfigured
from lamin_utils import logger
try:
    from spatialdata_db.lamin_spatialdatadb_curator import SpatialDataDBCurator
except ImproperlyConfigured:
    logger.warning("Importing SpatialDataValidator currently requires being connected to a lamindb instance.")

__all__ = ["load_10x_metadata", "SpatialDataDBCurator"]
__version__ = version("spatialdata-db")
