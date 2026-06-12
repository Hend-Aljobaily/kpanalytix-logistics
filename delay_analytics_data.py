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
from routing import get_route_alternatives as _osrm_get_alternatives

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


# Center of the Arabian Peninsula interior — detours bias toward this
# point so routes never cross water (Red Sea / Persian Gulf).
_SA_INTERIOR = [24.0, 44.0]


def _generate_detour_waypoints(waypoints, strength=0.2):
    """Create a road-realistic detour by shifting middle waypoints toward
    the Arabian Peninsula interior.

    Shifts are **capped at 0.35 degrees (~39 km)** so routes through the
    UAE / Qatar corridor never get pulled across the Gulf even at high
    strength values.
    """
    _MAX_SHIFT = 0.35  # ~39 km — keeps detours realistic

    if not waypoints or len(waypoints) < 2:
        return list(waypoints)

    def _clamp(v):
        return max(-_MAX_SHIFT, min(_MAX_SHIFT, v))

    if len(waypoints) == 2:
        start, end = waypoints[0], waypoints[1]
        mid = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
        shift_lat = _clamp((_SA_INTERIOR[0] - mid[0]) * strength)
        shift_lon = _clamp((_SA_INTERIOR[1] - mid[1]) * strength)
        return [start[:], [mid[0] + shift_lat, mid[1] + shift_lon], end[:]]

    alt = [waypoints[0][:]]
    for i in range(1, len(waypoints) - 1):
        curr = waypoints[i]
        t = i / (len(waypoints) - 1)
        taper = math.sin(t * math.pi)
        shift_lat = _clamp((_SA_INTERIOR[0] - curr[0]) * strength * taper)
        shift_lon = _clamp((_SA_INTERIOR[1] - curr[1]) * strength * taper)
        alt.append([curr[0] + shift_lat, curr[1] + shift_lon])
    alt.append(waypoints[-1][:])
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

        # Place incident along route (~40-70% of the way)
        frac = random.uniform(0.4, 0.7)
        idx = int(frac * (len(waypoints) - 1))
        idx = max(1, min(idx, len(waypoints) - 2))
        incident_loc = waypoints[idx]

        # Try OSRM alternatives for a real road-following alternate route
        port_coords = PORTS.get(s["port"])
        dest_coords = ALL_DESTINATIONS.get(s["destination"])
        alt_waypoints = None
        alt_dist = None
        alt_duration = None

        if port_coords and dest_coords:
            alts = _osrm_get_alternatives(
                {"lat": port_coords["lat"], "lon": port_coords["lon"]},
                {"lat": dest_coords["lat"], "lon": dest_coords["lon"]},
                num_alternatives=3,
            )
            if alts and len(alts) >= 2:
                alt = alts[1]
                alt_waypoints = alt["geometry"]
                alt_dist = round(alt["distance_km"], 1)
                alt_duration = round(alt["duration_hrs"], 1)

        orig_dist = s["route"]["distance_km"]
        orig_duration = s["route"]["duration_hrs"]

        if alt_waypoints is None:
            # Fallback: if OSRM returned 1 route, use it (follows real roads);
            # otherwise fall back to original waypoints as-is.
            if port_coords and dest_coords:
                alts_single = _osrm_get_alternatives(
                    {"lat": port_coords["lat"], "lon": port_coords["lon"]},
                    {"lat": dest_coords["lat"], "lon": dest_coords["lon"]},
                    num_alternatives=1,
                )
                if alts_single:
                    alt_waypoints = alts_single[0]["geometry"]
                    alt_dist = round(alts_single[0]["distance_km"] * 1.05, 1)
                    alt_duration = round(alts_single[0]["duration_hrs"], 1)
            if alt_waypoints is None:
                alt_waypoints = list(waypoints)
                alt_dist = round(orig_dist * 1.15)
                alt_duration = round(orig_duration * 1.05, 1)

        time_diff = round(alt_duration - orig_duration, 1)
        now = datetime.now()

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
# 1e. Route Optimization Options
# ═══════════════════════════════════════════════════════════════
def _calc_cost(distance_km, duration_hrs, cost_params, is_cooled=False):
    """Compute total route cost from parameters."""
    fuel = distance_km * cost_params["fuel_cost_per_km"]
    driver = duration_hrs * cost_params["driver_cost_per_hr"]
    maint = distance_km * cost_params["maintenance_per_km"]
    toll = cost_params["toll_flat_rate"]
    cooled = distance_km * cost_params.get("cooled_surcharge_per_km", 0) if is_cooled else 0
    return {
        "fuel": round(fuel, 2),
        "driver": round(driver, 2),
        "maintenance": round(maint, 2),
        "toll": round(toll, 2),
        "cooled": round(cooled, 2),
        "total": round(fuel + driver + maint + toll + cooled, 2),
    }


