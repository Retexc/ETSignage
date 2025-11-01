# app.py
import os, sys, time, json, logging, subprocess, threading, re, requests
from datetime import datetime
from flask_cors import CORS
from flask import Flask, render_template, request, jsonify, redirect

from flask import Flask, render_template, request, jsonify
# ────── PACKAGE IMPORTS ───────────────────────────────────────
from .config            import WEATHER_API_KEY
from .utils             import is_service_unavailable

from .loaders.stm       import (
    fetch_stm_alerts,
    fetch_stm_general_alerts,
    fetch_stm_route_specific_alerts, 
    fetch_all_stm_alerts,  
    fetch_stm_realtime_data,
    fetch_stm_positions_dict,
    load_stm_gtfs_trips,
    load_stm_stop_times,
    load_stm_routes,
    process_stm_trip_updates,
    stm_map_occupancy_status,
    debug_print_stm_occupancy_status,
    validate_trip,
)

from .alerts import process_stm_alerts

# ────────────────────────────────────────────────────────────────

print("__name__:", __name__)
print("__package__:", __package__)
print("sys.path:", sys.path)

_weather_cache = {
    "ts":   0,     # last fetch timestamp
    "data": None,  # cached weather dict
}

CACHE_TTL = 5 * 60  # seconds (5 minutes)
logger = logging.getLogger('BdeB-GTFS')
app = Flask(__name__)
CORS(app)
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
GTFS_BASE = os.path.join(PACKAGE_DIR, "GTFS")  # points to backend/GTFS
STM_DIR = os.path.join(GTFS_BASE, "stm")

os.makedirs(STM_DIR, exist_ok=True)

# ─── check for required GTFS files ────────────────────────────
required_stm = ["routes.txt", "trips.txt", "stop_times.txt"]

missing = []
for fname in required_stm:
    if not os.path.isfile(os.path.join(STM_DIR, fname)):
        missing.append(f"stm/{fname}")

if missing:
    print("Fichiers GTFS manquants:")
    for m in missing:
        print(f"   • {m}")
    print("\nS'il-vous-plaît, téléchargez les fichiers manquants dans le menu paramètres et relancez l'application.")
    sys.exit(1)
# ────────────────────────────────────────────────────────────────

# ====================================================================
# Load static GTFS data once at startup
# ====================================================================
stm_routes_fp      = os.path.join(STM_DIR,       "routes.txt")
stm_trips_fp       = os.path.join(STM_DIR,       "trips.txt")
stm_stop_times_fp  = os.path.join(STM_DIR,       "stop_times.txt")

routes_map      = load_stm_routes(stm_routes_fp)
stm_trips       = load_stm_gtfs_trips(stm_trips_fp, routes_map)
stm_stop_times  = load_stm_stop_times(stm_stop_times_fp)

def get_weather():
    """Fetch weather from WeatherAPI at most once per CACHE_TTL."""
    now = time.time()
    # if cache is stale, refresh it
    if now - _weather_cache["ts"] > CACHE_TTL:
        try:
            resp = requests.get(
                f"http://api.weatherapi.com/v1/current.json"
                f"?key={WEATHER_API_KEY}"
                "&q=Montreal,QC"
                "&aqi=no"
                "&lang=fr",
                timeout=5
            ).json()
            _weather_cache["data"] = {
                "icon": "https:" + resp["current"]["condition"]["icon"],
                "text":  resp["current"]["condition"]["text"],
                "temp":  int(round(resp["current"]["temp_c"])),
            }
        except Exception:
            # leave last good data or None
            pass
        _weather_cache["ts"] = now

    return _weather_cache["data"] or {"icon":"", "text":"", "temp":""}

# ====================================================================
# Metro Alerts Processing Functions
# ====================================================================
def process_metro_alerts():
    """
    Fetch and process metro line alerts from STM API.
    Returns a list of metro lines with simplified status display.
    """
    try:
        # Fetch all STM alerts
        alerts_data = fetch_stm_alerts()
        
        # Default status for all lines
        metro_status = {
            "1": {
                "name": "Ligne 1",
                "color": "Verte",
                "status": "Service normal",
                "statusColor": "text-green-400",
                "icon": "green-line",
                "is_normal": True,
                "alert_description": None
            },
            "2": {
                "name": "Ligne 2",
                "color": "Orange",
                "status": "Service normal",
                "statusColor": "text-green-400",
                "icon": "orange-line",
                "is_normal": True,
                "alert_description": None
            },
            "4": {
                "name": "Ligne 4",
                "color": "Jaune",
                "status": "Service normal",
                "statusColor": "text-green-400",
                "icon": "yellow-line",
                "is_normal": True,
                "alert_description": None
            },
            "5": {
                "name": "Ligne 5",
                "color": "Bleue",
                "status": "Service normal",
                "statusColor": "text-green-400",
                "icon": "blue-line",
                "is_normal": True,
                "alert_description": None
            }
        }
        
        # Process alerts to check for metro disruptions
        if alerts_data:
            for alert in alerts_data:
                try:
                    informed_entities = alert.get("informed_entities", [])
                    
                    for entity in informed_entities:
                        # Check if this is a metro alert
                        route_id = entity.get("route_id", "")
                        
                        # Metro routes in STM are typically "1", "2", "4", "5"
                        if route_id in metro_status:
                            # Get French header text
                            header_texts = alert.get("header_texts", [])
                            header = ""
                            for ht in header_texts:
                                if ht.get("language") == "fr":
                                    header = ht.get("text", "")
                                    break
                            
                            if header:
                                route_short_name = route_id
                                metro_status[route_short_name]["is_normal"] = False
                                metro_status[route_short_name]["status"] = "Service perturbé"
                                metro_status[route_short_name]["alert_description"] = header
                                metro_status[route_short_name]["statusColor"] = "text-red-400"
                        
                except Exception as e:
                    logger.error(f"Error processing individual metro alert: {e}")
                    continue
        
        # Convert to list format for frontend
        result = list(metro_status.values())
        return result
        
    except Exception as e:
        logger.error(f"Error in process_metro_alerts: {e}")
        import traceback
        traceback.print_exc()
        return get_default_metro_status()

