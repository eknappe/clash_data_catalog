# Download google sheet, and convert it into yaml format for dataset.yaml

from pathlib import Path
import re
from datetime import date, datetime
import os
import yaml
import csv

# set working directory to be the current folder
working_directory = Path.cwd()

data_directory = working_directory / 'data'
google_directory = working_directory / 'data/gdownload'

# just downloaded from google cause no permissions for google api
gfile = google_directory / 'CLaSH dataset submission.csv'
#where the exisiting dataset lives
yaml_path = data_directory / 'datasets.yaml' 
yaml_save = data_directory / 'datasets_check.yaml' #don't want to overwrite the current, until checked

# do you want to update everything, e.g. reprocess the old datasets
UPDATE = False #set to True 


### Column mapping ###
# the csv naming does not exactly match the dataset.yaml naming
# left = csv, right = yaml

column_map = {
   "Dataset title/name" :           "name",
   "Short description" :            "description",
   "PI name" :                      "pi",
   "Institution" :                  "institution",
   "Primary contact" :              "primary_contact",
   "Collaborating personnel" :      "personnel",
   "Data type / classification" :   "data_type",
   "Instrument / equipment" :       "instrument",
   "Parameters measured" :          "parameters_measured",
   "Observatory" :                  "observatories",
   "Field site / geographic location": "field_site",
   "Spatial coverage" :             "_spatial_type",
   "Latitude, Longitude" :          "_latlon",
   "Collection start date" :        "colletion_start",
   "Collection end date" :          "collection_end",
   "Temporal resolution" :          "temporal_resolution",
   "Spatial resolution" :           "spatial_resolution",
   "File format" :                  "format",
   "Approximate size (GB)" :        "size_gb",
   "Data level" :                   "data_level",
   "Processing_contact":            "processing_contact",
   "Collection status" :            "collection_status",
   "Where does the data live?" :    "data_location",
   "Access Notes" :                 "access_notes",
   "DOI" :                          "doi",
   "Timestamp" :                    "date_added",
   "Additional notes" :             "notes"  
}

# list fields - field that should become yaml lists 
list_fields = {'observatories', 'personnel', 'parameters_measured'}

# field that has to be numeric (because we calculate total amount using)
numeric_fields = {'size_gb'}

# map values to controlled vocabs that we have
spatial_type_map = {
    "point observation(s)" :    "points",
    "bounding box(es)" :        "bboxes"
}

collection_status_map = {
    "Active - ongoing collection" :                 "Active",
    "Complete - collection finished" :              "Complete",
    "Published - data is in a data repository" :    "Published"
}


# fields in the order they should appear in the yaml
field_order = [
    'id', 'name', 'description', 'pi', 'institution', 'primary_contact', 'personnel',
    'observatories', 'data_type', 'instrument', 'parameters_measured',
    'field_site', 'spatial', 'collection_start', 'collection_end',
    'temporal_resolution', 'spatial_resolution', 'format', 'size_gb',
    'data_level', 'processing_contact', 'collection_status', 'data_location', 'access_notes',
    'doi', 'date_added', 'notes'
]

# fields that should NOT get quotes
no_quote_fields = {'observatories', 'size_gb', 'collection_status', 'data_type', 'id'}

# fields that are lists of simple strings
list_string_fields = {'personnel', 'parameters_measured', 'observatories'}



########## conjunction junction whats your function ##########

# assign dataset ids (DS###) based on existing entries
def next_id(all_datasets):
    nums = []
    for d in all_datasets:
        try:
            nums.append(int(str(d.get('id')).replace('DS', '')))
        except ValueError:
            pass
    return f"DS{max(nums, default=0) + 1:03d}"


def normalize_date(val):
    if not val:
        return None
    #already datetime object (this is google formatting)
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    
    #or convert to string if not already
    val = str(val).strip()
    if not val:
        return None
    
    for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y'):
        try:
            return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    # if it has a time component 
    try:
        return datetime.strptime(val.split()[0], '%m/%d/%Y').strftime('%Y-%m-%d')
    except ValueError:
        pass
    print(f"  warning: could not parse date '{val}', keeping as-is")
    return val


