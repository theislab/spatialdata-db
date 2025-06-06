from pathlib import Path
import pandas as pd
import spatialdata as sd
from datetime import datetime
from enum import Enum
import numpy as np
import lamindb as ln
from typing import List, Dict, Set, Tuple

def locate_sdata_object(uid: str, base_path: Path) -> Path:
    matches_glob = []
    for subfolder in base_path.glob(f"{uid}*"):
        matches_glob.extend(subfolder.glob("*.zarr"))
    assert len(matches_glob) <= 1, f"Multiple zarr files found for UID {uid}."
    assert len(matches_glob) == 1, f"No zarr file found for UID {uid}."
    return matches_glob[0]

def clean_dict(d: dict, is_optional: set = None, dtype_lookup: pd.DataFrame = None) -> dict:
    is_optional = is_optional or set()

    def clean_value(k, v):
        if pd.isna(v):
            return 'unknown' if k not in is_optional else None

        dtype = dtype_lookup.get(k, None)
        if dtype is not None:
            if dtype.startswith("int"):
                return int(str(v).replace(",", ""))
            elif dtype.startswith("float"):
                return float(str(v).replace(",", ""))
        return v

    return {
        k: clean_value(k, v)
        for k, v in d.items()
        if not (pd.isna(v) and k in is_optional)
    }

class LogTypes(Enum):
    ERROR = "error"
    WARN = "warn"
    INFO = "info"

class Logger:
    def __init__(self):
        self.error_records = []
        self.upload_log = []

    def add_error_record(self, uid, message, type: LogTypes = LogTypes.ERROR):
        record = {"UID": uid, "Type": type.value, "Message": message}
        self.error_records.append(record)
    
    def add_upload_log(self, uid, lamin_uid):
        record = {"UID": uid, "LaminUID": lamin_uid, 'Upload Date': datetime.now().strftime('%Y-%m-%d')}
        self.upload_log.append(record)

    def save_logs_to_csv(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(self.error_records).to_csv(path / 'upload_error_log.csv', index=False)
        pd.DataFrame(self.upload_log).to_csv(path / 'upload_log.csv', index=False)

class WriteProcessor:
    def __init__(self):
        self.buf = ""
        self.full_text = ""

    def reset(self):
        self.buf = ""
        self.full_text = ""

    def write(self, buf):
        while buf:
            try:
                newline_index = buf.index("\n")
            except ValueError:
                self.buf += buf
                break
            data = self.buf + buf[:newline_index + 1]
            self.buf = ""
            buf = buf[newline_index + 1:]
            self.full_text += data + '\n'
            
    def flush(self):
        pass

def correct_cell_radii(sdata: sd.SpatialData, CELL_CIRCLES="cell_circles", TABLE="table", CELL_ID="cell_id") -> None:
    """
    See issue: https://github.com/scverse/spatialdata/discussions/657
    """
    
    # default keys from the xenium() reader in spatialdata-io
    assert CELL_CIRCLES in sdata.shapes, f"Expected {CELL_CIRCLES} in the spatial data."
    assert TABLE in sdata.tables, f"Expected {TABLE} in the spatial data."

    circles = sdata[CELL_CIRCLES]
    table = sdata[TABLE]

    radii = circles.radius
    assert radii.isna().sum() > 0, "There is no NaN value in the radii column that we can correct."

    assert np.array_equal(
        circles.index.to_numpy(), table.obs[CELL_ID].to_numpy()
    ), "The indices of the circles and the table do not match, please adjust to your data."

    table.obs.set_index(CELL_ID, inplace=True, drop=False)

    original_cell_radii = (table.obs.cell_area / np.pi) ** 0.5
    original_nucleus_radii = (table.obs.nucleus_area / np.pi) ** 0.5

    nan_mask = radii.isna()

    assert np.allclose(
        radii[~nan_mask], original_nucleus_radii.iloc[np.where(~nan_mask)[0]]
    ), "The non-NaN values in the radii column do not match the nucleus radii as it would be expected."
    circles.radius = original_cell_radii

    CELL_CIRCLES_CORRECTED = f"{CELL_CIRCLES}_corrected"
    sdata[CELL_CIRCLES_CORRECTED] = circles

    return

def get_schema_configs_for_techs(
    techs: List[str]
) -> Tuple[
    Dict[str, list],
    Dict[str, Set[str]],
    Dict[str, Set[str]],
    Dict[str, Dict[str, str]]
]:
    """
    Retrieve schema configuration information for a list of spatial transcriptomics technologies.

    Returns:
        - schemas: mapping of tech -> Schema object
        - features: mapping of tech -> list of feature names (includes 'general')
        - is_optional: mapping of tech -> set of optional feature names
        - non_categorical: mapping of tech -> set of non-categorical feature names
        - type_lookup: mapping of tech -> {feature_name: dtype}
    """
    general_schema = ln.Schema.get(name='SampleLevel')
    general_features = general_schema.features.df()[['name', 'dtype']].copy()
    features = {'general': general_features['name'].tolist()}
    is_optional = {}
    non_categorical = {}
    type_lookup = {}

    available_schemas = {
        'xenium': {
            'specific': ln.Schema.get(name='XeniumSpecifc'),
            'base': ln.Schema.get(name='Xenium'),
        },
        'visium': {
            'specific': ln.Schema.get(name='VisiumSpecifc'),
            'base': ln.Schema.get(name='Visium'),
        }
    }

    schemas = {
        tech: available_schemas[tech]['base']
        for tech in techs
        if tech in available_schemas
    }

    for tech in techs:
        if tech not in available_schemas:
            print(f"Warning: No schema available for tech '{tech}'")
            continue

        specific_schema = available_schemas[tech]['specific']
        specific_df = specific_schema.features.df()[['name', 'dtype']].copy()
        features[tech] = specific_df['name'].tolist()
        optional_fields = (
            set(specific_schema.optionals.get().df()['name']) |
            set(general_schema.optionals.get().df()['name'])
        )
        is_optional[tech] = optional_fields

        combined_features = pd.concat([specific_df, general_features], ignore_index=True).copy()
        non_cat_df = combined_features[~combined_features['dtype'].str.startswith('cat')].copy()

        non_categorical[tech] = set(non_cat_df['name'])
        type_lookup[tech] = non_cat_df.set_index('name')['dtype'].to_dict()

        return schemas, features, is_optional, non_categorical, type_lookup