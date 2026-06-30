"""
Saudi Arabia & GCC Shipping Optimizer — Configuration
Ports, cities, coordinates, theme colors, precomputed routes, and operational parameters.
"""

import math

# ── Theme Colors (Dark Mode) ──
COLORS = {
    "bg_primary": "#0E0B16",
    "bg_surface": "#1A1527",
    "bg_elevated": "#241E35",
    "text_primary": "#F0ECF5",
    "text_secondary": "#9B8FB5",
    "accent": "#9B72CF",
    "accent_bright": "#B68FE8",
    "royal_purple": "#442270",
    "deep_plum": "#240F3E",
    "border": "#2E2545",
    "on_time": "#2ECC71",
    "at_risk": "#F39C12",
    "delayed": "#E74C3C",
    "cooled": "#3498DB",
    "route_line": "#B68FE8",
    "route_line_alt": "#9B72CF",
    "route_colors": [
        "#B68FE8", "#5DADE2", "#F39C12", "#2ECC71",
        "#E74C3C", "#1ABC9C", "#E67E22", "#AF7AC5",
        "#3498DB", "#F1C40F", "#E91E63", "#00BCD4",
    ],
}

# ── Saudi Arabia Major Ports (Origins) ──
PORTS = {
    "Jeddah Islamic Port": {"lat": 21.4858, "lon": 39.1925},
    "King Abdulaziz Port (Dammam)": {"lat": 26.4473, "lon": 50.1044},
    "Jubail Commercial Port": {"lat": 27.0046, "lon": 49.6609},
    "Yanbu Commercial Port": {"lat": 24.0895, "lon": 38.0618},
    "Ras Al-Khair Port": {"lat": 27.4800, "lon": 49.2500},
    "NEOM Port (Oxagon)": {"lat": 27.5729, "lon": 35.5305},
}

# ── Saudi Arabia Destination Cities ──
SAUDI_CITIES = {
    "Riyadh": {"lat": 24.7136, "lon": 46.6753},
    "Makkah": {"lat": 21.3891, "lon": 39.8579},
    "Madinah": {"lat": 24.5247, "lon": 39.5692},
    "Tabuk": {"lat": 28.3838, "lon": 36.5550},
    "Abha": {"lat": 18.2164, "lon": 42.5053},
    "Najran": {"lat": 17.4933, "lon": 44.1322},
    "Hail": {"lat": 27.5114, "lon": 41.7208},
    "Buraidah": {"lat": 26.3260, "lon": 43.9750},
    "Jazan": {"lat": 16.8892, "lon": 42.5611},
    "Al Khobar": {"lat": 26.2172, "lon": 50.1971},
    "Ta'if": {"lat": 21.2703, "lon": 40.4158},
    "NEOM": {"lat": 26.5000, "lon": 36.0700},
}

# ── GCC Destination Cities ──
GCC_CITIES = {
    "Dubai, UAE": {"lat": 25.2048, "lon": 55.2708},
    "Abu Dhabi, UAE": {"lat": 24.4539, "lon": 54.3773},
    "Sharjah, UAE": {"lat": 25.3463, "lon": 55.4209},
    "Kuwait City, Kuwait": {"lat": 29.3759, "lon": 47.9774},
    "Manama, Bahrain": {"lat": 26.2285, "lon": 50.5860},
    "Doha, Qatar": {"lat": 25.2854, "lon": 51.5310},
    "Muscat, Oman": {"lat": 23.5880, "lon": 58.3829},
    "Salalah, Oman": {"lat": 17.0151, "lon": 54.0924},
}

ALL_DESTINATIONS = {**SAUDI_CITIES, **GCC_CITIES}

# ── Country → City Mapping ──
DEST_COUNTRY_MAP = {}
for _city in SAUDI_CITIES:
    DEST_COUNTRY_MAP[_city] = "Saudi Arabia"
for _city in GCC_CITIES:
    _parts = _city.rsplit(", ", 1)
    DEST_COUNTRY_MAP[_city] = _parts[1] if len(_parts) == 2 else "Other"

DEST_COUNTRIES = sorted(set(DEST_COUNTRY_MAP.values()))

# ── OSRM API ──
OSRM_BASE_URL = "https://router.project-osrm.org"

# ── Map Defaults ──
MAP_CENTER = {"lat": 24.0, "lon": 45.0}
MAP_ZOOM = 5

