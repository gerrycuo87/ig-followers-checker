"""
Configuration constants for Instagram Followers Checker.
"""
from pathlib import Path

# File paths
SESSION_FILE = "session.json"
CACHE_DIR = Path("cache")

# API rate limiting settings
MIN_DELAY = 2  # Minimum delay between requests (seconds)
MAX_DELAY = 5  # Maximum delay between requests (seconds)
OPERATION_COOLDOWN = 3  # Delay between major operations (seconds)

# Batch sizes for fetching
FOLLOWING_BATCH_SIZE = 500  # Fetch following in batches to avoid rate limiting
FOLLOWERS_BATCH_SIZE = 500  # Fetch followers in batches to avoid rate limiting

# Device settings for Instagram API mimicking
DEVICE_SETTINGS = {
    "app_version": "269.0.0.18.75",
    "android_version": 26,
    "android_release": "8.0.0",
    "dpi": "480dpi",
    "resolution": "1080x1920",
    "manufacturer": "OnePlus",
    "device": "ONEPLUS A3003",
    "model": "OnePlus3",
    "cpu": "qcom"
}

# Ensure cache directory exists
CACHE_DIR.mkdir(exist_ok=True)
