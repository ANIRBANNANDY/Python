import json
from flask import Flask, render_template_string

# Load Config
with open('config.json', 'r') as f:
    config = json.load(f)

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Perl Process Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .status-processing { color: #fd7e14; font-weight: bold; }
        .status-idle { color: #6c757d; }
        .server-header { background-color: #f8f9fa; font-weight: bold; }
    </style>
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>Multi-Server Perl Monitor</h2>
            <button class="btn btn-primary" onclick="loadData()">🔄 Refresh All</button>
        </div>
        
        <div class="table-responsive shadow-sm bg-white rounded">
            <table class="table table-hover mb-0">
                <thead class="table-dark">
                    <tr>
                        <th>Server IP</th>
                        <th>Filename</th>
                        <th>Status</th>
                        <th class="text-end">Actions</th>
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
            table.innerHTML = '<tr><td colspan="4" class="text-center py-4">Scanning servers...</td></tr>';
            let html = '';

            for (let ip of config.servers) {
                try {
                    const response = await fetch(`http://${ip}:${config.agent_port}/scan`);
                    const data = await response.json();
                    
                    if (data.files.length === 0) {
                        html += `<tr class="server-header"><td>${ip}</td><td colspan="3" class="text-muted italic">No files in directory</td></tr>`;
                    }

                    data.files.forEach(file => {
                        html += `
                            <tr>
                                <td><span class="badge bg-secondary">${ip}</span></td>
                                <td><code>${file.name}</code></td>
                                <td class="status-${file.status.toLowerCase()}">${file.status}</td>
                                <td class="text-end">
                                    <button class="btn btn-outline-danger btn-sm" 
                                            onclick="killFile('${ip}', '${file.name}')">Kill & Delete</button>
                                </td>
                            </tr>`;
                    });
                } catch (e) {
                    html += `<tr class="table-danger"><td>${ip}</td><td colspan="3">⚠️ Connection Failed (Check Agent)</td></tr>`;
                }
            }
            table.innerHTML = html;
        }

        async function killFile(ip, filename) {
            if (!confirm(`Stop perl and delete ${filename} on ${ip}?`)) return;
            
            try {
                const res = await fetch(`http://${ip}:${config.agent_port}/kill-delete`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({filename: filename})
                });
                if(res.ok) loadData();
                else alert("Action failed");
            } catch (e) {
                alert("Network error");
            }
        }

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
