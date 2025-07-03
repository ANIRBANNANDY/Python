import paramiko
import os
import configparser
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("sftp_operations.log"),
                        logging.StreamHandler(sys.stdout)
                    ])

class SFTPHandler:
    def __init__(self, hostname, port, username, password):
        self.hostname = hostname
        self.port = int(port)
        self.username = username
        self.password = password
        self.transport = None
        self.sftp_client = None

    def _connect(self):
        """Establishes an SFTP connection."""
        try:
            logging.info(f"Attempting to connect to SFTP server: {self.hostname}:{self.port} as {self.username}")
            self.transport = paramiko.Transport((self.hostname, self.port))
            self.transport.connect(username=self.username, password=self.password)
            self.sftp_client = paramiko.SFTPClient.from_transport(self.transport)
            logging.info("SFTP connection established successfully.")
            return True
        except paramiko.AuthenticationException:
            logging.error("Authentication failed. Please check your username and password.")
            return False
        except paramiko.SSHException as e:
            logging.error(f"Unable to establish SSH connection: {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during connection: {e}")
            return False

    def _disconnect(self):
        """Closes the SFTP connection."""
        if self.sftp_client:
            self.sftp_client.close()
            logging.info("SFTP client closed.")
        if self.transport:
            self.transport.close()
            logging.info("SFTP transport closed.")

    def download_file(self, remote_path, local_path):
        """
        Downloads a single file from the SFTP server to a local path.
        Returns True on success, False otherwise.
        """
        if not self._connect():
            return False

        try:
            # Ensure local directory exists
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)
                logging.info(f"Created local directory: {local_dir}")

            logging.info(f"Attempting to download '{remote_path}' to '{local_path}'")
            self.sftp_client.get(remote_path, local_path)
            logging.info(f"Successfully downloaded '{remote_path}' to '{local_path}'.")
            return True
        except FileNotFoundError:
            logging.error(f"Remote file not found: '{remote_path}'.")
            return False
        except IOError as e:
            logging.error(f"IOError during download of '{remote_path}': {e}")
            return False
        except paramiko.SFTPError as e:
            logging.error(f"SFTP error during download of '{remote_path}': {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during download of '{remote_path}': {e}")
            return False
        finally:
            self._disconnect()

    def upload_file(self, local_path, remote_path):
        """
        Uploads a single file from a local path to the SFTP server.
        Returns True on success, False otherwise.
        """
        if not self._connect():
            return False

        try:
            if not os.path.exists(local_path):
                logging.error(f"Local file not found for upload: '{local_path}'.")
                return False

            logging.info(f"Attempting to upload '{local_path}' to '{remote_path}'")
            self.sftp_client.put(local_path, remote_path)
            logging.info(f"Successfully uploaded '{local_path}' to '{remote_path}'.")
            return True
        except FileNotFoundError:
            logging.error(f"Local file not found: '{local_path}'.")
            return False
        except IOError as e:
            logging.error(f"IOError during upload of '{local_path}': {e}")
            return False
        except paramiko.SFTPError as e:
            logging.error(f"SFTP error during upload of '{local_path}': {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during upload of '{local_path}': {e}")
            return False
        finally:
            self._disconnect()

def load_config(filename='config.ini'):
    """Loads configuration from the specified INI file."""
    config = configparser.ConfigParser()
    if not os.path.exists(filename):
        logging.critical(f"Config file '{filename}' not found. Please create it.")
        sys.exit(1)
    config.read(filename)
    return config

def run_download_operations(config):
    """Runs the download operations based on config."""
    try:
        download_config = config['SFTP_SERVER_DOWNLOAD']
        hostname = download_config['hostname']
        port = download_config['port']
        username = download_config['username']
        password = download_config['password']
        remote_download_base_path = download_config['remote_download_path']
        local_download_base_path = download_config['local_download_path']
        files_to_download = [f.strip() for f in config['FILES']['files_to_download'].split(',')]

        sftp_downloader = SFTPHandler(hostname, port, username, password)

        for file_name in files_to_download:
            remote_file_path = os.path.join(remote_download_base_path, file_name).replace("\\", "/") # Ensure Unix-like path
            local_file_path = os.path.join(local_download_base_path, file_name)
            sftp_downloader.download_file(remote_file_path, local_file_path)

    except KeyError as e:
        logging.error(f"Missing configuration key for download operations: {e}")
    except Exception as e:
        logging.error(f"An error occurred during download operations: {e}")

def run_upload_operations(config):
    """Runs the upload operations based on config."""
    try:
        upload_config = config['SFTP_SERVER_UPLOAD']
        hostname = upload_config['hostname']
        port = upload_config['port']
        username = upload_config['username']
        password = upload_config['password']
        local_upload_base_path = upload_config['local_upload_path']
        remote_upload_base_path = upload_config['remote_upload_path']
        file_to_upload = config['FILES']['file_to_upload']

        sftp_uploader = SFTPHandler(hostname, port, username, password)

        local_file_path = os.path.join(local_upload_base_path, file_to_upload)
        remote_file_path = os.path.join(remote_upload_base_path, file_to_upload).replace("\\", "/") # Ensure Unix-like path
        sftp_uploader.upload_file(local_file_path, remote_file_path)

    except KeyError as e:
        logging.error(f"Missing configuration key for upload operations: {e}")
    except Exception as e:
        logging.error(f"An error occurred during upload operations: {e}")

