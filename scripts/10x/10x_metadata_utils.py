# metadata_utils.py

import os
import glob
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def find_html_file(base_path, uid):
    """
    Finds the first .html file under raw_output/ for a given uid folder.
    """
    pattern = os.path.join(base_path, f"{uid}*", "raw_output", "*.html")
    matches = glob.glob(pattern)
    if len(matches) == 0:
        raise FileNotFoundError(f"No HTML file found for UID: {uid} in {base_path}")
    return matches[0]

def extract_rendered_html(file_path, sleep_time=3):
    """
    Uses Selenium to render HTML from file.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=options)
    url = "file://" + file_path
    driver.get(url)
    time.sleep(sleep_time)
    rendered_html = driver.page_source
    driver.quit()
    return rendered_html

def is_number_string(s):
    try:
        float(s.replace(',', ''))
        return True
    except (ValueError, TypeError):
        return False

def clean_html(raw_text):
    return BeautifulSoup(raw_text, "lxml").get_text(separator=" ").strip()

def safe_int(val):
    try:
        return int(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0

def extract_summary_fields_from_html(html_content, field_map, field_behaviors=None):
    """
    Extract summary values from rendered HTML using a schema of expected fields.

    Parameters:
    - html_content: str, rendered HTML text
    - field_map: dict of {desired_key: list of possible label strings}
    - field_behaviors: dict of {desired_key: {"fallback": "prev"|"next"}}

    Returns:
    - dict of {key: extracted value or None}
    """
    soup = BeautifulSoup(html_content, "lxml")
    all_text = soup.get_text(separator="\n").splitlines()
    cleaned_lines = [line.strip() for line in all_text if line.strip()]

    summary = {key: None for key in field_map}

    field_behaviors = field_behaviors or {}

    for i, line in enumerate(cleaned_lines):
        for key, aliases in field_map.items():
            if summary[key] is not None:
                continue

            for alias in aliases:
                if alias.lower() in line.lower():
                    # Try value after colon
                    if ":" in line:
                        summary[key] = line.split(":", 1)[1].strip()
                    else:
                        fallback = field_behaviors.get(key, {}).get("fallback", "next")
                        if fallback == "prev" and i > 0:
                            prev_line = cleaned_lines[i - 1].strip()
                            if is_number_string(prev_line):
                                summary[key] = prev_line
                        elif fallback == "next" and i + 1 < len(cleaned_lines):
                            next_line = cleaned_lines[i + 1].strip()
                            if is_number_string(next_line) or next_line:
                                summary[key] = next_line
                    break

    return summary
