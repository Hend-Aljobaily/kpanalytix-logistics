"""
Saudi Arabia & GCC Shipping Optimizer — Company / Driver / Fleet Data
Generates per-company data for the Micro dashboard view.
"""

import random
from datetime import datetime

from config import PORTS, ALL_DESTINATIONS

# ── Company Definitions ──
COMPANIES = [
    {
        "id": "CMP-001",
        "name": "Al Jazirah Logistics",
        "hq_city": "Riyadh",
        "fleet_size": 18,
        "specialization": "General Freight & Industrial",
    },
    {
        "id": "CMP-002",
        "name": "Gulf Express Transport",
        "hq_city": "Dammam",
        "fleet_size": 14,
        "specialization": "GCC Cross-Border Express",
    },
    {
        "id": "CMP-003",
        "name": "Red Sea Carriers",
        "hq_city": "Jeddah",
        "fleet_size": 16,
        "specialization": "Port-to-City Distribution",
    },
    {
        "id": "CMP-004",
        "name": "NEOM Freight Solutions",
        "hq_city": "NEOM",
        "fleet_size": 10,
        "specialization": "NEOM & Northern Region",
    },
    {
        "id": "CMP-005",
        "name": "Saudi Cold Chain Co.",
        "hq_city": "Jeddah",
        "fleet_size": 12,
        "specialization": "Temperature-Controlled Cargo",
    },
    {
        "id": "CMP-006",
        "name": "Peninsula Haulers",
        "hq_city": "Al Khobar",
        "fleet_size": 15,
        "specialization": "Heavy & Oversized Loads",
    },
]

# ── Driver Name Pool ──
DRIVER_FIRST_NAMES = [
    "Mohammed", "Abdullah", "Fahad", "Khalid", "Sultan", "Ahmed",
    "Omar", "Saad", "Nasser", "Faisal", "Ibrahim", "Hassan",
    "Ali", "Youssef", "Tariq", "Hamad", "Saleh", "Majed",
    "Rashed", "Turki", "Bandar", "Mansour", "Waleed", "Zayed",
    "Nawaf", "Badr", "Saud", "Mazen", "Adel", "Jamal",
    "Khaled", "Osama", "Hamed", "Abdulaziz", "Abdulrahman",
    "Mishal", "Muhannad", "Thamer", "Naif", "Hatim",
]

DRIVER_LAST_NAMES = [
    "Al-Otaibi", "Al-Qahtani", "Al-Harbi", "Al-Ghamdi", "Al-Shehri",
    "Al-Dosari", "Al-Mutairi", "Al-Zahrani", "Al-Malki", "Al-Subaie",
    "Al-Rashidi", "Al-Anazi", "Al-Shamrani", "Al-Yami", "Al-Khaldi",
    "Al-Bishi", "Al-Juhani", "Al-Thubaiti", "Al-Enezi", "Al-Tamimi",
    "Al-Shammari", "Al-Dossary", "Al-Omari", "Al-Ajmi", "Al-Fadhli",
]

# ── Truck Models ──
TRUCK_MODELS = [
    ("MAN TGS 26.440", "Regular"),
    ("Volvo FH16 540", "Regular"),
    ("Mercedes Actros 2645", "Regular"),
    ("Scania R500", "Regular"),
    ("Isuzu FVZ 34T", "Regular"),
    ("DAF XF 480", "Regular"),
    ("Hino 700 Series", "Regular"),
    ("MAN TGX 18.500", "Cooled"),
    ("Volvo FH 460 Reefer", "Cooled"),
    ("Mercedes Actros Reefer", "Cooled"),
    ("Scania R450 Reefer", "Cooled"),
    ("Carrier Transicold XTC", "Cooled"),
]

# ── City Coordinates for Driver Locations ──
CITY_COORDS = {
    "Riyadh": (24.7136, 46.6753),
    "Jeddah": (21.4858, 39.1925),
    "Dammam": (26.4473, 50.1044),
    "NEOM": (26.5000, 36.0700),
    "Al Khobar": (26.2172, 50.1971),
    "Makkah": (21.3891, 39.8579),
    "Madinah": (24.5247, 39.5692),
    "Tabuk": (28.3838, 36.5550),
    "Buraidah": (26.3260, 43.9750),
}


def _seed_consistent():
    """Use hour-based seed for stable data within the same hour."""
    now = datetime.now()
    random.seed(now.year * 1000000 + now.month * 10000 + now.day * 100 + now.hour + 7)


