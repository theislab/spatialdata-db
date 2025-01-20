from importlib.metadata import version
from spatialdata_db.parsing import load_10x_metadata
from django.core.exceptions import ImproperlyConfigured
from lamin_utils import logger
try:
<<<<<<< HEAD
    from spatialdata_db.lamin_spatialdata_validator_outdated import SpatialDataValidator
    from spatialdata_db.lamin_spatialdatadb_curator import SpatialDataDBCurator
=======
    from spatialdata_db.lamin_spatialdata_validator import SpatialDataCurator
>>>>>>> 6bd94b08dd9b0645d390d644300bd2d2f6cfe3ee
except ImproperlyConfigured:
    logger.warning("Importing SpatialDataCurator currently requires being connected to a lamindb instance.")

<<<<<<< HEAD
__all__ = ["load_10x_metadata", "SpatialDataValidator", "SpatialDataDBCurator"]
=======
__all__ = ["load_10x_metadata", "SpatialDataCurator"]
>>>>>>> 6bd94b08dd9b0645d390d644300bd2d2f6cfe3ee
__version__ = version("spatialdata-db")
