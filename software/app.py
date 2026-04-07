"""
SMILE-IoT Dashboard
Energy Monitoring and Inspection System — Real-time power consumption dashboard.

This dashboard displays power consumption data from the SMILE-IoT system
(ESP32 + SCT-013 current sensor). It uses simulated data by default and can
be connected to a live MQTT broker for real-time readings.
"""

import datetime
import math

import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SMILE-IoT Dashboard",
    page_icon=":material/electric_bolt:",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Simulated data helpers
# ---------------------------------------------------------------------------

GRID_VOLTAGE = 127  # Typical Brazilian grid voltage (V)
SENSOR_MAX_A = 30   # SCT-013-030 rated current


@st.cache_data(ttl=5)
def generate_realtime_data(minutes: int = 60) -> pd.DataFrame:
    """Generate synthetic current/power readings as if coming from the ESP32."""
    now = datetime.datetime.now()
    timestamps = pd.date_range(end=now, periods=minutes, freq="min")
    np.random.seed(now.minute)
    # Simulate a base load + periodic spikes (e.g. appliance cycles)
    base_current = 2.5 + 0.5 * np.sin(np.linspace(0, 4 * math.pi, minutes))
    noise = np.random.normal(0, 0.15, minutes)
    spikes = np.where(np.random.random(minutes) > 0.92, np.random.uniform(3, 8, minutes), 0)
    current_rms = np.clip(base_current + noise + spikes, 0.1, SENSOR_MAX_A)
    power_w = current_rms * GRID_VOLTAGE
    return pd.DataFrame({
        "timestamp": timestamps,
        "current_rms_A": np.round(current_rms, 3),
        "power_W": np.round(power_w, 2),
        "voltage_V": GRID_VOLTAGE,
    })


@st.cache_data(ttl=60)
def generate_daily_data(days: int = 30) -> pd.DataFrame:
    """Generate daily energy consumption summary (kWh)."""
    today = datetime.date.today()
    dates = pd.date_range(end=today, periods=days, freq="D")
    np.random.seed(today.day)
    base_kwh = 3.5 + 1.2 * np.sin(np.linspace(0, 2 * math.pi, days))
    noise = np.random.normal(0, 0.4, days)
    kwh = np.clip(base_kwh + noise, 0.5, 12)
    cost_per_kwh = 0.25  # BRL approximation
    return pd.DataFrame({
        "date": dates,
        "energy_kWh": np.round(kwh, 2),
        "cost_PT": np.round(kwh * cost_per_kwh, 2),
    })


# ---------------------------------------------------------------------------
# Sidebar — global filters & settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## :material/electric_bolt: SMILE-IoT")
    st.caption("Local Energy Monitoring & Inspection System")

    st.markdown("---")
    data_source = st.radio(
        "Data source",
        ["Simulated", "MQTT (live)"],
        index=0,
        help="Switch to MQTT when the ESP32 broker is running.",
    )

    if data_source == "MQTT (live)":
        mqtt_host = st.text_input("Broker host", value="localhost")
        mqtt_port = st.number_input("Broker port", value=1883, min_value=1, max_value=65535)
        mqtt_topic = st.text_input("Topic", value="smile-iot/power")
        st.warning("MQTT integration is a placeholder — connect your broker to enable live data.")

    st.markdown("---")
    history_window = st.text_input("Realtime window", value="60 min")
    daily_days = st.slider("Daily history (days)", min_value=7, max_value=90, value=30)

    st.markdown("---")
    st.caption("v0.1.0 — SMILE-IoT Prototype")

# Resolve filter values
rt_minutes = int(history_window.split()[0])

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
rt_df = generate_realtime_data(rt_minutes)
daily_df = generate_daily_data(daily_days)

latest = rt_df.iloc[-1]
current_now = latest["current_rms_A"]
power_now = latest["power_W"]

avg_power = rt_df["power_W"].mean()
max_power = rt_df["power_W"].max()
total_kwh_today = daily_df.iloc[-1]["energy_kWh"]
total_cost_today = daily_df.iloc[-1]["cost_PT"]

# Sparkline data
power_trend = rt_df["power_W"].tolist()[-20:]
daily_trend = daily_df["energy_kWh"].tolist()[-14:]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title(":material/electric_bolt: SMILE-IoT energy dashboard")
st.caption(
    f"Last reading: {latest['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}  ·  "
    f"Grid voltage: {GRID_VOLTAGE} V  ·  Sensor: SCT-013-030"
)

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
with st.container(horizontal=True):
    st.metric(
        "Current (RMS)",
        f"{current_now:.2f} A",
        f"{current_now - rt_df['current_rms_A'].iloc[-2]:.2f} A",
        border=True,
    )
    st.metric(
        "Instant power",
        f"{power_now:.0f} W",
        f"{power_now - rt_df['power_W'].iloc[-2]:.0f} W",
        border=True,
    )
    st.metric(
        "Avg power ({} min)".format(rt_minutes),
        f"{avg_power:.0f} W",
        border=True,
    )
    st.metric(
        "Peak power",
        f"{max_power:.0f} W",
        border=True,
    )
    st.metric(
        "Energy today",
        f"{total_kwh_today:.2f} kWh",
        f"R$ {total_cost_today:.2f}",
        border=True,
    )

