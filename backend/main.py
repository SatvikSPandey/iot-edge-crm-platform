from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from backend.services.salesforce_service import create_case
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'imp', '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="IoT Edge CRM Integration API",
    description="Receives IoT fault alerts from edge processor, stores in Supabase, creates Salesforce Cases",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SensorReading(BaseModel):
    compressor_id: str
    temperature: float
    vibration: float
    pressure: float
    runtime_hours: float
    timestamp: float

class FaultAlert(BaseModel):
    compressor_id: str
    fault_type: str
    severity: str
    sensor_value: float
    threshold_value: float

@app.get("/")
def root():
    return {"status": "IoT Edge CRM Integration API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/v1/readings")
def save_reading(reading: SensorReading):
    try:
        data = {
            "compressor_id": reading.compressor_id,
            "temperature": reading.temperature,
            "vibration": reading.vibration,
            "pressure": reading.pressure,
            "runtime_hours": reading.runtime_hours,
        }
        supabase.table("sensor_readings").insert(data).execute()
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/alerts")
def create_alert(alert: FaultAlert):
    try:
        sf_result = create_case(
            compressor_id=alert.compressor_id,
            fault_type=alert.fault_type,
            severity=alert.severity,
            sensor_value=alert.sensor_value,
            threshold_value=alert.threshold_value
        )

        data = {
            "compressor_id": alert.compressor_id,
            "fault_type": alert.fault_type,
            "severity": alert.severity,
            "sensor_value": alert.sensor_value,
            "threshold_value": alert.threshold_value,
            "sf_case_id": sf_result["sf_case_id"],
            "sf_case_number": sf_result["sf_case_number"],
            "sf_case_url": sf_result["sf_case_url"],
        }
        supabase.table("fault_alerts").insert(data).execute()

        return {
            "status": "alert created",
            "sf_case_id": sf_result["sf_case_id"],
            "sf_case_number": sf_result["sf_case_number"],
            "sf_case_url": sf_result["sf_case_url"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/alerts")
def get_alerts():
    try:
        result = supabase.table("fault_alerts") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(50) \
            .execute()
        return {"alerts": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/readings/latest")
def get_latest_readings():
    try:
        compressors = [f"compressor-{i}" for i in range(1, 6)]
        latest = []
        for cid in compressors:
            result = supabase.table("sensor_readings") \
                .select("*") \
                .eq("compressor_id", cid) \
                .order("recorded_at", desc=True) \
                .limit(1) \
                .execute()
            if result.data:
                latest.append(result.data[0])
        return {"readings": latest}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cases")
def get_cases():
    try:
        result = supabase.table("fault_alerts") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(20) \
            .execute()
        return {"cases": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))