#!/usr/bin/env python3

"""Build script for CLasH Dataset Catalog. 
Reads in data/datasets.yaml and generates site/index.html

inputs:
    data/datasets.yaml              — dataset metadata records
    templates/index.html.jinja     — HTML page structure (Jinja2 template)
    templates/style.css             — stylesheet (copied as-is)

outputs:
    site/index.html                 — the catalog page
    site/style.css                  — the stylesheet (unchanged copy)


useage:
    python build.py

The GitHub Action runs this automatically on every push to main. This is new for me, lets see how she works. 
dependencies: pyyaml, jinja2  (pip install pyyaml jinja2) 

"""

import yaml
import json
import os
import shutil
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader

#################################################
# paths - keeping these as constants makes them easy to update if the project structure ever changes
DATA_FILE     = "data/datasets.yaml"
TEMPLATE_DIR  = "templates"
TEMPLATE_FILE = "index.html.jinja"
CSS_SRC       = "templates/style.css"
OUTPUT_DIR    = "site"
OUTPUT_HTML   = os.path.join(OUTPUT_DIR, "index.html")
OUTPUT_CSS    = os.path.join(OUTPUT_DIR, "style.css")

## Hardcoded metadata about the catalog ##
observatories = ["Alaska", "Appalachia", "SoCal", "Puerto Rico",  "Network wide", "Other"]
DATA_TYPES = [
    "Airborne",
    "Drone / UAS",
    "Hydrologic",
    "Meteorological",
    "Seismic / Geodetic",
    "Geotechnical",
    "Remote Sensing",
    "Laboratory",
    "Model Output",
    "Other",
]

DATA_LEVELS = [
    "L0: Raw",
    "L1: Calibrated",
    "L2: Quality Controlled",
    "L2b: Finalized quality controlled",
    "L3: Aggregated",
    "L4: Derived products",
]

COLLECTION_STATUS = [
    "Active",
    "Complete",
    "Published",
]

#################################################

# Load dataset 
print("Loading dataset metadata from YAML...")
with open("data/datasets.yaml", "r") as f:
    raw_data = yaml.safe_load(f)

datasets = raw_data.get("datasets", []) #the list of datasets entries
print(f"Loaded {len(datasets)} datasets")
#migrate to json for easier handling later on
datasets_json = json.dumps(datasets, default=str, indent=2)


# compute some summary statistics for the sidebar filters and catalog summary
total = len(datasets)
total_gb = sum(d.get("size_gb", 0) or 0 for d in datasets) 

# count how many datasets are associated with each observatory, for the sidebar filter counts and summary stats. 
obs_counts = {obs: sum(1 for d in datasets if d.get("observatory") == obs) for obs in observatories}

# timestamp shown in page header and footer, to indicate when the catalog was last updated. Using UTC time 
yaml_mtime = os.path.getmtime('data/datasets.yaml')  
built_at = datetime.fromtimestamp(yaml_mtime, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

# Set up Jinja2 environment and load template
print("Setting up Jinja2 environment...")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
template = env.get_template(TEMPLATE_FILE)

# Render the template with the dataset and summary statistics
print("Rendering template...")
rendered_html = template.render(
    datasets_json=datasets_json,
    total=total,
    total_gb=total_gb,
    built_at=built_at,
    #controlled vocab
    observatories=observatories,
    obs_counts=obs_counts,
    data_types=DATA_TYPES,
    data_levels=DATA_LEVELS,
    collection_statuses=COLLECTION_STATUS,
)   

#write the rendered HTML to the output file
print(f"Writing output to {OUTPUT_HTML}...")
os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(rendered_html)

# copy the CSS file to the output directory
print(f"Copying CSS from {CSS_SRC} to {OUTPUT_CSS}...")
shutil.copy(CSS_SRC, OUTPUT_CSS)
# add the logo image to the output directory
shutil.copy("templates/clash_logo.png", os.path.join(OUTPUT_DIR, "clash_logo.png"))


print(f"Build complete! {total} datasets, {total_gb:.1f} GB total")
print(f"Open {OUTPUT_HTML} in a browser to view the catalog.")

