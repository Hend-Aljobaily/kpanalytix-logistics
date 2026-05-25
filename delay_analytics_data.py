"""
Saudi Arabia & GCC Shipping Optimizer — Delay Analytics Data
Root-cause analysis, driver trip history, location hotspots, and route optimization.
"""

import random
import math
from datetime import datetime, timedelta

from config import (
    PORTS, ALL_DESTINATIONS, CARGO_TYPES, PRECOMPUTED_ROUTES,
    get_precomputed_route,
)

# ── Delay Cause Pool ──
CAUSE_TEMPLATES = [
    {
        "cause": "Port Congestion",
        "tpl": "High vessel queue at {port}, +{hrs:.1f}h unloading delay",
        "delay_range": (1.5, 4.0),
        "type": "port",
    },
    {
        "cause": "Customs Clearance",
        "tpl": "Extended inspection for {cargo}, +{hrs:.1f}h processing",
        "delay_range": (1.0, 3.5),
        "type": "port",
    },
    {
        "cause": "Driver Break",
        "tpl": "Driver exceeded rest period by {hrs:.1f}h at {location}",
        "delay_range": (0.5, 2.5),
        "type": "road",
    },
    {
        "cause": "Road Congestion",
        "tpl": "Heavy traffic on {route_segment}, added {hrs:.1f}h",
        "delay_range": (1.0, 3.0),
        "type": "road",
    },
    {
        "cause": "Weather",
        "tpl": "Sandstorm advisory on {route_segment}, speed reduced to {speed} km/h",
        "delay_range": (1.5, 4.5),
        "type": "road",
    },
    {
        "cause": "Mechanical Issue",
        "tpl": "Truck required {issue} near {location}",
        "delay_range": (2.0, 6.0),
        "type": "road",
    },
    {
        "cause": "Checkpoint Delay",
        "tpl": "Extended security check at {location}, +{hrs:.1f}h",
        "delay_range": (0.5, 2.0),
        "type": "checkpoint",
    },
    {
        "cause": "Loading Delay",
        "tpl": "Cargo {cargo} required additional securing, +{hrs:.1f}h at port",
        "delay_range": (1.0, 3.0),
        "type": "port",
    },
]

MECHANICAL_ISSUES = [
    "tire replacement", "brake inspection", "coolant refill",
    "engine diagnostics", "fuel filter change", "alternator repair",
]

CHECKPOINT_NAMES = [
    "Al Batha Border", "King Fahd Causeway", "Haradh Checkpoint",
    "Tuwaiq Checkpoint", "Salwa Border", "Al Khafji Gate",
    "Jizan Gateway", "Tabuk Northern Post", "Ras Tanura Gate",
]

ROUTE_SEGMENTS = [
    "Riyadh-Dammam Highway", "Jeddah-Makkah Expressway",
    "Northern Corridor (Tabuk-Hail)", "Dammam-Qatar Coastal Road",
    "Red Sea Highway (Jeddah-Yanbu)", "Southern Route (Jeddah-Abha)",
    "Trans-Arabia Highway", "Eastern Ring Road",
    "Madinah-Buraidah Highway", "Gulf Coastal Road",
]


def _seed_analytics():
    """Same hour-based seed pattern as company_data for consistency."""
    now = datetime.now()
    random.seed(now.year * 1000000 + now.month * 10000 + now.day * 100 + now.hour + 42)


def _pick_route_location(shipment):
    """Pick a realistic location name along a shipment's route."""
    port_short = shipment["port"].split("(")[0].strip()
    dest = shipment["destination"]
    segment = f"{port_short} \u2192 {dest}"
    return random.choice([segment] + CHECKPOINT_NAMES[:4])


