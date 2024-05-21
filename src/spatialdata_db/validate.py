import logging
from datetime import datetime
from typing import Literal

from anndata import AnnData
from cellxgene_schema.ontology import GeneChecker, SupportedOrganisms
from cellxgene_schema.utils import enforce_canonical_format
from cellxgene_schema.validate import Validator as CellxgeneValidator
from cellxgene_schema.validate import logger
from cellxgene_schema.write_labels import AnnDataLabelAppender as CellxgeneAnnDataLabelAppender


METADATA_REMOVE = [
    "cell_type_ontology_term_id",
    "disease_ontology_term_id",
    # "tissue_ontology_term_id",
    "self_reported_ethnicity_ontology_term_id",
    "development_stage_ontology_term_id",
    "is_primary_data",
]


def validate(
    adata: AnnData,
    organism: Literal["mouse", "human"] = "mouse",
    ignore_labels: bool = False,
    verbose: bool = False,
) -> tuple[AnnData, bool, list, bool]:
    """
    Entry point for validation.

    :param AnnData to validate.

    :return (True, [], <bool>) if successful validation, (False, [list_of_errors], <bool>) otherwise; last bool is for
    seurat convertibility
    :rtype tuple
    """
    # Perform validation
    start = datetime.now()
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    return False