import os
import re
import requests

# --- Configuration ---
BITBUCKET_API_URL = "https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/refs/tags"
USERNAME = "your_username"
APP_PASSWORD = "your_app_password"  # Use Bitbucket App Passwords, not your real password
PROPERTIES_FILE_PATH = "service.properties"
VERSION_KEY = "framework.version"

def get_latest_bitbucket_tag():
    """Fetches the most recent tag name from the Core Framework repo."""
    try:
        response = requests.get(BITBUCKET_API_URL, auth=(USERNAME, APP_PASSWORD))
        response.raise_for_status()
        data = response.json()
        # Bitbucket returns tags sorted by date; first one is usually the latest
        return data['values'][0]['name']
    except Exception as e:
        return f"Error fetching tag: {e}"

def get_local_version():
    """Reads the version currently set in the properties file."""
    if not os.path.exists(PROPERTIES_FILE_PATH):
        return None
    
    with open(PROPERTIES_FILE_PATH, 'r') as f:
        for line in f:
            if line.startswith(VERSION_KEY):
                # Splits 'key=value' and takes the value
                return line.split('=')[1].strip()
    return None

def compare_versions():
    latest_tag = get_latest_bitbucket_tag()
    current_version = get_local_version()

    print(f"--- Version Check ---")
    print(f"Latest Framework Tag: {latest_tag}")
    print(f"Current Service Property: {current_version}")
    print("-" * 21)

    if latest_tag == current_version:
        print("✅ SUCCESS: Versions match. Your service is up to date.")
    else:
        print("❌ WARNING: Version mismatch detected!")
        print(f"Please update {PROPERTIES_FILE_PATH} to use {latest_tag}.")

if __name__ == "__main__":
    compare_versions()
