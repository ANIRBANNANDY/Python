{
    "source_path": "C:/MySourceFiles",
    "target_folder_name": "SharedFolder",
    "servers": [
        "192.168.1.10",
        "192.168.1.11",
        "192.168.1.12"
    ]
}

import os
import shutil
import json

CONFIG_FILE = "config.json"

def distribute():
    # Load config
    if not os.path.exists(CONFIG_FILE):
        return print("Config file missing.")
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    src = config['source_path']
    folder = config['target_folder_name']
    servers = config['servers']

    # Get files sorted by creation time (FIFO)
    if not os.path.exists(src):
        return print(f"Source {src} not found.")
        
    files = sorted([os.path.join(src, f) for f in os.listdir(src) 
                   if os.path.isfile(os.path.join(src, f))], key=os.path.getctime)

    if not files:
        return print("No files to distribute.")

    # Distribute to available servers
    for ip in servers:
        if not files:
            break
        
        dest = rf"\\{ip}\{folder}"
        
        # Check if server folder exists and is empty
        try:
            if os.path.exists(dest) and not os.listdir(dest):
                file_to_move = files.pop(0)
                shutil.move(file_to_move, os.path.join(dest, os.path.basename(file_to_move)))
                print(f"Moved to {ip}")
        except Exception as e:
            print(f"Skipping {ip} due to error: {e}")

if __name__ == "__main__":
    distribute()
