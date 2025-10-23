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

from .loaders.exo       import (
    fetch_exo_alerts,
    fetch_exo_realtime_data,
    load_exo_gtfs_trips,
    load_exo_stop_times,
    process_exo_vehicle_positions,
    process_exo_train_schedule_with_occupancy,
)

from .alerts            import process_stm_alerts, process_exo_alerts

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
EXO_TRAIN_DIR = os.path.join(GTFS_BASE, "exo")

os.makedirs(STM_DIR,       exist_ok=True)
os.makedirs(EXO_TRAIN_DIR, exist_ok=True)

_chrono_cache = {
    "timestamp": 0,
    "data": None
}
CHRONO_CACHE_TTL = 60

# ─── check for required GTFS files ────────────────────────────
required_stm = ["routes.txt", "trips.txt", "stop_times.txt"]
required_exo = ["trips.txt",   "stop_times.txt"]

missing = []
for fname in required_stm:
    if not os.path.isfile(os.path.join(STM_DIR, fname)):
        missing.append(f"stm/{fname}")
for fname in required_exo:
    if not os.path.isfile(os.path.join(EXO_TRAIN_DIR, fname)):
        missing.append(f"exo/{fname}")

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
exo_trips_fp       = os.path.join(EXO_TRAIN_DIR, "trips.txt")
exo_stop_times_fp  = os.path.join(EXO_TRAIN_DIR, "stop_times.txt")

routes_map      = load_stm_routes(stm_routes_fp)
stm_trips       = load_stm_gtfs_trips(stm_trips_fp,      routes_map)
stm_stop_times  = load_stm_stop_times(stm_stop_times_fp)
exo_trips       = load_exo_gtfs_trips(exo_trips_fp)
exo_stop_times  = load_exo_stop_times(exo_stop_times_fp)

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
        alerts_data = fetch_stm_alerts()
        if not alerts_data:
            logger.warning("No metro alerts data received")
            return get_default_metro_status()
        
        # Handle different response formats from STM API
        alerts_list = []
        if isinstance(alerts_data, list):
            alerts_list = alerts_data
        else:
            logger.error(f"Unexpected alerts_data type: {type(alerts_data)}")
            return get_default_metro_status()
        
        logger.info(f"Processing {len(alerts_list)} alerts for metro status")
        
        # Initialize metro lines with default normal status
        metro_status = {
            "1": {
                "name": "Ligne 1",
                "color": "Verte", 
                "status": "Service normal du métro",
                "statusColor": "text-green-400",
                "icon": "green-line",
                "is_normal": True,
                "alert_description": None  # Store full description for alerts
            },
            "2": {
                "name": "Ligne 2",
                "color": "Orange",
                "status": "Service normal du métro", 
                "statusColor": "text-green-400",
                "icon": "orange-line",
                "is_normal": True,
                "alert_description": None
            },
            "4": {
                "name": "Ligne 4", 
                "color": "Jaune",
                "status": "Service normal du métro",
                "statusColor": "text-green-400", 
                "icon": "yellow-line",
                "is_normal": True,
                "alert_description": None
            },
            "5": {
                "name": "Ligne 5",
                "color": "Bleue", 
                "status": "Service normal du métro",
                "statusColor": "text-green-400",
                "icon": "blue-line", 
                "is_normal": True,
                "alert_description": None
            }
        }
        
        # Process alerts from API
        for alert in alerts_list:
            try:
                if not isinstance(alert, dict):
                    continue
                
                informed_entities = alert.get("informed_entities", [])
                if not isinstance(informed_entities, list):
                    continue
                    
                for entity in informed_entities:
                    if not isinstance(entity, dict):
                        continue
                        
                    route_short_name = entity.get("route_short_name")
                    
                    # Only process metro lines (1, 2, 4, 5)
                    if route_short_name in ["1", "2", "4", "5"]:
                        description_texts = alert.get("description_texts", [])
                        if not isinstance(description_texts, list):
                            continue
                            
                        french_description = None
                        for desc in description_texts:
                            if isinstance(desc, dict) and desc.get("language") == "fr":
                                french_description = desc.get("text", "")
                                break
                        
                        if french_description:
                            is_normal_service = "service normal" in french_description.lower()
                            
                            if is_normal_service:
                                # Keep normal status
                                metro_status[route_short_name]["status"] = "Service normal du métro"
                                metro_status[route_short_name]["is_normal"] = True
                                metro_status[route_short_name]["statusColor"] = "text-green-400"
                            else:
                                # Service disrupted - hide status text, mark as not normal
                                metro_status[route_short_name]["status"] = ""  # Empty status for disrupted lines
                                metro_status[route_short_name]["is_normal"] = False
                                metro_status[route_short_name]["statusColor"] = "text-red-400"
                                metro_status[route_short_name]["alert_description"] = french_description
                            
                            logger.info(f"Updated metro line {route_short_name}: {'Normal' if is_normal_service else 'Disrupted'}")
                            
            except Exception as e:
                logger.error(f"Error processing individual metro alert: {e}")
                continue
        
        # Convert to list format expected by frontend
        metro_lines = []
        for line_id, line_data in metro_status.items():
            metro_lines.append({
                "id": int(line_id),
                "name": line_data["name"],
                "color": line_data["color"],
                "status": line_data["status"],
                "statusColor": line_data["statusColor"],
                "icon": line_data["icon"],
                "is_normal": line_data["is_normal"],
                "alert_description": line_data["alert_description"]  
            })
        

        metro_lines.sort(key=lambda x: x["id"])
        
        logger.info(f"Processed {len(metro_lines)} metro lines")
        return metro_lines
        
    except Exception as e:
        logger.error(f"Error in process_metro_alerts: {e}")
        return get_default_metro_status()


