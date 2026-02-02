import os, json, psutil, socket, time
from flask import Flask, jsonify, request
from flask_cors import CORS
import glob
from collections import deque
import shutil

with open('config.json', 'r') as f:
    config = json.load(f)

app = Flask(__name__)
CORS(app)

def is_target_proc(proc, proc_name_filter, cmd_filter=None):
    """Checks if a process matches the User, Name, and Command Line filter."""
    try:
        # Windows usernames often come as DOMAIN\user, so we check if 'xyz' is in the string
        if config['target_user'].lower() not in proc.username().lower():
            return False
        
        if proc_name_filter.lower() not in proc.name().lower():
            return False
            
        if cmd_filter:
            cmdline = " ".join(proc.info['cmdline'] or [])
            if cmd_filter not in cmdline:
                return False
                
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False

def kill_sequence(filename):
    """Kill Perl first, then SAS, then verify."""
    filters = [
        {"name": "perl", "cmd": config['perl_filter']},
        {"name": config['sas_process'], "cmd": None}
    ]

    # Attempt cleanup loop (3 attempts, 5 seconds apart)
    for attempt in range(3):
        found_anything = False
        
        for f in filters:
            for proc in psutil.process_iter(['name', 'username', 'cmdline']):
                if is_target_proc(proc, f['name'], f['cmd']):
                    # Additional check: only kill if this process is tied to the specific file
                    cmdline = " ".join(proc.info['cmdline'] or [])
                    if filename in cmdline or f['name'] == config['sas_process']:
                        proc.kill()
                        found_anything = True
        
        if not found_anything and attempt > 0:
            break # Everything is dead, we can stop checking
        
        time.sleep(5) # Wait 5 seconds before re-checking/re-killing
    
    # Finally, delete the file
    path = os.path.join(config['target_folder'], filename)
    if os.path.exists(path):
        try:
            os.remove(path)
            return True
        except:
            return False
    return True

@app.route('/scan', methods=['GET'])
def scan():
    active_perl_cmds = get_perl_processes() # Existing function that looks for perl + ci_job.pl
    files_list = []
    
    if os.path.exists(config['target_folder']):
        for f in os.listdir(config['target_folder']):
            # Logic: If the filename is found in any running Perl command line
            is_busy = any(f in cmd for cmd in active_perl_cmds)
            files_list.append({
                "name": f, 
                "status": "Processing" if is_busy else "Idle"
            })
    
    return jsonify({"server": socket.gethostname(), "files": files_list})

@app.route('/kill-delete', methods=['POST'])
def handle_kill():
    filename = request.json.get('filename')
    success = kill_sequence(filename)
    return jsonify({"status": "success" if success else "error"})

@app.route('/folders', methods=['GET'])
def list_secondary_folders():
    folder_path = config['secondary_folder']
    folders = []
    if os.path.exists(folder_path):
        # List only directories, not files
        folders = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
    return jsonify({"server": socket.gethostname(), "folders": folders})

@app.route('/get-log', methods=['POST'])
def get_log():
    filename = request.json.get('filename') # e.g., xyz_abcd123456.zip
    try:
        # 1. Extract segment (assumes format xyz_SEGMENT_numbers.zip)
        # Using abcd123 logic: split by underscore, take second part
        parts = filename.split('_')
        if len(parts) < 2: return jsonify({"log": "Invalid filename format"})
        segment = parts[1][:7] # Take the 'abcd123' part

        # 2. Search for folders containing that segment
        search_path = os.path.join(config['log_search_root'], f"*{segment}*")
        folders = [d for d in glob.glob(search_path) if os.path.isdir(d)]

        if not folders:
            return jsonify({"log": f"No folder found for segment: {segment}"})

        # 3. Get latest folder
        latest_folder = max(folders, key=os.path.getmtime)

        # 4. Construct path to proglogs.txt
        log_file = os.path.join(latest_folder, "log", "db", "proglogs.txt")

        if not os.path.exists(log_file):
            return jsonify({"log": f"Log file not found at: {log_file}"})

        # 5. Read last 50 lines (or 5-10 for the box)
        with open(log_file, 'r') as f:
            lines = deque(f, 50) # Efficiently get last 50 lines
            return jsonify({"log": "".join(lines), "folder": os.path.basename(latest_folder)})

    except Exception as e:
        return jsonify({"log": f"Error: {str(e)}"})

@app.route('/get-queue', methods=['GET'])
def get_queue():
    """Lists files in the separate Queue Folder."""
    queue_path = config['queue_folder']
    files = []
    if os.path.exists(queue_path):
        for f in os.listdir(queue_path):
            if os.path.isfile(os.path.join(queue_path, f)):
                files.append({"name": f})
    return jsonify({"files": files})

@app.route('/delete-from-queue', methods=['POST'])
def delete_from_queue():
    """Deletes a file from the separate Queue Folder."""
    filename = request.json.get('filename')
    file_path = os.path.join(config['queue_folder'], filename)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "File not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete-folder', methods=['POST'])
def delete_folder():
    folder_name = request.json.get('folder_name')
    # Use secondary_folder from config
    target_path = os.path.join(config['secondary_folder'], folder_name)
    
    try:
        if os.path.exists(target_path) and os.path.isdir(target_path):
            shutil.rmtree(target_path) # Deletes folder and all contents
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Folder not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get-log-from-folder', methods=['POST'])
def get_log_from_folder():
    folder_name = request.json.get('folder_name')
    # Path: secondary_folder / folder_name / log / db / proglogs.txt
    log_path = os.path.join(config['secondary_folder'], folder_name, "log", "db", "proglogs.txt")
    
    try:
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                lines = deque(f, 50)
                return jsonify({"log": "".join(lines), "path": log_path})
        return jsonify({"log": "proglogs.txt not found in this folder structure."})
    except Exception as e:
        return jsonify({"log": f"Error reading log: {str(e)}"})

@app.route('/disk-usage', methods=['GET'])
def disk_usage():
    stats = {}
    for drive in ['C:', 'D:']:
        try:
            usage = psutil.disk_usage(drive)
            stats[drive] = {
                "total": round(usage.total / (1024**3), 1), # GB
                "used": round(usage.used / (1024**3), 1),   # GB
                "free": round(usage.free / (1024**3), 1),   # GB
                "percent": usage.percent
            }
        except:
            stats[drive] = None # Drive might not exist
    return jsonify(stats)

@app.route('/get-queue', methods=['GET'])
def get_queue():
    """Lists files in the separate Queue Folder and returns count."""
    queue_path = config['queue_folder']
    files = []
    if os.path.exists(queue_path):
        for f in os.listdir(queue_path):
            if os.path.isfile(os.path.join(queue_path, f)):
                files.append({"name": f})
    
    return jsonify({
        "files": files,
        "total_count": len(files)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config['agent_port'])