def _generate_drivers(company, count):
    """Generate drivers for a company."""
    drivers = []
    used_names = set()
    for i in range(count):
        while True:
            first = random.choice(DRIVER_FIRST_NAMES)
            last = random.choice(DRIVER_LAST_NAMES)
            full = f"{first} {last}"
            if full not in used_names:
                used_names.add(full)
                break

        license_type = random.choice(["Heavy Vehicle", "Heavy Vehicle", "Hazmat Certified", "Reefer Certified"])
        hq = company["hq_city"]
        loc_city = random.choice([hq, hq, hq] + list(CITY_COORDS.keys()))
        loc_coords = CITY_COORDS.get(loc_city, (24.7, 46.7))

        drivers.append({
            "id": f'{company["id"]}-DRV-{i+1:02d}',
            "name": full,
            "company_id": company["id"],
            "phone": f"+966 5{random.randint(10,99)} {random.randint(100,999)} {random.randint(1000,9999)}",
            "license_type": license_type,
            "status": "off_duty",  # will be updated by assignment logic
            "current_city": loc_city,
            "current_location": loc_coords,
            "assigned_shipment_id": None,
            "assigned_truck_id": None,
            "stats": {
                "total_deliveries": random.randint(120, 980),
                "on_time_pct": round(random.uniform(85, 99.5), 1),
                "avg_rating": round(random.uniform(3.8, 5.0), 1),
                "km_per_month": random.randint(4000, 12000),
            },
        })
    return drivers


