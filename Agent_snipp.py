<div class="container-fluid pt-4 px-4">
    <div class="row align-items-center mb-4">
        <div class="col-md-6">
            <h2 class="fw-bold mb-0">Enterprise Process Monitor</h2>
            <p class="text-muted mb-0">User Context: <span class="badge bg-dark">{{ config.target_user }}</span></p>
        </div>
        <div class="col-md-6 d-flex justify-content-end">
            <div class="clock-section">
                <div class="clock-group">
                    <div class="clock-box clock-date">
                        <span class="clock-label">Current Date</span>
                        <span id="display-date">-- --- ----</span>
                    </div>
                    <div class="clock-box">
                        <span class="clock-label">IST (India)</span>
                        <span id="ist-time" class="clock-time">00:00:00</span>
                    </div>
                    <div class="clock-box">
                        <span class="clock-label">CET (Europe)</span>
                        <span id="cet-time" class="clock-time">00:00:00</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // Live Clock Logic
    function tick() {
        const now = new Date();
        
        // Options for formatting
        const timeOptions = { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit', 
            hour12: false 
        };

        const dateOptions = { 
            day: '2-digit', 
            month: 'short', 
            year: 'numeric' 
        };

        // Timezone specific strings
        const istStr = now.toLocaleTimeString('en-GB', { ...timeOptions, timeZone: 'Asia/Kolkata' });
        const cetStr = now.toLocaleTimeString('en-GB', { ...timeOptions, timeZone: 'Europe/Paris' });
        const dateStr = now.toLocaleDateString('en-GB', dateOptions);

        document.getElementById('ist-time').innerText = istStr;
        document.getElementById('cet-time').innerText = cetStr;
        document.getElementById('display-date').innerText = dateStr;
    }

    // Start the clock
    setInterval(tick, 1000);
    tick();
</script>
