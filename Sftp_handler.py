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
    def __init__(self, hostname, port, username, private_key_path, passphrase=None, known_hosts_path=None, host_key_policy='RejectPolicy'):
        self.hostname = hostname
        self.port = int(port)
        self.username = username
        self.private_key_path = os.path.expanduser(private_key_path) # Expand ~ to home directory
        self.passphrase = passphrase
        self.known_hosts_path = os.path.expanduser(known_hosts_path) if known_hosts_path else None
        self.host_key_policy = host_key_policy
        self.transport = None
        self.sftp_client = None
        self.ssh_client = None # Using SSHClient for better host key handling

    def _load_private_key(self):
        """Loads the SSH private key."""
        try:
            if not os.path.exists(self.private_key_path):
                logging.error(f"Private key file not found at: {self.private_key_path}")
                return None

            # Attempt to load as various key types
            try:
                # Try RSA
                private_key = paramiko.RSAKey.from_private_key_file(self.private_key_path, password=self.passphrase)
            except paramiko.SSHException:
                try:
                    # Try EdDSA
                    private_key = paramiko.EdDSAKey.from_private_key_file(self.private_key_path, password=self.passphrase)
                except paramiko.SSHException:
                    try:
                        # Try ECDSA
                        private_key = paramiko.ECDSAKey.from_private_key_file(self.private_key_path, password=self.passphrase)
                    except paramiko.SSHException:
                        try:
                            # Try DSS
                            private_key = paramiko.DSSKey.from_private_key_file(self.private_key_path, password=self.passphrase)
                        except paramiko.SSHException as e:
                            logging.error(f"Could not load private key from '{self.private_key_path}'. Is the format correct or passphrase wrong? {e}")
                            return None
            logging.info(f"Private key loaded from {self.private_key_path}.")
            return private_key
        except paramiko.PasswordRequiredException:
            logging.error(f"Private key at '{self.private_key_path}' is encrypted, but no passphrase was provided.")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading private key: {e}")
            return None

    def _connect(self):
        """Establishes an SFTP connection using SSHClient for key-based auth and host key verification."""
        try:
            logging.info(f"Attempting to connect to SFTP server: {self.hostname}:{self.port} as {self.username} using key.")
            
            self.ssh_client = paramiko.SSHClient()

            # Set host key policy
            if self.host_key_policy == 'AutoAddPolicy':
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                logging.warning("Using AutoAddPolicy: Unknown host keys will be automatically added. This is NOT recommended for production environments.")
            elif self.host_key_policy == 'RejectPolicy':
                self.ssh_client.set_missing_host_key_policy(paramiko.RejectPolicy())
                logging.info("Using RejectPolicy: Connections to unknown hosts will be rejected.")
            elif self.host_key_policy == 'WarningPolicy':
                self.ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())
                logging.warning("Using WarningPolicy: Unknown host keys will issue a warning.")
            else:
                logging.error(f"Invalid host_key_policy: {self.host_key_policy}. Defaulting to RejectPolicy.")
                self.ssh_client.set_missing_host_key_policy(paramiko.RejectPolicy())

            # Load known hosts if specified
            if self.known_hosts_path and os.path.exists(self.known_hosts_path):
                self.ssh_client.load_host_keys(self.known_hosts_path)
                logging.info(f"Loaded known hosts from {self.known_hosts_path}")
            elif self.known_hosts_path:
                logging.warning(f"Known hosts file not found at: {self.known_hosts_path}. Host key verification might be affected.")

            private_key = self._load_private_key()
            if not private_key:
                return False

            self.ssh_client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                pkey=private_key, # Pass the loaded private key
                timeout=10 # Add a connection timeout
            )
            self.sftp_client = self.ssh_client.open_sftp()
            logging.info("SFTP connection established successfully using SSH key.")
            return True
        except paramiko.AuthenticationException:
            logging.error("Authentication failed. Please check your private key, passphrase, and username, or if the public key is on the server.")
            return False
        except paramiko.SSHException as e:
            logging.error(f"Unable to establish SSH connection: {e}")
            return False
        except paramiko.BadHostKeyException as e:
            logging.error(f"Host key for {e.hostname} does not match the known host key. Possible MITM attack or changed host key. Fingerprint: {e.key.get_fingerprint()}")
            return False
        except FileNotFoundError as e:
            logging.error(f"File not found during connection attempt (e.g., known_hosts or private key): {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during connection: {e}")
            return False

    def _disconnect(self):
        """Closes the SFTP connection."""
        if self.sftp_client:
            self.sftp_client.close()
            logging.info("SFTP client closed.")
        if self.ssh_client:
            self.ssh_client.close()
            logging.info("SSH client closed.")

    # download_file and upload_file methods remain the same as before,
    # as they call _connect() and _disconnect()
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
        private_key_path = download_config['private_key_path']
        passphrase = download_config.get('passphrase', None) # Get passphrase, default to None if not present
        remote_download_base_path = download_config['remote_download_path']
        local_download_base_path = download_config['local_download_path']
        files_to_download = [f.strip() for f in config['FILES']['files_to_download'].split(',')]

        known_hosts_path = config['HOST_KEYS'].get('known_hosts_path', None)
        host_key_policy = config['HOST_KEYS'].get('host_key_policy', 'RejectPolicy')


        sftp_downloader = SFTPHandler(hostname, port, username, private_key_path, passphrase, known_hosts_path, host_key_policy)

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
        private_key_path = upload_config['private_key_path']
        passphrase = upload_config.get('passphrase', None) # Get passphrase, default to None if not present
        local_upload_base_path = upload_config['local_upload_path']
        remote_upload_base_path = upload_config['remote_upload_path']
        file_to_upload = config['FILES']['file_to_upload']

        known_hosts_path = config['HOST_KEYS'].get('known_hosts_path', None)
        host_key_policy = config['HOST_KEYS'].get('host_key_policy', 'RejectPolicy')

        sftp_uploader = SFTPHandler(hostname, port, username, private_key_path, passphrase, known_hosts_path, host_key_policy)

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
    
    known_hosts_path = config['HOST_KEYS'].get('known_hosts_path', None)
    host_key_policy = config['HOST_KEYS'].get('host_key_policy', 'RejectPolicy')

    # Test Case 1: Non-existent remote file download
    logging.info("\nTest Case 1: Attempting to download a non-existent remote file.")
    downloader = SFTPHandler(download_server_config['hostname'], download_server_config['port'],
                             download_server_config['username'], download_server_config['private_key_path'],
                             download_server_config.get('passphrase', None), known_hosts_path, host_key_policy)
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
                             download_server_config['username'], download_server_config['private_key_path'],
                             download_server_config.get('passphrase', None), known_hosts_path, host_key_policy)
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
                           upload_server_config['username'], upload_server_config['private_key_path'],
                           upload_server_config.get('passphrase', None), known_hosts_path, host_key_policy)
    non_existent_local_file = "./non_existent_local_file_for_upload.txt"
    remote_upload_target = os.path.join(upload_server_config['remote_upload_path'], "temp_upload.txt").replace("\\", "/")
    uploader.upload_file(non_existent_local_file, remote_upload_target)
    # Manual check on SFTP server is needed to verify it wasn't uploaded.
    logging.info("Test Case 3: Please manually verify that 'temp_upload.txt' was NOT uploaded to the remote server.")

    # Test Case 4: Uploading to a remote path with potential permission issues (requires manual setup)
    logging.info("\nTest Case 4: Attempting to upload to a remote path with potential permission issues.")
    uploader = SFTPHandler(upload_server_config['hostname'], upload_server_config['port'],
                           upload_server_config['username'], upload_server_config['private_key_path'],
                           upload_server_config.get('passphrase', None), known_hosts_path, host_key_policy)
    local_existing_file = os.path.join(config['SFTP_SERVER_UPLOAD']['local_upload_path'],
                                       config['FILES']['file_to_upload'])
    remote_permissions_path = os.path.join(test_config['permissions_issue_remote_path'], "permission_test.txt").replace("\\", "/")
    uploader.upload_file(local_existing_file, remote_permissions_path)
    logging.info("Test Case 4: Please manually verify if the file was uploaded. If not, it means permission error was handled.")

    # Test Case 5: Invalid SFTP credentials (e.g., wrong private key path)
    logging.info("\nTest Case 5: Attempting connection with invalid private key path.")
    bad_sftp = SFTPHandler(download_server_config['hostname'], download_server_config['port'],
                           download_server_config['username'], test_config['invalid_private_key_path'],
                           None, known_hosts_path, host_key_policy)
    bad_sftp.download_file("dummy.txt", "./dummy_local.txt")
    logging.info("Test Case 5: Expected 'Private key file not found' error message above.")
    
    # Test Case 6: Invalid SFTP credentials (e.g., wrong passphrase for encrypted key)
    # This test requires an encrypted private key configured in config.ini
    if download_server_config.get('passphrase') and 'passphrase' in download_server_config:
        logging.info("\nTest Case 6: Attempting connection with wrong private key passphrase.")
        wrong_passphrase_sftp = SFTPHandler(download_server_config['hostname'], download_server_config['port'],
                                            download_server_config['username'], download_server_config['private_key_path'],
                                            "wrong_passphrase_123", known_hosts_path, host_key_policy)
        wrong_passphrase_sftp.download_file("dummy.txt", "./dummy_local_wrong_pass.txt")
        logging.info("Test Case 6: Expected 'Could not load private key' or 'Authentication failed' error message above.")
    else:
        logging.info("\nTest Case 6 Skipped: No passphrase configured for download server in config.ini to test wrong passphrase.")

    # Test Case 7: Unknown Host Key (requires host_key_policy='RejectPolicy' for explicit failure)
    logging.info("\nTest Case 7: Testing Unknown Host Key (requires manual setup for 'RejectPolicy' to fail).")
    logging.info("To truly test this, remove the target SFTP server's host key from your known_hosts file, set host_key_policy = RejectPolicy, and try connecting.")
    logging.info("Expected: 'BadHostKeyException' error if host key is unknown and policy is RejectPolicy.")
    # This test case is more about demonstrating the policy. You'd need to manually
    # clear the host's entry from your known_hosts file for it to fail with RejectPolicy.
    # The current code's logging will show if a BadHostKeyException occurs.


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
