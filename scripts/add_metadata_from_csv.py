import os
import pandas as pd
import spatialdata as sd
import datetime

SDDB_KEY = "sample"

DATA_PATH = "/lustre/groups/ml01/projects/2024_spatialdata_db/data"
CSV_FILE_PATH = './data/metadata_10x_clean_wo_VisiumHD_wo_duplicates.csv'

df = pd.read_csv(CSV_FILE_PATH, sep=";", index_col=0)

error_rows = []
for index, row in df.iterrows():
    uid = index
    meta = row

    folder_path = None
    for folder in os.listdir(DATA_PATH):
        if folder.startswith(str(uid)):
            folder_path = os.path.join(DATA_PATH, folder)
            break

    if folder_path is None:
        print(f"Folder for UID {uid} not found.")
        continue

    zarr_file = None
    for file in os.listdir(folder_path):
        if file.endswith(".zarr"):
            if not "metadata" in file and not "attrs" in file:
                zarr_file = os.path.join(folder_path, file)
                break

    # if zarr_file is None and 'metadata' not in zarr_file and 'attrs' not in zarr_file:
    #     print(f"Zarr file not found in folder {folder_path}.")
    #     continue

    try:
        sdata = sd.read_zarr(zarr_file)

        meta_df = pd.DataFrame([meta])
        index = meta_df.index[0]
        metadata = {k: v[index] for k, v in meta_df.to_dict().items()}
        # sddb_version = spatialdata_db.__version__
        # metadata['spatialdata_db_attrs'] = {
        #     'version': sddb_version
        # }
        sdata.attrs[SDDB_KEY] = metadata

        metadata_zarr_file = os.path.splitext(zarr_file)[0] + "_attrs_v2.zarr"

        sdata.write(metadata_zarr_file, overwrite=True)
        print(f"Processed UID {uid} and updated metadata.")
    except Exception as e:
        print(f"Error processing index {uid}: {e}")  # Log the error message
        error_dict = row.to_dict()
        error_dict["index"] = index  # Explicitly store the index
        error_rows.append(error_dict)

if error_rows:
    error_df = pd.DataFrame(error_rows)

    # Move "index" column to the first position
    error_df = error_df.set_index("index").reset_index()

    # Save to CSV with current date
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"datasets_with_errors_{date_str}.csv"
    error_df.to_csv(filename, index=False)
    print(f"Errors saved to {filename}")
else:
    print("No errors found.")