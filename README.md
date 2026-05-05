# IoT Edge Computing & Salesforce CRM Integration Platform

Real-time industrial compressor monitoring with automated Salesforce Case generation via edge computing and MQTT.

## Live Demo
- **Dashboard:** https://iot-edge-crm-satvik.streamlit.app
- **API Docs:** https://iot-edge-crm.onrender.com/docs

## Architecture

[IoT Simulator] → MQTT → [HiveMQ Cloud] → MQTT → [Edge Processor]
│
Fault Detected
│
HTTP POST → [FastAPI Backend]
│
┌──────────┴──────────┐
│                     │
[Supabase DB]     [Salesforce REST API]
│                     │
└──────────┬──────────┘
│
[Streamlit Dashboard]


## What It Does

Five industrial compressors continuously publish sensor readings (temperature, vibration, pressure) via MQTT to HiveMQ Cloud. An edge processor subscribes to all readings and evaluates them locally against fault thresholds. When a fault is detected, the edge processor POSTs an alert to the FastAPI backend, which simultaneously saves the alert to Supabase PostgreSQL and creates a Salesforce Case via the REST API. A live Streamlit dashboard displays real-time sensor readings, fault alerts, and Salesforce Cases with direct links.

## Tech Stack

| Layer | Technology |
|---|---|
| IoT Protocol | MQTT (paho-mqtt) |
| MQTT Broker | HiveMQ Cloud Serverless |
| Edge Processing | Python rules engine |
| Backend API | FastAPI + Uvicorn on Render |
| Database | Supabase PostgreSQL |
| CRM Integration | Salesforce Developer Edition REST API (OAuth 2.0 Client Credentials) |
| Dashboard | Streamlit Cloud |
| Containerization | Docker |
| CI/CD | GitHub Actions |

## Fault Detection Thresholds

| Sensor | Warning | Critical |
|---|---|---|
| Temperature | > 85°C | > 95°C |
| Vibration | > 6.0 mm/s | > 9.0 mm/s |
| Pressure | < 5.5 bar | < 4.0 bar |

## Project Structure

├── simulator/          # IoT device simulator (5 compressors via MQTT)
├── edge_processor/     # Edge fault detection + alert dispatch
├── backend/            # FastAPI backend + Salesforce + Supabase services
├── dashboard/          # Streamlit live dashboard
├── .github/workflows/  # GitHub Actions CI/CD
├── Dockerfile
├── docker-compose.yml
└── requirements.txt

## Local Setup

```bash
git clone https://github.com/SatvikSPandey/iot-edge-crm-platform.git
cd iot-edge-crm-platform
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# Add credentials to imp/.env
python -m backend.main          # Terminal 1
python -m simulator.simulator   # Terminal 2
python -m edge_processor.edge_processor  # Terminal 3
```

## Author

**Satvik Pandey**
- GitHub: [github.com/SatvikSPandey](https://github.com/SatvikSPandey)
- LinkedIn: [linkedin.com/in/satvikpandey-433555365](https://linkedin.com/in/satvikpandey-433555365)
- Portfolio: [satvikspandey.netlify.app](https://satvikspandey.netlify.app)