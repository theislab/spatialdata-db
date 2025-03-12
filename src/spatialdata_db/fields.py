import bionty as bt
import lamindb as ln
import pandas as pd
from datetime import datetime
from lamindb import ULabel as Ulabel


class SpatialDataDBFields:
    """SpatialDataDB fields.
    One large schema including fields for different technologies.
    Later, we can split this into different schemas for different technologies, when hierarchical validation is implemented.
    """

    SAMPLE_LEVEL_FIELDS = {
        # general metadata
        "Product": Ulabel.name,
        "Assay": bt.ExperimentalFactor.name,
        'Biomaterial Type': Ulabel.name,
        "Organism": bt.Organism.name,
        "Tissue": bt.Tissue.name,
        "Modality": Ulabel.name,
        "Publish Date": Ulabel.name,
        "License": Ulabel.name,
        "Dataset Url": Ulabel.name,

        # patient metadata
        "Development Stage": bt.DevelopmentalStage.name,
        "Disease": bt.Disease.name,
        "Disease Details": Ulabel.name,

        # technical metadata
        "Replicate": Ulabel.name,
        "Instrument(s)": Ulabel.name,
        "Software": Ulabel.name,
        "Analysis Steps":  Ulabel.name,
        "Chemistry Version": Ulabel.name,
        "Preservation Method": Ulabel.name,
        "Staining Method": Ulabel.name,
        "Cells or Nuclei": Ulabel.name,
        "Panel": Ulabel.name,
    }

    SAMPLE_LEVEL_FIELD_DEFAULTS = {
        # general metadata
        "Product": "unknown",
        "Modality": "unknown",
        "License": "unknown",
        "Dataset Url": "",

        # patient metadata
        "Development Stage": "unknown",
        "Disease": "unknown",
        "Disease Details": "",

        # technical metadata
        "Sample ID at Source": "",
        "Replicate": "",
        "Instrument(s)": "unknown",
        "Software": "unknown",
        "Analysis Steps": "",
        "Preservation Method": "unknown",
        "Staining Method": "unknown",
        "Cells or Nuclei": "unknown",
    }

    VAR_INDEX_DEFAULT = {"table": bt.Gene.ensembl_gene_id}