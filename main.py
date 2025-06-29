import os
import json
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from logger import logger  

# Global constants object
from config_loader import constants

"""
Constants
"""
FILE_TIMESTAMP = time.strftime("%Y%m%d-%H%M%S")
RESULT_DIR = constants['RES_DIR']
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

THRESHOLD = 30
REGION_ENUM = ["delhi", "gurgaon", "noida", "ghaziabad", "faridabad"]
PROFILE_PATH = "./profiles.json"

get_filename = lambda x, ext: os.path.join(RESULT_DIR, f"{x}-{FILE_TIMESTAMP}.{ext}")

"""
Functions
"""

def load_profile():
    with open(PROFILE_PATH, "r") as f:
        data = json.load(f)
    profiles = data["profiles"]
    if len(profiles) == 1:
        return profiles[0]
    print("Available profiles:")
    for i, profile in enumerate(profiles):
        print(f"{i + 1}. {profile['name']}")
    choice = int(input("Select profile number: ")) - 1
    return profiles[choice]

def get_element_text(listing, selector, fallback, default):
    text = ""
    try:
        text = listing.find_element(By.CSS_SELECTOR, selector).text.strip()
    except:
        pass
    # Try with fallback selector
    if not text and fallback:
        try:
            text = listing.find_element(By.CSS_SELECTOR, fallback).text.strip()
        except:
            return default

    # If we have text, and it is string
    if not isinstance(text, str):
        logger.warning(f"⚠ Expected string but got {type(text)} for selector: {selector}")
        return default
    
    # Clean text
    text = text \
    .replace("\n", " ") \
    .replace("\r", " ") \
    .replace(",", " ") \
    .strip()
    
    return text


def get_element_attr(listing, selector, attr, default):
    try:
        return listing.find_element(By.CSS_SELECTOR, selector).get_attribute(attr)
    except:
        return default

"""
Main
"""

# Load profile
profile = load_profile()

# Setup Selenium
options = Options()
options.headless = False
options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
service = Service("./bin/geckodriver.exe")
driver = webdriver.Firefox(service=service, options=options)

# Start scraping
url = profile["baseUrl"] + "Delhi/Interior-Designers"
driver.get(url)

WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, profile["querySelectors"]["listing"]))
)

all_listings = []
results = []
seen_ids = set()
prev_count = 0
scroll_attempt = 0
max_scroll_attempts = 10

while scroll_attempt < max_scroll_attempts:
    listings = driver.find_elements(By.CSS_SELECTOR, profile["querySelectors"]["listing"])

    all_listings.extend(listings)
    current_count = len(all_listings)

    if current_count > prev_count:
        scroll_attempt = 0
        prev_count = current_count
        logger.info(f"✅ Loaded {current_count} listings so far...")
    else:
        scroll_attempt += 1
        logger.info(f"⚠ Scroll attempt {scroll_attempt} — no new listings")

    if current_count >= THRESHOLD:
        logger.info(f"✅ Threshold of {THRESHOLD} listings reached. Stopping scroll.")
        break

    driver.execute_script(profile["nextScript"])
    time.sleep(random.uniform(1.5, 3.0))

# Parse listings
parser = profile["querySelectors"]["parser"]

for listing in all_listings:
    try:
        name = get_element_text(
            listing,
            parser["name"]["main"],
            parser["name"]["fallback"],
            parser["name"]["default"]
        )

        location = get_element_text(
            listing,
            parser["location"]["main"],
            parser["location"]["fallback"],
            parser["location"]["default"]
        )

        rating = get_element_text(
            listing,
            parser["rating"]["main"],
            parser["rating"]["fallback"],
            parser["rating"]["default"]
        )

        phone = get_element_text(
            listing,
            parser["phone"]["main"],
            parser["phone"]["fallback"],
            parser["phone"]["default"]
        )

        url = get_element_attr(
            listing,
            parser["url"]["main"],
            "href",
            parser["url"]["default"]
        )

        # Region detection
        region = "Delhi"

        if not location:
            logger.warning("⚠ No location found for listing. Skipping...")
            continue

        loc_lower = location.lower()
        for reg in REGION_ENUM:
            if loc_lower.endswith(reg):
                region = reg.capitalize()
                break

        logger.debug(f"Parsed: Name={name}, Location={location}, Region={region}, Phone={phone}, URL={url}")



        results.append({
            "Name / Firm": name,
            "Location": location,
            "Region": region,
            "Rating": rating,
            "Phone": phone,
            "URL": url
        })

    except Exception as e:
        logger.error(f"⚠ Error parsing listing: {e}")

driver.quit()

# Save
df = pd.DataFrame(results)
if df.empty:
    logger.error("❌ No listings found. Exiting.")
    exit(1)

excel_path = get_filename("Delhi_Designers_Architects", "xlsx")
# csv_path = get_filename("Delhi_Designers_Architects", "csv")

df.to_excel(excel_path, index=False)
# df.to_csv(csv_path, index=False)

logger.info(f"✅ Data saved as Excel: {excel_path} with {len(df)} listings.")
