# Setup before running this script for the first time
#   1) Ensure you have a lamin.ai account
#   2) Run `lamin login` to authenticate
#   3) Activate lamin db connection with `lamin load scverse/spatialdata-db`
#   4) Execute script once and replace the stem_uid for this file

import bionty as bt
import lamindb as ln
import pandas as pd

# ln.settings.transform.stem_uid = "nkdyAzUAOgH70000"
# ln.settings.transform.version = "3"

# (spatialdata-workshop) [lea.zimmermann@cpusrv39 10ktp__10X__Visium__Mouse__brain__20200623__v1.1.0]$ python 10ktp_to_lamin.py
# → connected lamindb: scverse/spatialdata-db
# ✗ you already have a transform with key '10ktp_to_lamin.py' ('KgGzOw8PUYKO7CpM')
#   - to make a revision, call `ln.track('KgGzOw8PUYKO7CpN')`
#   - to create a new transform, rename your file and run: `ln.track()`
# ln.track("KgGzOw8PUYKO7CpM")

# after renaming:
# (spatialdata-workshop) [lea.zimmermann@cpusrv39 10ktp__10X__Visium__Mouse__brain__20200623__v1.1.0]$ python 10ktp_to_lamin_test.py
# → connected lamindb: scverse/spatialdata-db
# ✗ to track this script, copy & paste `ln.track("b2q7qhDuWCQ40000")` and re-run
ln.track("b2q7qhDuWCQ40000")

# ADJUST
uid = "10ktp"

try:
    artifact = ln.Artifact.filter(ulabels__name=uid).one()
    artifact.delete(permanent=True)
except:
    pass

### From here on we assume Lamin is set up correctly
DATASET_PATH = "/lustre/groups/ml01/projects/2024_spatialdata_db/data/10ktp__10X__Visium__Mouse__brain__20200623__v1.1.0/10ktp__10X__Visium__Mouse__brain__20200623__v1.1.0.spatialdata.zarr"

artifact = ln.Artifact(DATASET_PATH, description="10X, Visium, Mouse, Brain")
artifact.save()  # transfers to Lamin

# Associate ID with the artifact so we can retrieve afterwards
tuid_parent = ln.ULabel.filter(name="theislab unique ID").one()
tuid = ln.ULabel(name=uid).save()
tuid.parents.add(tuid_parent)
artifact.labels.add(tuid)

all_metadata_10x = pd.read_csv("../../utils/data/10x_datasets.csv", sep=";")
assert len(all_metadata_10x.query(f"uid == '{uid}'")) == 1
metadata = all_metadata_10x.query(f"uid == '{uid}'").iloc[0]

# Associate metadata as features
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

artifact.organisms.add(feature_organism)
artifact.tissues.add(feature_tissue)

# finish for tracing in Lamin

ln.finish()
