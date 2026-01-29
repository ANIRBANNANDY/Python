import os
import json
import psutil
import socket
from flask import Flask, jsonify, request
from flask_cors import CORS

# Load Config
with open('config.json', 'r') as f:
    config = json.load(f)

app = Flask(__name__)
CORS(app)

TARGET_FOLDER = config['target_folder']

def get_perl_processes():
    processing_files = set()
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] and 'perl' in proc.info['name'].lower():
                cmdline = " ".join(proc.info['cmdline'] or [])
                processing_files.add(cmdline)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processing_files

@app.route('/scan', methods=['GET'])
def scan():
    active_perl_cmds = get_perl_processes()
    files_list = []
    
    if os.path.exists(TARGET_FOLDER):
        for f in os.listdir(TARGET_FOLDER):
            is_busy = any(f in cmd for cmd in active_perl_cmds)
            files_list.append({"name": f, "status": "Processing" if is_busy else "Idle"})
    
    return jsonify({"server": socket.gethostname(), "files": files_list})

@app.route('/kill-delete', methods=['POST'])
def kill_delete():
    filename = request.json.get('filename')
    # Kill Process
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] and 'perl' in proc.info['name'].lower():
                if any(filename in part for part in (proc.info['cmdline'] or [])):
                    proc.kill()
        except: continue
        
    # Delete File
    try:
        path = os.path.join(TARGET_FOLDER, filename)
        if os.path.exists(path):
            os.remove(path)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config['agent_port'])
