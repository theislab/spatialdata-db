uid = "1rw9r_"

# CONSTANT
from spatialdata_io import visium
import spatialdata as sd
from pathlib import Path
import shutil

DATA_DIR = Path("/lustre/groups/ml01/projects/2024_spatialdata_db/data")
datasets_with_uid = [DATA_DIR / d.name for d in DATA_DIR.iterdir() if d.is_dir() and uid in str(d.name)]

assert len(datasets_with_uid) == 1
dataset_path = Path(datasets_with_uid[0])
dataset_name = dataset_path.name

##
path_read = dataset_path / "raw_output"
path_write = dataset_path / f"{dataset_name}.zarr"

##
print("parsing the data... ", end="")
sdata = visium(
    path=str(path_read),
    dataset_id="V1_Adult_Mouse_Brain_Coronal_Section_2",
    counts_file=str(path_read / "V1_Adult_Mouse_Brain_Coronal_Section_2_filtered_feature_bc_matrix.h5"),
    fullres_image_file=str(path_read / "spatial" /"tissue_hires_image.png"),
    tissue_positions_file=str(path_read / "spatial" / "tissue_positions_list.csv"),
    scalefactors_file=str(path_read / "spatial" / "scalefactors_json.json"),
)
print("done")

##
print("writing the data... ", end="")
if path_write.exists():
    shutil.rmtree(path_write)
sdata.write(path_write)
print("done")

##
sdata = sd.SpatialData.read(path_write)

with open(dataset_path / f"{dataset_name}.contents", 'w') as file:
    print(sdata, file=file)

print(sdata)
