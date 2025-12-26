# File: PROJECTPATH/main.py

import os
import sys
import subprocess
from pathlib import Path
import configparser

# ----------------------------- CONFIG -----------------------------
# Automatically detect PROJECTPATH as the directory containing main.py
PROJECTPATH = Path(__file__).parent.resolve()

CONFIG_FILE = PROJECTPATH / "config.ini"
UTILS_DIR = PROJECTPATH / "PythonUtils"

# Full pipeline in correct order
SCRIPTS = [
    "extract_identifiers.py",                   # 1. Extract all visible identifiers (skip hideinmenus=true)
    "check_localization_coverage.py",           # 2. Compare with main localization → find missing
    "check_trcn_translations_coverage.py",      # 3. Remove any already translated in TraditionalChinese
    "find_missing_details.py",                  # 4. Generate detailed CSV with tag, name, desc, file (filtered)
    "generate_localization_xml.py"              # 5. NEW: Create single MissingTranslations.xml with English text
]

# ----------------------------------------------------------------

def load_config():
    """Load and validate config.ini"""
    config = configparser.ConfigParser()
    if not CONFIG_FILE.exists():
        print(f"Error: config.ini not found at {CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)
    
    config.read(CONFIG_FILE, encoding="utf-8")
    
    required_keys = ["SRCDIR", "TRANSLATIONS_DIR"]
    missing = [key for key in required_keys if key not in config["CONFIG"]]
    if missing:
        print(f"Error: Missing required keys in config.ini: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    
    return config

def run_script(script_name: str):
    """Run a single Python script using subprocess"""
    script_path = UTILS_DIR / script_name
    
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"Running [{SCRIPTS.index(script_name)+1}/{len(SCRIPTS)}]: {script_name}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECTPATH,
            check=True,
            text=True
        )
        print(f"✓ {script_name} completed successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"✗ {script_name} failed with return code {e.returncode}", file=sys.stderr)
        print("Aborting pipeline.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error running {script_name}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    print("Starting FULL MOD LOCALIZATION PIPELINE")
    print(f"Project path: {PROJECTPATH}")
    print(f"Utils directory: {UTILS_DIR}")
    print(f"Total steps: {len(SCRIPTS)}\n")
    
    # Basic validation
    if not UTILS_DIR.is_dir():
        print(f"Error: PythonUtils directory not found at {UTILS_DIR}", file=sys.stderr)
        sys.exit(1)
    
    load_config()  # Validate config early
    
    # Run the entire pipeline
    for script in SCRIPTS:
        run_script(script)
    
    print("="*70)
    print("FULL PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nFinal outputs generated:")
    print("  • extracted_identifiers.txt           - All visible identifiers")
    print("  • missing_identifiers.txt             - Only truly missing & translatable ones")
    print("  • missing_identifiers_details.csv     - Detailed list (sorted by file)")
    print("  • MissingTranslations.xml             - Ready-to-translate XML with original English text")
    print("\nYou can now:")
    print("   1. Send MissingTranslations.xml to your translator")
    print("   2. Have them replace the English text inside the tags with Traditional Chinese")
    print("   3. Place the finished file in your mod's localization overrides folder")
    print("\nHappy translating!")

if __name__ == "__main__":
    main()