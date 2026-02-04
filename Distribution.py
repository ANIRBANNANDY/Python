import os
import shutil
import json
import logging

CONFIG_FILE = "config.json"

def setup_logging(log_path):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

def distribute():
    if not os.path.exists(CONFIG_FILE):
        print("Error: config.json not found.")
        return

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    setup_logging(config.get('log_file', 'distributor.log'))
    
    src = config['source_path']
    folder = config['target_folder_name']
    servers = config['servers']

    if not os.path.exists(src):
        logging.error(f"Source path missing: {src}")
        return

    # FIFO: Get files sorted by creation time
    files = sorted([os.path.join(src, f) for f in os.listdir(src) 
                   if os.path.isfile(os.path.join(src, f))], key=os.path.getctime)

    if not files:
        logging.info("No files found in source. Exiting.")
        return

    for ip in servers:
        if not files:
            break
        
        dest_path = rf"\\{ip}\{folder}"
        
        try:
            # Check if destination is accessible and empty
            if os.path.exists(dest_path):
                if not os.listdir(dest_path):
                    file_to_move = files.pop(0)
                    file_name = os.path.basename(file_to_move)
                    
                    shutil.move(file_to_move, os.path.join(dest_path, file_name))
                    logging.info(f"SUCCESS: {file_name} -> {ip}")
                else:
                    logging.info(f"SKIP: Server {ip} is currently busy (folder not empty).")
            else:
                logging.warning(f"OFFLINE: Cannot reach {dest_path}")
        except Exception as e:
            logging.error(f"FAILED: Error communicating with {ip}: {str(e)}")

if __name__ == "__main__":
    distribute()

{
    "source_path": "C:/MySourceFiles",
    "target_folder_name": "SharedFolder",
    "log_file": "distribution_log.txt",
    "servers": [
        "192.168.1.10",
        "192.168.1.11",
        "192.168.1.12"
    ]
        }
