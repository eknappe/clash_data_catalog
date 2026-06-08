# CLaSH Metadata Catalog

This is a simple display of metadata of datasets that are relevant to CLaSH. This catalog is designed to make it easier to find datasets related to CLaSH activites and increase collaboration. This catalog does not store the actual data and all data should be stored in a different location until it can be published on an open data repository. This catalog is meant for project team members and collaborators. 

The project is currently hosted on the CLaSH GitHub here: https://clash-geohazards.github.io/metadata_catalog/

The metadata catalog has multiple filtering options to make it easier to find the data of interest including by date, observatory location, data type, and data level (as well as combining filters).

The catalog is a static website generated from a YAML and built to easily add additional datasets. To add additional datasets, enter the information in the `data/dataset.yaml` and push to GitHub. The site rebuilds and redeploys. 

## Getting Started

### Repository structure

    clash_data_catalog/
    ├── .github/
    │   └── workflows/
    │       └── deploy.yml          — GitHub Action: builds and deploys on push
    ├── data/
    │   └── datasets.yaml           — the dataset catalog (edit this to add entries)
    ├── templates/
    │   ├── index.html.jinja        — HTML page template
    │   └── style.css               — stylesheet
    ├── site/                       — generated output (do not edit — overwritten on each build)
    │   ├── index.html
    │   └── style.css
    ├── build.py                    — build script: reads YAML, renders site
    ├── requirements.txt            — Python dependencies
    ├── License.md                  - MIT license info
    ├── READMe.md                   - we're here
    └── .gitignore

### Dependencies

Required dependencies are within the requirements.txt

### Adding a dataset

Open `data/datasets.yaml` and add a new entry following the below structure. Required field are marked with `*`. 


```yaml
- id: DS008                          # * unique ID, increment from last entry
  name: "..."                        # * short descriptive title
  description: >                     # * 2-4 sentence description
    ...
  pi: "..."                          # * PI full name
  institution: "..."                 # * university or organisation
  primary_contact: "..."             # primary contact for the data if different from PI
  personnel:                         # list of contributors/co-authors
    - "..."
  observatories:                     # * list — use exact names below, can list multiple
    - Alaska                         #   Alaska | Appalachia | SoCal |
    - SoCal                          #   Puerto Rico | Network wide | Other
  data_type: "..."                   # * see controlled vocabulary below
  instrument: "..."                  # instrument or platform used
  parameters_measured:               # list of measured variables
    - "..."
  field_site: "..."                  # location name
  spatial:
    type: points                     # or as bboxes
    locations:                       # bbox list as:
    - {lat: xx.xx, lon: xx.xx}       # - {north: xx.xx, south: xx.xx, east: xx.xx,   west: xx.xx}                                  
  collection_start: "YYYY-MM-DD"    # * ISO date
  collection_end: "YYYY-MM-DD"      # leave blank if ongoing
  temporal_resolution: "..."         # e.g. "15 minutes", "single campaign"
  spatial_resolution: "..."          # e.g. "0.5 m", "point (6 stations)"
  format: "..."                      # e.g. "CSV", "GeoTIFF", "miniSEED"
  size_gb:                           # approximate size as a number
  data_level: "..."                  # * see controlled vocabulary below
  processing_contact: "..."          # who to contact about the data processing
  collection_status: "..."           # * Active | Complete | Published
  data_location: "..."               # server path or link to where data lives
  access_notes: "..."                # who can access, any restrictions
  doi: ""                            # leave blank until published
  publications: []                   # list of related publication DOIs
  date_added: "YYYY-MM-DD"          # today's date
  notes: "..."                       # any additional notes — sensor outages,
                                     # known gaps, publication intentions, etc.
```

### Controlled vocabularies

For the filters to work properly, these values must be used exactly as written, including capitalization. 

observatory
`Alaska` · `Appalachia` · `SoCal` · `Puerto Rico` · `Network wide`· `Other`

data_type:
`Airborne` · `Drone / UAS` · `Hydrologic` · `Meteorological` · `Seismic / Geodetic` · `Geotechnical` · `Remote Sensing` · `Laboratory` · `Model Output` · `Other`

data_level:
`L0: Raw` · `L1: Calibrated` · `L2: Quality Controlled` · `L2b: Finalized quality controlled` · `L3: Aggregated` · `L4: Derived products`

collection_status:
`Active` · `Complete` · `Published`


### Running and building locally

**First time setup:**

```bash
# clone the repo
git clone https://github.com/your-org/clash-catalog.git
cd clash-catalog

# create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac / Linux
venv\Scripts\activate           # Windows

# install dependencies
pip install -r requirements.txt
```

**Build and preview:**

```bash
python build.py
open site/index.html            # or just open the file in any browser
```

## Making changes to the site

| What you want to change | File to edit |
|---|---|
| Add or update a dataset | `data/datasets.yaml` |
| Change page layout or structure | `templates/index.html.jinja` |
| Change colours, fonts, or styling | `templates/style.css` |
| Add a new data type or status option | `build.py` (vocabulary lists at the top) |
| Change deployment behaviour | `.github/workflows/deploy.yml` |

## Authors

E. Knappe 


## License

This project is licensed under the MIT License - see the LICENSE.md file for details

## Funding

This work was supported by the Center for Land Surface Hazards (CLaSH), funded via National Science Foundation Cooperative Agreement NSF-2425607.