# ---------------------------------------------------------------------------
# Realtime charts
# ---------------------------------------------------------------------------
col_power, col_current = st.columns(2)

with col_power:
    with st.container(border=True):
        st.subheader("Power consumption (W)")
        st.area_chart(rt_df, x="timestamp", y="power_W", color="#2196F3")

with col_current:
    with st.container(border=True):
        st.subheader("Current draw (A)")
        st.line_chart(rt_df, x="timestamp", y="current_rms_A", color="#FF9800")

# ---------------------------------------------------------------------------
# Daily energy history
# ---------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Daily energy consumption")
    col_bar, col_cost = st.columns([3, 1])
    with col_bar:
        st.bar_chart(daily_df, x="date", y="energy_kWh", color="#4CAF50")
    with col_cost:
        st.dataframe(
            daily_df.sort_values("date", ascending=False).head(10),
            column_config={
                "date": st.column_config.DateColumn("Date", format="MMM DD"),
                "energy_kWh": st.column_config.NumberColumn("Energy", format="%.2f kWh"),
                "cost_BRL": st.column_config.NumberColumn("Cost", format="R$ %.2f"),
            },
            hide_index=True,
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# System architecture reference
# ---------------------------------------------------------------------------
with st.expander(":material/architecture: System architecture"):
    st.code("""
[ AC Electrical Grid ]
       │
       ▼ (Magnetic Field)
┌────────────────────┐     ┌──────────────────────┐     ┌────────────────────┐
│ 1. SCT-013 Sensor  ├────►│ 2. Signal            ├────►│ 3. Microcontroller │
│ (Current           │     │ Conditioning         │     │ ESP32 (12-bit ADC) │
│  Transformer       │     │ (Voltage Divider +   │     │ RMS Processing     │
│  30A/1V)           │     │  DC Offset Filter)   │     │                    │
└────────────────────┘     └──────────────────────┘     └─────────┬──────────┘
                                                                   │
                                                                   ▼ (Wi-Fi / MQTT)
┌────────────────────┐     ┌──────────────────────┐     ┌────────────────────┐
│ 6. End User        │◄────┤ 5. Web Dashboard     │◄────┤ 4. IoT Server      │
│ (Browser/Mobile)   │     │ (Real-Time Charts)   │     │ (Broker/Backend)   │
└────────────────────┘     └──────────────────────┘     └────────────────────┘
""", language="text")

# ---------------------------------------------------------------------------
# Proposed features — roadmap section
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader(":material/rocket_launch: Feature roadmap")
st.caption("Possible enhancements for future iterations of SMILE-IoT.")

roadmap = [
    {
        "feature": ":material/wifi: Live MQTT integration",
        "description": "Connect directly to the ESP32 MQTT broker for real-time streaming data instead of simulated values.",
        "status": "Planned",
        "priority": "High",
    },
    {
        "feature": ":material/notifications_active: Consumption alerts",
        "description": "Configurable thresholds to trigger notifications when power exceeds a set limit (e.g. > 2 kW).",
        "status": "Planned",
        "priority": "High",
    },
    {
        "feature": ":material/analytics: Appliance detection",
        "description": "Use current waveform signatures (NILM - Non-Intrusive Load Monitoring) to identify which appliances are running.",
        "status": "Research",
        "priority": "Medium",
    },
    {
        "feature": ":material/history: Historical data export",
        "description": "Export consumption data to CSV/Excel for external analysis or compliance reporting.",
        "status": "Planned",
        "priority": "Medium",
    },
    {
        "feature": ":material/database: Persistent storage",
        "description": "Store readings in SQLite or InfluxDB for long-term trend analysis and auditing.",
        "status": "Planned",
        "priority": "High",
    },
    {
        "feature": ":material/co2: Carbon footprint estimation",
        "description": "Estimate CO₂ emissions based on regional grid emission factors and measured consumption.",
        "status": "Idea",
        "priority": "Low",
    },
    {
        "feature": ":material/sensors: Multi-sensor support",
        "description": "Monitor multiple circuits simultaneously with different SCT-013 sensors on separate ADC channels.",
        "status": "Idea",
        "priority": "Medium",
    },
    {
        "feature": ":material/smartphone: Mobile-friendly layout",
        "description": "Responsive design optimizations for viewing the dashboard on phones and tablets.",
        "status": "Planned",
        "priority": "Low",
    },
]

roadmap_df = pd.DataFrame(roadmap)
st.dataframe(
    roadmap_df,
    column_config={
        "feature": st.column_config.TextColumn("Feature", width="medium"),
        "description": st.column_config.TextColumn("Description", width="large"),
        "status": st.column_config.TextColumn("Status"),
        "priority": st.column_config.TextColumn("Priority"),
    },
    hide_index=True,
    use_container_width=True,
)
