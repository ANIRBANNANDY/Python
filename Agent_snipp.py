<div class="card shadow-sm queue-card mt-3">
    <div class="explorer-header d-flex justify-content-between align-items-center bg-light">
        <div class="d-flex align-items-center">
            <span class="fw-bold">Queue Manager</span>
            <span id="queue-count-badge" class="queue-badge">0</span>
        </div>
        <button class="btn btn-sm btn-link p-0 text-decoration-none" onclick="updateQueue()">🔄</button>
    </div>
    <div class="p-2">
        <div id="queue-container" style="max-height: 300px; overflow-y: auto;">
            <table class="table table-sm table-borderless small mb-0">
                <tbody id="queue-list">
                    </tbody>
            </table>
        </div>
    </div>
</div>

<script>
    async function updateQueue() {
        const server1Ip = config.servers[0]; 
        const queueList = document.getElementById('queue-list');
        const badge = document.getElementById('queue-count-badge');
        
        try {
            const res = await fetch(`http://${server1Ip}:${config.agent_port}/get-queue`);
            const data = await res.json();
            
            // Update the badge count
            badge.innerText = data.total_count;
            
            // Highlight badge if queue is getting large (e.g., > 10 files)
            if (data.total_count > 10) {
                badge.classList.replace('bg-purple', 'bg-danger');
            } else {
                badge.style.backgroundColor = '#6f42c1';
            }

            let html = '';
            if (data.files.length === 0) {
                html = '<tr><td class="text-center text-muted py-3">Queue is empty</td></tr>';
            } else {
                data.files.forEach(file => {
                    html += `
                        <tr class="border-bottom">
                            <td class="align-middle"><code>${file.name}</code></td>
                            <td class="text-end">
                                <button class="btn btn-link text-danger btn-sm p-0 fw-bold" 
                                        style="text-decoration:none"
                                        onclick="confirmQueueDelete('${file.name}')">
                                    [ Delete ]
                                </button>
                            </td>
                        </tr>`;
                });
            }
            queueList.innerHTML = html;
        } catch (e) {
            queueList.innerHTML = '<tr><td class="text-danger text-center">Connection error</td></tr>';
            badge.innerText = '!';
        }
    }
</script>
