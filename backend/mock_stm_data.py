def get_mock_bus_data():
    return {
        'stop_52743': [
            {'route': '36', 'headsign': 'Monk', 'arrival_time': 5, 'occupancy': 'MANY_SEATS_AVAILABLE'},
            {'route': '36', 'headsign': 'Monk', 'arrival_time': 15, 'occupancy': 'STANDING_ROOM_ONLY'},
        ],
        'stop_52744': [
            {'route': '36', 'headsign': 'Crémazie', 'arrival_time': 8, 'occupancy': 'FEW_SEATS_AVAILABLE'},
        ],
        'stop_62248': [
            {'route': '61', 'headsign': 'Laurier', 'arrival_time': 3, 'occupancy': 'MANY_SEATS_AVAILABLE'},
            {'route': '61', 'headsign': 'Laurier', 'arrival_time': 12, 'occupancy': 'FEW_SEATS_AVAILABLE'},
        ],
        'stop_62355': [
            {'route': '61', 'headsign': 'Maurice-Duplessis', 'arrival_time': 7, 'occupancy': 'STANDING_ROOM_ONLY'},
        ]
    }

def get_mock_metro_data():
    return {
        'green_line': {'status': 'normal', 'message': None},
        'orange_line': {'status': 'normal', 'message': None},
    }

def get_mock_alerts():
    return []