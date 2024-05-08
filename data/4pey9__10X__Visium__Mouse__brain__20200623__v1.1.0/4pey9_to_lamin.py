# ADJUST
uid = "4pey9"

# Setup before running this script for the first time
#   1) Ensure you have a lamin.ai account
#   2) Run `lamin login` to authenticate
#   3) Activate lamin db connection with `lamin load scverse/spatial`
#   4) Execute script once and replace the stem_uid for this file

import lamindb as ln

ln.settings.transform.stem_uid = "KgGzOw8PUYKO"
ln.settings.transform.version = "3"

ln.track()

try:
    artifact = ln.Artifact.filter(ulabels__name=uid).one()
    artifact.delete(permanent=True)
except:
    pass

### From here on we assume Lamin is set up correctly
DATASET_PATH = "/lustre/groups/ml01/projects/2024_spatialdata_db/data/4pey9__10X__Visium__Mouse__brain__20200623__v1.1.0/4pey9__10X__Visium__Mouse__brain__20200623__v1.1.0.spatialdata.zarr"

artifact = ln.Artifact(DATASET_PATH, description="10X, Visium, Mouse, Brain")
artifact.save() # transfers to Lamin

# Associate ID with the artifact so we can retrieve afterwards
tuid_parent = ln.ULabel.filter(name="theislab unique ID").one()
tuid = ln.ULabel(name=uid).save()
tuid.parents.add(tuid_parent)
artifact.labels.add(tuid)

# load 10X metadata we have on disk
import pandas as pd

all_metadata_10x = pd.read_csv("../../utils/data/10x_datasets.csv", sep=";")
assert len(all_metadata_10x.query(f"uid == '{uid}'")) == 1
metadata = all_metadata_10x.query(f"uid == '{uid}'").iloc[0]

# Associate metadata as features
import bionty as bt

feature_lo = ln.Feature.lookup()
organism_lo = bt.Organism.public().lookup()
tissue_lo = bt.Tissue.public().lookup()

# Species --

if metadata["Species"].lower() == "mouse":
    feature_organism = bt.Organism.from_public(name=organism_lo.mouse.name)
elif metadata["Species"].lower() == "human":
    feature_organism = bt.Organism.from_public(name=organism_lo.human.name)
else:
    raise NotImplementedError("Unknown species!")

feature_organism.save()

# Tissue

if metadata["organ"].lower() == "olfactory_bulb":
    metadata["organ"] = "olfactorybulb"

if metadata["organ"].lower() == "brain":
    feature_tissue = bt.Tissue.from_public(name=tissue_lo.brain.name)
elif metadata["organ"].lower() == "kidney":
    feature_tissue = bt.Tissue.from_public(name=tissue_lo.kidney.name)
elif metadata["organ"].lower() == "colon":
    feature_tissue = bt.Tissue.from_public(name=tissue_lo.colon.name)
else:
    raise NotImplementedError("Unknown tissue!")

feature_tissue.save()

# Associate bionty terms to artifact

artifact.labels.add(feature_organism, feature=feature_lo.organism)
artifact.labels.add(feature_tissue, feature=feature_lo.tissue)


# finish for tracing in Lamin

ln.finish()