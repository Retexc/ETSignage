# How to Change Bus Routes Configuration

This guide shows you how to easily change which bus routes are displayed on the ETSignage system.

## Quick Start

All bus route configuration is now centralized in **one file**: `backend/config.py`

## What You Need to Change

Open `backend/config.py` and scroll down to the section marked:
```python
# ============================================================================
# BUS ROUTES CONFIGURATION - ETS (École de technologie supérieur)
# ============================================================================
```

### 1. Bus Routes List
```python
BUS_ROUTES = ["61", "36"]
```
**Change this** to the route numbers you want to monitor (e.g., `["171", "180", "164"]`)

### 2. Stop IDs
```python
BUS_STOP_IDS = ["52744", "52743", "62355", "62248"]
```
**Change this** to your specific bus stop IDs. You can find these in the STM GTFS data `stops.txt` file.

### 3. Route Combinations
```python
BUS_ROUTE_COMBOS = [
    ("61", "52744", "61_Est"),
    ("61", "52743", "61_Ouest"),
    ("36", "62355", "36_Est"),
    ("36", "62248", "36_Ouest"),
]
```
Each tuple represents: `(route_number, stop_id, internal_key)`
- **route_number**: The bus route (e.g., "61")
- **stop_id**: The specific stop at your location
- **internal_key**: A unique identifier (keep format: `route_direction`)

### 4. Display Information
```python
BUS_DISPLAY_INFO = {
    "61_Est": {
        "direction": "Est",
        "location": "Station de Métro Bonaventure"
    },
    "61_Ouest": {
        "direction": "Ouest",
        "location": "Station de Métro Côte-Vertu"
    },
    # ... more routes
}
```
**Change this** to match your internal_keys from step 3. Update the location names to match your destination.

## Example: Switching Back to BDEB Routes

If you want to switch back to the original Collège de Bois-de-Boulogne configuration:

```python
BUS_ROUTES = ["171", "180", "164"]

BUS_STOP_IDS = ["50270", "62374", "62420"]

BUS_ROUTE_COMBOS = [
    ("171", "50270", "171_Est"),
    ("171", "62374", "171_Ouest"),
    ("180", "50270", "180_Est"),
    ("180", "62374", "180_Ouest"),
    ("164", "50270", "164_Est"),
    ("164", "62420", "164_Ouest"),
]

BUS_DISPLAY_INFO = {
    "171_Est": {
        "direction": "Est",
        "location": "Collège de Bois-de-Boulogne"
    },
    "171_Ouest": {
        "direction": "Ouest",
        "location": "Henri-Bourassa/du Bois-de-Boulogne"
    },
    "180_Est": {
        "direction": "Est",
        "location": "Collège de Bois-de-Boulogne"
    },
    "180_Ouest": {
        "direction": "Ouest",
        "location": "Henri-Bourassa/du Bois-de-Boulogne"
    },
    "164_Est": {
        "direction": "Est",
        "location": "Collège de Bois-de-Boulogne"
    },
    "164_Ouest": {
        "direction": "Ouest",
        "location": "du Bois-de-Boulogne/Henri-Bourassa"
    },
}
```

## After Making Changes

1. Save `backend/config.py`
2. Restart the application:
   ```bash
   # Stop the app (Ctrl+C if running)
   # Then restart:
   start.bat
   ```

That's it! No need to search through multiple files anymore. Everything is in one place.

## Files That Were Updated

The following files now automatically use the configuration from `backend/config.py`:
- `backend/main.py` - Main application server
- `backend/loaders/stm.py` - STM data loading
- `backend/alerts.py` - Alert processing

You **don't need to edit** these files anymore!