def format_metro_alerts_for_banner(metro_lines):
    """
    Extract metro disruptions and format them for the alert banner.
    """
    metro_alerts = []
    
    for metro_line in metro_lines:
        if not metro_line.get("is_normal", True) and metro_line.get("alert_description"):
            metro_alerts.append({
                "header": f"Métro {metro_line['name']} ({metro_line['color']})",
                "description": metro_line["alert_description"],
                "routes": f"Métro {metro_line['color']}",
                "stop": "Métro",
                "alert_type": "metro",
                "status": "active"
            })
    
    return metro_alerts

def get_default_metro_status():
    """
    Returns default metro status when API is unavailable.
    """
    return [
        {
            "id": 1,
            "name": "Ligne 1",
            "color": "Verte",
            "status": "Données non disponibles pour le moment",
            "statusColor": "text-green-400",
            "icon": "green-line",
            "is_normal": True
        },
        {
            "id": 2,
            "name": "Ligne 2", 
            "color": "Orange",
            "status": "Données non disponibles pour le moment",
            "statusColor": "text-green-400",
            "icon": "orange-line",
            "is_normal": True
        },
        {
            "id": 4,
            "name": "Ligne 4",
            "color": "Jaune", 
            "status": "Données non disponibles pour le moment",
            "statusColor": "text-green-400",
            "icon": "yellow-line",
            "is_normal": True
        },
        {
            "id": 5,
            "name": "Ligne 5",
            "color": "Bleue",
            "status": "Données non disponibles pour le moment", 
            "statusColor": "text-green-400",
            "icon": "blue-line",
            "is_normal": True
        }
    ]


# ====================================================================
# Merge STM alerts into bus rows and update location styling
# ====================================================================
def merge_alerts_into_buses(buses, stm_alerts):
    """
    For each bus row, check if there's a matching STM alert that references the same
    route and stop (based on the processed alert's "routes" and "stop" fields). If the
    alert description contains "annulé","déplacé" or "relocalisé", append a styled HTML badge
    next to the bus's location.
    """
    for bus in buses:
        route_id = bus.get("route_id", "").strip()
        bus_location = bus.get("location", "").strip()
        for alert in stm_alerts:
            if route_id in alert.get("routes", ""):
                if bus_location in alert.get("stop", ""):
                    desc = alert.get("description", "").lower()
                    if "déplacé" in desc:
                        bus["location"] = f"{bus_location} <span class='alert-badge alert-deplace'>Arrêt déplacé</span>"
                        break
                    elif "relocalisé" in desc:
                        bus["location"] = f"{bus_location} <span class='alert-badge alert-relocalise'>Arrêt relocalisé</span>"
                        break
                    elif "annulé" in desc:
                        bus["location"] = f"{bus_location} <span class='alert-badge alert-annule'>Arrêt annulé</span>"
                        bus["canceled"] = True 
                        break                    
    return buses

