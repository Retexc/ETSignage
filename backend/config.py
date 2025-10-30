import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# STM API Credentials
STM_API_KEY = os.getenv("STM_API_KEY")
STM_REALTIME_ENDPOINT = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/tripUpdates"
STM_VEHICLE_POSITIONS_ENDPOINT = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions"
STM_ALERTS_ENDPOINT = "https://api.stm.info/pub/od/i3/v2/messages/etatservice"


# Weather API key
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Global delay configuration
GLOBAL_DELAY_MINUTES = int(os.getenv("GLOBAL_DELAY_MINUTES", "0"))

if not STM_API_KEY:
    raise ValueError("STM_API_KEY not found in environment variables")
if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY not found in environment variables")

# ============================================================================
# BUS ROUTES CONFIGURATION - ETS (École de technologie supérieur)
# ============================================================================

BUS_ROUTES = ["61", "36"]

BUS_STOP_IDS = ["52743", "52744", "62248", "62355"]

BUS_ROUTE_COMBOS = [
    ("61", "52743", "61_Est"),
    ("61", "52744", "61_Ouest"),
    ("36", "62248", "36_Est"),
    ("36", "62355", "36_Ouest"),
]

BUS_DISPLAY_INFO = {
    "61_Est": {
        "direction": "Est",
        "location": "École de technologie supérieure (Peel / Notre-Dame)"
    },
    "61_Ouest": {
        "direction": "Ouest",
        "location": "École de technologie supérieure (Peel / Notre-Dame)"
    },
    "36_Est": {
        "direction": "Est",
        "location": "Notre-Dame / Peel"
    },
    "36_Ouest": {
        "direction": "Ouest",
        "location": "Notre-Dame / Peel"
    },
}