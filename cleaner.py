import os
import sys
import re
import json
import time
import pandas as pd
from logger import logger

# Global Config object
from config_loader import constants

# Find the directories
XL_DIR = constants.get("excel")
RES_DIR = constants.get("res")
LOG_DIR = constants.get("logs")

MERGED_FILE_NAME = constants.get("merged_file_name", "merged_data.xlsx")
REGEX_MAP = {
    "name": re.compile(constants["regex_map"]["name"]),
    "mobile": re.compile(constants["regex_map"]["mobile"]),
    "URL": re.compile(constants["regex_map"]["URL"])
}

# ==============================
# Setup clean-specific logger
# ==============================

file_timestamp = time.strftime("%Y%m%d-%H%M%S")
log_filename = f"{constants.get('prefix', 'clean-')}-{file_timestamp}.{constants.get('ext', 'log')}"
clean_log_file = os.path.join(LOG_DIR, log_filename)

for handler in logger.getLogger().handlers[:]:
    logger.getLogger().removeHandler(handler)

file_handler = logger.FileHandler(clean_log_file, mode="w")
file_handler.setLevel(logger.DEBUG)
file_formatter = logger.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

console_handler = logger.StreamHandler()
console_handler.setLevel(logger.INFO)
console_formatter = logger.Formatter("%(message)s")
console_handler.setFormatter(console_formatter)

logger.getLogger().addHandler(file_handler)
logger.getLogger().addHandler(console_handler)

# ==============================
# Utility Functions
# ==============================

def ensure_directories(xl_dir: str, res_dir: str):
    """Ensure directories exist or can be created."""
    if not os.path.exists(xl_dir):
        logger.error(f"❌ XL_DIR does not exist: {xl_dir}")
        sys.exit(-1)
    if not os.path.exists(res_dir):
        try:
            os.makedirs(res_dir)
        except Exception as e:
            logger.error(f"❌ Could not create RES_DIR: {res_dir} | Error: {e}")
            sys.exit(-1)

def validate_field(value, pattern):
    """Validate a value against regex pattern."""
    if pd.isna(value):
        return False
    return bool(pattern.match(str(value).strip()))

def load_excel_files(xl_dir: str):
    """Load Excel files and tag source info."""
    files = [os.path.join(xl_dir, f) for f in os.listdir(xl_dir) if f.endswith(".xlsx")]
    if not files:
        logger.error(f"❌ No Excel files found in {xl_dir}")
        sys.exit(-1)

    df_list = []
    for file in files:
        logger.info(f"📂 Opening file '{os.path.basename(file)}'")
        df = pd.read_excel(file)
        logger.info(f"📌 Recording column names -> Column names OK!")
        df["source_file"] = os.path.basename(file)
        df["source_row"] = range(len(df))
        df_list.append(df)

    return df_list, files

def merge_dataframes(df_list):
    """Merge list of DataFrames into one."""
    return pd.concat(df_list, ignore_index=True)

def deduplicate_and_merge(df: pd.DataFrame):
    """Deduplicate by name and merge fields with detailed logging."""
    merged_data = {}

    for _, row in df.iterrows():
        name = str(row["name"]).strip()
        mobile = str(row["mobile"]).strip()
        location = str(row["location"]).strip()
        region = str(row["region"]).strip()
        url = str(row["URL"]).strip()

        record_id = f"{row['source_file']}.{row['source_row']}"
        logger.info(f"🔹 Reading record [{record_id}] name -> {name if name else 'Invalid'}")

        # Validate + log each field
        for col, pattern in REGEX_MAP.items():
            val = str(row[col]).strip()
            if validate_field(val, pattern):
                logger.info(f"{col} -> Ok!")
            else:
                logger.warning(f"{col} -> Invalid value: {val}")

        if name not in merged_data:
            merged_data[name] = {
                "mobile": set([mobile]),
                "location": location,
                "region": region,
                "URL": set([url]),
                "source_id": record_id
            }
        else:
            entry = merged_data[name]
            logger.info(f"🟠 Duplicate of {entry['source_id']}.name")

            if mobile not in entry["mobile"]:
                logger.info(f"mobile -> Found new, merging...")
                entry["mobile"].add(mobile)

            if url not in entry["URL"]:
                logger.info(f"URL -> Found new, merging...")
                entry["URL"].add(url)

            if entry["location"] == location:
                logger.info(f"location -> Ok! (same as {entry['source_id']})")
            else:
                logger.info(f"location -> Found new, merging...")
                entry["location"] = f"{entry['location']}; {location}"

            if entry["region"] == region:
                logger.info(f"region -> Ok! (same as {entry['source_id']})")
            else:
                logger.info(f"region -> Found new, merging...")
                entry["region"] = f"{entry['region']}; {region}"

    # Build final list
    final_rows = []
    for name, data in merged_data.items():
        final_rows.append({
            "name": name,
            "mobile": "; ".join(sorted(data["mobile"])),
            "location": data["location"],
            "region": data["region"],
            "URL": "; ".join(sorted(data["URL"]))
        })

    return pd.DataFrame(final_rows)

def save_merged_excel(df: pd.DataFrame, res_dir: str, filename: str):
    """Save merged DataFrame to Excel."""
    output_path = os.path.join(res_dir, filename)
    df.to_excel(output_path, index=False)
    logger.info(f"✅ Merged file saved to {output_path} with {len(df)} unique names.")
    return output_path

def offer_file_cleanup(files):
    """Prompt user to delete original Excel files."""
    choice = input("❓ Do you want to delete the original Excel files? (y/n): ").strip().lower()
    if choice == 'y':
        for file in files:
            try:
                os.remove(file)
                logger.info(f"🗑️ Deleted: {file}")
            except Exception as e:
                logger.warning(f"⚠ Could not delete {file}: {e}")
    else:
        logger.info("ℹ️ Original Excel files retained.")

# ==============================
# Main Entry Point
# ==============================

def clean_and_merge_directory(xl_dir=XL_DIR, res_dir=RES_DIR):
    """Main workflow for cleaning + merging + logging."""
    ensure_directories(xl_dir, res_dir)
    df_list, files = load_excel_files(xl_dir)
    combined_df = merge_dataframes(df_list)

    merged_df = deduplicate_and_merge(combined_df)

    for file in files:
        logger.info(f"✅ All records read, closing file '{os.path.basename(file)}'")

    save_merged_excel(merged_df, res_dir, MERGED_FILE_NAME)

    offer_file_cleanup(files)

if __name__ == "__main__":
    clean_and_merge_directory()