# ── Cargo Types & Truck Classification ──
CARGO_TYPES = [
    "Industrial Equipment", "Construction Materials", "Food & Perishables",
    "Medical Supplies", "Government Documents", "Automotive Parts",
    "Electronics", "Textiles", "Petrochemicals", "Agricultural Goods",
]

COOLED_CARGO = {"Food & Perishables", "Medical Supplies", "Agricultural Goods"}

# ── Cargo Revenue Estimates (SAR per shipment) ──
CARGO_REVENUE_MAP = {
    "Medical Supplies": 12000,
    "Electronics": 10000,
    "Food & Perishables": 8500,
    "Petrochemicals": 9000,
    "Automotive Parts": 7500,
    "Industrial Equipment": 7000,
    "Government Documents": 6500,
    "Construction Materials": 5500,
    "Textiles": 5000,
    "Agricultural Goods": 6000,
}
PRIORITY_REVENUE_MULTIPLIER = {"Critical": 1.5, "High": 1.2, "Standard": 1.0}

# ── Vessel Names ──
VESSEL_NAMES = [
    "MV Saudi Progress", "MV Gulf Pioneer", "MV Arabian Star",
    "MV Desert Falcon", "MV Red Sea Voyager", "MV Eastern Promise",
    "MV Kingdom Express", "MV Dhow Legacy", "MV NEOM Horizon",
    "MV Oxagon Carrier",
]