def get_default_metro_status():
    """Return default metro status when API fails"""
    return [
        {
            "name": "Ligne 1",
            "color": "Verte",
            "status": "Service normal",
            "statusColor": "text-green-400",
            "icon": "green-line",
            "is_normal": True,
            "alert_description": None
        },
        {
            "name": "Ligne 2",
            "color": "Orange",
            "status": "Service normal",
            "statusColor": "text-green-400",
            "icon": "orange-line",
            "is_normal": True,
            "alert_description": None
        },
        {
            "name": "Ligne 4",
            "color": "Jaune",
            "status": "Service normal",
            "statusColor": "text-green-400",
            "icon": "yellow-line",
            "is_normal": True,
            "alert_description": None
        },
        {
            "name": "Ligne 5",
            "color": "Bleue",
            "status": "Service normal",
            "statusColor": "text-green-400",
            "icon": "blue-line",
            "is_normal": True,
            "alert_description": None
        }
    ]

def merge_alerts_into_buses(buses, processed_alerts):
    """
    Merge alert information into bus objects.
    """
    for bus in buses:
        route_id = bus.get("route_id")
        
        # Find matching alert
        for alert in processed_alerts:
            if route_id in alert.get("routes", []):
                if alert.get("effect") == "NO_SERVICE":
                    bus["cancelled"] = True
                    bus["delayed_text"] = None
                break
    
    return buses

# ====================== API Routes ======================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    """
    Main API endpoint that returns all transit data
    """
    try:
        # Process metro alerts first
        metro_lines = process_metro_alerts()
        
        # ========== STM ALERTS ==========
        filtered_alerts = []
        try:
            processed_stm = process_stm_alerts()
            logger.debug(f"Processed STM alerts: {processed_stm}")
            
            # Format alerts for frontend
            for alert in processed_stm:
                alert_obj = {
                    "header": alert.get("header", "Alerte"),
                    "description": alert.get("description", ""),
                    "alert_type": alert.get("alert_type", "info"),
                    "severity": alert.get("severity", "info")
                }
                
                # Add route information if it exists
                if alert.get("is_network_wide"):
                    alert_obj["routes"] = "Réseau STM"
                    alert_obj["stop"] = "Général"
                elif alert.get("routes"):
                    routes_str = ", ".join(alert["routes"])
                    alert_obj["routes"] = routes_str
                    alert_obj["stop"] = "Ligne spécifique"
                else:
                    alert_obj["routes"] = "N/A"
                    alert_obj["stop"] = "N/A"
                
                filtered_alerts.append(alert_obj)
                
        except Exception as e:
            logger.error(f"ERROR processing STM alerts: {e}")
            import traceback
            traceback.print_exc()

        # ========== STM BUSES WITH OCCUPANCY ==========
        buses = []
        try:
            # Get the bus routes from config
            from .config import BUS_ROUTES
            
            stm_trip_entities = fetch_stm_realtime_data()
            positions_dict = fetch_stm_positions_dict(BUS_ROUTES, stm_trips)
            
            buses = process_stm_trip_updates(
                stm_trip_entities,
                stm_trips,
                stm_stop_times,
                positions_dict
            )

            # Enhanced debug logging for occupancy
            logger.info("----- DEBUG: Final Merged STM Buses with Occupancy -----")
            status_map = {0: "INCOMING_AT", 1: "STOPPED_AT", 2: "IN_TRANSIT_TO"}
            
            for b in buses:
                raw_stat = b.get("current_status")
                if isinstance(raw_stat, int):
                    stat_str = status_map.get(raw_stat, f"Unknown({raw_stat})")
                else:
                    stat_str = str(raw_stat)
                
                # Log occupancy information
                occupancy = b.get("occupancy", "Unknown")
                logger.info(
                    f"Route={b['route_id']}, Trip={b['trip_id']}, "
                    f"Stop={b['stop_id']}, ArrTime={b['arrival_time']}, "
                    f"Occupancy={occupancy}, AtStop={b['at_stop']}, "
                    f"Lat={b.get('lat')}, Lon={b.get('lon')}, Dist={b.get('distance_m')}m, "
                    f"currentStatus={stat_str}"
                )
            logger.info("-----------------------------------------")

            buses = merge_alerts_into_buses(buses, processed_stm if 'processed_stm' in locals() else [])
        except Exception as e:
            logger.error(f"ERROR processing buses: {e}")
            import traceback
            traceback.print_exc()

        # ========== WEATHER ==========
        weather = get_weather()

        # Build response
        response = {
            "buses": buses,
            "metro_lines": metro_lines,
            "weather": weather,
            "alerts": filtered_alerts,
            "debug": {
                "total_buses": len(buses),
                "total_metro_lines": len(metro_lines),
                "alerts_count": len(filtered_alerts)
            }
        }

        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in get_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)