#convert the location from what's entered to how its in the yaml
def parse_latlon(val, spatial_type_hint):
    if not val or not val.strip():
        return None
    
    #default to points if not defined
    stype = spatial_type_map.get(spatial_type_hint.lower().strip(), 'points')
    
    if stype == "points":
        # split on semicolon or fall back and try sequentials numbers being pairs
        raw_pairs = [p.strip() for p in val.split(';') if p.strip()]
        
        if len(raw_pairs) > 1:
            locations = []
            for pair in raw_pairs:
                nums = re.findall(r'-?\d+\.?\d*', pair)
                if len(nums) >= 2:
                    locations.append({'lat': float(nums[0]), 'lon': float(nums[1])})
                else:
                    print(f" warning: could not parse point pair {pair} - skipping")
            if not locations:
                print(f"warning no valid points parsed from {val}")
                return None
            return {'type': 'points', 'locations': locations}
    
        else:
            # single pair 
            nums = re.findall(r'-?\d+\.?\d*', val)
            if len(nums) < 2:
                print(f"  warning: could not parse lat/lon from {val}")
                return None
            return {'type': 'points', 'locations': [{'lat': float(nums[0]), 'lon': float(nums[1])}]}
           

    elif stype == 'bboxes':
        # expect N, S, E, W order — split on semicolons for multiple boxes
        raw_boxes = [b.strip() for b in val.split(';') if b.strip()]
        boxes = []
        for box_str in raw_boxes:
            nums = re.findall(r'-?\d+\.?\d*', box_str)
            if len(nums) >= 4:
                boxes.append({
                    'north': float(nums[0]),
                    'south': float(nums[1]),
                    'east':  float(nums[2]),
                    'west':  float(nums[3]),
                })
            else:
                print(f"  warning: bbox needs 4 values (N,S,E,W), got {len(nums)} in '{box_str}' — skipping")
        if not boxes:
            return None
        return {'type': 'bboxes', 'boxes': boxes}

    return None
    

# convert the csv row to the dataset
def convert_row(row, all_datasets):
    d = {'id': next_id(all_datasets)}
    spatial_type_hint = ''
    latlon_val = ''
    unmapped = []
    
    for csv_key, val in row.items():
        val = (val or '').strip()
        yaml_key = column_map.get(csv_key)
        
        #keep track of unmapped/skipped cols
        if csv_key not in column_map:
            if csv_key:
                unmapped.append(csv_key)
            continue
        
        #explicitly skipped cols
        if yaml_key is None:
            continue
        
        #stash special fields for more processing
        if yaml_key == '_spatial_type':
            spatial_type_hint = val
            continue
        if yaml_key == '_latlon':
            latlon_val = val
            continue
        
        if not val:
            continue
        
        #list fields
        if yaml_key in list_fields:
            d[yaml_key] = [v.strip() for v in val.split(',') if v.strip()]
        
        #handle the numbers
        elif yaml_key in numeric_fields:
            try:
                d[yaml_key] = float(val)
            except ValueError:
                print(f" Warning could not parse number {val} for {csv_key}")
                d[yaml_key] = val
        
        #date fields
        elif yaml_key in ('collection_start', 'collection_end', 'date_added'):
            parsed = normalize_date(val)
            if parsed:
                d[yaml_key] = parsed
        
        #handle controlled vocab
        elif yaml_key == 'collection_status':
            d[yaml_key] = collection_status_map.get(val.lower(), val)
            
        else:
            d[yaml_key] = val
        
    #build spatial
    if latlon_val:
        spatial = parse_latlon(latlon_val, spatial_type_hint)
        if spatial:
            d['spatial'] = spatial
 
    # auto assign date_added if missing
    if 'date_added' not in d:
        d['date_added'] = str(date.today())
 
    # auto assign ID last (so next_id sees all previously added datasets)
    d['id'] = next_id(all_datasets)
 
    if unmapped:
        print(f"  note: unmapped columns skipped for '{d.get('name','?')}': {unmapped}")
 
    return d        


