from flask import Flask, render_template, request, redirect, url_for
import psutil

app = Flask(__name__)

# Route to display the process list
@app.route('/')
def list_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        try:
            proc_info = proc.info
            processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue  # Skip processes that are no longer available
    return render_template('process_list.html', processes=processes)

# Route to kill a process by PID
@app.route('/kill/<int:pid>', methods=['POST'])
def kill_process(pid):
    try:
        process = psutil.Process(pid)
        process.terminate()  # Terminate the process
        process.wait(timeout=3)  # Wait for the process to terminate
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
        pass  # Handle cases where the process cannot be terminated
    return redirect(url_for('list_processes'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
