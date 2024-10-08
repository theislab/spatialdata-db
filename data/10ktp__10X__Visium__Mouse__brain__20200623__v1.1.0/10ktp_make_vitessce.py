theislab_uid = "10ktp"

import lamindb as ln

ln.context.track("5PYtTxDE7LvE")

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


artifact = ln.Artifact.filter(ulabels__name=theislab_uid).one()

vc = VitessceConfig(
    schema_version="1.0.16",
    name='Visium + Xenium demo',
    description='From https://spatialdata.scverse.org/en/latest/tutorials/notebooks/datasets/README.html'
)

wrapper = SpatialDataWrapper(
    spatialdata_url=artifact.path.to_url(),
    image_elem="images/Visium_Adult_Mouse_Brain_hires_image",
    shapes_elem = "shapes/Visium_Adult_Mouse_Brain",
    table_path = "tables/table",
)

dataset = vc.add_dataset(name='Visium demo').add_object(wrapper)
spatial = vc.add_view("spatialBeta", dataset=dataset)
vc.layout(spatial)
view = save_vitessce_config(vc, description="Visium HD demo vitessce config")
