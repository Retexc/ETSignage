"""
Mock STM data for development/testing
Prevents hitting real API rate limits
"""

def get_mock_trip_entities():
    """Mock GTFS realtime trip updates"""
    # Return empty list - we'll build mock buses in process function
    return []

def get_mock_vehicle_positions():
    """Mock vehicle position data"""
    return []

def get_mock_alerts():
    """Mock STM alerts data"""
    return []

def get_mock_processed_buses():
    """Mock processed bus data ready for frontend"""
    return [
        {
            "route_id": "36",
            "route_short_name": "36",
            "trip_headsign": "Monk",
            "stop_id": "52743",
            "stop_name": "de Maisonneuve / du Fort",
            "arrival_time": 5,
            "occupancy_status": "MANY_SEATS_AVAILABLE",
            "cancelled": False,
            "delayed_text": None
        },
        {
            "route_id": "36",
            "route_short_name": "36",
            "trip_headsign": "Monk",
            "stop_id": "52743",
            "stop_name": "de Maisonneuve / du Fort",
            "arrival_time": 15,
            "occupancy_status": "FEW_SEATS_AVAILABLE",
            "cancelled": False,
            "delayed_text": None
        },
        {
            "route_id": "36",
            "route_short_name": "36",
            "trip_headsign": "Crémazie",
            "stop_id": "52744",
            "stop_name": "de Maisonneuve / Atwater",
            "arrival_time": 8,
            "occupancy_status": "STANDING_ROOM_ONLY",
            "cancelled": False,
            "delayed_text": None
        },
        {
            "route_id": "61",
            "route_short_name": "61",
            "trip_headsign": "Laurier",
            "stop_id": "62248",
            "stop_name": "Notre-Dame / Peel",
            "arrival_time": 3,
            "occupancy_status": "MANY_SEATS_AVAILABLE",
            "cancelled": False,
            "delayed_text": None
        },
        {
            "route_id": "61",
            "route_short_name": "61",
            "trip_headsign": "Maurice-Duplessis",
            "stop_id": "62355",
            "stop_name": "Notre-Dame / University",
            "arrival_time": 12,
            "occupancy_status": "FEW_SEATS_AVAILABLE",
            "cancelled": False,
            "delayed_text": None
        }
    ]

def get_mock_metro_lines():
    """Mock metro line status"""
    return [
        {
            "id": 1,
            "name": "Ligne 1",
            "color": "Verte",
            "status": "Service normal du métro",
            "statusColor": "text-green-400",
            "icon": "green-line",
            "is_normal": True,
            "alert_description": None
        },
        {
            "id": 2,
            "name": "Ligne 2",
            "color": "Orange",
            "status": "Service normal du métro",
            "statusColor": "text-orange-400",
            "icon": "orange-line",
            "is_normal": True,
            "alert_description": None
        }
    ]