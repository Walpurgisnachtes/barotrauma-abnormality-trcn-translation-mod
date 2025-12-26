import re
import sys
import configparser
from pathlib import Path

# ----------------------------- CONFIG -----------------------------
CONFIG_FILE = "config.ini"

config = configparser.ConfigParser()
if not Path(CONFIG_FILE).exists():
    print(f"Error: {CONFIG_FILE} not found!", file=sys.stderr)
    sys.exit(1)

config.read(CONFIG_FILE, encoding="utf-8")
try:
    IDENTIFIERS_FILE = config["CONFIG"]["IDENTIFIERS_FILE"].strip('"\' ')
    LOCALIZATION_FILE = config["CONFIG"]["LOCALIZATION_FILE"].strip('"\' ')
    MATCHES_OUTPUT = config.get("CONFIG", "MATCHES_OUTPUT", fallback="matched_identifiers.txt").strip('"\' ')
    MISSING_OUTPUT = config.get("CONFIG", "MISSING_OUTPUT", fallback="missing_identifiers.txt").strip('"\' ')
except KeyError as e:
    print(f"Error: Missing required key in config.ini: {e}", file=sys.stderr)
    sys.exit(1)
# ----------------------------------------------------------------

def load_identifiers(file_path: Path) -> set[str]:
    if not file_path.exists():
        print(f"Error: Identifiers file not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    identifiers = set()
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            ident = line.strip()
            if ident:
                identifiers.add(ident)
    print(f"Loaded {len(identifiers)} unique identifiers from {file_path}")
    return identifiers

def find_used_identifiers(file_path: Path) -> set[str]:
    if not file_path.exists():
        print(f"Error: Localization file not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    pattern = re.compile(r'(?:<|&lt;)[^>]*\.([^>]+?)(?:>|/&gt;|&gt;)')
    used = set()
    
    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            matches = pattern.findall(line)
            for match in matches:
                ident = match.strip()
                if ident:
                    used.add(ident)
    
    print(f"Found {len(used)} identifiers used in {file_path}.")
    return used

def main():
    identifiers_path = Path(IDENTIFIERS_FILE)
    localization_path = Path(LOCALIZATION_FILE)
    
    all_identifiers = load_identifiers(identifiers_path)
    used_identifiers = find_used_identifiers(localization_path)
    
    matched = all_identifiers & used_identifiers
    missing = all_identifiers - used_identifiers
    
    print("\n" + "="*50)
    print(f"Total identifiers in XMLs:       {len(all_identifiers)}")
    print(f"Identifiers used in localization: {len(used_identifiers)}")
    print(f"Matched (present in both):       {len(matched)}")
    print(f"Missing in localization file:    {len(missing)}")
    print("="*50)
    
    if matched:
        sorted_matched = sorted(matched)
        Path(MATCHES_OUTPUT).write_text("\n".join(sorted_matched) + "\n", encoding="utf-8")
        print(f"\nMatched identifiers saved to: '{MATCHES_OUTPUT}'.")
    
    if missing:
        sorted_missing = sorted(missing)
        Path(MISSING_OUTPUT).write_text("\n".join(sorted_missing) + "\n", encoding="utf-8")
        print(f"Missing identifiers saved to: '{MISSING_OUTPUT}'.")
    else:
        print("\nAll identifiers are present in the localization file!")

if __name__ == "__main__":
    main()