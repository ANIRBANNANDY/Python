from flask import Flask, render_template
import os

app = Flask(__name__)

# Define the base directory to search for the latest folder
BASE_DIRECTORY = "C:/path/to/your/directory"  # Replace with the actual directory path

def get_latest_folder(base_directory):
    """
    Finds the latest folder in the specified base directory.
    """
    all_folders = [os.path.join(base_directory, d) for d in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, d))]
    latest_folder = max(all_folders, key=os.path.getmtime) if all_folders else None
    return latest_folder

def get_log_file_path(latest_folder):
    """
    Finds the log file ending with '_P.log' inside the 'log' subfolder of the latest folder.
    """
    log_folder = os.path.join(latest_folder, 'log')
    if os.path.exists(log_folder) and os.path.isdir(log_folder):
        for file in os.listdir(log_folder):
            if file.endswith('_P.log'):
                return os.path.join(log_folder, file)
    return None

def get_last_10_lines(log_file_path):
    """
    Retrieves the last 10 lines of the specified log file.
    """
    try:
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            return lines[-10:]  # Return the last 10 lines
    except Exception as e:
        return [f"Error reading log file: {e}"]

@app.route('/')
def index():
    # Step 1: Get the latest folder
    latest_folder = get_latest_folder(BASE_DIRECTORY)
    
    if not latest_folder:
        return render_template('index.html', error="No folders found in the specified directory.")
    
    # Step 2: Find the log file in the 'log' subfolder
    log_file_path = get_log_file_path(latest_folder)
    
    if not log_file_path:
        return render_template('index.html', error="No log file ending with '_P.log' found in the latest folder.")
    
    # Step 3: Get the last 10 lines of the log file
    log_lines = get_last_10_lines(log_file_path)
    
    # Pass the details to the template
    return render_template('index.html', latest_folder=latest_folder, log_file=log_file_path, log_lines=log_lines)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
