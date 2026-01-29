import os, json, psutil, socket, time
from flask import Flask, jsonify, request
from flask_cors import CORS

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
    files_list = []
    if os.path.exists(config['target_folder']):
        for f in os.listdir(config['target_folder']):
            is_busy = False
            for proc in psutil.process_iter(['name', 'username', 'cmdline']):
                if is_target_proc(proc, "perl", config['perl_filter']) and f in " ".join(proc.info['cmdline'] or []):
                    is_busy = True
                    break
            files_list.append({"name": f, "status": "Processing" if is_busy else "Idle"})
    return jsonify({"server": socket.gethostname(), "files": files_list})

@app.route('/kill-delete', methods=['POST'])
def handle_kill():
    filename = request.json.get('filename')
    success = kill_sequence(filename)
    return jsonify({"status": "success" if success else "error"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config['agent_port'])
