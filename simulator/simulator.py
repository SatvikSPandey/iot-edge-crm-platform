import paho.mqtt.client as mqtt
import json
import time
import random
import ssl
import os
import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'imp', '.env'))

HIVEMQ_HOST = os.getenv("HIVEMQ_HOST")
HIVEMQ_PORT = int(os.getenv("HIVEMQ_PORT"))
HIVEMQ_USERNAME = os.getenv("HIVEMQ_USERNAME")
HIVEMQ_PASSWORD = os.getenv("HIVEMQ_PASSWORD")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

COMPRESSORS = [
    {"id": "compressor-1", "base_temp": 72.0, "base_vibration": 2.1, "base_pressure": 8.5, "runtime": 1200.0},
    {"id": "compressor-2", "base_temp": 68.0, "base_vibration": 1.8, "base_pressure": 8.8, "runtime": 980.0},
    {"id": "compressor-3", "base_temp": 75.0, "base_vibration": 2.4, "base_pressure": 8.2, "runtime": 2100.0},
    {"id": "compressor-4", "base_temp": 70.0, "base_vibration": 2.0, "base_pressure": 8.6, "runtime": 450.0},
    {"id": "compressor-5", "base_temp": 73.0, "base_vibration": 2.2, "base_pressure": 8.4, "runtime": 1750.0},
]

def generate_reading(compressor):
    fault_chance = random.random()
    
    if fault_chance < 0.05:
        temperature = compressor["base_temp"] + random.uniform(20.0, 35.0)
    else:
        temperature = compressor["base_temp"] + random.uniform(-2.0, 4.0)

    if fault_chance < 0.04:
        vibration = compressor["base_vibration"] + random.uniform(5.0, 10.0)
    else:
        vibration = compressor["base_vibration"] + random.uniform(-0.3, 0.5)

    if fault_chance < 0.04:
        pressure = compressor["base_pressure"] - random.uniform(3.0, 5.0)
    else:
        pressure = compressor["base_pressure"] + random.uniform(-0.3, 0.3)

    compressor["runtime"] += round(random.uniform(0.001, 0.003), 3)

    return {
        "compressor_id": compressor["id"],
        "temperature": round(temperature, 2),
        "vibration": round(vibration, 2),
        "pressure": round(pressure, 2),
        "runtime_hours": round(compressor["runtime"], 3),
        "timestamp": time.time()
    }

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Simulator connected to HiveMQ")
    else:
        print(f"Simulator connection failed with code {rc}")

def on_publish(client, userdata, mid, reason_code=None, properties=None):
    pass

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="iot-simulator")
client.username_pw_set(HIVEMQ_USERNAME, HIVEMQ_PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
client.on_connect = on_connect
client.on_publish = on_publish

client.connect(HIVEMQ_HOST, HIVEMQ_PORT, keepalive=60)
client.loop_start()

print("IoT Simulator starting — publishing every 5 seconds")

try:
    while True:
        for compressor in COMPRESSORS:
            reading = generate_reading(compressor)
            topic = f"sensors/plant-01/{compressor['id']}"
            payload = json.dumps(reading)
            client.publish(topic, payload, qos=1)
            print(f"Published → {topic} | temp={reading['temperature']}°C | vib={reading['vibration']} mm/s | pres={reading['pressure']} bar")
            try:
                httpx.post(f"{BACKEND_URL}/api/v1/readings", json=reading, timeout=5.0)
            except Exception:
                pass
        time.sleep(5)
except KeyboardInterrupt:
    print("Simulator stopped")
    client.loop_stop()
    client.disconnect()