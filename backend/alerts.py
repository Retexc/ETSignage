"""
STM Alerts Processing Module
Filters alerts to only show relevant ones for your specific stops
"""

# Your specific stops - only show alerts for these
OUR_STOP_IDS = {"52743", "52744", "62248", "62355"}
OUR_ROUTES = {"36", "61"}

def process_stm_alerts():
    """
    Process STM alerts directly from raw API data
    Shows:
    - ALL network-wide alerts (like strikes)
    - Alerts for routes 36, 61 that affect our specific stops
    - General route alerts (without specific stops) for routes 36, 61
    """
    from .loaders.stm import fetch_stm_alerts
    import re
    
    all_alerts = []
    
    try:
        print("=" * 60)
        print("FETCHING STM ALERTS (DIRECT FROM API)...")
        
        # Fetch raw alerts directly
        raw_alerts = fetch_stm_alerts()
        print(f"Got {len(raw_alerts)} raw alerts from STM API")
        
        if not raw_alerts:
            print("No alerts returned from STM API")
            return []
        
        # Process each raw alert
        for i, alert in enumerate(raw_alerts):
            try:
                print(f"\nProcessing alert {i+1}...")
                
                # Get informed entities
                informed_entities = alert.get("informed_entities", [])
                print(f"  Informed entities: {informed_entities}")
                
                # Check if network-wide alert
                is_network_alert = False
                affected_routes = set()
                affected_stops = set()
                
                for entity in informed_entities:
                    if entity.get("agency_id") == "STM":
                        is_network_alert = True
                        print("  -> This is a NETWORK-WIDE alert")
                    
                    route = entity.get("route_short_name")
                    if route:
                        affected_routes.add(route)
                        print(f"  -> Affects route: {route}")
                    
                    # Check for stop_code
                    stop_code = entity.get("stop_code")
                    if stop_code:
                        affected_stops.add(stop_code)
                        print(f"  -> Affects stop: {stop_code}")
                
                # Get French header and description
                header_texts = alert.get("header_texts", [])
                description_texts = alert.get("description_texts", [])
                
                french_header = ""
                french_description = ""
                
                for header in header_texts:
                    if header.get("language") == "fr":
                        french_header = header.get("text", "")
                        break
                
                for desc in description_texts:
                    if desc.get("language") == "fr":
                        french_description = desc.get("text", "")
                        break
                
                # Remove HTML tags
                french_description = re.sub(r'<[^>]+>', '', french_description)
                
                print(f"  Header: {french_header[:50]}...")
                print(f"  Description: {french_description[:80]}...")
                
                # Decide what to do with this alert
                if is_network_alert:
                    # NETWORK-WIDE ALERT - Always include
                    alert_obj = {
                        "header": french_header or "Alerte STM",
                        "description": french_description or "Aucune description disponible",
                        "routes": [],
                        "is_network_wide": True,
                        "alert_type": "general_network",
                        "severity": "info"
                    }
                    all_alerts.append(alert_obj)
                    print("  [OK] Added as NETWORK alert")
                    
                elif affected_routes:
                    # Check if our routes (36, 61) are affected
                    our_routes = affected_routes & OUR_ROUTES
                    
                    if our_routes:
                        # Check if alert mentions specific stops
                        if affected_stops:
                            # This alert is for specific stops - check if it's one of ours
                            our_stops = affected_stops & OUR_STOP_IDS
                            
                            if our_stops:
                                # STOP-SPECIFIC ALERT for our stops!
                                alert_obj = {
                                    "header": french_header or "Alerte d'arrêt",
                                    "description": french_description or "Aucune description disponible",
                                    "routes": list(our_routes),
                                    "stops": list(our_stops),
                                    "is_network_wide": False,
                                    "alert_type": "stop_specific",
                                    "severity": "warning"
                                }
                                all_alerts.append(alert_obj)
                                print(f"  [OK] Added as STOP alert for stops {', '.join(our_stops)} on route {', '.join(our_routes)}")
                            else:
                                print(f"  [SKIP] Stops {affected_stops} don't include our stops {OUR_STOP_IDS}")
                        else:
                            # General route alert (no specific stops in informed_entities)
                            # BUT we need to check if the description mentions our stops
                            mentioned_our_stops = False
                            for stop_id in OUR_STOP_IDS:
                                if stop_id in french_description:
                                    mentioned_our_stops = True
                                    print(f"  -> Found our stop {stop_id} in description!")
                                    break
                            
                            if mentioned_our_stops:
                                # The description mentions one of our stops
                                alert_obj = {
                                    "header": french_header or "Alerte de ligne",
                                    "description": french_description or "Aucune description disponible",
                                    "routes": list(our_routes),
                                    "is_network_wide": False,
                                    "alert_type": "route_specific",
                                    "severity": "warning"
                                }
                                all_alerts.append(alert_obj)
                                print(f"  [OK] Added as ROUTE alert (mentions our stops in text) for {', '.join(our_routes)}")
                            else:
                                print(f"  [SKIP] Route alert doesn't mention our specific stops in description")
                    else:
                        print(f"  [SKIP] Routes {affected_routes} don't include 36 or 61")
                else:
                    print("  [SKIP] No agency_id or route info")
                
            except Exception as e:
                print(f"  [ERROR] Processing alert {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'=' * 60}")
        print(f"TOTAL ALERTS PROCESSED: {len(all_alerts)}")
        print(f"{'=' * 60}\n")
        
        return all_alerts
        
    except Exception as e:
        print(f"CRITICAL ERROR in process_stm_alerts: {e}")
        import traceback
        traceback.print_exc()
        return []