import logging
import time
import os

LOG_DIR = "logs"
# Ensure log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create a timestamped log file
get_filename = lambda ext: os.path.join(LOG_DIR, f"scraper-log-{time.strftime('%Y%m%d-%H%M%S')}.{ext}")

# Setup logger
file_timestamp = time.strftime("%Y%m%d-%H%M%S")
logging.basicConfig(
    filename=get_filename("log"),
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Suppress Selenium and urllib3 debug logs
for noisy_logger in [
    "selenium.webdriver.remote.remote_connection",
    "urllib3.connectionpool",
    "selenium",
]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

# Also print to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)


# Export logger
logger = logging
