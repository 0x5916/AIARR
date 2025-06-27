from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from website.machine_stat import CPRMachineStatus

app = FastAPI()
machine_status = CPRMachineStatus()
# m`+achine_status.update_status(shocks=2, cpr_cycles=2, ventilations=2)

@app.get("/record")
def get_status():
    return {
        "electric_shocks": machine_status.electric_shocks,
        "cpr_cycles": machine_status.cpr_cycles,
        "breathe": machine_status.breathe,
        "start_time": machine_status.start_time
    }

@app.get("/", response_class=HTMLResponse)
def index():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Machine Record</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            color: #333;
            text-align: center;
            margin: 0;
            padding: 0;
        }
        h1 {
            background-color: #6200ea;
            color: white;
            padding: 20px 0;
            margin: 0;
        }
        div {
            margin: 20px auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background-color: #fff;
            width: 80%;
            max-width: 600px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        p {
            font-size: 1.2em;
        }
        span {
            font-weight: bold;
            color: #6200ea;
        }
    </style>
    <script>
        let startTime = null;
        let runTimeInterval = null;

        async function fetchStatus() {
            try {
                const response = await fetch('/record');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                document.getElementById('electricShocks').innerText = data.electric_shocks;
                document.getElementById('cprCycles').innerText = data.cpr_cycles;
                document.getElementById('breathe').innerText = data.breathe;

                if (data.start_time === null) {
                    startTime = null;
                    clearInterval(runTimeInterval);
                    document.getElementById('runTime').innerText = "Not started";
                } else if (!startTime) {
                    startTime = new Date(data.start_time);
                    updateRunTime();
                    runTimeInterval = setInterval(updateRunTime, 1000);
                }
            } catch (error) {
                console.error('Error fetching record:', error);
            }
        }

        function updateRunTime() {
            if (startTime) {
                const now = new Date();
                const elapsed = Math.floor((now - startTime) / 1000); // Calculate elapsed time in seconds
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                document.getElementById('runTime').innerText = `${minutes}m ${seconds}s`;
            } else {
                document.getElementById('runTime').innerText = "Not started";
            }
        }

        function showLoadingAnimation() {
            const elements = document.querySelectorAll('span');
            elements.forEach(el => el.innerText = 'Loading...');
        }

        // Fetch record every second
        setInterval(fetchStatus, 1000);

        // Fetch record on page load
        window.onload = () => {
            showLoadingAnimation();
            fetchStatus();
        };
    </script>
</head>
<body>
    <h1>CPR Machine Record</h1>
    <div>
        <p><strong>Electric Shocks:</strong> <span id="electricShocks">Loading...</span></p>
        <p><strong>CPR Cycles:</strong> <span id="cprCycles">Loading...</span></p>
        <p><strong>Breathe:</strong> <span id="breathe">Loading...</span></p>
        <p><strong>Run Time:</strong> <span id="runTime">Not started</span></p>
    </div>
</body>
</html>

    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
