# NVIDIA DGX Fleet Telemetry (A2A Protocol)

An Agent-to-Agent (A2A) implementation for monitoring hardware telemetry across a fleet of NVIDIA DGX Spark nodes.

## Architecture

This project consists of two autonomous agents:
1. **Telemetry Worker (`dgx_worker.py`)**: Runs on DGX Spark nodes. Discovers hardware metrics (Grace Blackwell GPU, Arm Cortex CPU, LPDDR5x RAM, NVMe) and exposes them via a standardized A2A endpoint. It hosts an AgentCard for capability discovery.
2. **Dashboard Commander (`dashboard_commander.py`)**: Central monitoring agent. Dynamically fetches AgentCards from fleet nodes, discovers telemetry endpoints, and aggregates real-time metrics and alerts.

## About the A2A Protocol

The Agent-to-Agent (A2A) protocol establishes a standardized method for autonomous AI agents to discover, understand, and interact with one another without hardcoded integrations. 

### How it Works in this Project

1. **Standardized Discovery (`/.well-known/agent-card.json`)**: 
   Instead of the Commander knowing exactly which API endpoints the Worker has, the Worker hosts an "AgentCard" at a globally recognized path. This JSON manifest details the agent's identity and its available skills (capabilities).
   
2. **Dynamic Capability Matching**:
   The Commander queries the AgentCard and looks for a specific skill it knows how to process—in this case, `get_system_telemetry`. 
   
3. **Decoupled Execution**:
   Once the Commander finds the required capability in the AgentCard, it extracts the target `endpoint` (e.g., `/a2a/telemetry`) and `method` (e.g., `POST`), and executes the request. 

This architecture allows the Worker's underlying endpoints to change or upgrade over time. As long as the AgentCard accurately reflects those changes, the Commander will automatically adapt without requiring code updates.

## Prerequisites

```bash
pip install fastapi uvicorn psutil requests nvidia-ml-py
```

## Usage

### 1. Start the Worker Node(s)
Run this on your DGX Spark or local node:
```bash
python3 dgx_worker.py
```
*The worker hosts the AgentCard at `http://<node-ip>:8000/.well-known/agent-card.json`.*

### 2. Start the Commander
Edit `dashboard_commander.py` to include your node IPs in the `FLEET_NODES` list, then run:
```bash
python3 dashboard_commander.py
```