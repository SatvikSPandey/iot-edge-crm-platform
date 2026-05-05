import paho.mqtt.client as mqtt
import json
import ssl
import os
import httpx
import time
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'imp', '.env'))

HIVEMQ_HOST = os.getenv("HIVEMQ_HOST")
HIVEMQ_PORT = int(os.getenv("HIVEMQ_PORT"))
HIVEMQ_USERNAME = os.getenv("HIVEMQ_USERNAME")
HIVEMQ_PASSWORD = os.getenv("HIVEMQ_PASSWORD")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

THRESHOLDS = {
    "temperature": {"warning": 85.0, "critical": 95.0},
    "vibration": {"warning": 6.0, "critical": 9.0},
    "pressure": {"warning": 5.5, "critical": 4.0},
}

COOLDOWN_SECONDS = 60
last_alert_time = {}

def evaluate_reading(reading):
    faults = []
    compressor_id = reading["compressor_id"]

    temp = reading["temperature"]
    if temp >= THRESHOLDS["temperature"]["critical"]:
        faults.append({
            "compressor_id": compressor_id,
            "fault_type": "HIGH_TEMPERATURE",
            "severity": "Critical",
            "sensor_value": temp,
            "threshold_value": THRESHOLDS["temperature"]["critical"]
        })
    elif temp >= THRESHOLDS["temperature"]["warning"]:
        faults.append({
            "compressor_id": compressor_id,
            "fault_type": "HIGH_TEMPERATURE",
            "severity": "High",
            "sensor_value": temp,
            "threshold_value": THRESHOLDS["temperature"]["warning"]
        })

    vib = reading["vibration"]
    if vib >= THRESHOLDS["vibration"]["critical"]:
        faults.append({
            "compressor_id": compressor_id,
            "fault_type": "VIBRATION_SPIKE",
            "severity": "Critical",
            "sensor_value": vib,
            "threshold_value": THRESHOLDS["vibration"]["critical"]
        })
    elif vib >= THRESHOLDS["vibration"]["warning"]:
        faults.append({
            "compressor_id": compressor_id,
            "fault_type": "VIBRATION_SPIKE",
            "severity": "High",
            "sensor_value": vib,
            "threshold_value": THRESHOLDS["vibration"]["warning"]
        })

    pres = reading["pressure"]
    if pres <= THRESHOLDS["pressure"]["critical"]:
        faults.append({
            "compressor_id": compressor_id,
            "fault_type": "PRESSURE_DROP",
            "severity": "Critical",
            "sensor_value": pres,
            "threshold_value": THRESHOLDS["pressure"]["critical"]
        })
    elif pres <= THRESHOLDS["pressure"]["warning"]:
        faults.append({
            "compressor_id": compressor_id,
            "fault_type": "PRESSURE_DROP",
            "severity": "High",
            "sensor_value": pres,
            "threshold_value": THRESHOLDS["pressure"]["warning"]
        })

    return faults

def send_alert(fault):
    cooldown_key = f"{fault['compressor_id']}_{fault['fault_type']}"
    now = time.time()
    if cooldown_key in last_alert_time:
        if now - last_alert_time[cooldown_key] < COOLDOWN_SECONDS:
            return
    last_alert_time[cooldown_key] = now

    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/v1/alerts",
            json=fault,
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Alert sent → {fault['compressor_id']} | {fault['fault_type']} | SF Case: {data.get('sf_case_number', 'N/A')}")
        else:
            print(f"Alert failed → status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Alert error → {e}")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Edge Processor connected to HiveMQ")
        client.subscribe("sensors/plant-01/#", qos=1)
        print("Subscribed to sensors/plant-01/#")
    else:
        print(f"Edge Processor connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        reading = json.loads(msg.payload.decode())
        print(f"Received → {msg.topic} | temp={reading['temperature']}°C | vib={reading['vibration']} mm/s | pres={reading['pressure']} bar")
        faults = evaluate_reading(reading)
        for fault in faults:
            print(f"FAULT DETECTED → {fault['compressor_id']} | {fault['fault_type']} | severity={fault['severity']}")
            send_alert(fault)
    except Exception as e:
        print(f"Message processing error → {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="iot-edge-processor")
client.username_pw_set(HIVEMQ_USERNAME, HIVEMQ_PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
client.on_connect = on_connect
client.on_message = on_message

client.connect(HIVEMQ_HOST, HIVEMQ_PORT, keepalive=60)

print("Edge Processor starting...")
client.loop_forever()