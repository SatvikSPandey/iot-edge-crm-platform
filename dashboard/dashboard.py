import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'imp', '.env'))

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="IoT Edge CRM Integration Platform",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5986 100%);
        padding: 20px;
        border-radius: 12px;
        margin: 8px 0;
        border-left: 4px solid #4a9eff;
    }
    .fault-critical {
        background-color: #ff4444;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 12px;
    }
    .fault-high {
        background-color: #ff8800;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 12px;
    }
    .status-healthy {
        color: #00cc66;
        font-weight: bold;
    }
    .status-fault {
        color: #ff4444;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏭 IoT Edge Computing & Salesforce CRM Integration Platform")
st.markdown("**Real-time industrial compressor monitoring with automated Salesforce Case generation**")

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/320px-Salesforce.com_logo.svg.png", width=160)
    st.markdown("### 🔧 System Status")
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if health.status_code == 200:
            st.success("✅ API Backend: Online")
        else:
            st.error("❌ API Backend: Error")
    except:
        st.error("❌ API Backend: Offline")

    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    st.markdown(f"**MQTT Broker:** HiveMQ Cloud")
    st.markdown(f"**Database:** Supabase PostgreSQL")
    st.markdown(f"**CRM:** Salesforce Developer Edition")
    st.markdown("---")
    refresh_rate = st.slider("Refresh rate (seconds)", min_value=5, max_value=60, value=10)
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    st.markdown("---")
    st.markdown("**Built by Satvik Pandey**")
    st.markdown("[GitHub](https://github.com/SatvikSPandey) | [Portfolio](https://satvikspandey.netlify.app)")

tab1, tab2, tab3 = st.tabs(["📡 Live Sensor Dashboard", "⚠️ Fault Alert Log", "📋 Salesforce Cases"])

with tab1:
    st.subheader("Live Compressor Sensor Readings")
    st.caption("Readings refresh automatically. Fault thresholds: Temperature > 85°C | Vibration > 6.0 mm/s | Pressure < 5.5 bar")

    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/readings/latest", timeout=10)
        readings = response.json().get("readings", [])

        if not readings:
            st.info("No sensor readings yet. Start the IoT simulator to begin receiving data.")
        else:
            for reading in readings:
                cid = reading["compressor_id"]
                temp = reading["temperature"]
                vib = reading["vibration"]
                pres = reading["pressure"]
                runtime = reading["runtime_hours"]

                temp_fault = temp >= 85.0
                vib_fault = vib >= 6.0
                pres_fault = pres <= 5.5
                any_fault = temp_fault or vib_fault or pres_fault

                status_label = "🔴 FAULT" if any_fault else "🟢 HEALTHY"

                with st.expander(f"{cid.upper()} — {status_label} | Runtime: {runtime:.1f} hrs", expanded=True):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        delta_color = "inverse" if temp_fault else "normal"
                        st.metric(
                            label="🌡️ Temperature",
                            value=f"{temp:.1f} °C",
                            delta=f"{'⚠️ ABOVE' if temp_fault else 'Normal'} threshold (85°C)",
                            delta_color=delta_color
                        )

                    with col2:
                        delta_color = "inverse" if vib_fault else "normal"
                        st.metric(
                            label="📳 Vibration",
                            value=f"{vib:.2f} mm/s",
                            delta=f"{'⚠️ ABOVE' if vib_fault else 'Normal'} threshold (6.0 mm/s)",
                            delta_color=delta_color
                        )

                    with col3:
                        delta_color = "inverse" if pres_fault else "normal"
                        st.metric(
                            label="💨 Pressure",
                            value=f"{pres:.2f} bar",
                            delta=f"{'⚠️ BELOW' if pres_fault else 'Normal'} threshold (5.5 bar)",
                            delta_color=delta_color
                        )

                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=temp,
                        title={"text": "Temperature (°C)"},
                        gauge={
                            "axis": {"range": [0, 130]},
                            "bar": {"color": "#ff4444" if temp_fault else "#00cc66"},
                            "steps": [
                                {"range": [0, 85], "color": "#1e3a5f"},
                                {"range": [85, 95], "color": "#ff8800"},
                                {"range": [95, 130], "color": "#ff2222"},
                            ],
                            "threshold": {
                                "line": {"color": "white", "width": 2},
                                "thickness": 0.75,
                                "value": 85
                            }
                        }
                    ))
                    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)", font_color="white")
                    st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching readings: {e}")

with tab2:
    st.subheader("Fault Alert Log")
    st.caption("All faults detected by the edge processor. Each fault triggered an automatic Salesforce Case.")

    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/alerts", timeout=10)
        alerts = response.json().get("alerts", [])

        if not alerts:
            st.info("No fault alerts yet. The edge processor will populate this when faults are detected.")
        else:
            total = len(alerts)
            critical = sum(1 for a in alerts if a["severity"] == "Critical")
            high = sum(1 for a in alerts if a["severity"] == "High")

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Alerts", total)
            col2.metric("Critical", critical)
            col3.metric("High", high)

            df = pd.DataFrame(alerts)
            df = df[["created_at", "compressor_id", "fault_type", "severity", "sensor_value", "threshold_value", "sf_case_number"]]
            df.columns = ["Timestamp", "Compressor", "Fault Type", "Severity", "Sensor Value", "Threshold", "SF Case #"]
            df["Timestamp"] = pd.to_datetime(df["Timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")

            st.dataframe(df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error fetching alerts: {e}")

with tab3:
    st.subheader("Salesforce Cases")
    st.caption("Cases automatically created in Salesforce when faults are detected. Click case links to open in Salesforce.")

    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/cases", timeout=10)
        cases = response.json().get("cases", [])

        if not cases:
            st.info("No Salesforce Cases yet. Cases are created automatically when the edge processor detects faults.")
        else:
            st.markdown(f"**{len(cases)} Cases created in Salesforce**")

            for case in cases:
                severity_color = "🔴" if case["severity"] == "Critical" else "🟠"
                with st.expander(f"{severity_color} Case #{case['sf_case_number']} — {case['fault_type'].replace('_', ' ')} on {case['compressor_id']}", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Compressor:** {case['compressor_id']}")
                        st.markdown(f"**Fault Type:** {case['fault_type'].replace('_', ' ')}")
                        st.markdown(f"**Severity:** {case['severity']}")
                        st.markdown(f"**Sensor Value:** {case['sensor_value']}")
                        st.markdown(f"**Threshold:** {case['threshold_value']}")
                    with col2:
                        st.markdown(f"**SF Case ID:** {case['sf_case_id']}")
                        st.markdown(f"**SF Case #:** {case['sf_case_number']}")
                        st.markdown(f"**Detected At:** {case['created_at']}")
                        if case.get("sf_case_url"):
                            st.link_button("🔗 Open in Salesforce", case["sf_case_url"])

    except Exception as e:
        st.error(f"Error fetching cases: {e}")

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()