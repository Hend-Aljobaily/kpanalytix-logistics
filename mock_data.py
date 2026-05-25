"""
Saudi Arabia & GCC Shipping Optimizer — Mock Live Shipment Data
Generates enriched shipments with routes, truck types, and optimization recommendations.
"""

import random
from datetime import datetime, timedelta
from config import (
    PORTS, ALL_DESTINATIONS, CARGO_TYPES, VESSEL_NAMES, COOLED_CARGO,
    get_precomputed_route,
)


def _seed_consistent():
    """Use hour-based seed so data stays stable within the same hour."""
    now = datetime.now()
    random.seed(now.year * 1000000 + now.month * 10000 + now.day * 100 + now.hour)


def generate_shipments(count=15):
    """
    Generate mock live shipments with routes, truck types, and recommendations.
    """
    _seed_consistent()

    now = datetime.now().replace(second=0, microsecond=0)
    port_names = list(PORTS.keys())
    dest_names = list(ALL_DESTINATIONS.keys())

    shipments = []
    for i in range(count):
        port = random.choice(port_names)
        dest = random.choice(dest_names)
        cargo = random.choice(CARGO_TYPES)
        vessel = random.choice(VESSEL_NAMES)
        priority = random.choices(
            ["Critical", "High", "Standard"], weights=[15, 35, 50],
        )[0]

        truck_type = "Cooled" if cargo in COOLED_CARGO else "Regular"

        route = get_precomputed_route(port, dest)
        drive_hrs = route["duration_hrs"]

        vessel_offset_hrs = random.uniform(-8, 16)
        vessel_arrival = now + timedelta(hours=vessel_offset_hrs)

        unload_hrs = random.uniform(2, 4)
        truck_dispatch = vessel_arrival + timedelta(hours=unload_hrs)

        if priority == "Critical":
            deadline_hrs = drive_hrs + random.uniform(2, 6)
        elif priority == "High":
            deadline_hrs = drive_hrs + random.uniform(4, 12)
        else:
            deadline_hrs = drive_hrs + random.uniform(8, 24)
        deadline = truck_dispatch + timedelta(hours=deadline_hrs)

        truck_eta = truck_dispatch + timedelta(hours=drive_hrs)

        if now < vessel_arrival:
            status = "Vessel En Route"
            progress = 0
        elif now < truck_dispatch:
            status = "At Port"
            progress = 0
        elif now < truck_eta:
            status = "In Transit"
            elapsed = (now - truck_dispatch).total_seconds() / 3600
            progress = min(95, max(5, (elapsed / drive_hrs) * 100))
        else:
            status = "Delivered"
            progress = 100

        buffer_hrs = (deadline - truck_eta).total_seconds() / 3600

        if status == "Delivered":
            time_status = "On Time"
        elif buffer_hrs > 4:
            time_status = "On Time"
        elif buffer_hrs > 0:
            time_status = "At Risk"
        else:
            time_status = "Delayed"

        optimal_dispatch = deadline - timedelta(hours=drive_hrs + 2)
        latest_dispatch = deadline - timedelta(hours=drive_hrs)
        actual_vs_optimal = (optimal_dispatch - truck_dispatch).total_seconds() / 3600

        if abs(actual_vs_optimal) <= 1:
            dispatch_verdict = "Optimal"
        elif actual_vs_optimal > 1:
            dispatch_verdict = "Early"
        elif actual_vs_optimal > -3:
            dispatch_verdict = "Late"
        else:
            dispatch_verdict = "Critical"

        if time_status == "Delayed":
            recovery_action = (
                f"EXPEDITE: {abs(buffer_hrs):.1f}h behind schedule. "
                "Reroute to shortest path, authorize priority lane access."
            )
        elif time_status == "At Risk":
            recovery_action = (
                f"MONITOR: Only {buffer_hrs:.1f}h buffer remaining. "
                "Avoid unscheduled stops, prepare contingency."
            )
        elif dispatch_verdict == "Critical":
            recovery_action = (
                "DISPATCH DELAYED: Truck dispatched significantly late. "
                "Expedite loading at next stop."
            )
        else:
            recovery_action = None

        shipments.append({
            "id": f"SHP-{2026}{(i + 1):04d}",
            "company_id": None,
            "vessel": vessel,
            "port": port,
            "destination": dest,
            "cargo": cargo,
            "priority": priority,
            "truck_type": truck_type,
            "vessel_arrival": vessel_arrival,
            "truck_dispatch": truck_dispatch,
            "deadline": deadline,
            "truck_eta": truck_eta,
            "status": status,
            "progress": round(progress, 1),
            "time_status": time_status,
            "port_coords": PORTS[port],
            "dest_coords": ALL_DESTINATIONS[dest],
            "route": route,
            "recommendation": {
                "optimal_dispatch": optimal_dispatch,
                "latest_dispatch": latest_dispatch,
                "dispatch_verdict": dispatch_verdict,
                "buffer_hrs": round(buffer_hrs, 1),
                "recovery_action": recovery_action,
            },
        })

    # ── Guarantee minimum delayed / at-risk shipments for analytics ──
    _ensure_status_mix(shipments, now)

    priority_order = {"Critical": 0, "High": 1, "Standard": 2}
    shipments.sort(key=lambda s: (priority_order[s["priority"]], s["deadline"]))
    return shipments


