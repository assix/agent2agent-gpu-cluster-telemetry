# dgx_worker.py
import psutil
import pynvml
from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI()

# Initialize NVML for Blackwell GPU telemetry
try:
    pynvml.nvmlInit()
    HAS_GPU = True
except pynvml.NVMLError:
    HAS_GPU = False

@app.get("/.well-known/agent-card.json")
def get_agent_card():
    return FileResponse("agent-card.json")

@app.post("/a2a/telemetry")
def get_system_telemetry():
    # 20-core Arm Cortex stats
    cpu_usage = psutil.cpu_percent(interval=0.1, percpu=True)
    
    # 128GB LPDDR5x unified memory stats
    mem = psutil.virtual_memory()
    
    # 4TB NVMe.M2 stats
    disk = psutil.disk_usage('/')

    telemetry = {
        "cpu": {
            "overall_utilization": sum(cpu_usage) / len(cpu_usage),
            "core_utilization": cpu_usage
        },
        "ram": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent
        },
        "disk": {
            "total_tb": round(disk.total / (1024**4), 2),
            "used_tb": round(disk.used / (1024**4), 2),
            "percent": disk.percent
        },
        "gpu": {}
    }

    if HAS_GPU:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0 # Convert mW to W
        
        telemetry["gpu"] = {
            "utilization_percent": gpu_util.gpu,
            "temperature_c": temp,
            "power_draw_w": power
        }

    return telemetry

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)