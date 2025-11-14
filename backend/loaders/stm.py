import requests
import os
import csv
import time
from datetime import datetime, timedelta
from google.transit import gtfs_realtime_pb2
from backend.config import (
    STM_API_KEY,
    STM_REALTIME_ENDPOINT,
    STM_VEHICLE_POSITIONS_ENDPOINT,
    STM_ALERTS_ENDPOINT,
    BUS_ROUTES,
    BUS_STOP_IDS,
    BUS_ROUTE_COMBOS,
    BUS_DISPLAY_INFO
)
from backend.utils import load_csv_dict  
# Cache for calendar data
_calendar_data = None
_calendar_dates_data = None

IS_DEV_MODE = os.environ.get('ENVIRONMENT') == 'development'



script_dir = os.path.dirname(os.path.abspath(__file__))

def load_calendar_data():
    global _calendar_data
    if _calendar_data is None:
        cal_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "STM", "calendar.txt")
        _calendar_data = {}
        try:
            with open(cal_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    service_id = row["service_id"]
                    _calendar_data[service_id] = row
        except Exception as e:
            print("Error loading calendar.txt:", e)
    return _calendar_data

def load_calendar_dates_data():
    global _calendar_dates_data
    if _calendar_dates_data is None:
        cal_dates_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "STM", "calendar_dates.txt")
        _calendar_dates_data = {}
        try:
            with open(cal_dates_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    service_id = row["service_id"]
                    if service_id not in _calendar_dates_data:
                        _calendar_dates_data[service_id] = []
                    _calendar_dates_data[service_id].append(row)
        except Exception as e:
            print("Error loading calendar_dates.txt:", e)
    return _calendar_dates_data

def serviceRunsToday(service_id):
    today = datetime.now().date()
    run_today = False

    cal_data = load_calendar_data()
    cal_dates = load_calendar_dates_data()

    # Check the regular calendar
    if service_id in cal_data:
        row = cal_data[service_id]
        try:
            start_date = datetime.strptime(row["start_date"], "%Y%m%d").date()
            end_date = datetime.strptime(row["end_date"], "%Y%m%d").date()
        except Exception as e:
            print(f"Error parsing dates for service_id {service_id}: {e}")
            return False
        weekday = today.weekday()  # Monday=0, Sunday=6
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if start_date <= today <= end_date and row[days[weekday]] == "1":
            run_today = True
    else:
        print(f"Service_id {service_id} not found in calendar.txt")

    # Apply exceptions from calendar_dates.txt
    if service_id in cal_dates:
        for row in cal_dates[service_id]:
            try:
                exception_date = datetime.strptime(row["date"], "%Y%m%d").date()
            except Exception as e:
                print(f"Error parsing exception date for service_id {service_id}: {e}")
                continue
            if exception_date == today:
                # exception_type "1" means added service, "2" means removed service.
                if row["exception_type"] == "2":
                    run_today = False
                elif row["exception_type"] == "1":
                    run_today = True
    return run_today

def fetch_stm_realtime_data():

    if IS_DEV_MODE:
        from backend.mock_stm_data import get_mock_trip_entities
        return get_mock_trip_entities()
    headers = {
        "accept": "application/x-protobuf",
        "apiKey": STM_API_KEY,
    }
    response = requests.get(STM_REALTIME_ENDPOINT, headers=headers)
    if response.status_code == 200:
        print("API Fetch Success")
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        return feed.entity
    else:
        print(f"API Error: {response.status_code} - {response.text}")
        return []
    
def fetch_stm_vehicle_positions():
    if IS_DEV_MODE:
        from backend.mock_stm_data import get_mock_vehicle_positions
        return get_mock_vehicle_positions()
    headers = {
        "accept": "application/x-protobuf",
        "apiKey": STM_API_KEY,
    }
    response = requests.get(STM_VEHICLE_POSITIONS_ENDPOINT, headers=headers)
    if response.status_code == 200:
        print("Vehicle Positions Fetch Success")
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        return feed.entity
    else:
        print(f"API Error: {response.status_code} - {response.text}")
        return []   


# Cache for STM alerts to avoid rate limits
_stm_alerts_cache = {
    "timestamp": 0,
    "data": None
}
STM_ALERTS_CACHE_TTL = 30  # Cache alerts for 30 seconds

def fetch_stm_alerts():
    if IS_DEV_MODE:
        from backend.mock_stm_data import get_mock_alerts
        return get_mock_alerts()
    
    global _stm_alerts_cache

    # Check if cache is still valid
    current_time = time.time()
    if current_time - _stm_alerts_cache["timestamp"] < STM_ALERTS_CACHE_TTL:
        if _stm_alerts_cache["data"] is not None:
            print(f"[CACHE] Using cached STM alerts (age: {int(current_time - _stm_alerts_cache['timestamp'])}s)")
            return _stm_alerts_cache["data"]
    
    # Cache expired or empty, fetch fresh data
    print("[API] Fetching fresh STM alerts from API...")
    
    headers = {
        "accept": "application/json",
        "apiKey": STM_API_KEY,
    }
    try:
        response = requests.get(STM_ALERTS_ENDPOINT, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            
            # Check if the data structure contains 'result' key (new JSON format)
            if isinstance(json_data, dict) and "result" in json_data:
                result = json_data["result"]
                if isinstance(result, dict):
                    # Extract metro line data if available
                    metro_lines = []
                    for key, value in result.items():
                        if key.startswith("ligne") and isinstance(value, dict):
                            # Process each metro line
                            metro_lines.append(value)
                    
                    # Also check for alerts in result
                    alerts = result.get("alerts", [])
                    if alerts:
                        # Normalize alert format
                        normalized = _normalize_alerts(alerts)
                        _stm_alerts_cache["data"] = normalized
                        _stm_alerts_cache["timestamp"] = current_time
                        return normalized
                    elif metro_lines:
                        # Convert metro line info to normalized alert format
                        converted_alerts = []
                        for line in metro_lines:
                            etat_obj = line.get("etat", {})
                            etat_status = etat_obj.get("etat", "NORMAL")
                            
                            # Only create alert if not normal
                            if etat_status != "NORMAL":
                                libelle = etat_obj.get("libelle", "Service perturbé")
                                detail = etat_obj.get("detail", libelle)
                                numero = line.get("numero", "")
                                
                                alert = {
                                    "informed_entities": [{"route_short_name": numero}],
                                    "header_texts": [{"language": "fr", "text": libelle}],
                                    "description_texts": [{"language": "fr", "text": detail}]
                                }
                                converted_alerts.append(alert)
                        _stm_alerts_cache["data"] = converted_alerts
                        _stm_alerts_cache["timestamp"] = current_time
                        return converted_alerts
                    
                    # No alerts found
                    _stm_alerts_cache["data"] = []
                    _stm_alerts_cache["timestamp"] = current_time
                    return []
                    
            # Fallback to old format
            elif isinstance(json_data, dict) and "alerts" in json_data:
                normalized = _normalize_alerts(json_data["alerts"])
                _stm_alerts_cache["data"] = normalized
                _stm_alerts_cache["timestamp"] = current_time
                return normalized
            elif isinstance(json_data, list):
                normalized = _normalize_alerts(json_data)
                _stm_alerts_cache["data"] = normalized
                _stm_alerts_cache["timestamp"] = current_time
                return normalized
            else:
                print(f"Unexpected STM alerts response format: {type(json_data)}")
                return _stm_alerts_cache["data"] or []
        else:
            print(f"[ERROR] STM API Error: {response.status_code} - {response.text}")
            # Return cached data if available even if stale
            return _stm_alerts_cache["data"] or []
    except Exception as e:
        print(f"[ERROR] Error fetching alerts: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return cached data if available even if stale
        return _stm_alerts_cache["data"] or []

def _normalize_alerts(alerts):
    """
    Normalize alert format to ensure consistent field names.
    Converts old format (informed_entity, header_text) to new format (informed_entities, header_texts).
    """
    normalized = []
    for alert in alerts:
        if not isinstance(alert, dict):
            continue
            
        normalized_alert = {}
        
        # Normalize informed_entities (handle both singular and plural)
        if "informed_entities" in alert:
            normalized_alert["informed_entities"] = alert["informed_entities"]
        elif "informed_entity" in alert:
            normalized_alert["informed_entities"] = alert["informed_entity"]
        else:
            normalized_alert["informed_entities"] = []
        
        # Normalize header_texts
        if "header_texts" in alert:
            normalized_alert["header_texts"] = alert["header_texts"]
        elif "header_text" in alert:
            # Convert old format to new format
            header_text = alert["header_text"]
            if isinstance(header_text, dict) and "translation" in header_text:
                normalized_alert["header_texts"] = [
                    {"language": t.get("language", "fr"), "text": t.get("text", "")}
                    for t in header_text["translation"]
                ]
            else:
                normalized_alert["header_texts"] = []
        else:
            normalized_alert["header_texts"] = []
        
        # Normalize description_texts
        if "description_texts" in alert:
            normalized_alert["description_texts"] = alert["description_texts"]
        elif "description_text" in alert:
            # Convert old format to new format
            description_text = alert["description_text"]
            if isinstance(description_text, dict) and "translation" in description_text:
                normalized_alert["description_texts"] = [
                    {"language": t.get("language", "fr"), "text": t.get("text", "")}
                    for t in description_text["translation"]
                ]
            else:
                normalized_alert["description_texts"] = []
        else:
            normalized_alert["description_texts"] = []
        
        # Copy over other fields that might be useful
        for key in ["active_periods", "cause", "effect"]:
            if key in alert:
                normalized_alert[key] = alert[key]
        
        normalized.append(normalized_alert)
    
    return normalized


def fetch_stm_general_alerts():
    """
    Fetch and process general STM network alerts (like strikes, service disruptions).
    Returns a list of general alerts affecting the entire network.
    """
    alerts_data = fetch_stm_alerts()
    if not alerts_data:
        print("No alerts data received")
        return []
    
    general_alerts = []
    for alert in alerts_data:
        if isinstance(alert, dict):
            # Check if this is a general network alert (no specific routes)
            informed_entity = alert.get("informed_entity", [])
            
            # If no informed_entity or it's empty, it's a general alert
            if not informed_entity or len(informed_entity) == 0:
                header_text = alert.get("header_text", {})
                description_text = alert.get("description_text", {})
                
                header = ""
                description = ""
                
                # Extract header text
                if isinstance(header_text, dict):
                    translations = header_text.get("translation", [])
                    if translations:
                        header = translations[0].get("text", "")
                elif isinstance(header_text, str):
                    header = header_text
                
                # Extract description text
                if isinstance(description_text, dict):
                    translations = description_text.get("translation", [])
                    if translations:
                        description = translations[0].get("text", "")
                elif isinstance(description_text, str):
                    description = description_text
                
                if header or description:
                    general_alerts.append({
                        "header": header,
                        "description": description,
                        "start_date": alert.get("active_period", [{}])[0].get("start") if alert.get("active_period") else None,
                        "end_date": alert.get("active_period", [{}])[0].get("end") if alert.get("active_period") else None
                    })
    
    return general_alerts

def fetch_stm_route_specific_alerts(route_ids):
    """
    Fetch alerts specific to given route IDs.
    Returns a dictionary of route_id -> list of alerts
    """
    alerts_data = fetch_stm_alerts()
    if not alerts_data:
        return {}
    
    route_alerts = {route_id: [] for route_id in route_ids}
    
    for alert in alerts_data:
        if isinstance(alert, dict):
            informed_entities = alert.get("informed_entity", [])
            
            for entity in informed_entities:
                if isinstance(entity, dict):
                    route_id = entity.get("route_id") or entity.get("route_short_name")
                    
                    if route_id in route_ids:
                        header_text = alert.get("header_text", {})
                        description_text = alert.get("description_text", {})
                        
                        header = ""
                        description = ""
                        
                        # Extract header
                        if isinstance(header_text, dict):
                            translations = header_text.get("translation", [])
                            if translations:
                                header = translations[0].get("text", "")
                        elif isinstance(header_text, str):
                            header = header_text
                        
                        # Extract description
                        if isinstance(description_text, dict):
                            translations = description_text.get("translation", [])
                            if translations:
                                description = translations[0].get("text", "")
                        elif isinstance(description_text, str):
                            description = description_text
                        
                        alert_info = {
                            "header": header,
                            "description": description,
                            "effect": alert.get("effect", "UNKNOWN_EFFECT"),
                            "cause": alert.get("cause", "UNKNOWN_CAUSE"),
                            "start_date": alert.get("active_period", [{}])[0].get("start") if alert.get("active_period") else None,
                            "end_date": alert.get("active_period", [{}])[0].get("end") if alert.get("active_period") else None
                        }
                        
                        route_alerts[route_id].append(alert_info)
    
    return route_alerts

def fetch_all_stm_alerts():
    """
    Fetch all alerts and categorize them.
    Returns a dictionary with general and route-specific alerts.
    """
    alerts_data = fetch_stm_alerts()
    if not alerts_data:
        return {"general_alerts": [], "route_alerts": {}}
    
    return {
        "general_alerts": fetch_stm_general_alerts(),
        "route_alerts": fetch_stm_route_specific_alerts(["61", "36", "171", "180", "164"])  # Your specific routes
    }
    
def debug_print_stm_occupancy_status():
    entities = fetch_stm_vehicle_positions()
    if not entities:
        print("No vehicle positions data received")
        return
        
    print("\n=== STM VEHICLE OCCUPANCY DEBUG ===")
    occupancy_counts = {}
    
    for entity in entities:
        if entity.HasField("vehicle"):
            vehicle = entity.vehicle
            if vehicle.HasField("occupancy_status"):
                status = vehicle.occupancy_status
                status_name = stm_map_occupancy_status(status)
                
                if status_name not in occupancy_counts:
                    occupancy_counts[status_name] = 0
                occupancy_counts[status_name] += 1
                
                # Print first 5 examples of each status
                if occupancy_counts[status_name] <= 5:
                    print(f"Route {vehicle.trip.route_id}, Trip {vehicle.trip.trip_id}: {status_name} (raw: {status})")
    
    print("\n=== OCCUPANCY SUMMARY ===")
    for status, count in occupancy_counts.items():
        print(f"{status}: {count} vehicles")
    print("========================\n")

def get_default_metro_status():
    return [
        {
            "id": 1,
            "name": "Ligne 1",
            "color": "Verte",
            "status": "Service normal du métro",
            "statusColor": "text-green-400",
            "icon": "green-line",
            "is_normal": True
        },
        {
            "id": 2,
            "name": "Ligne 2", 
            "color": "Orange",
            "status": "Service normal du métro",
            "statusColor": "text-green-400",
            "icon": "orange-line",
            "is_normal": True
        },
        {
            "id": 4,
            "name": "Ligne 4",
            "color": "Jaune", 
            "status": "Service normal du métro",
            "statusColor": "text-green-400",
            "icon": "yellow-line",
            "is_normal": True
        },
        {
            "id": 5,
            "name": "Ligne 5",
            "color": "Bleue",
            "status": "Service normal du métro", 
            "statusColor": "text-green-400",
            "icon": "blue-line",
            "is_normal": True
        }
    ]

def load_stm_routes(routes_file):
    routes_data = {}
    with open(routes_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            real_id = row["route_id"]              
            short_name = row["route_short_name"] 
            routes_data[real_id] = short_name
    return routes_data

def load_stm_stop_times(filepath):
    stop_times = {}
    with open(filepath, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = (row["trip_id"], row["stop_id"])
            stop_times[key] = row["arrival_time"]
    return stop_times

def load_stm_gtfs_trips(filepath, routes_map):
    trips_data = {}
    with open(filepath, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            trip_id = row["trip_id"]
            real_route_id = row["route_id"]  
            # Convert real_route_id -> short_name
            short_name = routes_map.get(real_route_id, real_route_id)
            w_str = row.get("wheelchair_accessible", "0")
            trips_data[trip_id] = {
                "route_id": short_name, 
                "wheelchair_accessible": w_str
            }
    return trips_data

def stm_map_occupancy_status(status):
    """
    Map GTFS-RT occupancy status to human-readable format
    """
    mapping = {
        0: "MANY_SEATS_AVAILABLE",
        1: "FEW_SEATS_AVAILABLE",
        2: "STANDING_ROOM_ONLY",
        3: "FULL",
    }
    return mapping.get(status, "Unknown")
      

def validate_trip(trip_id, route_id, gtfs_trips):
    trip_info = gtfs_trips.get(trip_id)
    if not trip_info:
        return False
    return trip_info["route_id"] == route_id


def fetch_stm_positions_dict(desired_routes, stm_trips):
    """
    Fetch vehicle positions and extract occupancy data
    """
    positions = {}
    entities = fetch_stm_vehicle_positions()
    if not entities:
        return positions 
    
    for entity in entities:
        if entity.HasField("vehicle"):
            vehicle = entity.vehicle
            route_id = vehicle.trip.route_id
            trip_id = vehicle.trip.trip_id

            # Only store if it's a route/trip we care about & is valid
            if route_id in desired_routes and validate_trip(trip_id, route_id, stm_trips):
                bus_lat = bus_lon = None
                if vehicle.HasField("position"):
                    bus_lat = vehicle.position.latitude
                    bus_lon = vehicle.position.longitude
                
                # Extract occupancy status
                occupancy_raw = None
                if vehicle.HasField("occupancy_status"):
                    occupancy_raw = vehicle.occupancy_status
                
                feed_stop_id = vehicle.stop_id if vehicle.HasField("stop_id") else None

                # Extract current status (IN_TRANSIT_TO, STOPPED_AT, etc.)
                current_status_str = None
                if vehicle.HasField("current_status"):
                    current_status_str = vehicle.current_status 

                positions[(route_id, trip_id)] = {
                    "lat": bus_lat,
                    "lon": bus_lon,
                    "occupancy": occupancy_raw,  # Store raw occupancy value
                    "stop_id": feed_stop_id,
                    "current_status": current_status_str
                }
    
    return positions

def process_stm_trip_updates(
    trip_entities,
    stm_trips,
    stm_stop_times,
    positions_dict,
    desired_combos=BUS_ROUTE_COMBOS,
    combo_info=BUS_DISPLAY_INFO
):
    """
    Process STM trip updates and merge with vehicle positions for occupancy data
    """
    closest_buses = { combo[2]: None for combo in desired_combos }

    # Process real-time updates
    for entity in trip_entities:
        if not entity.HasField("trip_update"):
            continue

        t_update = entity.trip_update
        route_id = t_update.trip.route_id
        trip_id  = t_update.trip.trip_id

        if route_id not in BUS_ROUTES:
            continue

        w_str = stm_trips.get(trip_id, {}).get("wheelchair_accessible", "0")
        wheelchair_accessible = (w_str == "1")

        for stop_time in t_update.stop_time_update:
            stop_id = stop_time.stop_id
            final_key = None
            for (gtfs_route, wanted_stop, key_name) in desired_combos:
                if route_id == gtfs_route and stop_id == wanted_stop:
                    final_key = key_name
                    break
            if not final_key:
                continue

            # Check for skipped stops
            is_skipped = False
            if stop_time.HasField("schedule_relationship"):
                if stop_time.schedule_relationship == 1:  # SKIPPED
                    is_skipped = True

            # Handle skipped/cancelled buses
            if is_skipped:
                bus_obj = {
                    "route_id": route_id,
                    "trip_id": trip_id,
                    "stop_id": stop_id,
                    "arrival_time": "Annulé",
                    "occupancy": "Unknown",
                    "direction": combo_info[final_key]["direction"],
                    "location": combo_info[final_key]["location"],
                    "delayed_text": None,
                    "early_text": None,
                    "at_stop": False,
                    "wheelchair_accessible": wheelchair_accessible,
                    "cancelled": True,
                    "service_status": "cancelled" 
                }
                
                existing = closest_buses[final_key]
                if existing is None or not existing.get("cancelled", False):
                    closest_buses[final_key] = bus_obj
                continue  

            arrival_unix = stop_time.arrival.time if stop_time.HasField("arrival") else None
            if not arrival_unix:
                continue

            # Calculate minutes until arrival
            now_ts = time.time()
            minutes_to_arrival = int((arrival_unix - now_ts) // 60)

            # Check for delays
            scheduled_arrival_str = stm_stop_times.get((trip_id, stop_id))
            delay_text = None
            if scheduled_arrival_str:
                try:
                    h, m, s = map(int, scheduled_arrival_str.split(":"))
                    sched_dt = datetime.now().replace(hour=h % 24, minute=m, second=s, microsecond=0)
                    if sched_dt < datetime.now():
                        sched_dt += timedelta(days=1)

                    predicted_dt = datetime.fromtimestamp(arrival_unix)
                    if predicted_dt > sched_dt:
                        delay_text = f"En retard (planifié à {sched_dt.strftime('%I:%M %p')})"
                except Exception:
                    pass

            # Get occupancy from positions dict
            pos_info = positions_dict.get((route_id, trip_id), {})
            raw_occ = pos_info.get("occupancy")
            occ_str = stm_map_occupancy_status(raw_occ) if raw_occ is not None else "Unknown"

            # Determine if bus is at stop
            at_stop_flag = minutes_to_arrival < 2

            # Get additional position info
            bus_lat = pos_info.get("lat")
            bus_lon = pos_info.get("lon")
            current_status = pos_info.get("current_status")

            bus_obj = {
                "route_id": route_id,
                "trip_id": trip_id,
                "stop_id": stop_id,
                "arrival_time": minutes_to_arrival,
                "occupancy": occ_str,  # Use mapped occupancy string
                "direction": combo_info[final_key]["direction"],
                "location": combo_info[final_key]["location"],
                "delayed_text": delay_text,
                "early_text": None,
                "at_stop": at_stop_flag,
                "wheelchair_accessible": wheelchair_accessible,
                "cancelled": False,
                "service_status": "normal",
                "lat": bus_lat,
                "lon": bus_lon,
                "current_status": current_status
            }

            # Update if this is the closest bus
            existing = closest_buses[final_key]
            if existing is None or (
                (not existing.get("cancelled", False) and not bus_obj["cancelled"]) and
                isinstance(existing["arrival_time"], (int, float)) and
                isinstance(minutes_to_arrival, (int, float)) and
                minutes_to_arrival < existing["arrival_time"]
            ) or (
                existing.get("cancelled", False) and not bus_obj["cancelled"]
            ):
                closest_buses[final_key] = bus_obj

    # Add fallback buses for routes with no real-time data
    now = datetime.now()
    for (gtfs_route, wanted_stop, final_key) in desired_combos:
        if closest_buses[final_key] is None:
            nextScheduled = None
            route_trip_ids = {
                tid for tid, data in stm_trips.items() if data["route_id"] == gtfs_route
            }
            for (trip_id, stop_id), schedTimeStr in stm_stop_times.items():
                if trip_id not in route_trip_ids or stop_id != wanted_stop:
                    continue
                try:
                    parts = schedTimeStr.split(":")
                    hours = int(parts[0]) % 24
                    mins  = int(parts[1])
                    secs  = int(parts[2]) if len(parts) > 2 else 0
                    schedDt = datetime(now.year, now.month, now.day, hours, mins, secs)
                    if schedDt <= now:
                        schedDt += timedelta(days=1)
                    if nextScheduled is None or schedDt < nextScheduled:
                        nextScheduled = schedDt
                except:
                    continue

            arrival_str = nextScheduled.strftime("%I:%M %p") if nextScheduled else "Indisponible"
            fallback = {
                "route_id": gtfs_route,
                "trip_id": "N/A",
                "stop_id": wanted_stop,
                "arrival_time": arrival_str,
                "occupancy": "Unknown",
                "direction": combo_info[final_key]["direction"],
                "location": combo_info[final_key]["location"],
                "delayed_text": None,
                "early_text": None,
                "at_stop": False,
                "wheelchair_accessible": False,
                "cancelled": False,
                "service_status": "scheduled"
            }
            closest_buses[final_key] = fallback

    # Return buses in predefined order
    order = ["61_Est","61_Ouest","36_Est","36_Ouest"]
    return [closest_buses[k] for k in order if closest_buses[k] is not None]


def display_current_alerts():
    """
    Display current STM alerts in a readable format.
    """
    all_alerts = fetch_all_stm_alerts()
    
    print("=== ALERTES GÉNÉRALES STM ===")
    general_alerts = all_alerts["general_alerts"]
    if general_alerts:
        for alert in general_alerts:
            print(f"\n🚨 {alert['header']}")
            print(f"📝 {alert['description']}")
            if alert['start_date']:
                date_info = f"Du {alert['start_date']}"
                if alert['end_date']:
                    date_info += f" au {alert['end_date']}"
                print(f"📅 {date_info}")
            print("-" * 50)
    else:
        print("Aucune alerte générale active.")