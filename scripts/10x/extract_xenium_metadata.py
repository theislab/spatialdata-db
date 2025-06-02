import pandas as pd
import numpy as np
import requests
from tqdm import tqdm

from metadata_utils import (
    find_html_file,
    extract_rendered_html,
    is_number_string,
    safe_int,
    extract_summary_fields_from_html,
)

# -------- Configuration --------
BASE_PATH = "/lustre/groups/ml01/projects/2024_spatialdata_db/data/"

XENIUM_FIELD_MAP = {
    "Panel Type": ["Panel type"],
    "Panel": ["Panel name"],
    "Number of Target Genes": ["Number of target genes"],
    "Number of predesigned target genes (RNA)": ["Number of predesigned target genes (RNA)"],
    "Number of Add-on Genes": ["Number of custom target genes (RNA)"],
    "Number of Cells": ["Number of cells detected"],
    "Median Transcripts per Cell": ["Median transcripts per cell"],
    "Region Area": ["Region area (µm²)"],
    "Total Cell Area": ["Total cell area (µm²)"],
    "Slide ID": ["Slide ID"],
    "Cassette name": ["Cassette name"],
}

XENIUM_FALLBACKS = {
    "Number of Cells": {"fallback": "prev"},
    "Median Transcripts per Cell": {"fallback": "prev"},
}

NUMERIC_FIELDS = [
    "Region Area",
    "Total Cell Area",
    "Median Transcripts per Cell",
]

INT_FIELDS = [
    "Number of Cells",
    "Number of Add-on Genes",
]

PANEL_RENAMES = {
    "Xenium Human Immuno-Oncology Add-on B Gene Expression": "Xenium Human Immuno-Oncology + Add-on",
    "Xenium Mouse Bone Add-on Gene Expression": "Xenium Mouse Bone + Add-on",
    "Xenium Human Bone Add-on Gene Expression": "Xenium Human Bone + Add-on",
    "Xenium Mouse Tissue Atlassing Gene Expression": "Xenium Mouse Tissue Atlassing",
    "Xenium Human Multi-Tissue and Cancer Gene Expression": "Xenium Human Multi-Tissue and Cancer",
    "Xenium Human Multi-Tissue + Add-on Gene Expression": "Xenium Human Multi-Tissue + Add-on",
    "Xenium Human Skin Gene Expression": "Xenium Human Skin",
    "Human Melanoma Add-on": "Xenium Human Melanoma + Add-on",
    "Xenium Human Colon Gene Expression": "Xenium Human Colon",
    "Human Colon Add-On": "Xenium Human Colon + Add-on",
    "Xenium Mouse Tissue Atlassing Panel": "Xenium Mouse Tissue Atlassing",
    "Human Multi-Tissue and Cancer Gene Expression": "Xenium Human Multi-Tissue and Cancer",
    "Mouse_Brain_With_Addon": "Xenium Mouse Brain + Add-on",
    "R&D Panel": "Xenium R&D Panel",
    "hBreast_v1_AddOn100g": "Xenium Human Breast + Add-on",
    "Xenium Mouse Brain GEX": "Xenium Mouse Brain",
    "Xenium Human Breast GEX": "Xenium Human Breast",
}

ADD_ON_RENAMES = {
    "Add_on": "Custom Add-on",
    "Add on": "Custom Add-on",
    "Add-on Custom": "Custom Add-on"
}

# -------- Utility --------
def fill_missing_target_genes(row):
    if pd.isna(row["Number of Target Genes"]) or row["Number of Target Genes"] == "":
        predesigned = safe_int(row.get("Number of predesigned target genes (RNA)", 0))
        custom = safe_int(row.get("Number of Add-on Genes", 0))
        return predesigned + custom
    return row["Number of Target Genes"]

# -------- Main Workflow --------
def main(input_csv, output_csv, failed_csv):
    df = pd.read_csv(input_csv, sep=";", index_col=0)
    df["uid"] = df.index

    required_cols = {"uid", "Dataset Url", "Assay"}
    if missing := (required_cols - set(df.columns)):
        raise ValueError(f"Missing required column(s): {missing}")

    xenium_df = df[df["Assay"].str.strip().str.lower().str.contains(r"\bxenium\b", na=False)].copy()
    extracted, failed = [], []

    for _, row in tqdm(xenium_df.iterrows(), desc="Scraping Xenium Dataset URLs"):
        uid, url = row["uid"], row["Dataset Url"]
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            html_path = find_html_file(BASE_PATH, uid)
            rendered_html = extract_rendered_html(html_path)
            metadata = extract_summary_fields_from_html(rendered_html, XENIUM_FIELD_MAP, XENIUM_FALLBACKS)

            metadata["uid"] = uid
            metadata["Dataset Url"] = url
            extracted.append(metadata)

        except Exception as e:
            failed.append({"uid": uid, "Dataset Url": url, "error": str(e)})

    # -------- DataFrame Processing --------
    df_extracted = pd.DataFrame(extracted)

    df_extracted["Number of Target Genes"] = df_extracted.apply(fill_missing_target_genes, axis=1)
    df_extracted = df_extracted.drop(columns=["Number of predesigned target genes (RNA)"], errors="ignore")

    # Compose "Sample ID at Source" from "Slide ID" and "Cassette name"
    slide = df_extracted["Slide ID"].astype(str).str.strip()
    cassette = df_extracted["Cassette name"].astype(str).str.strip()
    valid_slide = (slide != "") & (slide != "N/A")
    valid_cassette = (cassette != "") & (cassette != "N/A")
    df_extracted["Sample ID at Source"] = np.where(
        valid_slide & valid_cassette,
        slide + " " + cassette,
        np.where(valid_slide, slide, np.where(valid_cassette, cassette, None))
    )
    df_extracted.drop(columns=["Slide ID", "Cassette name"], inplace=True)

    # Convert numbers
    for col in NUMERIC_FIELDS:
        df_extracted[col] = pd.to_numeric(
            df_extracted[col].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        ).fillna(0).astype(float)

    for col in INT_FIELDS:
        df_extracted[col] = pd.to_numeric(
            df_extracted[col].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        ).fillna(0).astype(int)

    # Normalize labels
    df_extracted["Panel Type"] = df_extracted["Panel Type"].replace(ADD_ON_RENAMES)

    df_extracted["Panel"] = df_extracted["Panel"].replace(PANEL_RENAMES)

    # Save
    df_extracted.to_csv(output_csv, index=False, sep=";")
    pd.DataFrame(failed).to_csv(failed_csv, index=False, sep=";")

    print(f"\n✅ Extracted: {len(df_extracted)} entries")
    print(f"❌ Failed: {len(failed)} entries")

# -------- Entry Point --------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract Xenium metadata from 10x dataset pages")
    parser.add_argument("--base_path", default=BASE_PATH, help="Base path for HTML files")
    parser.add_argument("--input", required=True, help="Input CSV with uid,Dataset Url,Assay columns")
    parser.add_argument("--output", default="xenium_metadata.csv", help="Output CSV for extracted metadata")
    parser.add_argument("--failed", default="failed_Dataset Urls.csv", help="Output CSV for failed Dataset Url extractions")
    args = parser.parse_args()

    main(args.input, args.output, args.failed)
