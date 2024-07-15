uid = "10pui_"

# CONSTANT
from spatialdata_io import xenium
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
sdata = xenium(
    path=str(path_read),
    n_jobs=8,
    cell_boundaries=True,
    nucleus_boundaries=True,
    morphology_focus=True,
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
