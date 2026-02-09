import git
from packaging import version
import re

def get_latest_release_branch(repo):
    # Get all remote branch names
    branches = [ref.name for ref in repo.remotes.origin.refs]
    
    # Filter for branches that match 'release/' or 'release-' patterns
    # Adjust the regex if your naming convention is different
    release_pattern = re.compile(r'origin/release[/-](\d+\.\d+\.\d+)')
    
    release_branches = []
    for b in branches:
        match = release_pattern.search(b)
        if match:
            v_string = match.group(1)
            release_branches.append((v_string, b))

    if not release_branches:
        return None

    # Sort by actual version number, not alphabetical string order
    latest = max(release_branches, key=lambda x: version.parse(x[0]))
    return latest[1] # Returns the full branch name, e.g., 'origin/release-1.1.1'

def check_sync_with_latest_release(repo_path):
    try:
        repo = git.Repo(repo_path)
        print("Fetching latest from remote...")
        repo.remotes.origin.fetch()

        latest_release = get_latest_release_branch(repo)
        
        if not latest_release:
            print("No release branches found.")
            return

        print(f"Found latest release branch: {latest_release}")
        
        # Compare master against the latest release branch
        # We use 'origin/master' to ensure we are looking at the server state
        behind = list(repo.iter_commits(f'origin/master..{latest_release}'))
        
        if not behind:
            print(f"✅ Master is in sync with {latest_release}.")
        else:
            print(f"⚠️ Master is BEHIND {latest_release} by {len(behind)} commits.")
            for commit in behind[:3]:
                print(f"   - {commit.hexsha[:7]}: {commit.summary}")

    except Exception as e:
        print(f"Error: {e}")

# Run it
check_sync_with_latest_release('./your-repo-folder')
