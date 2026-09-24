# spatialdata-db

Central hub for SpatialData-DB. Two sibling repos are vendored as git submodules
under `extern/`:

- `extern/schemas` → [spatialdata-schemas](https://github.com/theislab/spatialdata-schemas)
  — the lamin metadata contract (pinned at a release tag; **external / read-only**,
  do not edit in place).
- `extern/curation` → [spatialdata-db-curation](https://github.com/theislab/spatialdata-db-curation)
  — dataset intake, registry, and UID assignment.

This repo (`spatialdata_db`) owns raw→zarr conversion, validation/curation, and
lamin registration.

### Getting the submodules

```bash
git clone --recursive https://github.com/theislab/spatialdata-db
# or, in an existing clone:
pixi run sync            # = git submodule update --init --recursive
```

### Building the schema into the instance

```bash
pixi run -e schema build-schema   # runs extern/schemas' build_all() against the connected lamin instance
```

To advance the schema, bump the `extern/schemas` submodule to a newer tag and re-run.

---

Currently focusing on the following datasets for diversity in testing:

- `10ktp`: Visium, Mouse, Brain
- `4b368`: Visium, Mouse, Lung
- `m1v5v`: Xenium, Human, Lung
- `oeuwa`: Xenium, Mouse, Brain
- `jqmx8`: VisiumHD, Mouse, Intestine

## Setup vitessce

Currently, the `SpatialDataWrapper` is not yet merged and released. Therefore, we have to install it via

```bash
pip install anywidget starlette uvicorn
pip install git+https://github.com/vitessce/vitessce-python.git@ig/spatial_data
```

from Ilan's PR: https://github.com/vitessce/vitessce-python/pull/333

## UID logic

- Absolute ID will be a 5 char string of lowercase letters and digits -> 60466176 IDs
- Leaving out the letters [l, b, o, g, q] due to their similarity to [1, 6, 0, 9, 9] -> 28629151 IDs
- Reserve ID spaces for technology providers
  - 10 \_ \_ \_ -> 29791 IDs for 10X Genomics
  - vg \_ \_ \_ -> 29791 IDs for Vizgen
  - ns \_ \_ \_ -> 29791 IDs for Nanostring
  - xx \_ \_ \_ -> 29791 IDs for miscellaneous, such as publication
