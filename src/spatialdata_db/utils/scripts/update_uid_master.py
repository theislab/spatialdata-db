import os
import pandas as pd


def update_master_with_ids(uid_master_csv_path, file_paths):
    uid_master_df = pd.read_csv(uid_master_csv_path, sep=";")

    # Iterate over the list of file paths
    for file_path in file_paths:
        # Load the current CSV file
        df = pd.read_csv(file_path, sep=";")

        # Ensure the CSV file contains the required columns
        if "uid" not in df.columns or "id" not in df.columns:
            raise ValueError(
                f"{file_path} does not contain 'uid' and 'id' columns. Please ensure the file has these columns."
            )

        print(uid_master_df)
        master_df = uid_master_df.merge(
            df[["uid", "id"]], on="uid", how="left", suffixes=("", "_new")
        )

        master_df["id"] = master_df["id"].combine_first(master_df["id_new"])
        print(master_df)
        master_df.drop(columns=["id_new"], inplace=True)

    master_df.to_csv(master_csv_path, index=False, sep=";")
    print(f"Master CSV updated and saved to {master_csv_path}.")


if __name__ == "__main__":
    master_csv_path = "../data/uid_master.csv" 
    dataset_paths = [
        "../data/datasets_10x.csv",
        # tbd
    ]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_paths = [os.path.join(script_dir, file_path) for file_path in dataset_paths]

    update_master_with_ids(master_csv_path, file_paths)