# ====================================================================
# Load background image from Background Manager
# ====================================================================        
def get_active_background(css_path):
    """
    Reads the MULTISLOT block from the CSS file and returns the URL (string)
    of the slot whose date range includes today's date.
    Returns None if no slot is active.
    """
    if not os.path.isfile(css_path):
        return None

    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()

    # Look for a block starting with "/* MULTISLOT:" and ending with "*/"
    pattern_block = re.compile(r"/\*\s*MULTISLOT:\s*(.*?)\*/", re.IGNORECASE | re.DOTALL)
    match = pattern_block.search(css_content)
    if not match:
        return None

    block_text = match.group(1).strip()
    today = datetime.today().date()
    active_bg = None

    # Each line should be like:
    # SLOT1: /static/assets/images/Printemps - Banner Big.png from 2025-03-19 to 2025-06-12
    for line in block_text.splitlines():
        line = line.strip()
        m = re.match(r"SLOT\d+:\s+(.*?)\s+from\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})", line, re.IGNORECASE)
        if m:
            bg_url = m.group(1).strip()
            start_str = m.group(2).strip()
            end_str = m.group(3).strip()
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if start_date <= today <= end_date:
                active_bg = bg_url
                break

    return active_bg      

# ====================================================================
# ROUTE: Home Page
# ====================================================================
@app.route("/")
def index():
    return redirect("http://localhost:3000") 

# ====================================================================
# ROUTE: API JSON Data for buses, trains, metro, and alerts
# ====================================================================
def format_stm_alerts_for_api():
    """
    Get STM alerts (general + route-specific + metro) and format them 
    to match your existing alert structure.
    """
    formatted_alerts = []
    
    try:
        print("=== format_stm_alerts_for_api() called ===")
        
        # Get general network alerts 
        print("Fetching general alerts...")
        general_alerts = fetch_stm_general_alerts()
        print(f"Got {len(general_alerts)} general alerts")
        
        for i, alert in enumerate(general_alerts):
            print(f"Processing general alert {i+1}: {alert.get('header', 'No header')}")
            description = alert.get("description", "")
            import re
            description = re.sub(r'<[^>]+>', '', description)
            
            formatted_alert = {
                "header": alert.get("header", "Alerte STM"),
                "description": description,
                "routes": "Réseau STM",
                "stop": "Général",
                "alert_type": "general_network",
                "status": "active"
            }
            formatted_alerts.append(formatted_alert)
            print(f"Added general alert: {formatted_alert['header']}")
    
        print("Fetching route-specific alerts...")
        route_alerts = fetch_stm_route_specific_alerts(["171", "180", "164"])
        print(f"Got {len(route_alerts)} route-specific alerts")
        
        for i, alert in enumerate(route_alerts):
            print(f"Processing route alert {i+1}: {alert.get('header', 'No header')}")
            description = alert.get("description", "")
            import re
            description = re.sub(r'<[^>]+>', '', description)
            
            routes_str = ", ".join(alert.get("affected_routes", []))
            formatted_alert = {
                "header": alert.get("header", "Alerte de ligne"),
                "description": description,
                "routes": routes_str,
                "stop": "Ligne spécifique",
                "alert_type": "route_specific",
                "status": "active"
            }
            formatted_alerts.append(formatted_alert)
            print(f"Added route alert: {formatted_alert['header']} for routes: {routes_str}")
        
        # Get metro alerts
        print("Fetching metro alerts...")
        metro_lines = process_metro_alerts()
        metro_alerts = format_metro_alerts_for_banner(metro_lines)
        print(f"Got {len(metro_alerts)} metro alerts")
        
        for metro_alert in metro_alerts:
            formatted_alerts.append(metro_alert)
            print(f"Added metro alert: {metro_alert['header']}")
            
        print(f"=== format_stm_alerts_for_api() returning {len(formatted_alerts)} formatted alerts ===")
        return formatted_alerts
            
    except Exception as e:
        print(f"ERROR in format_stm_alerts_for_api: {e}")
        import traceback
        traceback.print_exc()
        return []



def get_schedule_relationship_name(value):
    """Convert schedule_relationship enum to readable name"""
    relationships = {
        0: "SCHEDULED",
        1: "ADDED", 
        2: "CANCELED",
        3: "NO_DATA"
    }
    return relationships.get(value, f"UNKNOWN({value})")
 
