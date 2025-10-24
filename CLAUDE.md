# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BdeB-Go (ETSignage) is a real-time public transit display system designed for Collège de Bois-de-Boulogne. It displays bus/train schedules, service alerts, and crowding levels using GTFS and GTFS-RT data from STM (Montreal metro/bus) and Exo (commuter trains).

**Architecture**: Python Flask backend + Vue 3 frontend (admin console + display interface)

## Development Commands

### Setup & Installation
```bash
# Initial setup (installs deps, builds frontend)
install.bat

# Silent mode (for automated updates)
install.bat silent
```

### Running the Application
```bash
# Start both backend and frontend
start.bat

# OR manually:
cd UI
npm run start  # Runs both backend (port 5001) and frontend (port 4173)
```

### Frontend Development (UI/)
```bash
cd UI

# Development mode (frontend only)
npm run dev:frontend

# Development mode (backend only)
npm run dev:backend

# Run both in dev mode
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Backend Development (backend/)
The backend is a Flask application served via Waitress in production.

**Main entry points:**
- `backend/main.py` - Main application server (port 5000) - serves transit data API
- `backend/admin.py` - Admin interface server (port 5001) - manages settings, updates, GTFS uploads

**Run backend directly:**
```bash
python -m backend.main  # Main app
python -m backend.admin # Admin app
```

## Code Architecture

### Backend Structure

**Core modules:**
- `backend/main.py` - Main Flask app serving `/api/data` endpoint with bus/train/metro/weather data
- `backend/admin.py` - Admin Flask app for configuration, GTFS updates, background management
- `backend/config.py` - Environment variables loader (API keys from `.env`)
- `backend/alerts.py` - Alert processing logic for STM and Exo
- `backend/utils.py` - Shared utilities (CSV parsing, date checks)

**Data loaders:**
- `backend/loaders/stm.py` - STM (Montreal metro/bus) GTFS & GTFS-RT data fetching and processing
- `backend/loaders/exo.py` - Exo (commuter trains) via Chrono API GTFS-RT processing

**Key architecture notes:**
- GTFS static files stored in `backend/GTFS/stm/` and `backend/GTFS/exo/`
- GTFS-RT data fetched from STM API and Chrono API (Exo) in real-time
- Realtime data merged with static GTFS schedules to show delays/occupancy
- Backend uses protocol buffers (gtfs_realtime_pb2) for GTFS-RT parsing
- Caching implemented for Exo data (60s TTL) and weather (5min TTL)

### Frontend Structure

**Vue 3 application with:**
- Vue Router for navigation
- Pinia for state management (minimal usage)
- TailwindCSS for styling
- Motion-v for animations

**Main views:**
- `Display.vue` - Public-facing transit display screen
- `Console.vue` - Admin control panel
- `Board.vue` - Transit schedule board view
- `Background.vue` - Background image scheduler management
- `Announcement.vue` - Custom alert message management
- `Settings.vue` - System configuration

**Key components:**
- `BusRow.vue`, `TrainRow.vue`, `MetroRow.vue` - Transit line display
- `AlertBanner.vue` - Scrolling alerts display
- `Header.vue` - Weather and time display

### Data Flow

1. **Static GTFS**: Uploaded via admin interface → stored in `backend/GTFS/{stm,exo}/`
2. **Real-time updates**:
   - STM: Fetched from `api.stm.info` using apiKey
   - Exo: Fetched from Chrono API using token
3. **Data merging**: `main.py` combines GTFS static + GTFS-RT to calculate:
   - Actual arrival times with delays
   - Vehicle occupancy status
   - Service disruptions
4. **API endpoint**: `/api/data` serves JSON to frontend every few seconds
5. **Frontend updates**: Vue components reactively display the merged data

### Background Image Scheduler

Managed via `backend/managers/background_manager.py`:
- Supports 4 time-based image slots
- Slot data stored in CSS file as JSON comment block: `/* MULTISLOT: [...] */`
- Admin can upload images and set date ranges
- Active background determined by current date matching slot range

### Update System

The application supports auto-updates via Git or HTTP download:
- Git method: `git pull` if `.git` exists
- HTTP method: Downloads ZIP from GitHub and extracts
- Update process: fetch code → install deps → rebuild frontend via `install.bat silent`
- Auto-update worker thread runs daily at configured time

## Environment Variables

Required in `.env` file at project root:

```env
STM_API_KEY=your_stm_api_key          # From https://portail.developpeurs.stm.info/apihub/
CHRONO_TOKEN=your_exo_token           # From https://portail-developpeur.chrono-saeiv.com/
WEATHER_API_KEY=your_weather_key      # From https://www.weatherapi.com/
GLOBAL_DELAY_MINUTES=0                # Optional: Add global delay offset
```

## Important Implementation Details

### Bus Stop IDs
- Bus stops use specific stop IDs that must match GTFS data
- Recent commit mentions changing bus stop IDs - verify against GTFS stop_times.txt

### Metro Status Processing
- Metro alerts fetched from STM API `/etatservice` endpoint
- 4 metro lines: 1 (Green), 2 (Orange), 4 (Yellow), 5 (Blue)
- Normal status: "Service normal du métro"
- Disrupted: Status text hidden, alert description shown in banner

### Occupancy Status Mapping
GTFS-RT occupancy enum mapped to display:
- 0: EMPTY
- 1: MANY_SEATS_AVAILABLE
- 2: FEW_SEATS_AVAILABLE
- 3: STANDING_ROOM_ONLY
- 4: CRUSHED_STANDING_ROOM_ONLY
- 5: FULL
- 6: NOT_ACCEPTING_PASSENGERS

### Alert Badge System
Alerts merged into bus/train rows to show stop status:
- "déplacé" → Yellow "Arrêt déplacé" badge
- "relocalisé" → Blue "Arrêt relocalisé" badge
- "annulé" → Red "Arrêt annulé" badge + canceled flag

## API Endpoints

### Main Application (port 5000)
- `GET /api/data` - Returns all transit data (buses, trains, metro, alerts, weather)
- `GET /api/messages` - Get custom alert messages
- `POST /api/messages` - Update custom alert messages

### Admin Application (port 5001)
- `GET /admin/status` - Check if main app is running
- `POST /admin/start` - Start main application
- `POST /admin/stop` - Stop main application
- `GET /admin/check_update` - Check for application updates
- `POST /admin/app_update` - Perform application update
- `POST /admin/update_gtfs` - Upload new GTFS data
- `GET /admin/gtfs_update_info` - Get last GTFS update timestamps
- `GET /admin/backgrounds` - Get background image slots
- `POST /admin/backgrounds` - Update background slots
- `POST /admin/backgrounds/import` - Upload new background image

## Testing & Debugging

- Backend logs printed to console via `print()` and Flask logger
- Frontend uses browser console for debugging
- Check GTFS files exist before startup (routes.txt, trips.txt, stop_times.txt)
- Verify API keys in `.env` are valid and not expired
- STM API rate limiting: Be mindful of request frequency
- Chrono API rate limiting: 60s cache to prevent excessive calls
