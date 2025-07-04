import os
import fnmatch
import yaml
import logging
import paramiko
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("file_transfer.log"),
        logging.StreamHandler()
    ]
)

def load_config(file_path='application.yml'):
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
            logging.info("Configuration loaded successfully.")
            return config
    except Exception as e:
        logging.exception("Failed to load configuration.")
        raise

def create_sftp_client(host, port, username, private_key_path):
    try:
        key = paramiko.RSAKey.from_private_key_file(private_key_path)
        transport = paramiko.Transport((host, port))
        transport.connect(username=username, pkey=key)
        sftp = paramiko.SFTPClient.from_transport(transport)
        logging.info(f"SFTP connection established with {host}.")
        return sftp
    except Exception as e:
        logging.exception(f"Failed to connect to SFTP server {host}.")
        raise

def download_files(sftp, remote_dir, local_dir, pattern):
    try:
        os.makedirs(local_dir, exist_ok=True)
        logging.info(f"Downloading files from {remote_dir} matching '{pattern}' to {local_dir}")

        for filename in sftp.listdir(remote_dir):
            if fnmatch.fnmatch(filename, pattern):
                remote_path = f"{remote_dir}/{filename}"
                local_path = os.path.join(local_dir, filename)
                try:
                    sftp.get(remote_path, local_path)
                    logging.info(f"Downloaded: {remote_path} → {local_path}")
                except Exception as e:
                    logging.error(f"Failed to download {remote_path}: {e}")
    except Exception as e:
        logging.exception("Error during file download.")
        raise

def upload_files(sftp, local_dir, remote_dir):
    try:
        logging.info(f"Uploading files from {local_dir} to {remote_dir}")
        for filename in os.listdir(local_dir):
            local_path = os.path.join(local_dir, filename)
            remote_path = f"{remote_dir}/{filename}"
            try:
                sftp.put(local_path, remote_path)
                logging.info(f"Uploaded: {local_path} → {remote_path}")
            except Exception as e:
                logging.error(f"Failed to upload {local_path}: {e}")
    except Exception as e:
        logging.exception("Error during file upload.")
        raise

def main():
    try:
        config = load_config()

        source = config['source_server']
        target = config['target_server']
        paths = config['paths']

        local_dir = paths['local_dir']
        file_pattern = paths['file_pattern']

        # Connect to source server
        logging.info("Connecting to source server...")
        source_sftp = create_sftp_client(
            source['host'], source['port'],
            source['username'], source['private_key']
        )

        download_files(source_sftp, paths['remote_source_dir'], local_dir, file_pattern)
        source_sftp.close()
        logging.info("Source SFTP session closed.")

        # Connect to target server
        logging.info("Connecting to target server...")
        target_sftp = create_sftp_client(
            target['host'], target['port'],
            target['username'], target['private_key']
        )

        upload_files(target_sftp, local_dir, paths['remote_target_dir'])
        target_sftp.close()
        logging.info("Target SFTP session closed.")

        logging.info("File transfer completed successfully.")

    except Exception as e:
        logging.critical("Script terminated due to an unrecoverable error.")
        exit(1)

if __name__ == "__main__":
    main()
