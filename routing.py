"""
KPAnalytix Logistics — Routing & Optimization
OSRM API integration, OR-Tools TSP solver, cost/ETA calculations.
"""

import requests
from datetime import datetime, timedelta
from config import OSRM_BASE_URL

# ── In-memory route cache ──
# Keyed by rounded (lat1, lon1, lat2, lon2) to avoid duplicate OSRM calls.
_route_cache = {}
_alt_cache = {}


def _cache_key(origin, destination):
    return (
        round(origin["lat"], 4), round(origin["lon"], 4),
        round(destination["lat"], 4), round(destination["lon"], 4),
    )


def get_route(origin, destination):
    """
    Get road route between two points using OSRM (cached).

    Args:
        origin: dict with 'lat' and 'lon'
        destination: dict with 'lat' and 'lon'

    Returns:
        dict with 'geometry' (list of [lat, lon]), 'distance_km', 'duration_hrs'
        or None on failure.
    """
    key = _cache_key(origin, destination)
    if key in _route_cache:
        return _route_cache[key]

    url = (
        f"{OSRM_BASE_URL}/route/v1/driving/"
        f"{origin['lon']},{origin['lat']};"
        f"{destination['lon']},{destination['lat']}"
        f"?overview=full&geometries=geojson"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            _route_cache[key] = None
            return None
        route = data["routes"][0]
        coords = route["geometry"]["coordinates"]
        # OSRM returns [lon, lat], convert to [lat, lon]
        geometry = [[c[1], c[0]] for c in coords]
        result = {
            "geometry": geometry,
            "distance_km": route["distance"] / 1000.0,
            "duration_hrs": route["duration"] / 3600.0,
        }
        _route_cache[key] = result
        return result
    except (requests.RequestException, KeyError, IndexError):
        _route_cache[key] = None
        return None


def get_route_alternatives(origin, destination, num_alternatives=3):
    """
    Get multiple route alternatives from OSRM (cached).

    Returns:
        list of dicts with 'geometry', 'distance_km', 'duration_hrs',
        or None on failure.  The first element is the primary (fastest) route.
    """
    key = _cache_key(origin, destination)
    if key in _alt_cache:
        return _alt_cache[key]

    url = (
        f"{OSRM_BASE_URL}/route/v1/driving/"
        f"{origin['lon']},{origin['lat']};"
        f"{destination['lon']},{destination['lat']}"
        f"?overview=full&geometries=geojson&alternatives={num_alternatives}"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            _alt_cache[key] = None
            return None
        routes = []
        for route in data["routes"]:
            coords = route["geometry"]["coordinates"]
            geometry = [[c[1], c[0]] for c in coords]
            routes.append({
                "geometry": geometry,
                "distance_km": route["distance"] / 1000.0,
                "duration_hrs": route["duration"] / 3600.0,
            })
        _alt_cache[key] = routes
        return routes
    except (requests.RequestException, KeyError, IndexError):
        _alt_cache[key] = None
        return None


def clear_route_cache():
    """Clear all cached routes (call on data refresh)."""
    _route_cache.clear()
    _alt_cache.clear()


def get_route_multi_stop(waypoints):
    """
    Get optimized multi-stop route using OSRM trip service.

    Args:
        waypoints: list of dicts with 'lat' and 'lon' (first is origin)

    Returns:
        dict with 'geometry', 'distance_km', 'duration_hrs', 'waypoint_order'
        or None on failure.
    """
    coords_str = ";".join(f"{wp['lon']},{wp['lat']}" for wp in waypoints)
    url = (
        f"{OSRM_BASE_URL}/trip/v1/driving/{coords_str}"
        f"?overview=full&geometries=geojson&source=first&roundtrip=false"
    )
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok" or not data.get("trips"):
            return None
        trip = data["trips"][0]
        coords = trip["geometry"]["coordinates"]
        geometry = [[c[1], c[0]] for c in coords]
        waypoint_order = [wp["waypoint_index"] for wp in data["waypoints"]]
        return {
            "geometry": geometry,
            "distance_km": trip["distance"] / 1000.0,
            "duration_hrs": trip["duration"] / 3600.0,
            "waypoint_order": waypoint_order,
        }
    except (requests.RequestException, KeyError, IndexError):
        return None


def build_distance_matrix(locations):
    """
    Build pairwise distance matrix using OSRM table service.

    Args:
        locations: list of dicts with 'lat' and 'lon'

    Returns:
        2D list of distances in km, or None on failure.
    """
    coords_str = ";".join(f"{loc['lon']},{loc['lat']}" for loc in locations)
    url = f"{OSRM_BASE_URL}/table/v1/driving/{coords_str}"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok":
            return None
        # OSRM returns durations in seconds; also get distances if available
        # The table service returns durations by default
        durations = data["durations"]
        # Convert seconds to km estimate (avg 80 km/h) as fallback
        # Use durations as the optimization metric
        return durations
    except (requests.RequestException, KeyError):
        return None


def optimize_route(origin_idx, num_locations, duration_matrix):
    """
    Use OR-Tools to solve TSP for multi-stop delivery order.

    Args:
        origin_idx: index of the origin (depot) in the matrix
        num_locations: total number of locations
        duration_matrix: 2D list of durations (seconds)

    Returns:
        Ordered list of indices representing optimal visit order,
        or None if optimization fails.
    """
    try:
        from ortools.constraint_solver import routing_enums_pb2, pywrapcp
    except ImportError:
        return None

    manager = pywrapcp.RoutingIndexManager(num_locations, 1, origin_idx)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        val = duration_matrix[from_node][to_node]
        return int(val) if val is not None else 999999

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(5)

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        return None

    order = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        order.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    return order


def calculate_cost(distance_km, duration_hrs, params):
    """
    Compute shipping cost from configurable parameters.

    Returns:
        dict with cost breakdown and total.
    """
    fuel = distance_km * params["fuel_cost_per_km"]
    driver = duration_hrs * params["driver_cost_per_hr"]
    maintenance = distance_km * params["maintenance_per_km"]
    toll = params["toll_flat_rate"]
    total = fuel + driver + maintenance + toll
    return {
        "fuel": round(fuel, 2),
        "driver": round(driver, 2),
        "maintenance": round(maintenance, 2),
        "toll": round(toll, 2),
        "total": round(total, 2),
    }


def calculate_eta(duration_hrs, departure_time):
    """
    Calculate ETA given duration and departure time.

    Args:
        duration_hrs: float hours
        departure_time: datetime object

    Returns:
        datetime of estimated arrival.
    """
    return departure_time + timedelta(hours=duration_hrs)


def get_leg_routes(waypoints_ordered):
    """
    Get individual route legs between consecutive waypoints.

    Args:
        waypoints_ordered: list of dicts with 'lat', 'lon', and 'name'

    Returns:
        list of dicts per leg with route info + names.
    """
    legs = []
    for i in range(len(waypoints_ordered) - 1):
        origin = waypoints_ordered[i]
        dest = waypoints_ordered[i + 1]
        route = get_route(origin, dest)
        if route:
            legs.append({
                "from": origin.get("name", f"Point {i}"),
                "to": dest.get("name", f"Point {i+1}"),
                "distance_km": route["distance_km"],
                "duration_hrs": route["duration_hrs"],
                "geometry": route["geometry"],
            })
        else:
            legs.append({
                "from": origin.get("name", f"Point {i}"),
                "to": dest.get("name", f"Point {i+1}"),
                "distance_km": 0,
                "duration_hrs": 0,
                "geometry": [
                    [origin["lat"], origin["lon"]],
                    [dest["lat"], dest["lon"]],
                ],
            })
    return legs
