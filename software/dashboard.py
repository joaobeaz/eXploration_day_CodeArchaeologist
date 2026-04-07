"""
SMILE-IoT Power Monitoring Dashboard

Streamlit web interface for real-time visualization of AC power consumption
data collected by the ESP32 + SCT-013 sensor system.

Usage:
    streamlit run dashboard.py
"""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SMILE-IoT | Power Monitor",
    page_icon=":material/bolt:",
    layout="wide",
)

DATA_FILE = Path(__file__).parent / "data.json"
CHART_HEIGHT = 300


# =============================================================================
# Data Loading
# =============================================================================


def _generate_synthetic_data() -> pd.DataFrame:
    """Generate 7 days of realistic power-consumption demo data."""
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    timestamps = pd.date_range(
        end=now, periods=7 * 24 * 60, freq="min"  # 1-min resolution, 7 days
    )

    hours = timestamps.hour + timestamps.minute / 60.0

    # Daily pattern: low at night, peak mid-day
    base_power = 60 + 120 * np.exp(-0.5 * ((hours - 13) / 4) ** 2)
    noise = np.random.normal(0, 8, len(timestamps))
    power_w = np.clip(base_power + noise, 5, 400)

    voltage = 220 + np.random.normal(0, 2, len(timestamps))
    irms = power_w / voltage

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "power_w": np.round(power_w, 2),
            "irms_a": np.round(irms, 3),
            "voltage_v": np.round(voltage, 1),
        }
    )


