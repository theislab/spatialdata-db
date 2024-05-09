# ADJUST
uid = "4pey9"

# Setup before running this script for the first time
#   1) Ensure you have a lamin.ai account
#   2) Run `lamin login` to authenticate
#   3) Activate lamin db connection with `lamin load scverse/spatial`
#   4) Execute script once and replace the stem_uid for this file

import lamindb as ln

ln.settings.transform.stem_uid = "5PYtTxDE7LvE"
ln.settings.transform.version = "1"

ln.track()

from vitessce import (
    VitessceConfig,
    Component as cm,
    CoordinationType as ct,
    CoordinationLevel as CL,
    AbstractWrapper,
    SpatialDataWrapper,
    get_initial_coordination_scope_prefix
)
from vitessce.data_utils import (
    optimize_adata,
    VAR_CHUNK_SIZE,
)
import spatialdata as sd
from lamindb.integrations import save_vitessce_config


artifact = ln.Artifact.filter(ulabels__name=uid).one()

vc = VitessceConfig(
    schema_version="1.0.16",
    name='Visium + Xenium demo',
    description='From https://spatialdata.scverse.org/en/latest/tutorials/notebooks/datasets/README.html'
)

wrapper = SpatialDataWrapper(
    spatialdata_url=artifact.path.to_url(),
    image_path="images/Visium_Adult_Mouse_Brain_hires_image",
    obs_feature_matrix_path = "tables/table/X",
    feature_labels_path = "tables/table/var/gene_ids",
    shapes_path = "shapes/Visium_Adult_Mouse_Brain",
    coordination_values={"obsType":"spot"}
)

dataset = vc.add_dataset(name='Visium demo').add_object(wrapper)
spatial = vc.add_view("spatialBeta", dataset=dataset)
vc.layout(spatial)
view = save_vitessce_config(vc, description="Visium HD demo vitessce config")