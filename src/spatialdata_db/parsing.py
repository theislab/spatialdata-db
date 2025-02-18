from importlib import resources

import pandas as pd


def load_10x_metadata():
    """
    Load 10x Genomics dataset metadata from a CSV file.

    The function reads the `datasets_10x.csv` file stored in the `spatialdata_db.utils.data`
    package directory and returns it as a pandas DataFrame.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing metadata for 10x Genomics datasets.
    """
    with resources.open_text("spatialdata_db.utils.data", "datasets_10x.csv") as file:
        return pd.read_csv(file, sep=";")
