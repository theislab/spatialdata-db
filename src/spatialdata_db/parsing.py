from importlib import resources
import pandas as pd


def load_10x_metadata():
    with resources.open_text("spatialdata_db.utils.data", "datasets_10x.csv") as file:
        return pd.read_csv(file, sep=";")
