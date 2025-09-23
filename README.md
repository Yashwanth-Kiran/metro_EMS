<<<<<<< HEAD
# metro_EMS

This repository contains a React frontend and a Python FastAPI backend for MetroEMS Station Radios monitoring and management.

## Structure

- `MetroEMS-main/` — React frontend (Create React App + Tailwind)
- `Backend_for_station_Radios/` — FastAPI backend (discovery, sessions, monitoring, logs)

## Quick Start

### Frontend (Dev)

Windows PowerShell from repo root:

```
./start_frontend.bat
# or
./start_frontend_real.bat
```

### Backend (Dev)

From `Backend_for_station_Radios`:

```
pip install fastapi uvicorn pydantic python-multipart
uvicorn real_backend:app --reload --host 0.0.0.0 --port 8000
```

Or run from repo root on Windows:

```
./start_backend.bat
```

## Notes

- Device discovery uses ARP + ping; you can pin a device via environment variables:
  - `METRO_STATION_RADIO_IP` and optional `METRO_STATION_RADIO_MAC`
- The frontend only lists reachable Station Radios (no simulated devices).
 - Monitoring and Logs endpoints update every second; values include light jitter so charts visibly move.
=======
# metro_EMS
>>>>>>> b1dd6255ffcc731257ad6121de6fa7308dbac9ba
