from flask import Flask, jsonify, request
import psutil
import os

app = Flask(__name__)

# Endpoint to get all processes
@app.route('/processes', methods=['GET'])
def list_processes():
    process_list = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        try:
            process_info = proc.info
            process_list.append(process_info)
        except psutil.NoSuchProcess:
            pass  # Process might have terminated since we started iterating
    return jsonify(process_list)

# Endpoint to kill a process by PID
@app.route('/kill_process', methods=['POST'])
def kill_process():
    data = request.json
    pid = data.get("pid")
    if pid is None:
        return jsonify({"error": "No PID provided"}), 400

    try:
        process = psutil.Process(pid)
        process.terminate()
        return jsonify({"status": "Process terminated", "pid": pid}), 200
    except psutil.NoSuchProcess:
        return jsonify({"error": "Process not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