def format_dataset(d):
    lines = []
    lines.append('  - id: ' + str(d.get('id', '')))

    for key in field_order:
        if key == 'id':
            continue  # already written
        if key not in d:
            continue
        val = d[key]

        # skip empty strings and empty lists
        if val == '' or val is None:
            lines.append(f'    {key}: ""')
            continue
        if val == []:
            lines.append(f'    {key}: []')
            continue

        # description and notes use block scalar style (>)
        if key in ('description', 'notes'):
            lines.append(f'    {key}: >')
            # wrap text to ~100 chars
            import textwrap
            wrapped = textwrap.fill(str(val).strip(), width=100)
            for wline in wrapped.splitlines():
                lines.append(f'      {wline}')
            continue

        # list fields
        if key in list_string_fields:
            lines.append(f'    {key}:')
            for item in val:
                lines.append(f'      - "{item}"')
            continue

        # spatial — custom inline flow for locations/boxes
        if key == 'spatial':
            lines.append('    spatial:')
            stype = val.get('type', '')
            lines.append(f'      type: {stype}')
            if stype == 'points':
                lines.append('      locations:')
                for loc in val.get('locations', []):
                    lines.append(f'        - {{lat: {loc["lat"]}, lon: {loc["lon"]}}}')
            elif stype == 'bboxes':
                lines.append('      boxes:')
                for box in val.get('boxes', []):
                    lines.append(
                        f'        - {{north: {box["north"]}, south: {box["south"]}, '
                        f'east: {box["east"]}, west: {box["west"]}}}'
                    )
            continue

        # numeric fields — no quotes
        if key in no_quote_fields or isinstance(val, (int, float)):
            lines.append(f'    {key}: {val}')
            continue

        # everything else — quoted string
        # escape any existing quotes in the value
        safe_val = str(val).replace('"', '\\"')
        lines.append(f'    {key}: "{safe_val}"')

    return '\n'.join(lines)

# load the existing dataset yaml
def load_existing(yaml_path):
    
    if not os.path.exists(yaml_path):
        return [], ''
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    header_lines = []
    
    for line in content.splitlines():
        if line.startswith('#'):
            header_lines.append(line)
        else:
            break
        
    header = '\n'.join(header_lines) + '\n\n' if header_lines else ''
    data = yaml.safe_load(content)
    
    return (data.get('datasets', []) if data else []), header

    
def write_yaml(yaml_path, existing, new_datasets, header):
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('datasets:\n')
        
        # write existing datasets
        for d in existing:
            f.write('\n')
            f.write(format_dataset(d))
            f.write('\n')
            
        # write new datasets
        for d in new_datasets:
            f.write('\n')
            f.write(format_dataset(d))
            f.write('\n')
#################### fin functions #############

############ RUN IT BAck ######################

#load in the existing datasets      
existing, header = load_existing(yaml_path)
existing_names = {d.get('name', '').lower(): d['id'] for d in existing}
print(f"Loaded {len(existing)} existing datasets from {yaml_path}")

with open(gfile, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    added = updated = skipped = 0
    
    all_datasets = list(existing)
    
    for i, row in enumerate(reader, start=1):
        name = (row.get('Dataset title/name', '') or '').strip()

        if not name:
            print(f"  row{i}: skipping - no name")
            skipped += 1
            continue
        
        name_lower= name.lower()
        
        if name_lower in existing_names:
            if UPDATE: #then we do them all
                existing_id = existing_names[name_lower]
                d = convert_row(row, all_datasets)
                d['id'] = existing_id
                all_datasets = [d if e['id'] == existing_id else e for e in all_datasets]
                print(f"   updated: {existing_id} : {name}")
                updated += 1
                
            else:
                print(f"   skipped (duplicated name): {name}")
                skipped += 1
            continue
        
        d = convert_row(row, all_datasets)
        all_datasets.append(d)
        existing_names[name_lower] = d['id']
        print(f"   added: d[{'id'}] : {name}")
        added += 1
        
if added > 0 or updated > 0:
    
    new_only = [d for d in all_datasets if d['id'] not in {e['id'] for e in existing}]
    
    write_yaml(yaml_save, existing, new_only, header)
    print(f"\nDone - {added} added, {updated} updated, {skipped} skipped")
    
else:
    print(f"No changes made {skipped} skipped.")