def _generate_cause(shipment):
    """Generate a single delay cause for a shipment."""
    tpl = random.choice(CAUSE_TEMPLATES)
    hrs = round(random.uniform(*tpl["delay_range"]), 1)
    port_short = shipment["port"].split("(")[0].strip()
    location = _pick_route_location(shipment)

    desc = tpl["tpl"].format(
        port=port_short,
        cargo=shipment["cargo"],
        hrs=hrs,
        location=location,
        route_segment=random.choice(ROUTE_SEGMENTS),
        speed=random.randint(30, 60),
        issue=random.choice(MECHANICAL_ISSUES),
    )

    now = datetime.now()
    ts = now - timedelta(hours=random.uniform(1, 12))

    return {
        "cause": tpl["cause"],
        "description": desc,
        "delay_hrs": hrs,
        "location": location,
        "timestamp": ts,
        "type": tpl["type"],
    }


# ═══════════════════════════════════════════════════════════════
# 1a. Delay Root Cause Generator
# ═══════════════════════════════════════════════════════════════
def generate_delay_causes(shipments):
    """For each delayed/at-risk shipment, generate 1-3 root causes."""
    causes = {}
    for s in shipments:
        if s["time_status"] not in ("Delayed", "At Risk"):
            continue
        count = 3 if s["time_status"] == "Delayed" else random.randint(1, 2)
        ship_causes = [_generate_cause(s) for _ in range(count)]
        causes[s["id"]] = ship_causes
    return causes


# ═══════════════════════════════════════════════════════════════
# 1b. Driver Trip History Generator
# ═══════════════════════════════════════════════════════════════
def generate_driver_history(driver, company_shipments):
    """Generate 30 historical trips for a driver over the past 60 days."""
    now = datetime.now()
    on_time_pct = driver["stats"]["on_time_pct"] / 100.0

    # Build route pool from company shipments and precomputed routes
    route_pool = []
    for s in company_shipments:
        route_pool.append((s["port"], s["destination"]))
    # Add some variety from precomputed routes
    for key in list(PRECOMPUTED_ROUTES.keys())[:8]:
        route_pool.append(key)
    if not route_pool:
        route_pool = list(PRECOMPUTED_ROUTES.keys())[:5]

    # Inject a recurring pattern: pick one route this driver is "bad" at
    pattern_route = random.choice(route_pool) if route_pool else None
    pattern_cause = random.choice(["Driver Break", "Road Congestion", "Checkpoint Delay"])

    trips = []
    for i in range(30):
        days_ago = random.uniform(1, 60)
        trip_date = (now - timedelta(days=days_ago)).replace(hour=random.randint(5, 20), minute=0, second=0, microsecond=0)

        port, dest = random.choice(route_pool)
        route_data = get_precomputed_route(port, dest)
        distance_km = route_data["distance_km"]
        expected_hrs = route_data["duration_hrs"]

        is_on_time = random.random() < on_time_pct

        # Pattern injection — this driver is worse on their pattern route
        is_pattern = (port, dest) == pattern_route
        if is_pattern:
            is_on_time = random.random() < (on_time_pct * 0.5)

        if is_on_time:
            variation = random.uniform(-0.5, 0.5)
            actual_hrs = max(expected_hrs * 0.9, expected_hrs + variation)
            delay_hrs = 0
            delay_reason = None
        else:
            delay_hrs = round(random.uniform(0.5, 5.0), 1)
            actual_hrs = expected_hrs + delay_hrs
            if is_pattern:
                delay_reason = pattern_cause
            else:
                delay_reason = random.choice([t["cause"] for t in CAUSE_TEMPLATES])

        port_short = port.split("(")[0].strip()
        trips.append({
            "trip_id": f'{driver["id"]}-T{i+1:02d}',
            "date": trip_date,
            "port": port_short,
            "destination": dest,
            "cargo": random.choice(CARGO_TYPES),
            "distance_km": distance_km,
            "expected_hrs": round(expected_hrs, 1),
            "actual_hrs": round(actual_hrs, 1),
            "delay_hrs": round(delay_hrs, 1),
            "on_time": is_on_time,
            "delay_reason": delay_reason,
            "route_name": f"{port_short} \u2192 {dest}",
        })

    trips.sort(key=lambda t: t["date"], reverse=True)
    return trips


