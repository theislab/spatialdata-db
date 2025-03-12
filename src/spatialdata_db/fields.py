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
        # "Assay Ontology ID": bt.ExperimentalFactor.ontology_id,
        'Biomaterial Type': Ulabel.name,
        "Organism": bt.Organism.name,
        # "Organism Ontology ID": bt.Organism.ontology_id,
        "Tissue": bt.Tissue.name,
        # "Tissue Ontology ID": bt.Tissue.ontology_id,
        "Modality": Ulabel.name, # can this be a list?
        "Publish Date": Ulabel.name, # TODO: use datetime when curator is fixed
        "License": Ulabel.name,
        "Dataset Url": Ulabel.name, # TODO: use str when curator is fixed

        # patient metadata
        "Development Stage": bt.DevelopmentalStage.name,
        # "Development Stage Ontology ID": bt.DevelopmentalStage.ontology_id,
        "Disease": bt.Disease.name,
        # "Disease Ontology ID": bt.Disease.ontology_id,
        "Disease Details": Ulabel.name,

        # technical metadata
        # "Sample ID at Source": Ulabel.name, # TODO: extract sample ID, slide serial number, reference & make str
        "Replicate": Ulabel.name, # TODO: make str when curator is fixed
        "Instrument(s)": Ulabel.name,
        "Software": Ulabel.name,
        "Analysis Steps":  Ulabel.name,
        "Chemistry Version": Ulabel.name,
        "Preservation Method": Ulabel.name,
        "Staining Method": Ulabel.name, # can this be a list? --> not yet apparently
        "Cells or Nuclei": Ulabel.name,
        "Panel": Ulabel.name,
        
        # visium specific metadata
        # "Capture Area": Ulabel.name,
        # "Probe Set": Ulabel.name,
        # "Custom Probe Set": str,
        # "Nr Spots": int,
        # "Number of Reads": int,
        # "Mean Reads Per Spot": int,
        # "Median Genes Per Spot": int,

        # # xenium specific metadata
        # "Gene Panel": Ulabel.name,
        # "Custom Gene Panel": str,
        # "Nr Cells Detected": int,
        # "Median Transcripts Per Cell": int,
        # "Median Genes Per Cell": int,
        # "Fraction of Empty Cells": float,
        # "Percent of Transcripts Within Cells": float,
        # "Region Area": float,
        # "Cells per 100 um^2": float,
    }

    SAMPLE_LEVEL_FIELD_DEFAULTS = {
        # general metadata
        "Product": "unknown",
        "Modality": "unknown", # can this be a list?
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
        "Staining Method": "unknown", # can this be a list?
        "Cells or Nuclei": "unknown",

        # visium specific metadata
        # "Capture Area": "",
        # "Probe Set": "",
        # "Custom Probe Set": "",
        # "Nr Spots": None,
        # "Number of Reads": None,
        # "Mean Reads Per Spot": None,
        # "Median Genes Per Spot": None,

        # # xenium specific metadata
        # "Gene Panel": "",
        # "Custom Gene Panel": "",
        # "Nr Cells Detected": None,
        # "Median Transcripts Per Cell": None,
        # "Median Genes Per Cell": None,
        # "Fraction of Empty Cells": None,
        # "Percent of Transcripts Within Cells": None,
        # "Region Area": None,
        # "Cells per 100 um^2": None,
    }

    OBS_FIELDS = {
        # obs level metadata
        "Cell Type": bt.CellType.name,
        "Cell Type Ontology ID": bt.CellType.ontology_id,
    }

    OBS_FIELD_DEFAULTS = {
        "Cell Type": "unknown",
    }

    VAR_INDEX_DEFAULT = {"table": bt.Gene.ensembl_gene_id}