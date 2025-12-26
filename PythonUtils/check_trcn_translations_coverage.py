import re
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
    MISSING_FILE = config["CONFIG"]["MISSING_OUTPUT"]  # Will be overwritten with truly missing
    TRANSLATIONS_DIR = config["CONFIG"]["TRANSLATIONS_DIR"].strip('"\' ')
except KeyError as e:
    print(f"Error: Missing required key in config.ini: {e}", file=sys.stderr)
    sys.exit(1)
# ----------------------------------------------------------------

def load_missing_identifiers(file_path: Path) -> set[str]:
    """Load previously missing identifiers from the text file (one per line)"""
    if not file_path.exists():
        print(f"Note: Missing identifiers file not found: {file_path}")
        print("Assuming there are no missing identifiers.")
        return set()
    
    missing = set()
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            ident = line.strip()
            if ident:
                missing.add(ident)
    
    print(f"Loaded {len(missing)} previously missing identifiers from {file_path}")
    return missing

def find_translated_identifiers_in_dir(trans_dir: str) -> set[str]:
    """
    Scan all .xml files in trans_dir (and subdirectories) for tags like:
    <prefix.identifier>text</prefix.identifier>
    Extract the identifier part after the dot.
    """
    if not os.path.isdir(trans_dir):
        print(f"Error: Translations directory not found: {trans_dir}", file=sys.stderr)
        sys.exit(1)
    
    pattern = re.compile(r'(?:<|&lt;)[^>]*\.([^>]+?)(?:>|/&gt;|&gt;)')
    translated = set()
    
    xml_count = 0
    for root_dir, _, files in os.walk(trans_dir):
        for file in files:
            if file.lower().endswith('.xml'):
                xml_count += 1
                file_path = os.path.join(root_dir, file)
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            matches = pattern.findall(line)
                            for match in matches:
                                ident = match.strip()
                                if ident:
                                    translated.add(ident)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}", file=sys.stderr)
    
    print(f"Scanned {xml_count} XML files in translations directory.")
    print(f"Found {len(translated)} translated identifiers.")
    return translated

def main():
    missing_path = Path(MISSING_FILE)
    previously_missing = load_missing_identifiers(missing_path)
    
    if not previously_missing:
        print("No previously missing identifiers. Nothing to update.")
        return
    
    translated_identifiers = find_translated_identifiers_in_dir(TRANSLATIONS_DIR)
    
    # Identifiers that are missing from main localization BUT present in translations
    falsely_missing = previously_missing & translated_identifiers
    truly_missing = previously_missing - translated_identifiers
    
    print("\n" + "="*60)
    print(f"Previously marked as missing:             {len(previously_missing)}")
    print(f"Actually HAVE translations (false misses): {len(falsely_missing)}")
    print(f"TRULY missing (no translation found):     {len(truly_missing)}")
    print("="*60)
    
    # Overwrite the original MISSING_OUTPUT file with only truly missing ones
    sorted_truly_missing = sorted(truly_missing)
    missing_path.write_text("\n".join(sorted_truly_missing) + "\n", encoding="utf-8")
    
    if truly_missing:
        print(f"\nUpdated '{MISSING_FILE}' with {len(truly_missing)} truly missing identifiers.")
    else:
        print(f"\nGreat! All previously missing identifiers now have translations!")
        print(f"'{MISSING_FILE}' has been cleared (now empty or contains only truly missing).")
    
    if falsely_missing:
        print(f"\nRemoved {len(falsely_missing)} identifiers that were falsely marked as missing.")

if __name__ == "__main__":
    main()