# ═══════════════════════════════════════════════════════════════
# 1c. Location Hotspot Generator
# ═══════════════════════════════════════════════════════════════
def generate_location_hotspots(shipments, company_id):
    """Identify delay-prone locations for a company."""
    comp_shipments = [s for s in shipments if s.get("company_id") == company_id]
    if not comp_shipments:
        return []

    hotspots = []

    # Port congestion hotspots
    ports_used = set(s["port"] for s in comp_shipments)
    for port_name in ports_used:
        port_coords = PORTS[port_name]
        avg_delay = round(random.uniform(1.0, 4.5), 1)
        frequency = random.randint(3, 12)
        hotspots.append({
            "name": port_name.split("(")[0].strip(),
            "lat": port_coords["lat"],
            "lon": port_coords["lon"],
            "type": "port",
            "avg_delay_hrs": avg_delay,
            "frequency": frequency,
            "description": f"Avg {avg_delay}h unloading wait, {frequency} delays in 30 days",
        })

    # Road segment / checkpoint hotspots along company routes
    route_keys = set()
    for s in comp_shipments:
        route_keys.add((s["port"], s["destination"]))

    checkpoint_idx = 0
    for port_name, dest_name in list(route_keys)[:3]:
        route = get_precomputed_route(port_name, dest_name)
        waypoints = route["waypoints"]
        if len(waypoints) < 3:
            continue
        # Pick a midpoint as a hotspot
        mid_idx = len(waypoints) // 2
        mid_wp = waypoints[mid_idx]
        # Add jitter
        lat = mid_wp[0] + random.uniform(-0.1, 0.1)
        lon = mid_wp[1] + random.uniform(-0.1, 0.1)

        cp_name = CHECKPOINT_NAMES[checkpoint_idx % len(CHECKPOINT_NAMES)]
        checkpoint_idx += 1
        avg_delay = round(random.uniform(0.5, 3.0), 1)
        frequency = random.randint(2, 8)

        hotspot_type = random.choice(["checkpoint", "road_segment"])
        if hotspot_type == "checkpoint":
            desc = f"Security/border check causing avg {avg_delay}h delay, {frequency} incidents"
        else:
            desc = f"Congestion hotspot, avg {avg_delay}h slowdown, {frequency} occurrences"

        hotspots.append({
            "name": cp_name,
            "lat": lat,
            "lon": lon,
            "type": hotspot_type,
            "avg_delay_hrs": avg_delay,
            "frequency": frequency,
            "description": desc,
        })

    # Sort by impact (delay * frequency)
    hotspots.sort(key=lambda h: h["avg_delay_hrs"] * h["frequency"], reverse=True)
    return hotspots


# ═══════════════════════════════════════════════════════════════
# 1d. Active Incidents & Alternate Routes
# ═══════════════════════════════════════════════════════════════
INCIDENT_TYPES = [
    {"type": "accident", "desc": "Multi-vehicle accident reported", "icon": "collision"},
    {"type": "road_closure", "desc": "Road section closed for maintenance", "icon": "roadblock"},
    {"type": "sandstorm", "desc": "Sandstorm reducing visibility to near-zero", "icon": "weather"},
    {"type": "construction", "desc": "Major construction zone, single-lane traffic", "icon": "construction"},
]


def _offset_waypoints(waypoints, offset_deg):
    """Create alternate route by offsetting middle waypoints perpendicular to the route."""
    if len(waypoints) < 3:
        return waypoints[:]

    alt = [waypoints[0][:]]  # copy start
    for i in range(1, len(waypoints) - 1):
        # Offset perpendicular to route direction
        prev = waypoints[i - 1]
        curr = waypoints[i]
        nxt = waypoints[i + 1]
        # Direction vector
        dx = nxt[1] - prev[1]
        dy = nxt[0] - prev[0]
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            alt.append(curr[:])
            continue
        # Perpendicular (rotate 90 deg)
        perp_lat = -dx / length * offset_deg
        perp_lon = dy / length * offset_deg
        # Taper offset: strongest in middle, weaker at edges
        t = i / (len(waypoints) - 1)
        taper = math.sin(t * math.pi)
        alt.append([
            curr[0] + perp_lat * taper,
            curr[1] + perp_lon * taper,
        ])
    alt.append(waypoints[-1][:])  # copy end
    return alt


