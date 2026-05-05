import httpx
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', 'imp', '.env'))

SF_CLIENT_ID = os.getenv("SF_CLIENT_ID")
SF_CLIENT_SECRET = os.getenv("SF_CLIENT_SECRET")
SF_LOGIN_URL = os.getenv("SF_LOGIN_URL")
SF_INSTANCE_URL = os.getenv("SF_INSTANCE_URL")
SF_ACCOUNT_ID = os.getenv("SF_ACCOUNT_ID")

_access_token = None
_token_expiry = 0

import time

def get_access_token() -> str:
    global _access_token, _token_expiry
    if _access_token and time.time() < _token_expiry:
        return _access_token

    response = httpx.post(
        f"{SF_LOGIN_URL}/services/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": SF_CLIENT_ID,
            "client_secret": SF_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15.0
    )

    if response.status_code != 200:
        raise Exception(f"Salesforce token error: {response.status_code} — {response.text}")

    token_data = response.json()
    _access_token = token_data["access_token"]
    _token_expiry = time.time() + 3600
    return _access_token


def create_case(compressor_id: str, fault_type: str, severity: str, sensor_value: float, threshold_value: float) -> dict:
    token = get_access_token()

    severity_to_priority = {
        "Critical": "P1 - Critical",
        "High": "P2 - High",
        "Medium": "P3 - Medium",
        "Low": "P4 - Low"
    }

    fault_descriptions = {
        "HIGH_TEMPERATURE": f"Compressor temperature reached {sensor_value}°C, exceeding the {threshold_value}°C threshold. Immediate inspection required to prevent equipment damage.",
        "VIBRATION_SPIKE": f"Abnormal vibration detected at {sensor_value} mm/s, exceeding the {threshold_value} mm/s threshold. Bearing or alignment failure suspected.",
        "PRESSURE_DROP": f"System pressure dropped to {sensor_value} bar, below the {threshold_value} bar minimum threshold. Check for leaks or valve failure."
    }

    case_payload = {
        "Subject": f"[{severity.upper()}] {fault_type.replace('_', ' ')} — {compressor_id}",
        "Description": fault_descriptions.get(fault_type, f"Fault detected on {compressor_id}: {fault_type}"),
        "Status": "New",
        "Priority": severity_to_priority.get(severity, "P3 - Medium"),
        "Origin": "IoT Edge Processor",
        "AccountId": SF_ACCOUNT_ID,
        "Type": "Mechanical"
    }

    response = httpx.post(
        f"{SF_INSTANCE_URL}/services/data/v63.0/sobjects/Case",
        json=case_payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        timeout=15.0
    )

    if response.status_code not in (200, 201):
        raise Exception(f"Salesforce Case creation error: {response.status_code} — {response.text}")

    case_data = response.json()
    case_id = case_data["id"]

    case_url = f"{SF_INSTANCE_URL}/lightning/r/Case/{case_id}/view"

    case_detail = httpx.get(
        f"{SF_INSTANCE_URL}/services/data/v63.0/sobjects/Case/{case_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15.0
    )
    case_number = case_detail.json().get("CaseNumber", "N/A")

    return {
        "sf_case_id": case_id,
        "sf_case_number": case_number,
        "sf_case_url": case_url
    }