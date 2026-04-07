# CHANGELOG — SMILE-IoT Dashboard

---

## [2026-04-07 — (software/utils/data.py)]
**Created new module.** Extracted all constants (`GRID_VOLTAGE`, `SENSOR_MAX_A`, `MAX_BUFFER_SIZE`, `COST_PER_KWH`) and the three data-generation functions (`generate_realtime_data`, `generate_daily_data`, `zero_rt_df`) from `app.py` into a standalone utility module. This module has zero Streamlit imports, making it independently unit-testable.

## [2026-04-07 — (software/utils/mqtt_client.py)]
**Created new module.** Extracted all MQTT logic from `app.py`: module-level `queue.Queue` and connection-state dict, the three paho callbacks (`_on_connect`, `_on_disconnect`, `_on_message`), the connection lifecycle helpers (`connect_mqtt`, `disconnect_mqtt`), the thread-boundary sync function (`sync_mqtt`), and session-state initialisation (`init_session_state`). Public API uses clean names without leading underscores.

## [2026-04-07 — (software/utils/__init__.py)]
**Created empty package init** to make `utils/` importable as a Python package.

## [2026-04-07 — (software/app.py)]
**Refactored into a thin UI orchestrator.** Removed all MQTT logic and data-generation functions. The file now only contains Streamlit layout code (sidebar, KPIs, charts, roadmap, auto-refresh) and imports business logic from `utils.data` and `utils.mqtt_client`. Reduced from ~527 lines to ~210 lines. Bumped version tag to v0.2.0.

## [2026-04-07 — (software/CHANGELOG.md)]
**Created this changelog file** to track all modifications to the SMILE-IoT dashboard codebase.

---

## [2026-04-07 — (software/app.py)]
**Added MQTT subscriber integration.** Implemented full paho-mqtt subscriber lifecycle: connect/disconnect buttons in the sidebar, connection status badges (Connected / Not Connected / Error), thread-safe message queue bridging paho's background thread to Streamlit's main thread via `_sync_mqtt()`, three-state data resolution (simulated / live MQTT / zeros while waiting), and an auto-refresh countdown loop. Messages expected in JSON format matching `generate_realtime_data` schema.

## [2026-04-07 — (software/app.py)]
**Initial dashboard creation.** Built Streamlit dashboard with KPI row (current, power, energy, cost), realtime power/current charts, daily energy bar chart with cost table, system architecture diagram, and feature roadmap table. Simulated data generators for demo purposes. Dark theme via `.streamlit/config.toml`.

## [2026-04-07 — (software/.streamlit/config.toml)]
**Created Streamlit theme configuration.** Dark theme with blue primary color (`#2196F3`), dark background, and sans-serif font.

## [2026-04-07 — (software/requirements.txt)]
**Created Python dependencies file.** Listed streamlit, pandas, numpy, and paho-mqtt as project requirements.
