import json
from flask import Flask, render_template_string

with open('config.json', 'r') as f:
    config = json.load(f)

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Enterprise Process Monitor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="d-flex justify-content-between">
            <h2>System Dashboard <small class="text-muted" style="font-size: 0.5em;">User: {{ config.target_user }}</small></h2>
            <div>
                <span id="last-update" class="badge bg-dark"></span>
                <button class="btn btn-primary btn-sm ms-2" onclick="loadData()">Manual Refresh</button>
            </div>
        </div>
        
        <div class="card mt-3 shadow-sm">
            <table class="table mb-0">
                <thead class="table-secondary">
                    <tr>
                        <th>Server</th>
                        <th>File Name</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="main-table"></tbody>
            </table>
        </div>
    </div>

    <script>
        const config = {{ config|tojson }};

        async function loadData() {
            const table = document.getElementById('main-table');
            table.style.opacity = '0.5';
            
            let html = '';
            for (let ip of config.servers) {
                try {
                    const res = await fetch(`http://${ip}:${config.agent_port}/scan`);
                    const data = await res.json();
                    data.files.forEach(f => {
                        html += `<tr>
                            <td><b>${ip}</b></td>
                            <td><code>${f.name}</code></td>
                            <td><span class="badge ${f.status=='Idle'?'bg-success':'bg-warning text-dark'}">${f.status}</span></td>
                            <td><button class="btn btn-danger btn-sm" onclick="killFile(this, '${ip}', '${f.name}')">Kill Perl & SAS</button></td>
                        </tr>`;
                    });
                } catch (e) {
                    html += `<tr class="table-danger"><td>${ip}</td><td colspan="3">Offline</td></tr>`;
                }
            }
            table.innerHTML = html;
            table.style.opacity = '1';
            document.getElementById('last-update').innerText = "Last Update: " + new Date().toLocaleTimeString();
        }

        async function killFile(btn, ip, filename) {
            if (!confirm("Start sequential kill (Perl -> SAS -> Verify)?")) return;
            
            btn.disabled = true;
            btn.innerText = "Killing & Verifying...";
            
            try {
                const res = await fetch(`http://${ip}:${config.agent_port}/kill-delete`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({filename: filename})
                });
                if (res.ok) loadData();
            } catch (e) {
                alert("Comm Error");
                btn.disabled = false;
            }
        }

        // Auto Refresh Logic
        const FIFTEEN_MINUTES = 15 * 60 * 1000;
        setInterval(loadData, FIFTEEN_MINUTES);
        window.onload = loadData;
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, config=config)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config['hub_port'])
