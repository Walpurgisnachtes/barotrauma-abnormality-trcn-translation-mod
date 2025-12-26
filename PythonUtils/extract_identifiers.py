# File: PythonUtils/extract_identifiers.py

import xml.etree.ElementTree as ET
import os
import configparser
import sys
from pathlib import Path

# ----------------------------- CONFIG -----------------------------
CONFIG_FILE = "config.ini"

config = configparser.ConfigParser()
if not Path(CONFIG_FILE).exists():
    print(f"Error: {CONFIG_FILE} not found!", file=sys.stderr)
    sys.exit(1)

config.read(CONFIG_FILE, encoding="utf-8")
try:
    SRCDIR = config["CONFIG"]["SRCDIR"].strip('"\' ')
    OUTPUT_FILE = config.get("CONFIG", "IDENTIFIERS_FILE", fallback="extracted_identifiers.txt").strip('"\' ')
except KeyError as e:
    print(f"Error: Missing required key in config.ini: {e}", file=sys.stderr)
    sys.exit(1)
# ----------------------------------------------------------------

def extract_identifiers_from_xml(file_path):
    identifiers = set()
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        for elem in root.iter():
            # Skip if hideinmenus="true" (case-insensitive)
            hide = elem.get('hideinmenus')
            if hide and hide.strip().lower() == 'true':
                continue  # Skip this entire element and its identifier
            
            identifier = elem.get('identifier')
            if identifier:
                ident = identifier.strip()
                if ident:
                    identifiers.add(ident)
                    
    except ET.ParseError as e:
        print(f"XML parse error in {file_path}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
    
    return identifiers

def extract_all_identifiers(src_dir):
    all_identifiers = set()
    if not os.path.isdir(src_dir):
        print(f"Error: Directory not found: {src_dir}", file=sys.stderr)
        return all_identifiers
    
    xml_count = 0
    skipped_count = 0  # Optional: track how many were skipped due to hideinmenus
    
    for root_dir, _, files in os.walk(src_dir):
        for file in files:
            if file.lower().endswith('.xml'):
                file_path = os.path.join(root_dir, file)
                ids = extract_identifiers_from_xml(file_path)
                if ids:
                    xml_count += 1
                    all_identifiers.update(ids)
    
    print(f"Processed {xml_count} XML files with visible identifiers.", file=sys.stderr)
    return all_identifiers

if __name__ == "__main__":
    identifiers = extract_all_identifiers(SRCDIR)
    sorted_ids = sorted(identifiers)

    print(f"Found {len(sorted_ids)} unique visible identifiers (hideinmenus!='true'):\n")
    for ident in sorted_ids:
        print(ident)

    # Save to the output file defined in config
    Path(OUTPUT_FILE).write_text("\n".join(sorted_ids) + "\n", encoding="utf-8")
    print(f"\nIdentifiers saved to '{OUTPUT_FILE}'")