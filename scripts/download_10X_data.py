#!/usr/bin/env python

# # Download 10X data

# In[1]:


import json
import pathlib as pl
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd
from tqdm.auto import tqdm

OUTPUT_DIR = pl.Path("/lustre/groups/ml01/projects/2024_spatialdata_db/data")


# In[2]:


data = pd.read_csv("/home/icb/tim.treis/projects/spatialdata-db/scripts/data/10x_datasets.csv")[:2]
data


# ## Create folders and jobs for downloading

# In[3]:


download_jobs = []


def create_directory(path: pl.Path):
    if not path.exists():
        path.mkdir()
        print(f"Created directory: {path}")


def sanitize_key(key: str):
    return key.replace(" ", "_").replace("(", "").replace(")", "").replace(":", "").replace("&", "n")


download_jobs = []

for idx, row in data.iterrows():
    dataset_path = OUTPUT_DIR / row["id"]
    create_directory(dataset_path)

    raw_input_path = dataset_path / "raw_input"
    create_directory(raw_input_path)
    raw_output_path = dataset_path / "raw_output"
    create_directory(raw_output_path)

    for idx, field in enumerate(["input_links", "output_links"]):
        if row.get(field):
            links = json.loads(row[field])
            links_dict = {sanitize_key(link["name"]): link["url"] for link in links}
            for name, url in links_dict.items():
                # filter out links to the support page and subsets
                if "https" in url and "subset" not in name:
                    download_jobs.append(
                        {"name": name, "url": url, "output_folder": [raw_input_path, raw_output_path][idx]}
                    )

download_jobs


# ## Download files

# In[5]:


def download_file(job):
    """Download a file using curl and save it to a specified path."""
    # Parse the file name from the URL
    parsed_url = urlparse(job["url"])
    file_name = pl.Path(parsed_url.path).name
    output_path = job["output_folder"] / file_name

    curl_command = ["curl", "-o", str(output_path), "-L", job["url"]]

    try:
        subprocess.run(curl_command, check=True, capture_output=True)
        return job, None
    except subprocess.CalledProcessError as e:
        return job, e


def main(download_jobs):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"failed_downloads_{timestamp}.log"
    with open(log_file, "w") as log:
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(download_file, job) for job in download_jobs]
            for future in tqdm(as_completed(futures), total=len(download_jobs), desc="Downloading files"):
                job, error = future.result()
                if error:
                    error_message = f"Failed to download {job['name']} from {job['url']}: {error}\n"
                    log.write(error_message)
                    print(error_message)


if __name__ == "__main__":
    main(download_jobs)
