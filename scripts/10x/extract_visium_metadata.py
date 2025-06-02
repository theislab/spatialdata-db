import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from tqdm import tqdm

from metadata_utils import (
    find_html_file,
    extract_rendered_html,
    is_number_string,
    clean_html,
    extract_summary_fields_from_html,
)

# -------- Configuration --------
BASE_PATH = "/lustre/groups/ml01/projects/2024_spatialdata_db/data/"

VISIUM_FIELD_MAP = {
    "Chemistry Details": ["Chemistry"],
    "Probe Set Name": ["Probe Set Name"],
    "Number of Target Genes": ["Number of Genes Targeted"],
    "Transcriptome": ["Transcriptome"],
    "Pipeline Version": ["Pipeline Version"],
    "Number of Spots": ["Number of Spots Under Tissue"],
    "Mean Reads per Spot": ["Mean Reads per Spot"],
    "Median Genes per Spot": ["Median Genes per Spot"],
    "Genes Detected": ["Genes Detected"],
}

VISIUM_FALLBACKS = {
    "Number of Spots Under Tissue": {"fallback": "prev"},
    "Mean Reads per Spot": {"fallback": "prev"},
    "Median Genes per Spot": {"fallback": "prev"},
}

NUMERIC_FIELDS = [
    'Mean Reads per Spot',
    'Median Genes per Spot'
]

INT_FIELDS = [
    'Number of Spots',
    'Genes Detected',
    'Number of Target Genes'
]

instruments_found = set()

# -------- Utilities --------
def extract(text, primary_regex, fallback_regex=None, group=1, default=None):
    match = re.search(primary_regex, text, re.IGNORECASE)
    if match:
        return match.group(group).strip()
    if fallback_regex:
        match = re.search(fallback_regex, text, re.IGNORECASE)
        if match:
            return match.group(group).strip()
    return default

def extract_instruments_10x(text):
    instruments = []
    capture = False
    for line in text.splitlines():
        line = line.strip()
        if re.search(r'^10x Instrument\(s\)', line, re.IGNORECASE):
            capture = True
            continue
        if capture:
            if not line or re.match(r'^[A-Z][a-z]+(?: [A-Z][a-z]+)*$', line):
                break
            if any(char.isalnum() for char in line):
                instruments.append(line)
    return instruments

def extract_microscope_settings(text):
    settings = {}

    microscope_match = re.search(
        r'acquired using (?:an? )?(.+?microscope)', text, re.IGNORECASE
    )
    if microscope_match:
        settings['Microscope'] = microscope_match.group(1).strip()

    block_match = re.search(
        r'(?:with the following settings|with these settings):(.+?)(?:\n\s*\n|$)',
        text, re.DOTALL | re.IGNORECASE
    )
    if block_match:
        for line in block_match.group(1).splitlines():
            line = clean_html(line.strip())
            if not line:
                continue

            if 'objective' in line.lower():
                match = re.search(r'(?:magnification\s*:)?\s*(\d+x[^:]*)', line, re.IGNORECASE)
                settings['Objective'] = match.group(1).strip() if match else line

            elif 'numerical aperture' in line.lower():
                match = re.search(r'Numerical Aperture\s*:\s*([\d.]+)', line, re.IGNORECASE)
                if match:
                    settings['Numerical Aperture'] = match.group(1)

            elif 'camera' in line.lower():
                match = re.search(r'Camera\s*:\s*(.+)', line, re.IGNORECASE)
                settings['Camera'] = match.group(1).strip() if match else line

            elif 'exposure' in line.lower():
                match = re.search(r'Exposure\s*:\s*([\d.]+\s*\w+)', line, re.IGNORECASE)
                if match:
                    settings['Exposure'] = match.group(1).strip()

            elif 'gain' in line.lower():
                match = re.search(r'Gain\s*:\s*([\d.]+X?)', line, re.IGNORECASE)
                if match:
                    settings['Gain'] = match.group(1).strip()

    return settings