def generate_active_incidents(shipments, company_id):
    """Generate 1-2 active incidents for in-transit shipments of a company."""
    comp_in_transit = [
        s for s in shipments
        if s.get("company_id") == company_id and s["status"] == "In Transit"
    ]
    if not comp_in_transit:
        return []

    count = min(2, len(comp_in_transit))
    selected = random.sample(comp_in_transit, count)
    incidents = []

    for s in selected:
        waypoints = s["route"]["waypoints"]
        if len(waypoints) < 2:
            continue

        incident_def = random.choice(INCIDENT_TYPES)

        # Place incident along route
        if len(waypoints) == 2:
            # For 2-point routes, place incident at midpoint
            mid_lat = (waypoints[0][0] + waypoints[1][0]) / 2
            mid_lon = (waypoints[0][1] + waypoints[1][1]) / 2
            incident_loc = [mid_lat, mid_lon]
            # Create a 3-point route so we can generate an alternate
            extended_wps = [waypoints[0], [mid_lat, mid_lon], waypoints[1]]
        else:
            frac = random.uniform(0.4, 0.7)
            idx = int(frac * (len(waypoints) - 1))
            idx = max(1, min(idx, len(waypoints) - 2))
            incident_loc = waypoints[idx]
            extended_wps = waypoints

        # Generate alternate route
        offset = random.choice([-1, 1]) * random.uniform(0.3, 0.5)
        alt_waypoints = _offset_waypoints(extended_wps, offset)

        # Calculate distances
        orig_dist = s["route"]["distance_km"]
        detour_pct = random.uniform(1.10, 1.25)
        alt_dist = round(orig_dist * detour_pct)

        orig_duration = s["route"]["duration_hrs"]
        # Alternate might save time (avoids incident wait) or add time (longer route)
        time_diff = round(random.uniform(-1.5, 1.0), 1)
        alt_duration = round(orig_duration + time_diff, 1)

        now = datetime.now()

        # Find assigned driver name
        driver_name = "Unknown"
        # We'll set this from outside if needed

        incidents.append({
            "shipment_id": s["id"],
            "incident_type": incident_def["type"],
            "description": f'{incident_def["desc"]} on {s["port"].split("(")[0].strip()} \u2192 {s["destination"]} route',
            "location": {"lat": incident_loc[0], "lon": incident_loc[1]},
            "original_route": waypoints,
            "alternate_route": alt_waypoints,
            "original_distance_km": orig_dist,
            "alternate_distance_km": alt_dist,
            "original_duration_hrs": orig_duration,
            "alternate_duration_hrs": alt_duration,
            "time_diff_hrs": time_diff,
            "reported_at": now - timedelta(minutes=random.randint(10, 90)),
            "port": s["port"],
            "destination": s["destination"],
        })

    return incidents


# ═══════════════════════════════════════════════════════════════
# 1e. Master Function
# ═══════════════════════════════════════════════════════════════
def generate_analytics_data(shipments, company_data):
    """Generate all analytics data for all companies."""
    _seed_analytics()

    delay_causes = generate_delay_causes(shipments)

    driver_history = {}
    for company_id, drivers in company_data["drivers"].items():
        comp_shipments = [s for s in shipments if s.get("company_id") == company_id]
        for driver in drivers:
            driver_history[driver["id"]] = generate_driver_history(driver, comp_shipments)

    location_hotspots = {}
    active_incidents = {}
    for comp in company_data["companies"]:
        cid = comp["id"]
        location_hotspots[cid] = generate_location_hotspots(shipments, cid)
        active_incidents[cid] = generate_active_incidents(shipments, cid)

    return {
        "delay_causes": delay_causes,
        "driver_history": driver_history,
        "location_hotspots": location_hotspots,
        "active_incidents": active_incidents,
    }