# ── Precomputed Routes ──
PRECOMPUTED_ROUTES = {
    # === Jeddah Islamic Port ===
    ("Jeddah Islamic Port", "Riyadh"): {
        "waypoints": [
            [21.49, 39.19], [21.39, 39.86], [21.27, 40.42],
            [22.30, 42.00], [23.00, 44.00], [24.00, 45.50], [24.71, 46.68],
        ],
        "distance_km": 949, "duration_hrs": 9.5,
    },
    ("Jeddah Islamic Port", "Makkah"): {
        "waypoints": [[21.49, 39.19], [21.45, 39.50], [21.39, 39.86]],
        "distance_km": 79, "duration_hrs": 0.9,
    },
    ("Jeddah Islamic Port", "Madinah"): {
        "waypoints": [
            [21.49, 39.19], [22.00, 39.30], [23.00, 39.20],
            [24.00, 39.40], [24.52, 39.57],
        ],
        "distance_km": 420, "duration_hrs": 4.2,
    },
    ("Jeddah Islamic Port", "Ta'if"): {
        "waypoints": [[21.49, 39.19], [21.39, 39.86], [21.27, 40.42]],
        "distance_km": 170, "duration_hrs": 1.8,
    },
    ("Jeddah Islamic Port", "Abha"): {
        "waypoints": [
            [21.49, 39.19], [21.39, 39.86], [21.27, 40.42],
            [20.50, 41.00], [19.50, 41.80], [18.22, 42.51],
        ],
        "distance_km": 625, "duration_hrs": 6.5,
    },
    ("Jeddah Islamic Port", "Jazan"): {
        "waypoints": [
            [21.49, 39.19], [20.50, 40.00], [19.00, 41.00],
            [17.80, 41.80], [16.89, 42.56],
        ],
        "distance_km": 710, "duration_hrs": 7.3,
    },
    ("Jeddah Islamic Port", "Tabuk"): {
        "waypoints": [
            [21.49, 39.19], [22.50, 39.10], [24.00, 38.50],
            [26.00, 37.50], [28.38, 36.56],
        ],
        "distance_km": 1024, "duration_hrs": 10.5,
    },
    # === King Abdulaziz Port (Dammam) ===
    ("King Abdulaziz Port (Dammam)", "Riyadh"): {
        "waypoints": [
            [26.45, 50.10], [26.22, 50.20], [25.80, 49.50],
            [25.20, 48.50], [24.71, 46.68],
        ],
        "distance_km": 410, "duration_hrs": 4.0,
    },
    ("King Abdulaziz Port (Dammam)", "Al Khobar"): {
        "waypoints": [[26.45, 50.10], [26.30, 50.18], [26.22, 50.20]],
        "distance_km": 30, "duration_hrs": 0.4,
    },
    ("King Abdulaziz Port (Dammam)", "Manama, Bahrain"): {
        "waypoints": [[26.45, 50.10], [26.30, 50.30], [26.23, 50.59]],
        "distance_km": 55, "duration_hrs": 0.8,
    },
    # Doha: south through Al Hofuf, Salwa border crossing, into Qatar
    ("King Abdulaziz Port (Dammam)", "Doha, Qatar"): {
        "waypoints": [
            [26.45, 50.10], [25.80, 49.80], [25.38, 49.59],
            [25.00, 50.20], [24.70, 50.76], [25.00, 51.15], [25.29, 51.53],
        ],
        "distance_km": 480, "duration_hrs": 5.0,
    },
    # Dubai: south via Al Hofuf, south of Qatar peninsula, Ghuweifat border, Abu Dhabi coast
    ("King Abdulaziz Port (Dammam)", "Dubai, UAE"): {
        "waypoints": [
            [26.45, 50.10], [25.38, 49.59], [24.50, 49.50],
            [24.10, 50.50], [24.05, 51.00], [24.12, 51.57],
            [24.10, 52.70], [24.45, 54.38], [25.20, 55.27],
        ],
        "distance_km": 930, "duration_hrs": 9.5,
    },
    # Kuwait: north-west along coast, inland through Khafji
    ("King Abdulaziz Port (Dammam)", "Kuwait City, Kuwait"): {
        "waypoints": [
            [26.45, 50.10], [26.80, 49.60], [27.50, 49.00],
            [28.50, 48.30], [29.38, 47.98],
        ],
        "distance_km": 420, "duration_hrs": 4.2,
    },
    ("King Abdulaziz Port (Dammam)", "Buraidah"): {
        "waypoints": [
            [26.45, 50.10], [26.00, 48.50], [26.20, 46.50], [26.33, 43.98],
        ],
        "distance_km": 600, "duration_hrs": 5.8,
    },
    ("King Abdulaziz Port (Dammam)", "Hail"): {
        "waypoints": [
            [26.45, 50.10], [26.00, 48.50], [26.33, 44.00], [27.51, 41.72],
        ],
        "distance_km": 880, "duration_hrs": 8.5,
    },
    # Abu Dhabi: south of Qatar, Ghuweifat border, UAE coast road
    ("King Abdulaziz Port (Dammam)", "Abu Dhabi, UAE"): {
        "waypoints": [
            [26.45, 50.10], [25.38, 49.59], [24.50, 49.50],
            [24.10, 50.50], [24.05, 51.00], [24.12, 51.57],
            [24.10, 52.70], [24.45, 54.38],
        ],
        "distance_km": 870, "duration_hrs": 9.0,
    },
    # Muscat: through UAE then east into Oman
    ("King Abdulaziz Port (Dammam)", "Muscat, Oman"): {
        "waypoints": [
            [26.45, 50.10], [25.38, 49.59], [24.50, 49.50],
            [24.10, 50.50], [24.05, 51.00], [24.12, 51.57],
            [24.10, 52.70], [24.45, 54.38], [24.20, 55.80], [23.59, 58.38],
        ],
        "distance_km": 1350, "duration_hrs": 13.5,
    },
    # Sharjah: same as Dubai corridor, then north to Sharjah
    ("King Abdulaziz Port (Dammam)", "Sharjah, UAE"): {
        "waypoints": [
            [26.45, 50.10], [25.38, 49.59], [24.50, 49.50],
            [24.10, 50.50], [24.05, 51.00], [24.12, 51.57],
            [24.10, 52.70], [24.45, 54.38], [25.35, 55.42],
        ],
        "distance_km": 920, "duration_hrs": 9.3,
    },
    # === Jubail Commercial Port ===
    ("Jubail Commercial Port", "Riyadh"): {
        "waypoints": [
            [27.00, 49.66], [26.50, 49.00], [25.80, 48.00],
            [25.00, 47.00], [24.71, 46.68],
        ],
        "distance_km": 450, "duration_hrs": 4.5,
    },
    ("Jubail Commercial Port", "Kuwait City, Kuwait"): {
        "waypoints": [
            [27.00, 49.66], [27.50, 49.00], [28.50, 48.30], [29.38, 47.98],
        ],
        "distance_km": 380, "duration_hrs": 3.8,
    },
    # Jubail → GCC: south through Dammam corridor, then land routes
    ("Jubail Commercial Port", "Dubai, UAE"): {
        "waypoints": [
            [27.00, 49.66], [26.45, 50.10], [25.38, 49.59],
            [24.50, 49.50], [24.10, 50.50], [24.05, 51.00],
            [24.12, 51.57], [24.10, 52.70], [24.45, 54.38], [25.20, 55.27],
        ],
        "distance_km": 990, "duration_hrs": 10.0,
    },
    ("Jubail Commercial Port", "Doha, Qatar"): {
        "waypoints": [
            [27.00, 49.66], [26.45, 50.10], [25.38, 49.59],
            [25.00, 50.20], [24.70, 50.76], [25.00, 51.15], [25.29, 51.53],
        ],
        "distance_km": 540, "duration_hrs": 5.5,
    },
    ("Jubail Commercial Port", "Abu Dhabi, UAE"): {
        "waypoints": [
            [27.00, 49.66], [26.45, 50.10], [25.38, 49.59],
            [24.50, 49.50], [24.10, 50.50], [24.05, 51.00],
            [24.12, 51.57], [24.10, 52.70], [24.45, 54.38],
        ],
        "distance_km": 930, "duration_hrs": 9.5,
    },
    ("Jubail Commercial Port", "Sharjah, UAE"): {
        "waypoints": [
            [27.00, 49.66], [26.45, 50.10], [25.38, 49.59],
            [24.50, 49.50], [24.10, 50.50], [24.05, 51.00],
            [24.12, 51.57], [24.10, 52.70], [24.45, 54.38], [25.35, 55.42],
        ],
        "distance_km": 980, "duration_hrs": 10.0,
    },
    ("Jubail Commercial Port", "Muscat, Oman"): {
        "waypoints": [
            [27.00, 49.66], [26.45, 50.10], [25.38, 49.59],
            [24.50, 49.50], [24.10, 50.50], [24.05, 51.00],
            [24.12, 51.57], [24.10, 52.70], [24.45, 54.38],
            [24.20, 55.80], [23.59, 58.38],
        ],
        "distance_km": 1410, "duration_hrs": 14.0,
    },
    # === Yanbu Commercial Port ===
    ("Yanbu Commercial Port", "Madinah"): {
        "waypoints": [
            [24.09, 38.06], [24.20, 38.50], [24.40, 39.10], [24.52, 39.57],
        ],
        "distance_km": 240, "duration_hrs": 2.5,
    },
    ("Yanbu Commercial Port", "Riyadh"): {
        "waypoints": [
            [24.09, 38.06], [24.52, 39.57], [24.50, 41.00],
            [24.50, 43.50], [24.71, 46.68],
        ],
        "distance_km": 1050, "duration_hrs": 10.5,
    },
    # === Ras Al-Khair Port ===
    ("Ras Al-Khair Port", "Riyadh"): {
        "waypoints": [
            [27.48, 49.25], [27.00, 48.50], [26.00, 47.00],
            [25.00, 46.50], [24.71, 46.68],
        ],
        "distance_km": 500, "duration_hrs": 5.0,
    },
    # Ras Al-Khair → GCC via Dammam/Jubail corridor
    ("Ras Al-Khair Port", "Dubai, UAE"): {
        "waypoints": [
            [27.48, 49.25], [27.00, 49.66], [25.38, 49.59],
            [24.50, 49.50], [24.10, 50.50], [24.05, 51.00],
            [24.12, 51.57], [24.10, 52.70], [24.45, 54.38], [25.20, 55.27],
        ],
        "distance_km": 1030, "duration_hrs": 10.5,
    },
    ("Ras Al-Khair Port", "Doha, Qatar"): {
        "waypoints": [
            [27.48, 49.25], [27.00, 49.66], [25.38, 49.59],
            [25.00, 50.20], [24.70, 50.76], [25.00, 51.15], [25.29, 51.53],
        ],
        "distance_km": 580, "duration_hrs": 6.0,
    },
    ("Ras Al-Khair Port", "Kuwait City, Kuwait"): {
        "waypoints": [
            [27.48, 49.25], [27.50, 49.00], [28.50, 48.30], [29.38, 47.98],
        ],
        "distance_km": 420, "duration_hrs": 4.3,
    },
    # === NEOM Port (Oxagon) ===
    ("NEOM Port (Oxagon)", "Tabuk"): {
        "waypoints": [
            [27.57, 35.53], [27.80, 35.80], [28.20, 36.20], [28.38, 36.56],
        ],
        "distance_km": 150, "duration_hrs": 1.6,
    },
    ("NEOM Port (Oxagon)", "NEOM"): {
        "waypoints": [[27.57, 35.53], [27.20, 35.80], [26.50, 36.07]],
        "distance_km": 130, "duration_hrs": 1.4,
    },
    ("NEOM Port (Oxagon)", "Madinah"): {
        "waypoints": [
            [27.57, 35.53], [27.00, 36.00], [26.00, 37.00],
            [25.00, 38.00], [24.52, 39.57],
        ],
        "distance_km": 580, "duration_hrs": 6.0,
    },
    ("NEOM Port (Oxagon)", "Riyadh"): {
        "waypoints": [
            [27.57, 35.53], [27.00, 36.50], [26.00, 38.00],
            [25.00, 40.50], [24.50, 43.50], [24.71, 46.68],
        ],
        "distance_km": 1350, "duration_hrs": 13.5,
    },
    ("NEOM Port (Oxagon)", "Hail"): {
        "waypoints": [
            [27.57, 35.53], [27.80, 36.50], [27.60, 38.50],
            [27.51, 41.72],
        ],
        "distance_km": 620, "duration_hrs": 6.2,
    },
}