@app.route("/api/data")
def api_data():
    try:
        api_debug = {
            "called_at": time.strftime('%H:%M:%S'),
            "endpoint": "/api/data"
        }    
        filtered_alerts = []
        
        try:
            # ========== ALERTS ==========
            try:
                stm_alert_json = fetch_stm_alerts()
                processed_stm = process_stm_alerts(stm_alert_json, WEATHER_API_KEY) if stm_alert_json else []
            except Exception as e:
                print(f"ERROR processing STM alerts: {e}")
                processed_stm = []

            try:
                exo_alert_entities = fetch_exo_alerts()
                print(f"DEBUG: EXO alerts returned: {len(exo_alert_entities) if exo_alert_entities else 0} entities")
                processed_exo = process_exo_alerts(exo_alert_entities)
                print(f"DEBUG: Processed EXO alerts: {len(processed_exo)} alerts")
            except Exception as e:
                print(f"ERROR processing EXO alerts: {e}")
                processed_exo = []
            
            try:
                formatted_stm_alerts = format_stm_alerts_for_api()
                print(f"DEBUG: New STM alerts found: {len(formatted_stm_alerts)} alerts")
            except Exception as e:
                print(f"ERROR in format_stm_alerts_for_api: {e}")
                import traceback
                traceback.print_exc()
                formatted_stm_alerts = []
            
            # Combine all alerts
            all_alerts = processed_stm + processed_exo + formatted_stm_alerts

            # === Custom Alert Logic ===
            try:
                custom_path = os.path.join(
                    os.path.dirname(__file__),
                    "GTFSManager",
                    "public",
                    "custom_messages.json"
                )
                if os.path.exists(custom_path):
                    with open(custom_path, "r", encoding="utf-8") as f:
                        try:
                            custom_alerts = json.load(f)
                            if not isinstance(custom_alerts, list):
                                custom_alerts = []
                        except:
                            custom_alerts = []
                    for c in custom_alerts:
                        all_alerts.append(c)
            except Exception as e:
                print(f"ERROR processing custom alerts: {e}")

            # ========= Filtering Out Pending Alerts =========
            try:
                now = datetime.now()
                filtered_alerts = []
                for alert in all_alerts:
                    if alert.get("status") == "pending":
                        st = alert.get("scheduledTime")
                        if st:
                            try:
                                scheduled_dt = datetime.fromisoformat(st)
                                if scheduled_dt > now:
                                    continue
                            except Exception as e:
                                pass
                    filtered_alerts.append(alert)

                print(f"DEBUG: Total filtered alerts being sent to frontend: {len(filtered_alerts)}")
                for alert in filtered_alerts:
                    print(f"  - {alert.get('header', 'No header')}: {alert.get('routes', 'No routes')}")
            except Exception as e:
                print(f"ERROR filtering alerts: {e}")
                filtered_alerts = []

        except Exception as e:
            print(f"ERROR in main alerts processing: {e}")
            import traceback
            traceback.print_exc()
            filtered_alerts = []

        # ========== STM BUSES ==========
        try:
            stm_trip_entities = fetch_stm_realtime_data()
            positions_dict = fetch_stm_positions_dict(["171", "180", "164"], stm_trips)
            buses = process_stm_trip_updates(
                stm_trip_entities,
                stm_trips,
                stm_stop_times,
                positions_dict
            )

            logger.info("----- DEBUG: Final Merged STM Buses -----")
            status_map = {0: "INCOMING_AT", 1: "STOPPED_AT", 2: "IN_TRANSIT_TO"}
            for b in buses:
                raw_stat = b.get("current_status")
                if isinstance(raw_stat, int):
                    stat_str = status_map.get(raw_stat, f"Unknown({raw_stat})")
                else:
                    stat_str = str(raw_stat)
                logger.info(
                    f"Route={b['route_id']}, Trip={b['trip_id']}, "
                    f"Stop={b['stop_id']}, ArrTime={b['arrival_time']}, "
                    f"Occupancy={b['occupancy']}, AtStop={b['at_stop']}, "
                    f"Lat={b.get('lat')}, Lon={b.get('lon')}, Dist={b.get('distance_m')}m, "
                    f"currentStatus={stat_str}"
                )
            logger.info("-----------------------------------------")

            buses = merge_alerts_into_buses(buses, processed_stm if 'processed_stm' in locals() else [])
        except Exception as e:
            print(f"ERROR processing buses: {e}")
            buses = []

        # ========== EXO TRAINS WITH CACHING ==========
        try:
            current_time = time.time()
            
            if current_time - _chrono_cache["timestamp"] < CHRONO_CACHE_TTL and _chrono_cache["data"]:
                exo_trains = _chrono_cache["data"]
                api_debug["chrono_cache"] = "using_cache"
            else:
                EXO_TRAIN_DIR = os.path.join(PACKAGE_DIR, "GTFS", "exo")
                exo_trips_fp = os.path.join(EXO_TRAIN_DIR, "trips.txt")
                exo_stop_times_fp = os.path.join(EXO_TRAIN_DIR, "stop_times.txt")

                fresh_exo_trips = load_exo_gtfs_trips(exo_trips_fp)
                fresh_exo_stop_times = load_exo_stop_times(exo_stop_times_fp)

                exo_trip_updates, exo_vehicle_positions = fetch_exo_realtime_data()
                
                if len(exo_trip_updates) > 0 or len(exo_vehicle_positions) > 0:
                    exo_vehicle_data = process_exo_vehicle_positions(exo_vehicle_positions, fresh_exo_stop_times)
                    exo_trains = process_exo_train_schedule_with_occupancy(
                        fresh_exo_stop_times,
                        fresh_exo_trips,
                        exo_vehicle_data,
                        exo_trip_updates
                    )
                    _chrono_cache["data"] = exo_trains
                    _chrono_cache["timestamp"] = current_time
                    api_debug["chrono_cache"] = f"fresh_data_{len(exo_trip_updates)}trips_{len(exo_vehicle_positions)}vehicles"
                else:
                    if _chrono_cache["data"]:
                        exo_trains = _chrono_cache["data"]
                        api_debug["chrono_cache"] = "rate_limited_using_cache"
                    else:
                        exo_vehicle_data = process_exo_vehicle_positions([], fresh_exo_stop_times)
                        exo_trains = process_exo_train_schedule_with_occupancy(
                            fresh_exo_stop_times,
                            fresh_exo_trips,
                            exo_vehicle_data,
                            []
                        )
                        api_debug["chrono_cache"] = "rate_limited_no_cache_static_fallback"
            
            if is_service_unavailable():
                for train in exo_trains:
                    train["no_service_text"] = "Aucun service aujourd'hui"
                    train["arrival_time"] = "N/A"
                    train["delayed_text"] = None
                    train["early_text"] = None
        except Exception as e:
            print(f"ERROR processing trains: {e}")
            exo_trains = []

        # ========== METRO LINES ==========
        try:
            metro_lines = process_metro_alerts()
        except Exception as e:
            print(f"ERROR processing metro: {e}")
            metro_lines = []

        # ========== WEATHER ==========
        try:
            weather = get_weather()
        except Exception as e:
            print(f"ERROR getting weather: {e}")
            weather = {"icon":"", "text":"", "temp":""}

        return jsonify({       
            "buses": buses,
            "next_trains": exo_trains,
            "metro_lines": metro_lines,
            "current_time": time.strftime("%I:%M:%S %p"),
            "alerts": filtered_alerts,
            "weather": weather        
        })
        
    except Exception as e:
        print(f"CRITICAL ERROR in /api/data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "buses": [],
            "next_trains": [],
            "metro_lines": [],
            "current_time": time.strftime("%I:%M:%S %p"),
            "alerts": [],
            "weather": {"icon":"", "text":"", "temp":""},
            "error": str(e)
        }), 500
