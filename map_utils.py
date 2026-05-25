"""
Saudi Arabia & GCC Shipping Optimizer — Map Utilities
Folium map rendering with ships, trucks (cooled/regular), ports, and route lines.
"""

import folium
from config import MAP_CENTER, MAP_ZOOM, COLORS

# ── SVG Icons ──

TRUCK_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 40" width="42" height="26">
  <rect x="0" y="8" width="38" height="24" rx="3" fill="#9B72CF"/>
  <rect x="38" y="14" width="20" height="18" rx="2" fill="#B68FE8"/>
  <polygon points="38,14 50,4 58,4 58,14" fill="#B68FE8"/>
  <rect x="42" y="8" width="10" height="8" rx="1" fill="#F0ECF5" opacity="0.7"/>
  <circle cx="12" cy="34" r="5" fill="#1A1527"/>
  <circle cx="12" cy="34" r="2.5" fill="#B68FE8"/>
  <circle cx="50" cy="34" r="5" fill="#1A1527"/>
  <circle cx="50" cy="34" r="2.5" fill="#B68FE8"/>
</svg>
"""

COOLED_TRUCK_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 40" width="42" height="26">
  <rect x="0" y="8" width="38" height="24" rx="3" fill="#2980B9"/>
  <rect x="38" y="14" width="20" height="18" rx="2" fill="#5DADE2"/>
  <polygon points="38,14 50,4 58,4 58,14" fill="#5DADE2"/>
  <rect x="42" y="8" width="10" height="8" rx="1" fill="#F0ECF5" opacity="0.7"/>
  <text x="12" y="26" font-size="12" fill="#D6EAF8" font-family="Arial" font-weight="bold">*</text>
  <circle cx="12" cy="34" r="5" fill="#1A1527"/>
  <circle cx="12" cy="34" r="2.5" fill="#5DADE2"/>
  <circle cx="50" cy="34" r="5" fill="#1A1527"/>
  <circle cx="50" cy="34" r="2.5" fill="#5DADE2"/>
</svg>
"""

PORT_ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="30" height="30">
  <circle cx="16" cy="16" r="14" fill="#9B72CF" stroke="#0E0B16" stroke-width="2"/>
  <text x="16" y="22" text-anchor="middle" font-size="16" fill="#0E0B16" font-family="Arial">&#9875;</text>
</svg>
"""

CITY_ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="20" height="30">
  <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24s12-15 12-24C24 5.4 18.6 0 12 0z" fill="#B68FE8"/>
  <circle cx="12" cy="12" r="5" fill="#0E0B16"/>
</svg>
"""

SHIP_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 28" width="36" height="25">
  <path d="M4 18 L8 8 L32 8 L36 18 Z" fill="#5DADE2" opacity="0.9"/>
  <rect x="14" y="2" width="12" height="8" rx="1" fill="#3498DB"/>
  <rect x="18" y="0" width="4" height="4" rx="0.5" fill="#2980B9"/>
  <path d="M2 18 Q20 24 38 18 L36 22 Q20 28 4 22 Z" fill="#1ABC9C" opacity="0.8"/>
  <circle cx="12" cy="14" r="1.5" fill="#F0ECF5" opacity="0.6"/>
  <circle cx="20" cy="14" r="1.5" fill="#F0ECF5" opacity="0.6"/>
  <circle cx="28" cy="14" r="1.5" fill="#F0ECF5" opacity="0.6"/>
