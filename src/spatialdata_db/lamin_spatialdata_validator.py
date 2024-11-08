import bionty as bt
import pandas as pd
import anndata as ad
import spatialdata as sd
import lamindb as ln

from lamindb.core import AnnDataCurator, DataFrameCurator
from lamindb_setup.core.types import UPathStr
from lnschema_core import Record
from lnschema_core.types import FieldAttr
from lamin_utils import logger, colors

def _add_defaults(data: pd.DataFrame | UPathStr, defaults: dict[str, str] = None) -> None:
    """Adds default values to a Pandas DataFrame if values are missing."""
    if defaults:
        if isinstance(data, UPathStr):
            data = pd.read_csv(UPathStr)  # TODO this parsing is not very safe
        
        for col, default in defaults.items():
            if col not in data.columns:
                data[col] = default
            else:
                data[col].fillna(default, inplace=True)
        

class SpatialDataMetadataValidator(DataFrameCurator):
    
    DEFAULT_CATEGORICALS = {
        "assay": bt.ExperimentalFactor.name,
        'license': ln.ULabel.name,
        'specimen': ln.ULabel.name,
        'magnification': ln.ULabel.name,
        'protocol_url': ln.ULabel.name,
        'study_link': ln.ULabel.name,
        'preproc_version': ln.ULabel.name,
        'omics': ln.ULabel.name,
        'chemistry_version': ln.ULabel.name,
        'data_provider': ln.ULabel.name,
        'disease_state': ln.ULabel.name,
        'organism': bt.Organism.name,
        'tissue': bt.Tissue.name,
        'publish_date': ln.ULabel.name,
        'disease': ln.ULabel.name, # TODO: disease ontology
    }

    DEFAULT_VALUES = {
        "license": "not provided",
        "magnification": "not provided",
        'protocol_url': "not provided",
        'preproc_version': "not provided",
        'omics': "not provided",
        'chemistry_version': "not provided",
        'data_provider': "not provided",
        'disease_state': "not provided",
        'publish_date': "not provided",
    }

    FIXED_SOURCES = {
        "assay": bt.Source.filter(entity="bionty.ExperimentalFactor", name="efo", version="3.70.0").one()
        }
    
    def __init__(
        self,
        data: pd.DataFrame | UPathStr,
        categoricals: dict[str, FieldAttr] = DEFAULT_CATEGORICALS,
        *,
        defaults: dict[str, str] = DEFAULT_VALUES,
        sources: dict[str, Record] = FIXED_SOURCES,
        organism="human",
    ):
        self.data = data
        
        _add_defaults(data, defaults)

        super().__init__(
            df=data, categoricals=categoricals, sources=sources, organism=organism
        )

    def validate(self, organism: str | None = None) -> bool:
        """Validate the global SpatialDataMetadata."""
        return DataFrameCurator.validate(self, organism)

class SpatialDataTableValidator(AnnDataCurator):
    
    DEFAULT_CATEGORICALS = {
        "celltype": bt.CellType.name,
    }

    DEFAULT_VALUES = {
        "celltype": "normal",
    }

    DEFAULT_SOURCES = {
        "celltype": bt.Source.filter(entity="bionty.CellType", name="cl", version="2023-08-24").one()
    }
    
    # TODO not every AnnData objects will have all of these obs columns present but one of them should
    # Figure out how to pass the categoricals to the respective tables
    
    def __init__(
        self,
        data: ad.AnnData | UPathStr,
        var_index: FieldAttr = bt.Gene.ensembl_gene_id,
        categoricals: dict[str, FieldAttr] = DEFAULT_CATEGORICALS,
        *,
        defaults: dict[str, str] = DEFAULT_VALUES,
        table_key: str,
        organism="human",
    ):
        self.data = data
        self.table_key = table_key
        
        _add_defaults(data.obs, defaults)

        super().__init__(
            data=data, var_index=var_index, categoricals=categoricals, organism=organism
        )

    def validate(self, organism: str | None = None) -> bool:
        """Validate the table."""
        return super().validate(organism)
    

class SpatialDataValidator:
    """Custom curation flow for SpatialData."""

    def __init__(
        self,
        sdata: sd.SpatialData | UPathStr,
        # categoricals: dict[str, FieldAttr] = DEFAULT_CATEGORICALS,
        *,
        # defaults: dict[str, str] = None,
        # sources: dict[str, Record] = FIXED_SOURCES,
        organism="human",
    ):
        self.sdata = sdata
        self.organism = organism
        
        # TODO think about how to integrate the parameters -> some weird nested quirky thing
        
        self.metadata_validator = SpatialDataMetadataValidator(data=self.sdata.metadata, organism=self.organism)
        self.table_validators = {table_key: SpatialDataTableValidator(data=sdata.tables[table_key], table_key=table_key, organism=self.organism) for table_key in self.sdata.tables.keys()}


    def validate(self, organism: str | None = None) -> bool:
        """Validating Spatialdata objects including the metadata and all tables (AnnData objects)."""
        # TODO this should very clearly state which things were able to be validate or not
        
        logger.info(f"Validating {colors.green('metadata')}.")
        is_metadata_validated = self.metadata_validator.validate(organism)
        is_tables_validated = False
        for table_key, sdtvalidator in self.table_validators.items():
            logger.info(f"Validating Anndata object with key {colors.green(table_key)}")
            is_tables_validated = sdtvalidator.validate(organism)
        
        return is_metadata_validated and is_tables_validated