def run_test_cases(config):
    """Executes various test cases for SFTP operations."""
    logging.info("\n--- Running Test Cases ---")
    test_config = config['TEST_CASES']
    download_server_config = config['SFTP_SERVER_DOWNLOAD']
    upload_server_config = config['SFTP_SERVER_UPLOAD']

    # Test Case 1: Non-existent remote file download
    logging.info("\nTest Case 1: Attempting to download a non-existent remote file.")
    downloader = SFTPHandler(download_server_config['hostname'], download_server_config['port'],
                             download_server_config['username'], download_server_config['password'])
    non_existent_remote_file = os.path.join(download_server_config['remote_download_path'],
                                            test_config['non_existent_remote_file']).replace("\\", "/")
    local_temp_path = os.path.join(download_server_config['local_download_path'], "temp_non_existent.txt")
    downloader.download_file(non_existent_remote_file, local_temp_path)
    if not os.path.exists(local_temp_path):
        logging.info("Test Case 1 Passed: File was not downloaded (as expected).")
    else:
        logging.error("Test Case 1 Failed: Non-existent file was downloaded unexpectedly.")
        os.remove(local_temp_path) # Clean up if it was created somehow

    # Test Case 2: Invalid local download path (permissions/non-existent parent)
    logging.info("\nTest Case 2: Attempting to download to an invalid local path.")
    downloader = SFTPHandler(download_server_config['hostname'], download_server_config['port'],
                             download_server_config['username'], download_server_config['password'])
    # This assumes 'file1.txt' exists on the remote server
    remote_existing_file = os.path.join(download_server_config['remote_download_path'],
                                        config['FILES']['files_to_download'].split(',')[0].strip()).replace("\\", "/")
    invalid_local_download_path = os.path.join(test_config['invalid_local_download_path'], "test_invalid_path.txt")
    downloader.download_file(remote_existing_file, invalid_local_download_path)
    if not os.path.exists(invalid_local_download_path):
        logging.info("Test Case 2 Passed: File was not downloaded to invalid path (as expected).")
    else:
        logging.error("Test Case 2 Failed: File was downloaded to an invalid path unexpectedly.")
        os.remove(invalid_local_download_path)


    # Test Case 3: Uploading a non-existent local file
    logging.info("\nTest Case 3: Attempting to upload a non-existent local file.")
    uploader = SFTPHandler(upload_server_config['hostname'], upload_server_config['port'],
                           upload_server_config['username'], upload_server_config['password'])
    non_existent_local_file = "./non_existent_local_file_for_upload.txt"
    remote_upload_target = os.path.join(upload_server_config['remote_upload_path'], "temp_upload.txt").replace("\\", "/")
    uploader.upload_file(non_existent_local_file, remote_upload_target)
    # Manual check on SFTP server is needed to verify it wasn't uploaded.
    logging.info("Test Case 3: Please manually verify that 'temp_upload.txt' was NOT uploaded to the remote server.")

    # Test Case 4: Uploading to a remote path with potential permission issues (requires manual setup)
    # For this test, you'd need to configure a remote folder on your SFTP server
    # where the SFTP user has read-only or no write permissions.
    logging.info("\nTest Case 4: Attempting to upload to a remote path with potential permission issues.")
    uploader = SFTPHandler(upload_server_config['hostname'], upload_server_config['port'],
                           upload_server_config['username'], upload_server_config['password'])
    local_existing_file = os.path.join(config['SFTP_SERVER_UPLOAD']['local_upload_path'],
                                       config['FILES']['file_to_upload'])
    remote_permissions_path = os.path.join(test_config['permissions_issue_remote_path'], "permission_test.txt").replace("\\", "/")
    # This will likely fail with SFTPError if permissions are correctly set on the remote server
    uploader.upload_file(local_existing_file, remote_permissions_path)
    logging.info("Test Case 4: Please manually verify if the file was uploaded. If not, it means permission error was handled.")

    # Test Case 5: Invalid SFTP credentials (e.g., wrong password)
    logging.info("\nTest Case 5: Attempting connection with invalid SFTP credentials.")
    bad_sftp = SFTPHandler(download_server_config['hostname'], download_server_config['port'],
                           download_server_config['username'], "wrong_password_123")
    # Try a dummy download to trigger the connection and authentication error
    bad_sftp.download_file("dummy.txt", "./dummy_local.txt")
    logging.info("Test Case 5: Expected 'Authentication failed' error message above.")


    logging.info("\n--- Test Cases Finished ---")


if __name__ == "__main__":
    config = load_config()

    # Create local directories if they don't exist
    os.makedirs(config['SFTP_SERVER_DOWNLOAD']['local_download_path'], exist_ok=True)
    os.makedirs(config['SFTP_SERVER_UPLOAD']['local_upload_path'], exist_ok=True)

    # Create a dummy file for upload test if it doesn't exist
    upload_file_path = os.path.join(config['SFTP_SERVER_UPLOAD']['local_upload_path'], config['FILES']['file_to_upload'])
    if not os.path.exists(upload_file_path):
        with open(upload_file_path, 'w') as f:
            f.write("This is a test file for upload.")
        logging.info(f"Created dummy file for upload: {upload_file_path}")

    # Run main operations
    logging.info("\n--- Running Main Download Operations ---")
    run_download_operations(config)

    logging.info("\n--- Running Main Upload Operations ---")
    run_upload_operations(config)

    # Run test cases if enabled
    if config.getboolean('TEST_CASES', 'enable_tests', fallback=False):
        run_test_cases(config)

    logging.info("\nSFTP operations complete. Check 'sftp_operations.log' for details.")
    