@st.cache_data(ttl=5)
def load_data() -> pd.DataFrame:
    """Load data from JSON store or fall back to synthetic demo data."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
            if records:
                df = pd.DataFrame(records)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                return df
        except (json.JSONDecodeError, KeyError):
            pass

    return _generate_synthetic_data()


# =============================================================================
# Filtering
# =============================================================================

TIME_RANGES = {
    "15min": timedelta(minutes=15),
    "1H": timedelta(hours=1),
    "6H": timedelta(hours=6),
    "24H": timedelta(hours=24),
    "7D": timedelta(days=7),
    "All": None,
}


def filter_by_time_range(df: pd.DataFrame, time_range: str) -> pd.DataFrame:
    if time_range == "All" or df.empty:
        return df
    delta = TIME_RANGES.get(time_range)
    if delta is None:
        return df
    cutoff = df["timestamp"].max() - delta
    return df[df["timestamp"] >= cutoff]


# =============================================================================
# Chart Helpers
# =============================================================================


def power_chart(df: pd.DataFrame) -> alt.Chart:
    """Power consumption line chart with 1-hour moving average."""
    df = df.copy()
    df["power_1h_ma"] = df["power_w"].rolling(60, min_periods=1).mean()

    melted = df.melt(
        id_vars=["timestamp"],
        value_vars=["power_w", "power_1h_ma"],
        var_name="series",
        value_name="value",
    )
    melted["series"] = melted["series"].map(
        {"power_w": "Instantaneous", "power_1h_ma": "1-Hour MA"}
    )

    return (
        alt.Chart(melted)
        .mark_line()
        .encode(
            x=alt.X("timestamp:T", title=None),
            y=alt.Y("value:Q", title="Power (W)", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "series:N", title=None, legend=alt.Legend(orient="bottom")
            ),
            strokeDash=alt.condition(
                alt.datum.series == "1-Hour MA",
                alt.value([5, 5]),
                alt.value([0]),
            ),
            tooltip=[
                alt.Tooltip("timestamp:T", title="Time", format="%Y-%m-%d %H:%M"),
                alt.Tooltip("series:N", title="Series"),
                alt.Tooltip("value:Q", title="Watts", format=",.1f"),
            ],
        )
        .properties(height=CHART_HEIGHT)
    )


def current_chart(df: pd.DataFrame) -> alt.Chart:
    """RMS current line chart."""
    return (
        alt.Chart(df)
        .mark_line(color="#e45756")
        .encode(
            x=alt.X("timestamp:T", title=None),
            y=alt.Y("irms_a:Q", title="Current (A)", scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip("timestamp:T", title="Time", format="%Y-%m-%d %H:%M"),
                alt.Tooltip("irms_a:Q", title="Amps", format=".3f"),
            ],
        )
        .properties(height=CHART_HEIGHT)
    )


def voltage_chart(df: pd.DataFrame) -> alt.Chart:
    """Voltage stability chart."""
    return (
        alt.Chart(df)
        .mark_line(color="#54a24b")
        .encode(
            x=alt.X("timestamp:T", title=None),
            y=alt.Y(
                "voltage_v:Q",
                title="Voltage (V)",
                scale=alt.Scale(zero=False),
            ),
            tooltip=[
                alt.Tooltip("timestamp:T", title="Time", format="%Y-%m-%d %H:%M"),
                alt.Tooltip("voltage_v:Q", title="Volts", format=".1f"),
            ],
        )
        .properties(height=200)
    )


# =============================================================================
# Sidebar
# =============================================================================

with st.sidebar:
    st.markdown("# :material/bolt: SMILE-IoT")
    st.caption("Non-Invasive AC Energy Monitor")
    st.divider()

    time_range = st.segmented_control(
        "Time Range",
        options=list(TIME_RANGES.keys()),
        default="24H",
    )

    auto_refresh = st.checkbox("Auto-refresh (every 5 s)", value=False)
    if auto_refresh:
        st.caption("Page will rerun automatically.")

    st.divider()
    st.markdown(
        "**Sensor:** SCT-013-030  \n"
        "**MCU:** ESP32 DevKit V1  \n"
        "**Protocol:** MQTT"
    )


# =============================================================================
# Main Layout
# =============================================================================

df = load_data()
filtered = filter_by_time_range(df, time_range)

if filtered.empty:
    st.warning("No data available for the selected time range.")
    st.stop()

latest = filtered.iloc[-1]
avg_power = filtered["power_w"].mean()
peak_power = filtered["power_w"].max()
avg_current = filtered["irms_a"].mean()

# Estimate daily kWh from average power
hours_in_range = (
    (filtered["timestamp"].max() - filtered["timestamp"].min()).total_seconds() / 3600
)
if hours_in_range > 0:
    total_kwh = (filtered["power_w"].sum() / len(filtered)) * hours_in_range / 1000
    daily_kwh = total_kwh / max(hours_in_range / 24, 1)
else:
    daily_kwh = 0.0

# Sparkline data (last 60 readings)
spark_power = filtered["power_w"].tail(60).tolist()
spark_current = filtered["irms_a"].tail(60).tolist()

# ---- KPI Row ----
st.markdown("## :material/monitoring: Power Dashboard")

with st.container(horizontal=True):
    st.metric(
        "Current Power",
        f"{latest['power_w']:.1f} W",
        border=True,
        chart_data=spark_power,
        chart_type="line",
    )
    st.metric(
        "Average Power",
        f"{avg_power:.1f} W",
        border=True,
        chart_data=spark_power,
        chart_type="line",
    )
    st.metric(
        "Peak Power",
        f"{peak_power:.1f} W",
        border=True,
        chart_data=spark_power,
        chart_type="bar",
    )
    st.metric(
        "Current (Irms)",
        f"{latest['irms_a']:.3f} A",
        border=True,
        chart_data=spark_current,
        chart_type="line",
    )
    st.metric(
        "Est. Daily kWh",
        f"{daily_kwh:.2f}",
        border=True,
    )

# ---- Charts ----
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("Power Consumption")
        st.altair_chart(power_chart(filtered))

with col2:
    with st.container(border=True):
        st.subheader("RMS Current")
        st.altair_chart(current_chart(filtered))

with st.container(border=True):
    st.subheader("Voltage Stability")
    st.altair_chart(voltage_chart(filtered))

# ---- Future Features ----
with st.expander(":material/lightbulb: Planned Features & Enhancements"):
    feat_col1, feat_col2 = st.columns(2)
    with feat_col1:
        st.markdown(
            """
            **Real-time Alerts**
            - Overcurrent threshold notifications
            - Overvoltage / undervoltage alerts
            - Configurable alert channels (email, webhook)

            **Multi-sensor Support**
            - Monitor multiple circuits simultaneously
            - Per-circuit dashboards and breakdowns
            - Aggregate whole-building view

            **Energy Cost Calculator**
            - Customizable electricity tariff rates
            - Time-of-use pricing support
            - Monthly cost projections and billing estimates
            """
        )
    with feat_col2:
        st.markdown(
            """
            **Data Export & Reporting**
            - Export filtered data to CSV / Excel
            - Scheduled PDF reports via email
            - API endpoint for third-party integrations

            **Power Factor Monitoring**
            - Add voltage waveform sensing
            - Calculate true power factor (cos phi)
            - Reactive power (VAR) tracking

            **Anomaly Detection**
            - ML-based consumption profiling
            - Detect unusual spikes or equipment faults
            - Predictive maintenance suggestions
            """
        )

# ---- Recent Readings Table ----
with st.container(border=True):
    st.subheader("Recent Readings")
    display_df = filtered.tail(100).sort_values("timestamp", ascending=False)
    st.dataframe(
        display_df,
        column_config={
            "timestamp": st.column_config.DatetimeColumn(
                "Timestamp", format="YYYY-MM-DD HH:mm:ss"
            ),
            "power_w": st.column_config.NumberColumn("Power (W)", format="%.1f"),
            "irms_a": st.column_config.NumberColumn("Current (A)", format="%.3f"),
            "voltage_v": st.column_config.NumberColumn("Voltage (V)", format="%.1f"),
        },
        hide_index=True,
    )

# ---- Auto-refresh ----
if auto_refresh:
    import time

    time.sleep(5)
    st.rerun()