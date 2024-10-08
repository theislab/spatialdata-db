import bionty as bt
import pandas as pd
import anndata as ad
import spatialdata as sd

from lamindb.core import AnnDataCurator, DataFrameCurator
from lamindb_setup.core.types import UPathStr
from lnschema_core import Record
from lnschema_core.types import FieldAttr

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
        "disease": bt.Disease.name,
    }

    DEFAULT_VALUES = {
        "disease": "normal",
    }

    FIXED_SOURCES = {
        "disease": bt.Source.filter(entity="bionty.Disease", name="mondo", version="2023-04-04").one()
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
        self.organism = organism
        
        _add_defaults(data, defaults)

        super().__init__(
            df=data, categoricals=categoricals, sources=sources, organism=organism
        )

    def validate(self, organism: str | None = None) -> bool:
        """Validate the global SpatialDataMetadata."""
        return DataFrameCurator.validate(self, organism)

class SpatialDataTableValidator(AnnDataCurator):
    
    DEFAULT_CATEGORICALS = {
        "disease": bt.Disease.name,
    }

    DEFAULT_VALUES = {
        "disease": "normal",
    }

    FIXED_SOURCES = {
        "disease": bt.Source.filter(entity="bionty.Disease", name="mondo", version="2023-04-04").one()
    }
    
    # TODO not every AnnData objects will have all of these obs columns present but one of them should -> define a rule
    
    def __init__(
        self,
        data: ad.AnnData | UPathStr,
        var_index: FieldAttr = bt.Gene.ensembl_gene_id,
        categoricals: dict[str, FieldAttr] = DEFAULT_CATEGORICALS,
        *,
        defaults: dict[str, str] = None,
        organism="human",
    ):
        _add_defaults(data, defaults)

        super().__init__(
            data=data, var_index=var_index, categoricals=categoricals, organism=organism
        )

    def validate(self) -> bool:
        """Further custom validation."""
        # --- Custom validation logic goes here --- #
        return super().validate()
    

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
        
        self.metadata_validator = SpatialDataMetadataValidator(self.sdata.metadata, organism=self.organism)
        self.table_validators = [SpatialDataTableValidator(table, organism=self.organism) for table in self.sdata.tables]


    def validate(self, organism: str | None = None) -> bool:
        """Further custom validation."""
        
        # TODO this should very clearly state which things were able to be validate or not
        
        is_metadata_validated = DataFrameCurator.validate(self.sdata.metadata, organism)
        is_table_validated = False
        for sdtvalidator in self.table_validators:
            is_table_validated = AnnDataCurator.validate(sdtvalidator, organism)
        
        return is_metadata_validated and is_table_validated
