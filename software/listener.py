"""
MQTT Listener - SMILE-IoT Telemetry Ingestion Daemon

Subscribes to the MQTT broker topic published by the ESP32 and
persists power-consumption payloads to data.json for the dashboard.
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "smile-iot/power")
DATA_FILE = Path(__file__).parent / "data.json"
MAX_RECORDS = 50_000
_lock = threading.Lock()


def _load_records():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_records(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f)


def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "irms_a": payload.get("irms", 0.0),
        "power_w": payload.get("power_w", 0.0),
        "voltage_v": payload.get("voltage", 220.0),
    }

    with _lock:
        records = _load_records()
        records.append(record)
        if len(records) > MAX_RECORDS:
            records = records[-MAX_RECORDS:]
        _save_records(records)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    main()