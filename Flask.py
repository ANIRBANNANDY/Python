from flask import Flask, render_template, request, redirect, url_for
import psutil
import os
from datetime import datetime

app = Flask(__name__)

# List of processes to monitor
TARGET_PROCESSES = ["perl.exe", "python.exe", "sas.exe"]

def get_process_details():
    process_details = []
    for proc in psutil.process_iter(attrs=['pid', 'name', 'username', 'exe', 'cmdline', 'create_time']):
        if proc.info['name'] in TARGET_PROCESSES:
            process_details.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'user': proc.info['username'],
                'full_path': proc.info['exe'],
                'cmdline': ' '.join(proc.info['cmdline']),
                'start_time': datetime.fromtimestamp(proc.info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
            })
    return process_details

@app.route('/')
def index():
    processes = get_process_details()
    return render_template('index.html', processes=processes)

@app.route('/kill/<int:pid>')
def kill_process(pid):
    try:
        p = psutil.Process(pid)
        p.terminate()  # You can use p.kill() if you want to force kill
        return redirect(url_for('index'))
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