def generate_route_options(incidents, cost_params):
    """For each incident, generate 3 route options using OSRM road-following alternatives."""
    options_by_incident = []
    for inc in incidents:
        orig_wps = inc.get("original_route", [])
        orig_dist = inc["original_distance_km"]
        orig_dur = inc["original_duration_hrs"]
        is_cooled = False

        # Try OSRM alternatives for real road-following route options
        port_coords = PORTS.get(inc.get("port", ""))
        dest_coords = ALL_DESTINATIONS.get(inc.get("destination", ""))
        osrm_alts = None
        if port_coords and dest_coords:
            osrm_alts = _osrm_get_alternatives(
                {"lat": port_coords["lat"], "lon": port_coords["lon"]},
                {"lat": dest_coords["lat"], "lon": dest_coords["lon"]},
                num_alternatives=3,
            )

        if osrm_alts and len(osrm_alts) >= 2:
            # Use real OSRM alternatives — all follow actual roads
            # Sort by duration to assign roles: fastest, then others
            sorted_alts = sorted(osrm_alts, key=lambda r: r["duration_hrs"])

            fastest_alt = sorted_alts[0]
            cheapest_alt = sorted_alts[-1]  # longest route tends to be cheapest (avoids highways)
            balanced_alt = sorted_alts[len(sorted_alts) // 2] if len(sorted_alts) >= 3 else sorted_alts[0]

            fastest_wps = fastest_alt["geometry"]
            fast_dist = round(fastest_alt["distance_km"], 1)
            fast_dur = round(fastest_alt["duration_hrs"], 1)

            cheapest_wps = cheapest_alt["geometry"]
            cheap_dist = round(cheapest_alt["distance_km"], 1)
            cheap_dur = round(cheapest_alt["duration_hrs"], 1)

            balanced_wps = balanced_alt["geometry"]
            bal_dist = round(balanced_alt["distance_km"], 1)
            bal_dur = round(balanced_alt["duration_hrs"], 1)
        elif osrm_alts and len(osrm_alts) == 1:
            # Single OSRM route — use same road-following geometry for all 3
            # (realistic: single highway, optimize speed vs fuel cost)
            the_route = osrm_alts[0]
            fastest_wps = cheapest_wps = balanced_wps = the_route["geometry"]
            fast_dist = round(the_route["distance_km"], 1)
            fast_dur = round(the_route["duration_hrs"] * 0.92, 1)  # higher speed
            cheap_dist = round(the_route["distance_km"], 1)
            cheap_dur = round(the_route["duration_hrs"] * 1.10, 1)  # lower speed, saves fuel
            bal_dist = round(the_route["distance_km"], 1)
            bal_dur = round(the_route["duration_hrs"], 1)
        else:
            # Final fallback: no OSRM at all — use precomputed waypoints as-is
            fastest_wps = cheapest_wps = balanced_wps = list(orig_wps)
            fast_dist = round(orig_dist * random.uniform(1.05, 1.12))
            fast_dur = round(orig_dur * random.uniform(0.85, 0.95), 1)
            cheap_dist = round(orig_dist * random.uniform(1.18, 1.30))
            cheap_dur = round(orig_dur * random.uniform(1.10, 1.25), 1)
            bal_dist = round(orig_dist * random.uniform(1.08, 1.18))
            bal_dur = round(orig_dur * random.uniform(0.95, 1.05), 1)

        fast_cost = _calc_cost(fast_dist, fast_dur, cost_params, is_cooled)

        cheap_cost_params = dict(cost_params)
        cheap_cost_params["toll_flat_rate"] = 0
        cheap_cost_params["fuel_cost_per_km"] = cost_params["fuel_cost_per_km"] * 0.85
        cheap_cost = _calc_cost(cheap_dist, cheap_dur, cheap_cost_params, is_cooled)

        bal_cost = _calc_cost(bal_dist, bal_dur, cost_params, is_cooled)

        options_by_incident.append({
            "shipment_id": inc["shipment_id"],
            "options": [
                {
                    "name": "Fastest",
                    "waypoints": fastest_wps,
                    "distance_km": fast_dist,
                    "duration_hrs": fast_dur,
                    "cost": fast_cost,
                    "pros": "Shortest travel time, avoids incident zone quickly",
                    "cons": "Slightly higher cost due to highway tolls",
                },
                {
                    "name": "Cheapest",
                    "waypoints": cheapest_wps,
                    "distance_km": cheap_dist,
                    "duration_hrs": cheap_dur,
                    "cost": cheap_cost,
                    "pros": "Lowest total cost, avoids toll roads",
                    "cons": "Longer travel time and distance",
                },
                {
                    "name": "Balanced",
                    "waypoints": balanced_wps,
                    "distance_km": bal_dist,
                    "duration_hrs": bal_dur,
                    "cost": bal_cost,
                    "pros": "Best trade-off between time and cost",
                    "cons": "Not the fastest or cheapest individually",
                },
            ],
        })
    return options_by_incident


# ═══════════════════════════════════════════════════════════════
# 1f. Fleet Optimization Recommendations
# ═══════════════════════════════════════════════════════════════
def generate_fleet_recommendations(shipments, company_data, company_id):
    """Generate actionable fleet optimization recommendations for a company."""
    comp_shipments = [s for s in shipments if s.get("company_id") == company_id]
    comp_drivers = company_data["drivers"].get(company_id, [])
    comp_trucks = company_data["trucks"].get(company_id, [])

    recommendations = []

    # 1. Cooled truck priority
    cooled_shipments = [s for s in comp_shipments if s.get("truck_type") == "Cooled"]
    if cooled_shipments:
        cooled_available = sum(1 for t in comp_trucks if t["type"] == "Cooled" and t["status"] != "maintenance")
        if len(cooled_shipments) >= cooled_available:
            recommendations.append({
                "title": "Cooled Fleet at Capacity",
                "description": f"{len(cooled_shipments)} shipments require cooled trucks but only {cooled_available} are available. "
                               "Prioritize highest-value perishable cargo (Food & Medical) for cooled fleet allocation.",
                "impact": "High",
                "estimated_savings": "Prevent spoilage losses of 15,000-30,000 SAR",
                "category": "fleet",
            })

    # 2. Fleet utilization
    idle_trucks = [t for t in comp_trucks if t["status"] == "available"]
    in_use = [t for t in comp_trucks if t["status"] == "in_use"]
    if idle_trucks and len(idle_trucks) >= 3:
        recommendations.append({
            "title": "Underutilized Fleet Assets",
            "description": f"{len(idle_trucks)} trucks are currently idle while {len(in_use)} are in use. "
                           "Consider reassigning idle trucks to cover upcoming port arrivals or cross-docking needs.",
            "impact": "Medium",
            "estimated_savings": f"{len(idle_trucks) * 800:,} SAR/day in idle costs",
            "category": "fleet",
        })

    # 3. Driver efficiency
    if comp_drivers:
        low_perf = [d for d in comp_drivers if d["stats"]["on_time_pct"] < 80]
        if low_perf:
            names = ", ".join(d["name"] for d in low_perf[:3])
            recommendations.append({
                "title": "Driver Performance Alert",
                "description": f"{len(low_perf)} driver(s) below 80% on-time rate ({names}). "
                               "Consider route reassignment to shorter or less congested corridors for improvement.",
                "impact": "Medium",
                "estimated_savings": f"Reduce delay penalties by ~{len(low_perf) * 2000:,} SAR/month",
                "category": "drivers",
            })

    # 4. Revenue optimization
    if comp_shipments:
        shipments_with_dist = [(s, s["route"]["distance_km"]) for s in comp_shipments if s["route"]["distance_km"] > 0]
        if shipments_with_dist:
            avg_dist = sum(d for _, d in shipments_with_dist) / len(shipments_with_dist)
            long_hauls = [(s, d) for s, d in shipments_with_dist if d > avg_dist * 1.5]
            if long_hauls:
                recommendations.append({
                    "title": "Long-Haul Route Optimization",
                    "description": f"{len(long_hauls)} shipments travel >50% above average distance ({avg_dist:.0f} km). "
                                   "Evaluate relay-point handoffs at midway hubs to reduce single-driver fatigue and improve turnaround.",
                    "impact": "High",
                    "estimated_savings": f"Up to {len(long_hauls) * 1500:,} SAR in driver overtime savings",
                    "category": "routes",
                })

    # 5. Maintenance scheduling
    maint_trucks = [t for t in comp_trucks if t["status"] == "maintenance"]
    high_mileage = [t for t in comp_trucks if t["mileage_km"] > 150000 and t["status"] != "maintenance"]
    if high_mileage:
        recommendations.append({
            "title": "Preventive Maintenance Due",
            "description": f"{len(high_mileage)} truck(s) exceed 150,000 km without scheduled maintenance. "
                           f"Currently {len(maint_trucks)} in maintenance. Schedule rotation to prevent breakdowns.",
            "impact": "High" if len(high_mileage) >= 3 else "Medium",
            "estimated_savings": f"Avoid breakdown costs of {len(high_mileage) * 5000:,} SAR",
            "category": "fleet",
        })

    # Always provide at least one recommendation
    if not recommendations:
        recommendations.append({
            "title": "Fleet Operating Optimally",
            "description": "All fleet assets, drivers, and routes are performing within optimal parameters. "
                           "Continue monitoring for seasonal demand fluctuations.",
            "impact": "Low",
            "estimated_savings": "Maintaining current efficiency saves ~10,000 SAR/month",
            "category": "general",
        })

    return recommendations


# ═══════════════════════════════════════════════════════════════
# 1g. Master Function
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
    fleet_recommendations = {}
    for comp in company_data["companies"]:
        cid = comp["id"]
        location_hotspots[cid] = generate_location_hotspots(shipments, cid)
        active_incidents[cid] = generate_active_incidents(shipments, cid)
        fleet_recommendations[cid] = generate_fleet_recommendations(shipments, company_data, cid)

    return {
        "delay_causes": delay_causes,
        "driver_history": driver_history,
        "location_hotspots": location_hotspots,
        "active_incidents": active_incidents,
        "fleet_recommendations": fleet_recommendations,
    }
