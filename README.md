# livehaul-server

Backend game server for **LiveHaul** — a real-world logistics management game.

Runs on a Raspberry Pi (or any machine). All connected browsers receive live vehicle
positions via WebSocket. Vehicles follow real roads using OpenStreetMap + OSRM.

**Client repo:** [livehaul-client](https://github.com/gerbain/livehaul-client)

---

## Stack

| Component | Technology |
|---|---|
| Game server | Python 3.11 + FastAPI |
| Real-time | WebSockets |
| Routing | OSRM (local Docker) |
| Map data | OpenStreetMap — Belgium |
| Database | SQLite |
| Config | YAML with hot-reload |

---

## Quick Start (PC — development)

**Requirements:** Python 3.11+, Docker Desktop

```bash
git clone https://github.com/gerbain/livehaul-server
cd livehaul-server

# Python environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Prepare map data once (~10 min, needs Docker)
./tools/prepare_map.sh

# Start OSRM
docker-compose up osrm -d

# Run server with hot-reload
uvicorn server.main:app --reload --port 8000
```

Visit http://localhost:8000/health — should show `"osrm": "ok"`

---

## Config Files

Edit any file in `config/` — most changes apply live without a restart.

| File | Controls |
|---|---|
| `game.yaml` | Tick rate, time scale, starting money |
| `vehicles.yaml` | Vehicle types, stats, costs, icons |
| `economy.yaml` | Pay rates, fuel costs, XP progression |
| `map.yaml` | OSRM connection, region, map defaults |
| `regions.yaml` | Playing zones, POI types for job generation |
| `traffic.yaml` | Rush hours, accidents, breakdowns |
| `multiplayer.yaml` | Companies, colours, starting balance |

---

## API

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Server + OSRM status |
| `/api/state` | GET | Full game state snapshot |
| `/ws` | WS | Live WebSocket feed |
| `/admin/pause` | POST | Pause game |
| `/admin/resume` | POST | Resume game |
| `/admin/reload-configs` | POST | Hot-reload all configs |
| `/admin/add-money?company_id=X&amount=Y` | POST | Add money to company |
| `/admin/vehicles` | GET | List all vehicles |

---

## Raspberry Pi Setup

```bash
# 1. On your PC — preprocess map (once)
./tools/prepare_map.sh

# 2. Copy OSRM data to Pi
rsync -av osrm/data/ pi@livehaul.local:~/livehaul-server/osrm/data/

# 3. On Pi — first-time setup
git clone https://github.com/gerbain/livehaul-server
cd livehaul-server
./pi/setup.sh

# 4. Start
docker-compose up -d
```

Accessible at `http://livehaul.local:8000` from any device on your network.
Auto-starts on Pi boot via systemd.

---

## Project Structure

```
livehaul-server/
├── config/                   # All YAML config files
├── server/
│   ├── main.py               # FastAPI app
│   ├── config.py             # Config loader + hot-reload
│   ├── api/
│   │   └── websocket_manager.py
│   ├── game/
│   │   ├── state.py          # Game loop + state
│   │   └── vehicle.py        # Vehicle model + movement
│   ├── routing/
│   │   └── osrm.py           # OSRM HTTP client
│   └── db/                   # SQLite (Phase 2)
├── pi/
│   ├── setup.sh              # Pi first-time setup
│   └── systemd/livehaul.service
├── tools/
│   └── prepare_map.sh        # Download + preprocess OSM data
├── osrm/data/                # OSRM files (git-ignored, generated)
├── data/                     # SQLite DB (git-ignored)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```