def _ensure_status_mix(shipments, now):
    """Ensure at least 3 delayed and 3 at-risk shipments by tightening deadlines."""
    min_delayed = 3
    min_at_risk = 3

    delayed = [s for s in shipments if s["time_status"] == "Delayed"]
    at_risk = [s for s in shipments if s["time_status"] == "At Risk"]
    on_time = [s for s in shipments if s["time_status"] == "On Time" and s["status"] != "Delivered"]

    need_delayed = max(0, min_delayed - len(delayed))
    need_at_risk = max(0, min_at_risk - len(at_risk))

    # Convert some on-time shipments to delayed
    for s in on_time[:need_delayed]:
        _force_time_status(s, "Delayed", now)
    remaining_on_time = on_time[need_delayed:]

    # Convert some on-time shipments to at-risk
    for s in remaining_on_time[:need_at_risk]:
        _force_time_status(s, "At Risk", now)


def _force_time_status(s, target_status, now):
    """Adjust a shipment's deadline to force a specific time_status."""
    if target_status == "Delayed":
        # Set deadline before ETA so buffer is negative
        offset_hrs = random.uniform(1.0, 4.0)
        s["deadline"] = s["truck_eta"] - timedelta(hours=offset_hrs)
    elif target_status == "At Risk":
        # Set deadline just after ETA so buffer is 0-4h
        offset_hrs = random.uniform(0.5, 3.5)
        s["deadline"] = s["truck_eta"] + timedelta(hours=offset_hrs)

    buffer_hrs = (s["deadline"] - s["truck_eta"]).total_seconds() / 3600
    s["time_status"] = target_status
    s["recommendation"]["buffer_hrs"] = round(buffer_hrs, 1)

    # Recalculate dispatch verdict & recovery action
    drive_hrs = s["route"]["duration_hrs"]
    optimal_dispatch = s["deadline"] - timedelta(hours=drive_hrs + 2)
    latest_dispatch = s["deadline"] - timedelta(hours=drive_hrs)
    actual_vs_optimal = (optimal_dispatch - s["truck_dispatch"]).total_seconds() / 3600

    if abs(actual_vs_optimal) <= 1:
        dispatch_verdict = "Optimal"
    elif actual_vs_optimal > 1:
        dispatch_verdict = "Early"
    elif actual_vs_optimal > -3:
        dispatch_verdict = "Late"
    else:
        dispatch_verdict = "Critical"

    s["recommendation"]["optimal_dispatch"] = optimal_dispatch
    s["recommendation"]["latest_dispatch"] = latest_dispatch
    s["recommendation"]["dispatch_verdict"] = dispatch_verdict

    if target_status == "Delayed":
        s["recommendation"]["recovery_action"] = (
            f"EXPEDITE: {abs(buffer_hrs):.1f}h behind schedule. "
            "Reroute to shortest path, authorize priority lane access."
        )
    elif target_status == "At Risk":
        s["recommendation"]["recovery_action"] = (
            f"MONITOR: Only {buffer_hrs:.1f}h buffer remaining. "
            "Avoid unscheduled stops, prepare contingency."
        )


def get_shipment_summary(shipments):
    """Return summary stats for the dashboard header."""
    total = len(shipments)
    on_time = sum(1 for s in shipments if s["time_status"] == "On Time")
    at_risk = sum(1 for s in shipments if s["time_status"] == "At Risk")
    delayed = sum(1 for s in shipments if s["time_status"] == "Delayed")
    in_transit = sum(1 for s in shipments if s["status"] == "In Transit")
    at_port = sum(1 for s in shipments if s["status"] == "At Port")
    vessel_enroute = sum(1 for s in shipments if s["status"] == "Vessel En Route")
    delivered = sum(1 for s in shipments if s["status"] == "Delivered")
    needs_action = sum(1 for s in shipments if s["recommendation"]["recovery_action"] is not None)
    cooled = sum(1 for s in shipments if s["truck_type"] == "Cooled")
    regular = sum(1 for s in shipments if s["truck_type"] == "Regular")

    active = [s for s in shipments if s["status"] in ("In Transit", "At Port", "Vessel En Route")]
    avg_buffer = 0.0
    if active:
        avg_buffer = sum(s["recommendation"]["buffer_hrs"] for s in active) / len(active)

    return {
        "total": total,
        "on_time": on_time,
        "at_risk": at_risk,
        "delayed": delayed,
        "in_transit": in_transit,
        "at_port": at_port,
        "vessel_enroute": vessel_enroute,
        "delivered": delivered,
        "needs_action": needs_action,
        "cooled": cooled,
        "regular": regular,
        "avg_buffer_hrs": round(avg_buffer, 1),
    }


def get_port_summary(shipments):
    """Return per-port breakdown: vessels, trucks needed (cooled vs regular)."""
    from config import PORTS
    port_data = {}
    for pname in PORTS:
        port_ships = [s for s in shipments if s["port"] == pname]
        vessels_enroute = sum(1 for s in port_ships if s["status"] == "Vessel En Route")
        vessels_at_port = sum(1 for s in port_ships if s["status"] == "At Port")
        trucks_dispatched = sum(1 for s in port_ships if s["status"] in ("In Transit", "Delivered"))
        cooled_needed = sum(1 for s in port_ships if s["truck_type"] == "Cooled" and s["status"] != "Delivered")
        regular_needed = sum(1 for s in port_ships if s["truck_type"] == "Regular" and s["status"] != "Delivered")
        port_data[pname] = {
            "total_shipments": len(port_ships),
            "vessels_enroute": vessels_enroute,
            "vessels_at_port": vessels_at_port,
            "trucks_dispatched": trucks_dispatched,
            "cooled_needed": cooled_needed,
            "regular_needed": regular_needed,
        }
    return port_data
