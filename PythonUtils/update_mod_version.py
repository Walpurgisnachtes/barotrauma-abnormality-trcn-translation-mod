import sys
import os
import shutil
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
    mod_name = config["CONFIG"]["MOD_NAME"].strip('"\' ')
    src_dir = config["CONFIG"]["AUTO_UPDATE_SRC_DIR"].strip('"\' ')
    dest_dir = config["CONFIG"]["AUTO_UPDATE_DES_DIR"].strip('"\' ')
    
    SRC_DIRECTORY = os.path.join(src_dir, mod_name)
    DEST_DIRECTORY = os.path.join(dest_dir, mod_name)
except KeyError as e:
    print(f"Error: Missing required key in config.ini: {e}", file=sys.stderr)
    sys.exit(1)
# ----------------------------------------------------------------

def recursive_copy_and_replace(source_dir, dest_dir):
    # 檢查來源目錄是否存在
    if not os.path.exists(source_dir):
        print(f"錯誤：來源目錄 '{source_dir}' 不存在。")
        return

    # 使用 os.walk 遍歷所有層級的子目錄與檔案
    for root, dirs, files in os.walk(source_dir):
        # 計算相對路徑，以便在目標位置建立對應結構
        rel_path = os.path.relpath(root, source_dir)
        dest_path = os.path.join(dest_dir, rel_path)

        # 如果目標子目錄不存在，則建立它
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        # 複製該目錄下的所有檔案
        for file in files:
            s_file = os.path.join(root, file)
            d_file = os.path.join(dest_path, file)
            
            # 複製並取代
            shutil.copy2(s_file, d_file)
            print(f"已複製: {os.path.join(rel_path, file)}")

if __name__ == "__main__":
    recursive_copy_and_replace(SRC_DIRECTORY, DEST_DIRECTORY)
    print("任務完成！")