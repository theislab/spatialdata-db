import argparse
from typing import Sequence, Dict, Set, Tuple
import pandas as pd
import sys
import spatialdata as sd
from pathlib import Path
from contextlib import redirect_stdout
import lamindb as ln

from utils import (
    locate_sdata_object,
    clean_dict,
    Logger,
    LogTypes,
    WriteProcessor,
    correct_cell_radii,
    get_schema_configs_for_techs
)

# Constants for metadata keys
METADATA_GENERAL_KEY = "metadata_general"
METADATA_XENIUM_KEY = "metadata_xenium"
METADATA_VISIUM_KEY = "metadata_visium"
# TODO: (new tech) add metadata key for new tech

AVAILABLE_SCHEMAS = {
    'xenium': {
        'specific': ln.Schema.get(name='XeniumSpecifc'),
        'composite': ln.Schema.get(name='Xenium'),
    },
    'visium': {
        'specific': ln.Schema.get(name='VisiumSpecifc'),
        'composite': ln.Schema.get(name='Visium'),
    }
    # TODO: (new tech) add schema name for specific and composite schemas of new techs
}

def main(args):
    data_path = Path(args.data_path)
    status_log_path = Path(args.status_log_path)
    metadata_path = Path(args.metadata)

    metadata = pd.read_csv(metadata_path, sep=';', index_col='uid')
    techs = set(metadata['Assay'].str.lower().unique())

    schemas, features, is_optional, non_categorical, type_lookup = get_schema_configs_for_techs(techs, AVAILABLE_SCHEMAS)

    logger = Logger()
    write_processor = WriteProcessor()
    for index, row in metadata.iterrows():
        uid = index

        try:
            sdata_path = locate_sdata_object(uid, data_path)
        except AssertionError as e:
            logger.add_error_record(uid, str(e))
            continue

        try:
            with redirect_stdout(write_processor):
                sdata = sd.read_zarr(sdata_path)
        except Exception as e:
            logger.add_error_record(uid, str(e))
            continue

        message = write_processor.full_text.strip()
        if "warning" in message.lower():
            logger.add_error_record(uid, str(message), type=LogTypes.WARN)
        write_processor.reset()

        try:
            assay = row['Assay'].lower()
        except KeyError:
            logger.add_error_record(uid, "Assay not found in metadata. Get your metadata in order! Skipping dataset.")
            continue

        metadata_cleaned = clean_dict(row.to_dict(), is_optional[assay], type_lookup[assay])
        metadata_cleaned['Publication Date'] = str(metadata_cleaned['Publication Date'])

        sdata.attrs[METADATA_GENERAL_KEY] = {k: v for k, v in metadata_cleaned.items() if k in features['general']}

        match assay:
            case 'xenium':
                if sdata['cell_circles'].radius.isna().sum() > 0:
                    correct_cell_radii(sdata)
                sdata.attrs[METADATA_XENIUM_KEY] = {
                    k: v for k, v in metadata_cleaned.items() if k in features['xenium']
                }

            case 'visium':
                sdata.attrs[METADATA_VISIUM_KEY] = {
                    k: v for k, v in metadata_cleaned.items() if k in features['visium']
                }

            # TODO: (new tech) if there're tech specific actions, add them here

            case _:
                logger.add_error_record(uid, f"Assay {assay} not yet supported. Skipping dataset.")
                continue

        curator = ln.curators.SpatialDataCurator(sdata, schemas[assay])

        try: # TODO: extract action from returned text
            curator.validate()
        except Exception as e:
            print(f"Validation error in UID {uid}: {e}")
            print('Retrying...')
            curator.slots['attrs:metadata_general'].cat.standardize("Assay")
            curator.slots['attrs:metadata_general'].cat.standardize("Organism")
            curator.slots['tables:table:var.T'].cat.add_new_from('columns')

        try:
            curator.validate()

            description = metadata_cleaned['Description']
            replicate = metadata_cleaned.get('Replicate', None)
            if replicate:
                description = f"{description} ({replicate})"

            if args.dry_run:
                print(f"[DRY RUN] Would save artifact for UID {uid} with description: {description}")
                logger.add_upload_log(uid, "[dry-run] not saved")
            else:
                artifact = curator.save_artifact(
                    key=f"{uid}.zarr",
                    description=description
                )

                values_to_add = {
                    k: v for k, v in metadata_cleaned.items()
                    if k in non_categorical[assay] and v not in [None, '', 'unknown']
                }
                artifact.features.add_values(values_to_add)

                logger.add_upload_log(uid, artifact.uid)

                # vc = vit.VitessceConfig(
                #     schema_version="1.0.17",
                #     description=description,
                # )
                
                # dataset = vc.add_dataset(name=description, uid=uid).add_object(
                #     vit.SpatialDataWrapper(
                #         sdata_artifact=artifact,
                #         image_path=path_to_your_default_image_eg_the_first_one))
                
                # spatial = vc.add_view("spatialBeta", dataset=dataset)
                
                # sdata_vc_artifact = ln.integrations.save_vitessce_config(
                #     vc, description=f"View {description}",
                # )

        except Exception as e:
            logger.add_error_record(uid, str(e))
            continue

    logger.save_logs_to_csv(status_log_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process SpatialData datasets with associated metadata.")
    parser.add_argument("--data-path", type=str, default="/lustre/groups/ml01/projects/2024_spatialdata_db/data", help="Root path to dataset storage")
    parser.add_argument("--status-log-path", type=str, required=True, help="Path to save status logs")
    parser.add_argument("--metadata", type=str, required=True, help="Path to a curated metadata CSV file")
    parser.add_argument("--dry-run", action="store_true", help="Run without saving artifacts to LaminDB")

    args = parser.parse_args()
    main(args)
