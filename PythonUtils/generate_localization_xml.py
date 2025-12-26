# File: PythonUtils/generate_localization_xml.py

import csv
import configparser
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom

# ----------------------------- CONFIG -----------------------------
CONFIG_FILE = "config.ini"

config = configparser.ConfigParser()
if not Path(CONFIG_FILE).exists():
    print(f"Error: {CONFIG_FILE} not found!", file=sys.stderr)
    sys.exit(1)

config.read(CONFIG_FILE, encoding="utf-8")
try:
    MISSING_DETAILS_CSV = config["CONFIG"]["MISSING_DETAILS_CSV"]
    SINGLE_XML_OUTPUT = config.get("CONFIG", "LOCALIZATION_XML_OUTPUT", fallback="MissingTranslations.xml").strip('"\' ')
except KeyError as e:
    print(f"Error: Missing required key in config.ini: {e}", file=sys.stderr)
    sys.exit(1)
# ----------------------------------------------------------------

def prettify(elem):
    """Return a pretty-printed XML string with proper indentation"""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent="  ")
    # Remove the <?xml version="1.0" ?> line to match common mod override format
    lines = pretty.splitlines()
    clean_lines = [line for line in lines if not line.strip().startswith("<?xml")]
    return "\n".join(clean_lines).strip() + "\n"

def generate_single_xml(rows):
    root = ET.Element("Overrides")
    
    total_lines = 0
    
    for row in rows:
        identifier = row['identifier'].strip()
        element_tag = row['element_tag'].strip()
        name = row['name'].strip()
        description = row['description'].strip()
        
        tag_lower = element_tag.lower()
        
        # Determine correct prefix for name and description
        if tag_lower in ["item", "structure"]:
            name_prefix = "entityname"
            desc_prefix = "entitydescription"
        else:
            name_prefix = element_tag.lower() + "name"
            desc_prefix = element_tag.lower() + "description"
        
        # Add name tag if present
        if name:
            name_tag = ET.SubElement(root, f"{name_prefix}.{identifier}")
            name_tag.text = name
            total_lines += 1
        
        # Add description tag if present
        if description:
            desc_tag = ET.SubElement(root, f"{desc_prefix}.{identifier}")
            desc_tag.text = description
            total_lines += 1
    
    # Sort children alphabetically by tag name for cleaner output (optional but nice)
    root[:] = sorted(root, key=lambda child: child.tag)
    
    # Write to single file
    output_path = Path(SINGLE_XML_OUTPUT)
    pretty_xml = prettify(root)
    output_path.write_text(pretty_xml, encoding="utf-8")
    
    print(f"\nGenerated single localization file:")
    print(f"   → {output_path.resolve()}")
    print(f"   → {len(rows)} identifiers processed")
    print(f"   → {total_lines} translation lines (with original English text)")

def load_csv(csv_path: Path):
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
    
    rows = []
    with csv_path.open("r", encoding="utf-8", newline='') as f:
        reader = csv.DictReader(f)
        expected = {'identifier', 'element_tag', 'name', 'description', 'file'}
        if not expected.issubset(set(reader.fieldnames or [])):
            print(f"Error: CSV missing required columns. Found: {reader.fieldnames}", file=sys.stderr)
            sys.exit(1)
        
        for row in reader:
            rows.append({
                'identifier': row['identifier'],
                'element_tag': row['element_tag'],
                'name': row['name'],
                'description': row['description'],
                'file': row['file']
            })
    
    print(f"Loaded {len(rows)} missing translatable entries from {csv_path}")
    return rows

def main():
    csv_path = Path(MISSING_DETAILS_CSV)
    entries = load_csv(csv_path)
    
    if not entries:
        print("No entries to process. Creating empty XML file.")
        Path(SINGLE_XML_OUTPUT).write_text("<Overrides>\n</Overrides>\n", encoding="utf-8")
        return
    
    generate_single_xml(entries)

if __name__ == "__main__":
    main()