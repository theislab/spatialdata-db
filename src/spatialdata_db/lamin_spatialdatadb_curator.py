import bionty as bt
import lamindb as ln
from lamindb.base.types import FieldAttr
from lamindb.curators._spatial import SpatialDataCurator
from lamindb.models import Record
from spatialdata import SpatialData
from .fields import SpatialDataDBFields as fields


class SpatialDataDBCurator(SpatialDataCurator):
    """Custom Curator for SpatialDataDB"""

    DEFAULT_CATEGORICALS = fields.SAMPLE_LEVEL_FIELDS
    DEFAULT_VALUES = fields.SAMPLE_LEVEL_FIELD_DEFAULTS

    FIXED_SOURCES = {  # type: ignore
        # TODO: fix ontologies
    }

    def __init__(
        self,
        sdata: SpatialData,
        var_index: dict[str, FieldAttr] = fields.VAR_INDEX_DEFAULT,
        categoricals: dict[str, dict[str, FieldAttr]] | None = None,
        using_key: str | None = None,
        verbosity: str = "hint",
        organism: str | None = None,
        sources: dict[str, dict[str, Record]] | None = None,
        exclude: dict[str, dict] | None = None,
        *,
        sample_metadata_key: str = "sample",
    ):
        if categoricals is None:
            categoricals = {sample_metadata_key: self.DEFAULT_CATEGORICALS}

        super().__init__(
            sdata,
            var_index,
            categoricals=categoricals,
            using_key=using_key,
            verbosity=verbosity,
            organism=organism,
            sources=sources,
            exclude=exclude,
            sample_metadata_key=sample_metadata_key,
        )
