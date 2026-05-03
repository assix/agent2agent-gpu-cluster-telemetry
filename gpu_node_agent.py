import os
import platform
import psutil
import pynvml
from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI()

try:
    pynvml.nvmlInit()
    HAS_GPU = True
except pynvml.NVMLError:
    HAS_GPU = False

@app.get("/.well-known/agent-card.json")
def get_agent_card():
    """Serves the static agent card for capability discovery."""
    return FileResponse("agent-card.json")

@app.get("/a2a/cpu")
def get_cpu_telemetry():
    """Gathers comprehensive CPU data including load, frequencies, and per-core utilization."""
    load1, load5, load15 = os.getloadavg() if hasattr(os, 'getloadavg') else (0.0, 0.0, 0.0)
    cpu_freq = psutil.cpu_freq()
    
    return {
        "architecture": platform.processor(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "load_average": {
            "1_min": load1,
            "5_min": load5,
            "15_min": load15
        },
        "utilization": {
            "overall_percent": psutil.cpu_percent(interval=0.1),
            "per_core_percent": psutil.cpu_percent(interval=0.1, percpu=True)
        },
        "frequency_mhz": {
            "current": cpu_freq.current if cpu_freq else 0.0,
            "max": cpu_freq.max if cpu_freq else 0.0
        }
    }

@app.get("/a2a/gpu")
def get_gpu_telemetry():
    """Queries NVML for deep GPU metrics, gracefully handling systems without NVIDIA GPUs."""
    if not HAS_GPU:
        return {"status": "No NVIDIA GPU detected."}

    device_count = pynvml.nvmlDeviceGetCount()
    gpus = []

    for i in range(device_count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        name = pynvml.nvmlDeviceGetName(handle)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0

        gpus.append({
            "id": i,
            "name": name,
            "memory": {
                "total_gb": round(mem_info.total / (1024**3), 2),
                "used_gb": round(mem_info.used / (1024**3), 2),
                "free_gb": round(mem_info.free / (1024**3), 2)
            },
            "utilization": {
                "gpu_percent": utilization.gpu,
                "memory_percent": utilization.memory
            },
            "thermals": {
                "temperature_c": temp
            },
            "power": {
                "draw_watts": power
            }
        })

    return {
        "driver_version": pynvml.nvmlSystemGetDriverVersion(),
        "device_count": device_count,
        "devices": gpus
    }

@app.get("/a2a/ram")
def get_ram_telemetry():
    """Collects system memory allocations and swap file usage."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        "system_memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent_used": mem.percent
        },
        "swap_memory": {
            "total_gb": round(swap.total / (1024**3), 2),
            "used_gb": round(swap.used / (1024**3), 2),
            "percent_used": swap.percent
        }
    }

@app.get("/a2a/disk")
def get_disk_telemetry():
    """Aggregates disk capacities and system-wide I/O counters."""
    disk_usage = psutil.disk_usage('/')
    io_counters = psutil.disk_io_counters()
    
    return {
        "root_partition": {
            "total_tb": round(disk_usage.total / (1024**4), 3),
            "used_tb": round(disk_usage.used / (1024**4), 3),
            "free_tb": round(disk_usage.free / (1024**4), 3),
            "percent_used": disk_usage.percent
        },
        "io_statistics": {
            "read_count": io_counters.read_count if io_counters else 0,
            "write_count": io_counters.write_count if io_counters else 0,
            "read_bytes_mb": round(io_counters.read_bytes / (1024**2), 2) if io_counters else 0.0,
            "write_bytes_mb": round(io_counters.write_bytes / (1024**2), 2) if io_counters else 0.0
        }
    }

@app.get("/a2a/network")
def get_network_telemetry():
    """Retrieves network throughput and packet statistics."""
    net = psutil.net_io_counters()
    
    return {
        "throughput": {
            "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2)
        },
        "packets": {
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
            "errors_in": net.errin,
            "errors_out": net.errout,
            "drops_in": net.dropin,
            "drops_out": net.dropout
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)