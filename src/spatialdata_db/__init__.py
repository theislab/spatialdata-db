from importlib.metadata import version
from importlib import resources
import pandas as pd


def load_10x_metadata():
    with resources.open_text("spatialdata_db.utils.data", "10x_datasets.csv") as file:
        return pd.read_csv(file, sep=";")


__all__ = ["load_10x_metadata"]
__version__ = version("spatialdata-db")