def extract_metadata_from_html(html):
    soup = BeautifulSoup(html, 'lxml')
    text = soup.get_text(separator='\n')

    metadata = {
        'Probe Set': extract(
            text,
            r'Visium Gene Expression library\s*\(([^)]+)\)',
            fallback_regex=r'Probe Set\s*:\s*(.+)'
        ),
        'Sequencing Instrument': extract(text, r'Sequencing instrument:\s*(.+?)(?:,|\n)'),
        'Sequencing Configuration': extract(text, r'Sequencing configuration:\s*(.+?)(?:\.|\n)'),
        'Slide': extract(
            text,
            r'Slide:\s*([A-Za-z0-9\-]+)',
            fallback_regex=r'Slides:\s*([A-Za-z0-9\-, ]+)'
        ).split(',')[-1].strip(),
        'Area': extract(
            text,
            r'Area:\s*([A-Za-z0-9]+)',
            fallback_regex=r'Areas:\s*([A-Za-z0-9, ]+)'
        ),
    }

    metadata['instruments_10x'] = ', '.join(extract_instruments_10x(text))
    return metadata

# -------- Main Workflow --------
def main(input_csv, output_csv, failed_csv):
    df = pd.read_csv(input_csv, sep=';', index_col=0)
    df['uid'] = df.index

    required_cols = {"uid", "Dataset Url", "Assay"}
    if missing := (required_cols - set(df.columns)):
        raise ValueError(f"Missing required column(s): {missing}")

    visium_df = df[df['Assay'].str.strip().str.lower().str.contains(r'\bvisium\b', na=False)].copy()
    extracted, failed = [], []

    for _, row in tqdm(visium_df.iterrows(), desc="Scraping Visium Dataset URLs"):
        uid, url = row['uid'], row['Dataset Url']
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            metadata = extract_metadata_from_html(response.text)
            metadata.update({
                'uid': uid,
                'Dataset Url': url,
                'Instrument(s)': '|'.join(filter(None, [
                    metadata.pop('instruments_10x', None),
                    metadata.pop('Sequencing Instrument', None)
                ]))
            })

            metadata.update(extract_microscope_settings(response.text))

            html_path = find_html_file(BASE_PATH, uid)
            rendered_html = extract_rendered_html(html_path)
            metadata.update(extract_summary_fields_from_html(rendered_html, VISIUM_FIELD_MAP, VISIUM_FALLBACKS))

            extracted.append(metadata)

        except Exception as e:
            failed.append({'uid': uid, 'Dataset Url': url, 'error': str(e)})

    # -------- DataFrame Processing --------
    df_extracted = pd.DataFrame(extracted).rename(columns={
        "Area": "Slide Area",
        "Slide": "Sample ID at Source",
        "Number of Spots Under Tissue": "Number of Spots",
        "Number of Genes Targeted": "Number of Target Genes"
    })

    # Merge config and probe set
    df_extracted['Sequencing Configuration'] = df_extracted.apply(
        lambda row: f"{row['Sequencing Configuration']}, {row['Probe Set']}"
        if pd.notna(row.get('Probe Set')) else row['Sequencing Configuration'],
        axis=1
    )

    df_extracted['Probe Set'] = df_extracted.pop('Probe Set Name')

    for col in NUMERIC_FIELDS:
        df_extracted[col] = pd.to_numeric(df_extracted[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(float)

    for col in INT_FIELDS:
        df_extracted[col] = pd.to_numeric(df_extracted[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)

    df_extracted.to_csv(output_csv, index=False, sep=';')
    pd.DataFrame(failed).to_csv(failed_csv, index=False, sep=';')

    print(f"\n✅ Extracted: {len(df_extracted)} entries")
    print(f"❌ Failed: {len(failed)} entries")

    if instruments_found:
        print("\n📟 Instruments found under '10x Instrument(s)':")
        for inst in sorted(instruments_found):
            print(f" - {inst}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract Visium metadata from 10x dataset pages")
    parser.add_argument("--base_path", default=BASE_PATH, help="Base path for HTML files")
    parser.add_argument("--input", required=True, help="Input CSV with uid,Dataset Url,Assay columns")
    parser.add_argument("--output", default="visium_metadata.csv", help="Output CSV for extracted metadata")
    parser.add_argument("--failed", default="failed_Dataset Urls.csv", help="Output CSV for failed Dataset Url extractions")
    args = parser.parse_args()
    main(args.input, args.output, args.failed)