</svg>
"""


def create_base_map():
    """Create a Folium map centered on Saudi Arabia with dark tiles."""
    m = folium.Map(
        location=[MAP_CENTER["lat"], MAP_CENTER["lon"]],
        zoom_start=MAP_ZOOM,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


def add_port_markers(m, ports, port_summary=None):
    """Add purple anchor markers for ports, with vessel count badges if available."""
    for name, coord in ports.items():
        badge_html = ""
        if port_summary and name in port_summary:
            ps = port_summary[name]
            total_v = ps["vessels_enroute"] + ps["vessels_at_port"]
            if total_v > 0:
                badge_html = (
                    f'<div style="position:absolute;top:-6px;right:-6px;'
                    f'background:#5DADE2;color:white;border-radius:50%;'
                    f'width:16px;height:16px;font-size:10px;text-align:center;'
                    f'line-height:16px;font-weight:bold;">{total_v}</div>'
                )

        icon_html = f'<div style="position:relative;">{PORT_ICON_SVG}{badge_html}</div>'
        icon = folium.DivIcon(html=icon_html, icon_size=(30, 30), icon_anchor=(15, 15))

        popup_lines = [
            f'<b style="color:#B68FE8;">&#9875; {name}</b>',
            f'<span style="color:#9B8FB5;">Port of Origin</span>',
        ]
        if port_summary and name in port_summary:
            ps = port_summary[name]
            popup_lines.append(f'<hr style="margin:4px 0;border-color:#2E2545;">')
            popup_lines.append(f'Ships inbound: <b>{ps["vessels_enroute"]}</b>')
            popup_lines.append(f'Ships at port: <b>{ps["vessels_at_port"]}</b>')
            popup_lines.append(f'Cooled trucks needed: <b style="color:#5DADE2;">{ps["cooled_needed"]}</b>')
            popup_lines.append(f'Regular trucks needed: <b style="color:#B68FE8;">{ps["regular_needed"]}</b>')

        folium.Marker(
            location=[coord["lat"], coord["lon"]],
            popup=folium.Popup(
                f'<div style="font-family:Arial;min-width:180px;background:#1A1527;color:#F0ECF5;padding:8px;border-radius:8px;">'
                + "<br>".join(popup_lines) + '</div>',
                max_width=300,
            ),
            tooltip=name,
            icon=icon,
        ).add_to(m)


def add_city_markers(m, cities):
    """Add purple pin markers for destination cities."""
    for name, coord in cities.items():
        icon = folium.DivIcon(html=CITY_ICON_SVG, icon_size=(20, 30), icon_anchor=(10, 30))
        folium.Marker(
            location=[coord["lat"], coord["lon"]],
            popup=folium.Popup(
                f'<div style="font-family:Arial;min-width:140px;background:#1A1527;color:#F0ECF5;padding:8px;border-radius:8px;">'
                f'<b style="color:#B68FE8;">{name}</b><br>'
                f'<span style="color:#9B8FB5;">Destination City</span></div>',
                max_width=250,
            ),
            tooltip=name,
            icon=icon,
        ).add_to(m)


def add_vessel_markers(m, shipments):
    """Place ship icons near ports for Vessel En Route and At Port shipments."""
    # Group by port and offset each ship slightly
    port_offsets = {}
    for s in shipments:
        if s["status"] not in ("Vessel En Route", "At Port"):
            continue
        port = s["port"]
        if port not in port_offsets:
            port_offsets[port] = 0
        idx = port_offsets[port]
        port_offsets[port] += 1

        pc = s["port_coords"]
        # Offset ships around port (spread in a small arc)
        offset_lat = 0.15 + (idx * 0.08)
        offset_lon = -0.2 + (idx * 0.12)
        if s["status"] == "Vessel En Route":
            offset_lat += 0.15  # further out for en-route

        ship_lat = pc["lat"] + offset_lat
        ship_lon = pc["lon"] + offset_lon

        icon = folium.DivIcon(html=SHIP_SVG, icon_size=(36, 25), icon_anchor=(18, 12))

        status_color = "#5DADE2" if s["status"] == "Vessel En Route" else "#1ABC9C"
        popup_html = (
            f'<div style="font-family:Arial;min-width:200px;background:#1A1527;color:#F0ECF5;padding:10px;border-radius:8px;">'
            f'<b style="color:#5DADE2;font-size:13px;">{s["vessel"]}</b>'
            f'<hr style="margin:5px 0;border-color:#2E2545;">'
            f'<b>Shipment:</b> {s["id"]}<br>'
            f'<b>Cargo:</b> {s["cargo"]}<br>'
            f'<b>Truck:</b> {"&#10052; Cooled" if s["truck_type"] == "Cooled" else "Regular"}<br>'
            f'<b>Destination:</b> {s["destination"]}<br>'
            f'<b>Arrival:</b> {s["vessel_arrival"].strftime("%b %d, %H:%M")}<br>'
            f'<span style="background:{status_color};color:white;padding:2px 8px;border-radius:10px;font-size:11px;">'
            f'{s["status"]}</span></div>'
        )

        folium.Marker(
            location=[ship_lat, ship_lon],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f'{s["vessel"]} ({s["id"]})',
            icon=icon,
        ).add_to(m)


def add_truck_marker(m, position, info=None, is_cooled=False):
    """Add a truck marker (regular or cooled) at the given position."""
    popup_html = (
        '<div style="font-family:Arial;min-width:210px;background:#1A1527;color:#F0ECF5;'
        'padding:10px;border-radius:8px;">'
        '<b style="color:#B68FE8;font-size:14px;">Shipment Details</b>'
    )
    if info:
        status_colors = {"On Time": "#2ECC71", "At Risk": "#F39C12", "Delayed": "#E74C3C"}
        sc = status_colors.get(info.get("time_status", ""), "#999")
        truck_label = "&#10052; Cooled" if is_cooled else "Regular"
        popup_html += f"""
        <hr style="margin:6px 0;border-color:#2E2545;">
        <b>ID:</b> {info.get('shipment_id', 'N/A')}<br>
        <b>Truck:</b> {truck_label}<br>
        <b>From:</b> {info.get('origin', 'N/A')}<br>
        <b>To:</b> {info.get('destination', 'N/A')}<br>
        <b>Progress:</b> {info.get('progress', 0):.0f}%<br>
        <b>ETA:</b> {info.get('eta', 'N/A')}<br>
        <b>Deadline:</b> {info.get('deadline', 'N/A')}<br>
        <span style="background:{sc};color:white;padding:2px 8px;border-radius:10px;font-size:12px;">
        {info.get('time_status', 'Unknown')}</span>
        """
    popup_html += "</div>"

    svg = COOLED_TRUCK_SVG if is_cooled else TRUCK_SVG
    icon = folium.DivIcon(html=svg, icon_size=(42, 26), icon_anchor=(21, 13))
    tooltip_prefix = "&#10052; " if is_cooled else ""
    folium.Marker(
        location=position,
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=f"{tooltip_prefix}Truck {info.get('shipment_id', '')}" if info else "Truck",
        icon=icon,
    ).add_to(m)


def add_route_line(m, route_coords, color=None, weight=4, opacity=0.85):
    """Draw a route polyline."""
    if route_coords and len(route_coords) >= 2:
        folium.PolyLine(
            locations=route_coords,
            color=color or COLORS["route_line"],
            weight=weight,
            opacity=opacity,
        ).add_to(m)


def simulate_truck_position(route_coords, progress_pct):
    """Interpolate truck position along route based on progress percentage (0-100)."""
    if not route_coords:
        return [MAP_CENTER["lat"], MAP_CENTER["lon"]]
    if progress_pct <= 0:
        return route_coords[0]
    if progress_pct >= 100:
        return route_coords[-1]

    import math

    def haversine_approx(p1, p2):
        dlat = p2[0] - p1[0]
        dlon = p2[1] - p1[1]
        return math.sqrt(dlat ** 2 + dlon ** 2)

    total_dist = 0
    segments = []
    for i in range(len(route_coords) - 1):
        d = haversine_approx(route_coords[i], route_coords[i + 1])
        segments.append(d)
        total_dist += d

    if total_dist == 0:
        return route_coords[0]

    target_dist = (progress_pct / 100.0) * total_dist
    cumulative = 0

    for i, seg_dist in enumerate(segments):
        if cumulative + seg_dist >= target_dist:
            remaining = target_dist - cumulative
            frac = remaining / seg_dist if seg_dist > 0 else 0
            lat = route_coords[i][0] + frac * (route_coords[i + 1][0] - route_coords[i][0])
            lon = route_coords[i][1] + frac * (route_coords[i + 1][1] - route_coords[i][1])
            return [lat, lon]
        cumulative += seg_dist

    return route_coords[-1]


def add_all_routes(m, shipments, route_colors, selected_id=None):
    """Draw all shipment routes; selected route is bright/thick, others dim/thin."""
    for i, s in enumerate(shipments):
        waypoints = s["route"]["waypoints"]
        if not waypoints or len(waypoints) < 2:
            continue
        color = route_colors[i % len(route_colors)]
        if selected_id and s["id"] == selected_id:
            add_route_line(m, waypoints, color=color, weight=5, opacity=0.95)
        else:
            add_route_line(m, waypoints, color=color, weight=2, opacity=0.4)


def add_shipment_trucks(m, shipments):
    """Place truck markers for all in-transit shipments at their interpolated positions."""
    for s in shipments:
        if s["status"] != "In Transit" or not s["route"]["waypoints"]:
            continue
        truck_pos = simulate_truck_position(s["route"]["waypoints"], s["progress"])
        is_cooled = s.get("truck_type") == "Cooled"
        add_truck_marker(m, truck_pos, info={
            "shipment_id": s["id"],
            "origin": s["port"],
            "destination": s["destination"],
            "progress": s["progress"],
            "eta": s["truck_eta"].strftime("%b %d, %H:%M"),
            "deadline": s["deadline"].strftime("%b %d, %H:%M"),
            "time_status": s["time_status"],
        }, is_cooled=is_cooled)


def fit_map_bounds(m, coords):
    """Fit map view to show all given coordinates."""
    if coords and len(coords) >= 2:
        lats = [c[0] for c in coords]
        lons = [c[1] for c in coords]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])


# ══════════════════════════════════════════════════════════════
# ANALYTICS MAP HELPERS
# ══════════════════════════════════════════════════════════════

def add_incident_marker(m, incident):
    """Add a red pulsing marker at an incident location."""
    loc = incident["location"]
    inc_type = incident["incident_type"].replace("_", " ").title()
    popup_html = (
        '<div style="font-family:Arial;min-width:220px;background:#1A1527;color:#F0ECF5;'
        'padding:10px;border-radius:8px;">'
        f'<b style="color:#ef4444;font-size:13px;">&#9888; {inc_type}</b>'
        '<hr style="margin:5px 0;border-color:#2E2545;">'
        f'<b>Shipment:</b> {incident["shipment_id"]}<br>'
        f'<b>Route:</b> {incident["port"].split("(")[0].strip()} &rarr; {incident["destination"]}<br>'
        f'<b>Details:</b> {incident["description"]}<br>'
        f'<b>Reported:</b> {incident["reported_at"].strftime("%H:%M")}'
        '</div>'
    )
    # Pulsing red circle
    folium.CircleMarker(
        location=[loc["lat"], loc["lon"]],
        radius=12,
        color="#ef4444",
        fill=True,
        fill_color="#ef4444",
        fill_opacity=0.6,
        weight=3,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Incident: {inc_type}",
    ).add_to(m)
    # Inner dot
    folium.CircleMarker(
        location=[loc["lat"], loc["lon"]],
        radius=5,
        color="#ffffff",
        fill=True,
        fill_color="#ef4444",
        fill_opacity=1.0,
        weight=1,
    ).add_to(m)


def add_alternate_route(m, original_waypoints, alternate_waypoints):
    """Draw original route as dashed red and alternate as solid green."""
    # Original route — red dashed (blocked)
    if original_waypoints and len(original_waypoints) >= 2:
        folium.PolyLine(
            locations=original_waypoints,
            color="#ef4444",
            weight=4,
            opacity=0.7,
            dash_array="10 8",
            tooltip="Original Route (blocked)",
        ).add_to(m)
    # Alternate route — green solid
    if alternate_waypoints and len(alternate_waypoints) >= 2:
        folium.PolyLine(
            locations=alternate_waypoints,
            color="#22c55e",
            weight=4,
            opacity=0.9,
            tooltip="Alternate Route",
        ).add_to(m)


def add_hotspot_markers(m, hotspots):
    """Add orange/red circles for delay hotspots with radius based on severity."""
    for hs in hotspots:
        severity = hs["avg_delay_hrs"] * hs["frequency"]
        if severity > 20:
            color = "#ef4444"
            radius = 18
        elif severity > 10:
            color = "#f59e0b"
            radius = 14
        else:
            color = "#f59e0b"
            radius = 10

        type_label = hs["type"].replace("_", " ").title()
        popup_html = (
            '<div style="font-family:Arial;min-width:200px;background:#1A1527;color:#F0ECF5;'
            'padding:10px;border-radius:8px;">'
            f'<b style="color:{color};font-size:13px;">{hs["name"]}</b>'
            f'<br><span style="color:#9B8FB5;font-size:0.8em;">{type_label}</span>'
            '<hr style="margin:5px 0;border-color:#2E2545;">'
            f'<b>Avg Delay:</b> {hs["avg_delay_hrs"]}h<br>'
            f'<b>Frequency:</b> {hs["frequency"]} incidents<br>'
            f'{hs["description"]}'
            '</div>'
        )
        folium.CircleMarker(
            location=[hs["lat"], hs["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.3,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f'{hs["name"]} — {hs["avg_delay_hrs"]}h avg delay',
        ).add_to(m)
