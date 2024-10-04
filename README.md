# spatialdata-db

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
  - 10 _ _ _ -> 29791 IDs for 10X Genomics
  - vg _ _ _ -> 29791 IDs for Vizgen
  - ns _ _ _ -> 29791 IDs for Nanostring
  - xx _ _ _ -> 29791 IDs for miscellaneous, such as publication
