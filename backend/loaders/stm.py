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
    STM_ALERTS_ENDPOINT
)
from backend.utils import load_csv_dict  
# Cache for calendar data
_calendar_data = None
_calendar_dates_data = None

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

def fetch_stm_alerts():
    headers = {
        "accept": "application/json",
        "apiKey": STM_API_KEY,
    }
    try:
        response = requests.get(STM_ALERTS_ENDPOINT, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            if isinstance(json_data, dict) and "alerts" in json_data:
                return json_data["alerts"]
            elif isinstance(json_data, list):
                return json_data
            else:
                print(f"Unexpected STM alerts response format: {json_data}")
                return []
        return []
    except Exception as e:
        print(f"Error fetching alerts: {str(e)}")
        return []

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
        try:
            informed_entities = alert.get("informed_entities", [])
            is_general_alert = False
            
            for entity in informed_entities:
                if entity.get("agency_id") == "STM":
                    is_general_alert = True
                    break
            
            if is_general_alert:
                header_texts = alert.get("header_texts", [])
                description_texts = alert.get("description_texts", [])
                
                french_header = None
                french_description = None
                
                for header in header_texts:
                    if header.get("language") == "fr":
                        french_header = header.get("text", "")
                        break
                
                for desc in description_texts:
                    if desc.get("language") == "fr":
                        french_description = desc.get("text", "")
                        break
                
                # Get active period information
                active_periods = alert.get("active_periods", {})
                start_time = active_periods.get("start")
                end_time = active_periods.get("end")
                

                start_date = None
                end_date = None
                if start_time:
                    start_date = datetime.fromtimestamp(start_time).strftime("%d/%m/%Y")
                if end_time:
                    end_date = datetime.fromtimestamp(end_time).strftime("%d/%m/%Y")
                
                # Create alert object
                alert_obj = {
                    "header": french_header or "Alerte STM",
                    "description": french_description or "Aucune description disponible",
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": True,  
                    "alert_type": "general" 
                }
                
                general_alerts.append(alert_obj)
                
        except Exception as e:
            print(f"Error processing general alert: {e}")
            continue
    
    return general_alerts

def fetch_stm_route_specific_alerts(routes_of_interest=None):
    """
    Fetch alerts for specific routes that explicitly affect your specific bus stops only.
    
    Args:
        routes_of_interest: List of route short names to filter for (e.g., ["171", "180", "164"])
    
    Returns:
        List of route-specific alerts that explicitly mention your specific stop IDs
    """
    if routes_of_interest is None:
        routes_of_interest = ["171", "180", "164"]  
    

    your_stop_ids = ["50270", "62374", "62420"]
    
    alerts_data = fetch_stm_alerts()
    if not alerts_data:
        return []
    
    route_alerts = []
    
    for alert in alerts_data:
        try:
            informed_entities = alert.get("informed_entities", [])
            relevant_routes = []
            
            for entity in informed_entities:
                route_short_name = entity.get("route_short_name")
                if route_short_name and route_short_name in routes_of_interest:
                    relevant_routes.append(route_short_name)
            
            if relevant_routes:
                description_texts = alert.get("description_texts", [])
                french_description = None
                
                for desc in description_texts:
                    if desc.get("language") == "fr":
                        french_description = desc.get("text", "")
                        break
                
                affects_your_stops = False
                if french_description:
                    for stop_id in your_stop_ids:
                        if stop_id in french_description:
                            affects_your_stops = True
                            print(f"Found alert for your stop {stop_id}: {french_description[:100]}...")
                            break
                
                if affects_your_stops:
                    # Get French header
                    header_texts = alert.get("header_texts", [])
                    french_header = None
                    
                    for header in header_texts:
                        if header.get("language") == "fr":
                            french_header = header.get("text", "")
                            break
                    
                    active_periods = alert.get("active_periods", {})
                    start_time = active_periods.get("start")
                    end_time = active_periods.get("end")
                    
                    start_date = None
                    end_date = None
                    if start_time:
                        start_date = datetime.fromtimestamp(start_time).strftime("%d/%m/%Y")
                    if end_time:
                        end_date = datetime.fromtimestamp(end_time).strftime("%d/%m/%Y")
                    
                    alert_obj = {
                        "header": french_header or "Alerte de ligne",
                        "description": french_description or "Aucune description disponible",
                        "affected_routes": relevant_routes,
                        "start_date": start_date,
                        "end_date": end_date,
                        "is_active": True,
                        "alert_type": "route_specific"
                    }
                    
                    route_alerts.append(alert_obj)
                else:
                    print(f"Filtered out alert for route {relevant_routes} - doesn't mention your stops")
                
        except Exception as e:
            print(f"Error processing route alert: {e}")
            continue
    
    print(f"Found {len(route_alerts)} route-specific alerts that affect your stops")
    return route_alerts

def fetch_all_stm_alerts():
    """
    Fetch both general network alerts and route-specific alerts.
    Returns a dictionary with both types of alerts.
    """
    return {
        "general_alerts": fetch_stm_general_alerts(),
        "route_alerts": fetch_stm_route_specific_alerts(),
        "metro_status": process_metro_alerts()  
    }

def process_metro_alerts():
    """
    Fetch and process metro line alerts from STM API.
    Returns a dictionary mapping line numbers to their status information.
    """
    alerts_data = fetch_stm_alerts()
    if not alerts_data:
        print("No alerts data received")
        return get_default_metro_status()
    
    metro_status = {
        "1": {
            "name": "Ligne 1",
            "color": "Verte", 
            "status": "Service normal du métro",
            "statusColor": "text-green-400",
            "icon": "green-line",
            "is_normal": True
        },
        "2": {
            "name": "Ligne 2",
            "color": "Orange",
            "status": "Service normal du métro", 
            "statusColor": "text-green-400",
            "icon": "orange-line",
            "is_normal": True
        },
        "4": {
            "name": "Ligne 4", 
            "color": "Jaune",
            "status": "Service normal du métro",
            "statusColor": "text-green-400", 
            "icon": "yellow-line",
            "is_normal": True
        },
        "5": {
            "name": "Ligne 5",
            "color": "Bleue", 
            "status": "Service normal du métro",
            "statusColor": "text-green-400",
            "icon": "blue-line", 
            "is_normal": True
        }
    }
    
    # Process alerts from API
    for alert in alerts_data:
        try:
            # Check if alert has informed_entities for metro lines
            informed_entities = alert.get("informed_entities", [])
            for entity in informed_entities:
                route_short_name = entity.get("route_short_name")
                
                # Only process metro lines (1, 2, 4, 5)
                if route_short_name in ["1", "2", "4", "5"]:
                    description_texts = alert.get("description_texts", [])
                    french_description = None
                    
                    for desc in description_texts:
                        if desc.get("language") == "fr":
                            french_description = desc.get("text", "")
                            break
                    
                    if french_description:
                        # Check if it's a normal service message
                        is_normal_service = "service normal" in french_description.lower()
                        
                        metro_status[route_short_name]["status"] = french_description
                        metro_status[route_short_name]["is_normal"] = is_normal_service
                        metro_status[route_short_name]["statusColor"] = "text-green-400" if is_normal_service else "text-red-400"
                        
        except Exception as e:
            print(f"Error processing alert: {e}")
            continue
    
    metro_lines = []
    for line_id, line_data in metro_status.items():
        metro_lines.append({
            "id": int(line_id),
            "name": line_data["name"],
            "color": line_data["color"],
            "status": line_data["status"],
            "statusColor": line_data["statusColor"],
            "icon": line_data["icon"],
            "is_normal": line_data["is_normal"]
        })
    
    metro_lines.sort(key=lambda x: x["id"])
    
    return metro_lines

def get_default_metro_status():
    """
    Returns default metro status when API is unavailable.
    """
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
    mapping = {
        1: "MANY_SEATS_AVAILABLE",
        2: "FEW_SEATS_AVAILABLE",
        3: "STANDING_ROOM_ONLY",
        4: "FULL",
    }
    return mapping.get(status, "Unknown")
      

def validate_trip(trip_id, route_id, gtfs_trips):
    trip_info = gtfs_trips.get(trip_id)
    if not trip_info:
        return False
    return trip_info["route_id"] == route_id


def fetch_stm_positions_dict(desired_routes, stm_trips):
    positions = {}
    entities = fetch_stm_vehicle_positions()
    if not entities:
        return positions 
    
    for entity in entities:
        if entity.HasField("vehicle"):
            vehicle = entity.vehicle
            route_id = vehicle.trip.route_id
            trip_id = vehicle.trip.trip_id

            # only store if it's a route/trip we care about & is valid
            if route_id in desired_routes and validate_trip(trip_id, route_id, stm_trips):
                bus_lat = bus_lon = None
                if vehicle.HasField("position"):
                    bus_lat = vehicle.position.latitude
                    bus_lon = vehicle.position.longitude
                
                occupancy_raw = None
                if vehicle.HasField("occupancy_status"):
                    occupancy_raw = vehicle.occupancy_status
                
                feed_stop_id = vehicle.stop_id if vehicle.HasField("stop_id") else None

                # currentStatus => e.g. IN_TRANSIT_TO, STOPPED_AT, etc.
                current_status_str = None
                if vehicle.HasField("current_status"):
                    current_status_str = vehicle.current_status 

                positions[(route_id, trip_id)] = {
                    "lat": bus_lat,
                    "lon": bus_lon,
                    "occupancy": occupancy_raw,
                    "feed_stop_id": feed_stop_id,
                    "current_status": current_status_str,
                }
    return positions


def process_stm_trip_updates(trip_entities, stm_trips, stm_stop_times, positions_dict):
    import time
    from datetime import datetime, timedelta

    desired_combos = [
        ("171","50270","171_Est"),
        ("171","62374","171_Ouest"),
        ("180","50270","180_Est"),
        ("180","62374","180_Ouest"),
        ("164","50270","164_Est"),
        ("164","62420","164_Ouest"),
    ]

    combo_info = {
        "171_Est":   {"direction": "Est",    "location": "Collège de Bois-de-Boulogne"},
        "171_Ouest": {"direction": "Ouest",  "location": "Henri-Bourassa/du Bois-de-Boulogne"},
        "180_Est":   {"direction": "Est",    "location": "Collège de Bois-de-Boulogne"},
        "180_Ouest": {"direction": "Ouest",  "location": "Henri-Bourassa/du Bois-de-Boulogne"},
        "164_Est":   {"direction": "Est",    "location": "Collège de Bois-de-Boulogne"},
        "164_Ouest": {"direction": "Ouest",  "location": "du Bois-de-Boulogne/Henri-Bourassa"},
    }

    closest_buses = { combo[2]: None for combo in desired_combos }

    # 1) Real-time updates
    for entity in trip_entities:
        if not entity.HasField("trip_update"):
            continue

        t_update = entity.trip_update
        route_id = t_update.trip.route_id
        trip_id  = t_update.trip.trip_id

        if route_id not in ["171","180","164"]:
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

            # CHECK FOR SKIPPED STOPS FIRST
            is_skipped = False
            if stop_time.HasField("schedule_relationship"):
                if stop_time.schedule_relationship == 1:  # SKIPPED
                    is_skipped = True

            # If this stop is skipped, create a cancelled bus entry
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

            # Minutes until arrival (floor)
            now_ts = time.time()
            minutes_to_arrival = (arrival_unix - now_ts) // 60

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

            # Occupancy
            pos_info = positions_dict.get((route_id, trip_id), {})
            raw_occ = pos_info.get("occupancy")
            occ_str = stm_map_occupancy_status(raw_occ) if raw_occ else "Unknown"

            at_stop_flag = isinstance(minutes_to_arrival, (int, float)) and minutes_to_arrival < 2

            bus_obj = {
                "route_id": route_id,
                "trip_id": trip_id,
                "stop_id": stop_id,
                "arrival_time": minutes_to_arrival,
                "occupancy": occ_str,
                "direction": combo_info[final_key]["direction"],
                "location": combo_info[final_key]["location"],
                "delayed_text": delay_text,
                "early_text": None,
                "at_stop": at_stop_flag,
                "wheelchair_accessible": wheelchair_accessible,
                "cancelled": False,  
                "service_status": "normal"  
            }

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

    order = ["171_Est","171_Ouest","180_Est","180_Ouest","164_Est","164_Ouest"]
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
    
    print("\n=== ALERTES DE LIGNES SPÉCIFIQUES ===")
    route_alerts = all_alerts["route_alerts"]
    if route_alerts:
        for alert in route_alerts:
            print(f"\n🚌 {alert['header']}")
            print(f"🛣️  Lignes affectées: {', '.join(alert['affected_routes'])}")
            print(f"📝 {alert['description']}")
            if alert['start_date']:
                date_info = f"Du {alert['start_date']}"
                if alert['end_date']:
                    date_info += f" au {alert['end_date']}"
                print(f"📅 {date_info}")
            print("-" * 50)
    else:
        print("Aucune alerte de ligne spécifique active.")


def debug_print_stm_occupancy_status(desired_routes, stm_trips):
    entities = fetch_stm_vehicle_positions()
    
    if not entities:
        print("No STM vehicle positions found.")
        return
    
    print("----- STM Vehicle Positions (Occupancy + Position + currentStatus) -----")
    for entity in entities:
        if entity.HasField("vehicle"):
            vehicle = entity.vehicle
            route_id = vehicle.trip.route_id
            trip_id = vehicle.trip.trip_id
            
            if route_id in desired_routes and validate_trip(trip_id, route_id, stm_trips):
                
                # Occupancy
                if vehicle.HasField("occupancy_status"):
                    raw_status = vehicle.occupancy_status
                    mapped_status = stm_map_occupancy_status(raw_status)
                else:
                    mapped_status = "Unknown"
                
                # Position
                lat_str = "no position"
                lon_str = ""
                if vehicle.HasField("position"):
                    pos = vehicle.position
                    lat_str = f"{pos.latitude:.6f}"
                    lon_str = f"{pos.longitude:.6f}"

                # currentStatus
                current_stat_str = "No current_status"
                if vehicle.HasField("current_status"):
                    current_stat_str = str(vehicle.current_status)  

                print(
                    f"Route={route_id}, Trip={trip_id}, "
                    f"Occupancy={mapped_status}, "
                    f"Lat/Lon={lat_str}{', '+lon_str if lon_str else ''}, "
                    f"currentStatus={current_stat_str}"
                )
    print("--------------------------------------------------------------------------")