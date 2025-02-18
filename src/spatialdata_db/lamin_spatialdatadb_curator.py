import bionty as bt
import lamindb as ln
from lamindb.base.types import FieldAttr
from lamindb.curators._spatial import SpatialDataCurator
from lamindb.models import Record
from spatialdata import SpatialData


class SpatialDataDBCurator(SpatialDataCurator):
    """Custom Curator for SpatialDataDB"""

    DEFAULT_CATEGORICALS = {
        "assay": bt.ExperimentalFactor.name,
        "chemistry_version": ln.ULabel.name,
        "organism": bt.Organism.name,
        "tissue": bt.Tissue.name,
        "disease": bt.Disease.name,
        "license": ln.ULabel.name,
        "preproc_version": ln.ULabel.name,
    }

    DEFAULT_VALUES = {
        "license": "unknown",
        "development_stage": "unknown",
        "self_reported_ethnicity": "unknown",
        "sex": "unknown",
        "preproc_version": "unknown",
    }

    FIXED_SOURCES = {  # type: ignore
        # TODO: fix ontologies
    }

    DEFAULT_VAR_INDEX = {"table": bt.Gene.ensembl_gene_id}

    def __init__(
        self,
        sdata: SpatialData,
        var_index: dict[str, FieldAttr] = DEFAULT_VAR_INDEX,
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
