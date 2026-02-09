import requests
import base64

# --- Configuration ---
USERNAME = "your_username"
APP_PASSWORD = "your_app_password" 
WORKSPACE = "your_workspace_name"

# Repo 1: The Core Framework (to get the latest tag)
CORE_REPO = "core-framework-repo"

# Repo 2: The Service (to check the properties file)
SERVICE_REPO = "service-repository"
FILE_PATH = "gradle.properties"  # Path to the file within the repo
VERSION_KEY = "plugin.version"

AUTH = (USERNAME, APP_PASSWORD)

def get_latest_framework_tag():
    """Fetches the most recent tag name from the Core Framework."""
    url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{CORE_REPO}/refs/tags?sort=-target.date"
    response = requests.get(url, auth=AUTH)
    response.raise_for_status()
    tags = response.json().get('values', [])
    return tags[0]['name'] if tags else None

def get_service_property_version():
    """Fetches the content of the properties file from the Service Repo API."""
    url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{SERVICE_REPO}/src/master/{FILE_PATH}"
    response = requests.get(url, auth=AUTH)
    
    if response.status_code == 200:
        # Parse the file content line by line
        lines = response.text.splitlines()
        for line in lines:
            if line.startswith(VERSION_KEY):
                return line.split('=')[1].strip()
    return None

def run_check():
    print(f"🔍 Fetching versions from Bitbucket...")
    
    latest_tag = get_latest_framework_tag()
    current_in_service = get_service_property_version()

    print("\n" + "="*30)
    print(f"Framework Latest Tag:  {latest_tag}")
    print(f"Service Current Prop:  {current_in_service}")
    print("="*30)

    if not latest_tag or not current_in_service:
        print("❌ Error: Could not retrieve one or both versions.")
    elif latest_tag == current_in_service:
        print("✅ MATCH: The service is using the latest framework version.")
    else:
        print("⚠️  MISMATCH: The service is outdated!")
        print(f"Action: Update '{VERSION_KEY}' to '{latest_tag}' in {SERVICE_REPO}.")

if __name__ == "__main__":
    run_check()
