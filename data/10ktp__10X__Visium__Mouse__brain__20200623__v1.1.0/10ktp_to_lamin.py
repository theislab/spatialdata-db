# Associate metadata as features
import bionty as bt
import lamindb as ln

from spatialdata_db import load_10x_metadata

theislab_uid = "10ktp"

ln.track("KgGzOw8PUYKO7CpM")

try:
    artifact = ln.Artifact.filter(ulabels__name=theislab_uid).one()
    artifact.delete(permanent=True)
except:
    pass

DATASET_PATH = "/lustre/groups/ml01/projects/2024_spatialdata_db/data/10ktp__10X__Visium__Mouse__brain__20200623__v1.1.0/10ktp__10X__Visium__Mouse__brain__20200623__v1.1.0.zarr"

artifact = ln.Artifact(DATASET_PATH, description="10X, Visium, Mouse, Brain")
artifact.save()

# Associate ID with the artifact so we can retrieve afterwards
tuid_parent = ln.ULabel.filter(name="theislab unique ID").one()
tuid = ln.ULabel(name=theislab_uid).save()
tuid.parents.add(tuid_parent)
artifact.labels.add(tuid)

# load 10X metadata we have on disk
all_metadata_10x = load_10x_metadata()
assert len(all_metadata_10x.query(f"uid == '{theislab_uid}'")) == 1
metadata = all_metadata_10x.query(f"uid == '{theislab_uid}'").iloc[0]

feature_lo = ln.Feature.lookup()
organism_lo = bt.Organism.public().lookup()
tissue_lo = bt.Tissue.public().lookup()

# Species (Organism)
organisms = bt.Organism.from_values(metadata["Species"].lower(), field="name")
ln.save(organisms)

# Orgna (Tissue)
if metadata["organ"].lower() == "olfactory_bulb":
    metadata["organ"] = "olfactorybulb"
tissues = bt.Tissue.from_values(metadata["organ"].lower(), field="name")
ln.save(tissues)

# Associate bionty terms to artifact
artifact.organism.set(organisms)
artifact.tissue.set(tissues)

ln.context.finish()