# ── Default Optimization Cost Parameters (SAR) ──
DEFAULT_COST_PARAMS = {
    "fuel_cost_per_km": 0.45,
    "driver_cost_per_hr": 35.0,
    "maintenance_per_km": 0.08,
    "toll_flat_rate": 50.0,
    "cooled_surcharge_per_km": 0.15,
}


def haversine_km(lat1, lon1, lat2, lon2):
    """Approximate great-circle distance in km between two points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def get_precomputed_route(port_name, dest_name):
    """Get pre-computed route data, falling back to interior-routed estimate.

    The fallback pulls the midpoint toward the Saudi interior [24, 46] so
    that routes between coastal ports and GCC cities never cross water.
    """
    key = (port_name, dest_name)
    if key in PRECOMPUTED_ROUTES:
        return PRECOMPUTED_ROUTES[key]
    port = PORTS[port_name]
    dest = ALL_DESTINATIONS[dest_name]
    straight_km = haversine_km(port["lat"], port["lon"], dest["lat"], dest["lon"])
    road_km = straight_km * 1.3
    duration_hrs = road_km / 100

    # Pull midpoint toward peninsula interior to avoid Gulf / Red Sea
    mid_lat = (port["lat"] + dest["lat"]) / 2
    mid_lon = (port["lon"] + dest["lon"]) / 2
    interior_lat = mid_lat + (24.0 - mid_lat) * 0.25
    interior_lon = mid_lon + (46.0 - mid_lon) * 0.25
    return {
        "waypoints": [
            [port["lat"], port["lon"]],
            [interior_lat, interior_lon],
            [dest["lat"], dest["lon"]],
        ],
        "distance_km": round(road_km, 1),
        "duration_hrs": round(duration_hrs, 1),
    }


# ── Region Map for Smart Location Search ──
REGION_MAP = {
    "Riyadh": "Central Region",
    "Tabuk": "Northern Region",
    "NEOM": "Northern Region",
    "Hail": "Northern Region",
    "Buraidah": "Qassim Region",
    "Makkah": "Western Region",
    "Madinah": "Western Region",
    "Ta'if": "Western Region",
    "Abha": "Southern Region",
    "Najran": "Southern Region",
    "Jazan": "Southern Region",
    "Al Khobar": "Eastern Region",
    "Jeddah Islamic Port": "Western Region",
    "King Abdulaziz Port (Dammam)": "Eastern Region",
    "Jubail Commercial Port": "Eastern Region",
    "Yanbu Commercial Port": "Western Region",
    "Ras Al-Khair Port": "Eastern Region",
    "NEOM Port (Oxagon)": "Northern Region",
}

# ── Combined Location Search List (display_label -> metadata) ──
ALL_LOCATIONS = {}
for _name, _coords in PORTS.items():
    _region = REGION_MAP.get(_name, "")
    _label = f"{_name} — {_region}, Saudi Arabia" if _region else f"{_name} — Saudi Arabia"
    ALL_LOCATIONS[_label] = {"key": _name, "coords": _coords, "type": "port"}
for _name, _coords in ALL_DESTINATIONS.items():
    _country = DEST_COUNTRY_MAP.get(_name, "Saudi Arabia")
    _region = REGION_MAP.get(_name, "")
    _tag = f"{_region}, {_country}" if _region else _country
    _label = f"{_name} — {_tag}"
    ALL_LOCATIONS[_label] = {"key": _name, "coords": _coords, "type": "city"}
