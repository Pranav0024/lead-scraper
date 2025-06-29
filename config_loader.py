import os
import sys
import json

# ==============================
# Load Config
# ==============================

__CONFIG_PATH = "./config.json"

if not os.path.exists(__CONFIG_PATH):
    print(f"❌ Config file not found at {__CONFIG_PATH}")
    sys.exit(-1)

with open(__CONFIG_PATH, "r") as f:
    global_config = json.load(f)
    config = global_config.get("config", None)

if config is None:
    print("❌ 'config' section not found in config.json")
    sys.exit(-1)

dir_config = config.get("directories", None)
if dir_config is None:
    print("❌ 'directories' section not found in config.json")
    sys.exit(-1)

cleaner_config = config.get("cleaner", None)
if cleaner_config is None:
    print("❌ 'cleaner' section not found in config.json")
    sys.exit(-1)

log_config = cleaner_config.get("logs", None)
if log_config is None:
    print("❌ 'logs' section not found in config.json")
    sys.exit(-1)

constants = {
    "XL_DIR": dir_config.get("excel", None),
    "RES_DIR": dir_config.get("res", None),
    "LOG_DIR": dir_config.get("logs", None),
    "PROFILE_DIR": dir_config.get("profiles", None),
    "MERGED_FILE_NAME": config.get("merged_file_name", "merged_data.xlsx"),
    "REGEX_MAP": {
        "name": cleaner_config["regex_map"]["name"],
        "mobile": cleaner_config["regex_map"]["mobile"],
        "URL": cleaner_config["regex_map"]["URL"]
    },
    "LOG_CONFIG": log_config
}

# Ensure all required directories are set
if not all(constants.values()):
    print("❌ One or more required directories are not set in the config.")
    sys.exit(-1)