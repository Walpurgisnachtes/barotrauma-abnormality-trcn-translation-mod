# File: PythonUtils/find_missing_details.py

import xml.etree.ElementTree as ET
import os
import csv
import configparser
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ----------------------------- CONFIG -----------------------------
CONFIG_FILE = "config.ini"

config = configparser.ConfigParser()
if not Path(CONFIG_FILE).exists():
    print(f"Error: {CONFIG_FILE} not found!", file=sys.stderr)
    sys.exit(1)

config.read(CONFIG_FILE, encoding="utf-8")
try:
    SRCDIR = config["CONFIG"]["SRCDIR"].strip('"\' ')
    MISSING_FILE = config["CONFIG"]["MISSING_OUTPUT"]
    MISSING_DETAILS_CSV = config["CONFIG"]["MISSING_DETAILS_CSV"].strip('"\' ')
    REJECTION_LOG = config.get("CONFIG", "REJECTION_LOG_FILE", fallback="rejection_log.txt").strip('"\' ')
except KeyError as e:
    print(f"Error: Missing required key in config.ini: {e}", file=sys.stderr)
    sys.exit(1)
# ----------------------------------------------------------------

# Regex for alphabetic characters (including Unicode letters)
HAS_ALPHA = re.compile(r'[a-zA-Z\u00C0-\u017F\u0180-\u024F\u1E00-\u1EFF]')

def has_alphabetic(text: str) -> bool:
    return bool(HAS_ALPHA.search(text or ""))

def load_missing_identifiers(file_path: Path) -> set[str]:
    if not file_path.exists():
        print(f"Note: Missing identifiers file not found: {file_path}. Assuming none.")
        return set()
    
    missing = set()
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            ident = line.strip()
            if ident:
                missing.add(ident)
    
    print(f"Loaded {len(missing)} missing identifiers from {file_path}")
    return missing

def scan_and_evaluate_identifiers(src_dir: str, target_identifiers: set[str]):
    """
    Scan entire SRCDIR and collect all occurrences of each target identifier.
    Apply strict rules:
      - If ANY occurrence has hideinmenus="true" → reject the identifier immediately
      - Otherwise, if AT LEAST ONE occurrence has:
          - non-empty name or description
          - AND at least one alphabetic character in name or description
        → accept the identifier (use the first valid occurrence for CSV)
      - If ALL occurrences fail the text validation → reject
    """
    occurrences = defaultdict(list)   # identifier -> list of dicts with details
    rejections = []
    
    if not os.path.isdir(src_dir):
        print(f"Error: Source directory not found: {src_dir}", file=sys.stderr)
        sys.exit(1)
    
    xml_count = 0
    
    for root_dir, _, files in os.walk(src_dir):
        for file in files:
            if not file.lower().endswith('.xml'):
                continue
            xml_count += 1
            file_path = os.path.join(root_dir, file)
            rel_path = os.path.relpath(file_path, src_dir)
            
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                for elem in root.iter():
                    identifier = elem.get('identifier')
                    if identifier and identifier in target_identifiers:
                        name = elem.get('name', '').strip()
                        description = elem.get('description', '').strip()
                        element_tag = elem.tag
                        hide = elem.get('hideinmenus')
                        is_hidden = hide and hide.strip().lower() == 'true'
                        
                        occurrences[identifier].append({
                            'element_tag': element_tag,
                            'name': name,
                            'description': description,
                            'file': rel_path,
                            'is_hidden': is_hidden
                        })
                        
            except ET.ParseError as e:
                print(f"XML parse error in {file_path}: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Error processing {file_path}: {e}", file=sys.stderr)
    
    # Evaluate each identifier
    final_results = []
    
    for identifier, occ_list in occurrences.items():
        # Rule 1: Immediate rejection if ANY occurrence is hidden
        if any(occ['is_hidden'] for occ in occ_list):
            rejections.append({
                'identifier': identifier,
                'file': '(one or more files)',
                'reason': 'hideinmenus="true" in at least one definition'
            })
            continue
        
        # Rule 2: Look for at least one valid text occurrence
        valid_occurrence = None
        for occ in occ_list:
            name = occ['name']
            desc = occ['description']
            
            if not name and not desc:
                rejections.append({
                    'identifier': identifier,
                    'file': occ['file'],
                    'reason': 'both name and description empty'
                })
                continue
            
            if not (has_alphabetic(name) or has_alphabetic(desc)):
                rejections.append({
                    'identifier': identifier,
                    'file': occ['file'],
                    'reason': 'no alphabetic characters in name/description'
                })
                continue
            
            # Valid! Use this one (first valid wins)
            if valid_occurrence is None:
                valid_occurrence = {
                    'identifier': identifier,
                    'element_tag': occ['element_tag'],
                    'name': name,
                    'description': desc,
                    'file': occ['file']
                }
        
        if valid_occurrence is None:
            # All occurrences failed text validation
            rejections.append({
                'identifier': identifier,
                'file': '(all files)',
                'reason': 'all occurrences lack valid translatable text (empty or no letters)'
            })
        else:
            final_results.append(valid_occurrence)
    
    return final_results, xml_count, rejections