# ====================================================================
# NEW: API endpoint to get and update custom messages
# ====================================================================
@app.route("/api/messages", methods=["GET", "POST"])
def api_messages():
    custom_path = os.path.join(
        os.path.dirname(__file__),
        "GTFSManager",
        "public",
        "custom_messages.json"
    )
    if request.method == "GET":
        if os.path.exists(custom_path):
            with open(custom_path, "r", encoding="utf-8") as f:
                messages = json.load(f)
            return jsonify(messages)
        else:
            return jsonify([]), 404
    elif request.method == "POST":
        data = request.get_json()
        try:
            with open(custom_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return jsonify({"status": "success"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
  

@app.route("/admin")
def admin_dashboard():
    return render_template("home.html")


app.config['APP_RUNNING'] = False
main_app_logs = []
app_process = None 

def capture_app_logs(process):
    """Continuously read output from the process and append to main_app_logs."""
    while True:
        line = process.stdout.readline()
        if not line:  
            break
        main_app_logs.append(line.rstrip())
    app.config['APP_RUNNING'] = False

@app.route('/admin/start', methods=['POST'])
def admin_start():
    global app_process
    if not app.config['APP_RUNNING']:
        try:
            # Spawn the main application as a subprocess.
            cmd = [PYTHON_EXEC, "-u", "app.py"]  
           
            app_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            app.config['APP_RUNNING'] = True
            main_app_logs.append(f"{datetime.now()} - Main app started.")
            # Start a background thread to capture the process logs:
            threading.Thread(target=capture_app_logs, args=(app_process,), daemon=True).start()
            return jsonify({'status': 'started'}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    else:
        return jsonify({'status': 'already_running'}), 200

@app.route('/admin/logs_data')
def logs_data():
    return "\n".join(main_app_logs)


from waitress import serve
if __name__ == "__main__":
    serve(app,
          host="127.0.0.1",
          port=5000,
          threads=8)

#serve(app, host="0.0.0.0", port=5000)