def _generate_trucks(company, count):
    """Generate trucks for a company."""
    trucks = []
    for i in range(count):
        model, base_type = random.choice(TRUCK_MODELS)
        year = random.randint(2019, 2025)
        plate_prefix = random.choice(["A", "B", "D", "H", "R", "S"])
        plate_num = random.randint(1000, 9999)
        plate = f"{plate_prefix} {plate_num} KSA"

        trucks.append({
            "id": f'{company["id"]}-TRK-{i+1:02d}',
            "plate": plate,
            "type": base_type,
            "model": model,
            "year": year,
            "company_id": company["id"],
            "status": "available",  # will be updated by assignment
            "mileage_km": random.randint(15000, 350000),
            "assigned_driver_id": None,
            "assigned_shipment_id": None,
        })

    # Ensure company has at least some cooled trucks if specialization involves cold
    if "Cold" in company["specialization"] or "Temperature" in company["specialization"]:
        for t in trucks[:max(3, len(trucks) // 2)]:
            if t["type"] != "Cooled":
                cooled_models = [m for m, tp in TRUCK_MODELS if tp == "Cooled"]
                t["type"] = "Cooled"
                t["model"] = random.choice(cooled_models)

    # Randomly mark 0-2 trucks as maintenance
    maint_count = random.randint(0, min(2, len(trucks) - 1))
    for t in random.sample(trucks, maint_count):
        t["status"] = "maintenance"

    return trucks


def generate_company_data(shipments):
    """
    Master function: create companies, drivers, trucks, assign shipments.
    Returns dict with companies, drivers, trucks (all keyed by company id).
    """
    _seed_consistent()

    all_companies = []
    all_drivers = {}   # company_id -> list
    all_trucks = {}    # company_id -> list

    for comp in COMPANIES:
        company = dict(comp)
        all_companies.append(company)

        driver_count = random.randint(5, 8)
        drivers = _generate_drivers(company, driver_count)
        all_drivers[company["id"]] = drivers

        truck_count = random.randint(4, 8)
        trucks = _generate_trucks(company, truck_count)
        all_trucks[company["id"]] = trucks

    # ── Assign shipments round-robin to companies ──
    company_ids = [c["id"] for c in all_companies]
    for idx, s in enumerate(shipments):
        cid = company_ids[idx % len(company_ids)]
        s["company_id"] = cid

    # ── Link drivers & trucks to active shipments ──
    for comp in all_companies:
        cid = comp["id"]
        comp_shipments = [s for s in shipments if s.get("company_id") == cid]
        drivers = all_drivers[cid]
        trucks = all_trucks[cid]

        available_drivers = [d for d in drivers if d["status"] != "maintenance"]
        available_trucks = [t for t in trucks if t["status"] not in ("maintenance",)]

        for i, s in enumerate(comp_shipments):
            if i >= len(available_drivers) or i >= len(available_trucks):
                break

            drv = available_drivers[i]
            trk = available_trucks[i]

            # Match truck type to shipment requirement
            if s["truck_type"] == "Cooled":
                cooled_trucks = [t for t in available_trucks if t["type"] == "Cooled" and t["assigned_shipment_id"] is None]
                if cooled_trucks:
                    trk = cooled_trucks[0]

            # Assign
            drv["assigned_shipment_id"] = s["id"]
            drv["assigned_truck_id"] = trk["id"]
            trk["assigned_driver_id"] = drv["id"]
            trk["assigned_shipment_id"] = s["id"]

            # Driver status based on shipment status
            if s["status"] == "In Transit":
                drv["status"] = "active"
                trk["status"] = "in_use"
                # Update driver location to truck position
                from map_utils import simulate_truck_position
                pos = simulate_truck_position(s["route"]["waypoints"], s["progress"])
                drv["current_location"] = (pos[0], pos[1])
                drv["current_city"] = f"En route to {s['destination']}"
            elif s["status"] in ("At Port", "Vessel En Route"):
                drv["status"] = "idle"
                trk["status"] = "available"
                port_coords = s["port_coords"]
                drv["current_location"] = (port_coords["lat"], port_coords["lon"])
                drv["current_city"] = s["port"].split("(")[0].strip()
            elif s["status"] == "Delivered":
                drv["status"] = "idle"
                trk["status"] = "available"
                dest_coords = s["dest_coords"]
                drv["current_location"] = (dest_coords["lat"], dest_coords["lon"])
                drv["current_city"] = s["destination"]

    return {
        "companies": all_companies,
        "drivers": all_drivers,
        "trucks": all_trucks,
    }


def get_company_summary(company_id, shipments, drivers, trucks):
    """Return KPI summary for a single company."""
    comp_shipments = [s for s in shipments if s.get("company_id") == company_id]
    comp_drivers = drivers.get(company_id, [])
    comp_trucks = trucks.get(company_id, [])

    total = len(comp_shipments)
    in_transit = sum(1 for s in comp_shipments if s["status"] == "In Transit")
    at_port = sum(1 for s in comp_shipments if s["status"] == "At Port")
    delivered = sum(1 for s in comp_shipments if s["status"] == "Delivered")
    vessel_enroute = sum(1 for s in comp_shipments if s["status"] == "Vessel En Route")

    on_time = sum(1 for s in comp_shipments if s["time_status"] == "On Time")
    at_risk = sum(1 for s in comp_shipments if s["time_status"] == "At Risk")
    delayed = sum(1 for s in comp_shipments if s["time_status"] == "Delayed")

    active_drivers = sum(1 for d in comp_drivers if d["status"] == "active")
    idle_drivers = sum(1 for d in comp_drivers if d["status"] == "idle")
    off_duty_drivers = sum(1 for d in comp_drivers if d["status"] == "off_duty")

    cooled_trucks = sum(1 for t in comp_trucks if t["type"] == "Cooled")
    regular_trucks = sum(1 for t in comp_trucks if t["type"] == "Regular")
    trucks_in_use = sum(1 for t in comp_trucks if t["status"] == "in_use")
    trucks_available = sum(1 for t in comp_trucks if t["status"] == "available")
    trucks_maintenance = sum(1 for t in comp_trucks if t["status"] == "maintenance")

    fleet_utilization = round(trucks_in_use / len(comp_trucks) * 100) if comp_trucks else 0
    on_time_rate = round(on_time / total * 100) if total else 0

    active = [s for s in comp_shipments if s["status"] in ("In Transit", "At Port", "Vessel En Route")]
    avg_buffer = 0.0
    if active:
        avg_buffer = sum(s["recommendation"]["buffer_hrs"] for s in active) / len(active)

    return {
        "total_shipments": total,
        "in_transit": in_transit,
        "at_port": at_port,
        "delivered": delivered,
        "vessel_enroute": vessel_enroute,
        "on_time": on_time,
        "at_risk": at_risk,
        "delayed": delayed,
        "on_time_rate": on_time_rate,
        "active_drivers": active_drivers,
        "idle_drivers": idle_drivers,
        "off_duty_drivers": off_duty_drivers,
        "cooled_trucks": cooled_trucks,
        "regular_trucks": regular_trucks,
        "trucks_in_use": trucks_in_use,
        "trucks_available": trucks_available,
        "trucks_maintenance": trucks_maintenance,
        "fleet_utilization": fleet_utilization,
        "avg_buffer_hrs": round(avg_buffer, 1),
    }