def write_rejection_log(rejections: list, log_path: Path):
    if not rejections:
        log_path.write_text("No identifiers were rejected during processing.\n", encoding="utf-8")
        return
    
    rejections.sort(key=lambda x: (x.get('file', ''), x['identifier']))
    
    lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"Rejection Log - Generated on {timestamp}")
    lines.append(f"Total rejected identifiers: {len(rejections)}")
    lines.append("=" * 80)
    lines.append("")
    
    for rej in rejections:
        lines.append(f"Identifier: {rej['identifier']}")
        lines.append(f"File:       {rej['file']}")
        lines.append(f"Reason:     {rej['reason']}")
        lines.append("-" * 50)
    
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Rejection log saved to: {log_path}")

def main():
    missing_path = Path(MISSING_FILE)
    missing_identifiers = load_missing_identifiers(missing_path)
    
    if not missing_identifiers:
        print("No missing identifiers to process. Creating empty outputs.")
        Path(MISSING_DETAILS_CSV).touch()
        missing_path.write_text("", encoding="utf-8")
        Path(REJECTION_LOG).write_text("No processing occurred (no missing identifiers).\n", encoding="utf-8")
        return
    
    results, xml_count, rejections = scan_and_evaluate_identifiers(SRCDIR, missing_identifiers)
    
    included_count = len(results)
    rejected_count = len(rejections)
    
    print("\n" + "="*80)
    print(f"Scanned {xml_count} XML files")
    print(f"Originally missing identifiers:     {len(missing_identifiers)}")
    print(f"→ Included (translatable):          {included_count}")
    print(f"→ Rejected:                         {rejected_count}")
    print("="*80)
    
    if not results:
        print("No translatable content remains after filtering. Clearing outputs.")
        Path(MISSING_DETAILS_CSV).write_text("", encoding="utf-8")
        missing_path.write_text("", encoding="utf-8")
    else:
        # Sort by file path, then identifier
        results.sort(key=lambda x: (x['file'], x['identifier']))
        
        # Write CSV
        fieldnames = ['identifier', 'element_tag', 'name', 'description', 'file']
        csv_path = Path(MISSING_DETAILS_CSV)
        with csv_path.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\nCleaned details saved to: {MISSING_DETAILS_CSV}")
        print(f"   → {included_count} translatable entries")
        
        # Update missing_identifiers.txt with only valid ones
        meaningful_ids = sorted({r['identifier'] for r in results})
        missing_path.write_text("\n".join(meaningful_ids) + "\n", encoding="utf-8")
        print(f"Updated '{MISSING_FILE}' with {len(meaningful_ids)} translatable identifiers.")
    
    # Write rejection log
    write_rejection_log(rejections, Path(REJECTION_LOG))
    
    if rejected_count > 0:
        print(f"\n{rejected_count} identifiers rejected — details in {REJECTION_LOG}")

if __name__ == "__main__":
    main()