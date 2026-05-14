"""
Saudi Arabia & GCC Shipping Optimizer
Automated Government Operations Center — Live Shipment Intelligence.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

from config import PORTS, ALL_DESTINATIONS, COLORS
from map_utils import (
    create_base_map,
    add_port_markers,
    add_city_markers,
    add_all_routes,
    add_shipment_trucks,
    add_vessel_markers,
    fit_map_bounds,
)
from mock_data import generate_shipments, get_shipment_summary, get_port_summary

# ── Page Config ──
st.set_page_config(
    page_title="Shipping Optimizer",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Auto-refresh every hour
st_autorefresh(interval=3_600_000, limit=None, key="auto_refresh")

# ══════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — Professional dark dashboard (Grafana / Datadog)
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* ── Reset & Base ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg-0: #0a0a0f;
        --bg-1: #111118;
        --bg-2: #1a1a24;
        --bg-3: #22222f;
        --border: rgba(255,255,255,0.06);
        --border-hover: rgba(255,255,255,0.1);
        --text-0: #f0f0f5;
        --text-1: #b0b0c0;
        --text-2: #70708a;
        --accent: #8b5cf6;
        --accent-dim: rgba(139,92,246,0.15);
        --green: #22c55e;
        --green-dim: rgba(34,197,94,0.12);
        --amber: #f59e0b;
        --amber-dim: rgba(245,158,11,0.12);
        --red: #ef4444;
        --red-dim: rgba(239,68,68,0.12);
        --blue: #3b82f6;
        --blue-dim: rgba(59,130,246,0.12);
        --radius: 8px;
        --radius-lg: 12px;
    }

    /* ── Streamlit Chrome Removal ── */
    .stApp { background: var(--bg-0) !important; font-family: 'Inter', -apple-system, sans-serif !important; }
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    .stDeployButton { display: none !important; }
    .stApp > .main > .block-container {
        padding: 1.25rem 2rem 2rem 2rem !important;
        max-width: 100% !important;
    }
    .main .block-container { color: var(--text-0); }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: var(--bg-1) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] * { color: var(--text-0) !important; }
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] input {
        background: var(--bg-2) !important;
        border-color: var(--border) !important;
        border-radius: var(--radius) !important;
    }
    section[data-testid="stSidebar"] hr { border-color: var(--border) !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label {
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        color: var(--text-2) !important;
        font-weight: 600 !important;
    }

    /* ── Inputs (main area) ── */
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background: var(--bg-2) !important;
        color: var(--text-0) !important;
        border-color: var(--border) !important;
        border-radius: var(--radius) !important;
    }
    .stSelectbox label { color: var(--text-2) !important; font-size: 0.8rem !important; }

    /* ── Buttons ── */
    .stButton > button {
        background: var(--bg-2) !important;
        color: var(--text-0) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        font-weight: 500 !important;
        font-size: 0.82rem !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background: var(--bg-3) !important;
        border-color: var(--border-hover) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--accent) !important;
        border: none !important;
        color: white !important;
    }

    /* ── Top Bar ── */
    .top-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.9rem 1.5rem;
        background: var(--bg-1);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        margin-bottom: 1.25rem;
    }
    .top-bar-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--text-0);
        letter-spacing: -0.01em;
    }
    .top-bar-sub {
        font-size: 0.78rem;
        color: var(--text-2);
        margin-top: 2px;
    }
    .top-bar-right { display: flex; align-items: center; gap: 16px; }
    .live-dot {
        width: 8px; height: 8px; border-radius: 50%; background: var(--green);
        display: inline-block; margin-right: 6px;
        animation: blink 2s infinite;
        box-shadow: 0 0 6px rgba(34,197,94,0.5);
    }
    @keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.4;} }
    .live-label {
        font-size: 0.75rem; font-weight: 600; color: var(--green);
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .top-bar-time { font-size: 0.78rem; color: var(--text-2); }

    /* ── KPI Cards ── */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin-bottom: 12px;
    }
    .kpi {
        background: var(--bg-1);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 16px 20px;
        position: relative;
        overflow: hidden;
        transition: border-color 0.15s ease;
    }
    .kpi:hover { border-color: var(--border-hover); }
    .kpi-label {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--text-2);
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-0);
        line-height: 1;
    }
    .kpi-accent {
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
    }
    .kpi-icon {
        position: absolute;
        top: 14px; right: 16px;
        font-size: 1.1rem;
        opacity: 0.5;
    }
    .kpi-sub {
        font-size: 0.72rem;
        color: var(--text-2);
        margin-top: 4px;
    }

    /* ── Alert Strip ── */
    .alert-strip {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 16px;
        border-radius: var(--radius);
        font-size: 0.82rem;
        margin-bottom: 14px;
        font-weight: 500;
    }
    .alert-strip.critical {
        background: var(--red-dim);
        border: 1px solid rgba(239,68,68,0.25);
        color: #fca5a5;
    }
    .alert-strip.warn {
        background: var(--amber-dim);
        border: 1px solid rgba(245,158,11,0.25);
        color: #fcd34d;
    }
    .alert-strip.ok {
        background: var(--green-dim);
        border: 1px solid rgba(34,197,94,0.25);
        color: #86efac;
    }
    .alert-strip .alert-icon { font-size: 1rem; flex-shrink: 0; }

    /* ── Section Titles ── */
    .sec-title {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: var(--text-2);
        margin: 1.5rem 0 0.75rem 0;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border);
    }

    /* ── Panel (generic card wrapper) ── */
    .panel {
        background: var(--bg-1);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 20px;
        margin-bottom: 14px;
    }

    /* ── Port Operations Table ── */
    .ops-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.82rem;
    }
    .ops-table th {
        text-align: left;
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-2);
        padding: 10px 14px;
        border-bottom: 1px solid var(--border);
        background: transparent;
    }
    .ops-table td {
        padding: 11px 14px;
        color: var(--text-0);
        border-bottom: 1px solid var(--border);
        font-variant-numeric: tabular-nums;
    }
    .ops-table tr:last-child td { border-bottom: none; }
    .ops-table tr:hover td { background: rgba(255,255,255,0.02); }
    .ops-table .port-name { font-weight: 600; color: var(--accent); }
    .ops-table .val-cool { color: var(--blue); font-weight: 600; }
    .ops-table .val-reg { color: var(--accent); font-weight: 600; }

    /* ── Detail Mini Cards ── */
    .detail-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 10px;
        margin-bottom: 14px;
    }
    .detail-card {
        background: var(--bg-2);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 12px 14px;
        text-align: center;
    }
    .detail-card .dc-label {
        font-size: 0.65rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.5px;
        color: var(--text-2); margin-bottom: 6px;
    }
    .detail-card .dc-value {
        font-size: 1.1rem; font-weight: 700; color: var(--text-0);
    }

    /* ── Recommendation Grid ── */
    .rec-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-bottom: 14px;
    }

    /* ── Recovery Banner ── */
    .recovery {
        padding: 14px 18px;
        border-radius: var(--radius);
        font-size: 0.85rem;
        line-height: 1.5;
        color: var(--text-0);
    }
    .recovery b { color: var(--accent); }
    .recovery.action {
        background: var(--amber-dim);
        border: 1px solid rgba(245,158,11,0.2);
    }
    .recovery.ok {
        background: var(--green-dim);
        border: 1px solid rgba(34,197,94,0.2);
    }

    /* ── Status Pill ── */
    .pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.2px;
    }
    .pill-green { background: var(--green-dim); color: var(--green); }
    .pill-amber { background: var(--amber-dim); color: var(--amber); }
    .pill-red { background: var(--red-dim); color: var(--red); }
    .pill-blue { background: var(--blue-dim); color: var(--blue); }
    .pill-purple { background: var(--accent-dim); color: var(--accent); }

    /* ── Sidebar Alerts ── */
    .sb-alert {
        padding: 10px 12px;
        border-radius: var(--radius);
        font-size: 0.8rem;
        margin-bottom: 8px;
        font-weight: 500;
        line-height: 1.45;
    }
    .sb-alert.crit {
        background: var(--red-dim);
        border: 1px solid rgba(239,68,68,0.2);
        color: #fca5a5;
    }
    .sb-alert.warn {
        background: var(--amber-dim);
        border: 1px solid rgba(245,158,11,0.2);
        color: #fcd34d;
    }
    .sb-alert.ok {
        background: var(--green-dim);
        border: 1px solid rgba(34,197,94,0.2);
        color: #86efac;
    }
    .sb-alert strong { font-weight: 700; }
    .sb-detail {
        font-size: 0.75rem;
        color: var(--text-2);
        margin-top: 4px;
        padding-left: 2px;
    }

    /* ── Dataframe / Table ── */
    [data-testid="stDataFrame"] {
        background: var(--bg-1);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border);
    }

    /* ── Native Streamlit overrides ── */
    .stAlert { display: none !important; }
    div[data-testid="stExpander"] {
        background: var(--bg-1) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
    }
    div[data-testid="stExpander"] summary {
        color: var(--text-0) !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
if "shipments" not in st.session_state:
    st.session_state.shipments = generate_shipments(15)
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if "selected_shipment_id" not in st.session_state:
    st.session_state.selected_shipment_id = None

if (datetime.now() - st.session_state.last_refresh).seconds > 3600:
    st.session_state.shipments = generate_shipments(15)
    st.session_state.last_refresh = datetime.now()

shipments = st.session_state.shipments
summary = get_shipment_summary(shipments)

# ══════════════════════════════════════════════════════════════════
# TOP BAR
# ══════════════════════════════════════════════════════════════════
now_str = datetime.now().strftime("%b %d, %Y  %H:%M")
st.markdown(f"""
<div class="top-bar">
    <div>
        <div class="top-bar-title">Saudi Arabia & GCC Shipping Optimizer</div>
        <div class="top-bar-sub">Government Operations Center &mdash; Automated Delivery Intelligence</div>
    </div>
    <div class="top-bar-right">
        <div><span class="live-dot"></span><span class="live-label">Live</span></div>
        <div class="top-bar-time">{now_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="padding:4px 0 12px 0;">
        <div style="font-size:0.92rem;font-weight:700;color:var(--text-0);margin-bottom:2px;">Filters</div>
        <div style="font-size:0.72rem;color:var(--text-2);">Narrow down shipment data</div>
    </div>
    """, unsafe_allow_html=True)

    filter_ports = st.multiselect("Port", list(PORTS.keys()), default=[])
    filter_status = st.multiselect("Status", ["Vessel En Route", "At Port", "In Transit", "Delivered"], default=[])
    filter_priority = st.multiselect("Priority", ["Critical", "High", "Standard"], default=[])
    filter_delivery = st.multiselect("Delivery Status", ["On Time", "At Risk", "Delayed"], default=[])

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Custom alerts (no native st.error/warning/success)
    critical_delayed = [s for s in shipments if s["priority"] == "Critical" and s["time_status"] == "Delayed"]
    needs_action = [s for s in shipments if s["recommendation"]["recovery_action"]]

    if critical_delayed:
        details = "".join(
            f'<div class="sb-detail">{s["id"]} &mdash; {s["port"].split("(")[0].strip()} &rarr; {s["destination"]}</div>'
            for s in critical_delayed
        )
        st.markdown(
            f'<div class="sb-alert crit"><strong>{len(critical_delayed)} critical shipment(s) delayed</strong>{details}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="sb-alert ok">No critical delays</div>',
            unsafe_allow_html=True,
        )

    if needs_action:
        st.markdown(
            f'<div class="sb-alert warn"><strong>{len(needs_action)} shipment(s)</strong> require attention</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.72rem;color:var(--text-2);padding:4px 0;">Last refresh &mdash; {st.session_state.last_refresh.strftime("%H:%M:%S")}</div>',
        unsafe_allow_html=True,
    )
    if st.button("Refresh Data", type="primary", use_container_width=True):
        st.session_state.shipments = generate_shipments(15)
        st.session_state.last_refresh = datetime.now()
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# APPLY FILTERS
# ══════════════════════════════════════════════════════════════════
filtered = shipments
if filter_ports:
    filtered = [s for s in filtered if s["port"] in filter_ports]
if filter_status:
    filtered = [s for s in filtered if s["status"] in filter_status]
if filter_priority:
    filtered = [s for s in filtered if s["priority"] in filter_priority]
if filter_delivery:
    filtered = [s for s in filtered if s["time_status"] in filter_delivery]

f_summary = get_shipment_summary(filtered)

# ══════════════════════════════════════════════════════════════════
# KPI CARDS — Row 1: Fleet Status
# ══════════════════════════════════════════════════════════════════
def kpi_html(label, value, color, icon, sub=None):
    accent = f'<div class="kpi-accent" style="background:{color};"></div>'
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi">{accent}'
        f'<div class="kpi-icon" style="color:{color};">{icon}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="color:{color};">{value}</div>'
        f'{sub_html}</div>'
    )

pct_on_time = round(f_summary["on_time"] / f_summary["total"] * 100) if f_summary["total"] else 0

st.markdown(f"""
<div class="kpi-grid">
    {kpi_html("Total Shipments", f_summary["total"], "var(--text-0)", "&#9776;", f'{f_summary["delivered"]} delivered')}
    {kpi_html("In Transit", f_summary["in_transit"], "var(--accent)", "&#10132;", f'{f_summary["vessel_enroute"]} vessels inbound')}
    {kpi_html("At Port", f_summary["at_port"], "var(--blue)", "&#9875;", f'{f_summary["cooled"]} cooled &bull; {f_summary["regular"]} regular')}
    {kpi_html("On Time", f"{pct_on_time}%", "var(--green)", "&#10003;", f'{f_summary["on_time"]} of {f_summary["total"]} shipments')}
    {kpi_html("Avg Buffer", f'{f_summary["avg_buffer_hrs"]}h', "var(--amber)" if f_summary["avg_buffer_hrs"] < 4 else "var(--green)", "&#9201;", f'{f_summary["needs_action"]} need action')}
</div>
""", unsafe_allow_html=True)

# KPI Row 2: Health breakdown
st.markdown(f"""
<div class="kpi-grid">
    {kpi_html("At Risk", f_summary["at_risk"], "var(--amber)", "&#9888;")}
    {kpi_html("Delayed", f_summary["delayed"], "var(--red)", "&#10006;")}
    {kpi_html("Cooled Fleet", f_summary["cooled"], "var(--blue)", "&#10052;")}
    {kpi_html("Regular Fleet", f_summary["regular"], "var(--accent)", "&#9951;")}
    {kpi_html("Vessels Inbound", f_summary["vessel_enroute"], "var(--text-1)", "&#9973;")}
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# ALERT STRIP
# ══════════════════════════════════════════════════════════════════
delayed_ships = [s for s in filtered if s["time_status"] == "Delayed"]
if delayed_ships:
    ids = ", ".join(s["id"] for s in delayed_ships[:5])
    more = f" +{len(delayed_ships)-5} more" if len(delayed_ships) > 5 else ""
    st.markdown(f"""
    <div class="alert-strip critical">
        <span class="alert-icon">&#9888;</span>
        <span><strong>{len(delayed_ships)} shipment(s)</strong> projected to miss deadline &mdash; {ids}{more}</span>
    </div>
    """, unsafe_allow_html=True)
elif needs_action:
    st.markdown(f"""
    <div class="alert-strip warn">
        <span class="alert-icon">&#9888;</span>
        <span><strong>{len(needs_action)} shipment(s)</strong> require monitoring or intervention</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="alert-strip ok">
        <span class="alert-icon">&#10003;</span>
        <span>All shipments operating within schedule</span>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# LIVE MAP
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-title">Live Operations Map</div>', unsafe_allow_html=True)

m = create_base_map()
port_summary = get_port_summary(shipments)
add_port_markers(m, PORTS, port_summary=port_summary)
add_city_markers(m, ALL_DESTINATIONS)

route_colors = COLORS["route_colors"]
add_all_routes(m, filtered, route_colors, selected_id=st.session_state.selected_shipment_id)
add_vessel_markers(m, filtered)
add_shipment_trucks(m, filtered)

all_wps = []
for s in filtered:
    all_wps.extend(s["route"]["waypoints"])
if all_wps:
    fit_map_bounds(m, all_wps)

st_folium(m, use_container_width=True, height=540, returned_objects=[])

# ══════════════════════════════════════════════════════════════════
# PORT OPERATIONS TABLE
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-title">Port Operations</div>', unsafe_allow_html=True)

rows_html = ""
for pname, ps in port_summary.items():
    if ps["total_shipments"] == 0:
        continue
    rows_html += (
        f'<tr>'
        f'<td class="port-name">{pname}</td>'
        f'<td>{ps["total_shipments"]}</td>'
        f'<td>{ps["vessels_enroute"]}</td>'
        f'<td>{ps["vessels_at_port"]}</td>'
        f'<td>{ps["trucks_dispatched"]}</td>'
        f'<td class="val-cool">{ps["cooled_needed"]}</td>'
        f'<td class="val-reg">{ps["regular_needed"]}</td>'
        f'</tr>'
    )

st.markdown(f"""
<div class="panel">
    <table class="ops-table">
        <thead><tr>
            <th>Port</th><th>Shipments</th><th>Vessels Inbound</th>
            <th>At Port</th><th>Dispatched</th><th>Cooled Needed</th><th>Regular Needed</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SHIPMENT DETAIL
# ══════════════════════════════════════════════════════════════════
if filtered:
    st.markdown('<div class="sec-title">Shipment Detail</div>', unsafe_allow_html=True)

    shipment_options = {
        s["id"]: f'{s["id"]}  |  {s["vessel"]}  |  {s["port"].split("(")[0].strip()} → {s["destination"]}  |  {s["time_status"]}'
        for s in filtered
    }
    selected_id = st.selectbox(
        "Select shipment",
        options=list(shipment_options.keys()),
        format_func=lambda x: shipment_options[x],
        key="shipment_selector",
    )
    st.session_state.selected_shipment_id = selected_id

    ship = next(s for s in filtered if s["id"] == selected_id)
    rec = ship["recommendation"]
    route = ship["route"]
    drive_h = int(route["duration_hrs"])
    drive_m = int((route["duration_hrs"] % 1) * 60)
    buf = rec["buffer_hrs"]

    # Status pill
    ts_pill = {"On Time": "pill-green", "At Risk": "pill-amber", "Delayed": "pill-red"}.get(ship["time_status"], "pill-purple")
    truck_pill = "pill-blue" if ship["truck_type"] == "Cooled" else "pill-purple"
    dispatched_str = ship["truck_dispatch"].strftime("%b %d, %H:%M") if ship["status"] != "Vessel En Route" else "Pending"
    buf_pill = "pill-green" if buf > 4 else ("pill-amber" if buf > 0 else "pill-red")

    st.markdown(f"""
    <div class="panel">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
            <span style="font-size:1rem;font-weight:700;color:var(--text-0);">{ship["id"]}</span>
            <span class="pill {ts_pill}">{ship["time_status"]}</span>
            <span class="pill {truck_pill}">{"&#10052; Cooled" if ship["truck_type"] == "Cooled" else "Regular"}</span>
            <span class="pill pill-purple">{ship["priority"]}</span>
        </div>
        <div class="detail-grid">
            <div class="detail-card">
                <div class="dc-label">Distance</div>
                <div class="dc-value">{route["distance_km"]:.0f} km</div>
            </div>
            <div class="detail-card">
                <div class="dc-label">Drive Time</div>
                <div class="dc-value">{drive_h}h {drive_m}m</div>
            </div>
            <div class="detail-card">
                <div class="dc-label">Dispatched</div>
                <div class="dc-value" style="font-size:0.95rem;">{dispatched_str}</div>
            </div>
            <div class="detail-card">
                <div class="dc-label">ETA</div>
                <div class="dc-value" style="font-size:0.95rem;">{ship["truck_eta"].strftime("%b %d, %H:%M")}</div>
            </div>
            <div class="detail-card">
                <div class="dc-label">Deadline</div>
                <div class="dc-value" style="font-size:0.95rem;">{ship["deadline"].strftime("%b %d, %H:%M")}</div>
            </div>
            <div class="detail-card">
                <div class="dc-label">Buffer</div>
                <div class="dc-value"><span class="pill {buf_pill}">{buf:.1f}h</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Optimization Recommendation
    verdict_color = {
        "Optimal": "var(--green)", "Early": "var(--accent)",
        "Late": "var(--amber)", "Critical": "var(--red)",
    }.get(rec["dispatch_verdict"], "var(--accent)")

    arrival_color = {
        "On Time": "var(--green)", "At Risk": "var(--amber)", "Delayed": "var(--red)",
    }.get(ship["time_status"], "var(--accent)")

    st.markdown(f"""
    <div class="panel">
        <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;color:var(--text-2);margin-bottom:14px;">
            Optimization Recommendation
        </div>
        <div class="rec-grid">
            <div class="detail-card">
                <div class="dc-label">Optimal Dispatch</div>
                <div class="dc-value" style="font-size:0.95rem;">{rec["optimal_dispatch"].strftime("%b %d, %H:%M")}</div>
            </div>
            <div class="detail-card">
                <div class="dc-label">Latest Dispatch</div>
                <div class="dc-value" style="font-size:0.95rem;">{rec["latest_dispatch"].strftime("%b %d, %H:%M")}</div>
            </div>
            <div class="detail-card">
                <div class="dc-label">Dispatch Verdict</div>
                <div class="dc-value" style="color:{verdict_color};font-size:1rem;">{rec["dispatch_verdict"]}</div>
            </div>
            <div class="detail-card">
                <div class="dc-label">Arrival Status</div>
                <div class="dc-value" style="color:{arrival_color};font-size:1rem;">{ship["time_status"]}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if rec["recovery_action"]:
        st.markdown(
            f'<div class="recovery action"><b>Recovery Action:</b> {rec["recovery_action"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="recovery ok"><b>Status:</b> Shipment is on track. No action required.</div>',
            unsafe_allow_html=True,
        )

# ══════════════════════════════════════════════════════════════════
# ALL SHIPMENTS TABLE
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-title">All Shipments</div>', unsafe_allow_html=True)

rows = []
for s in filtered:
    rec = s["recommendation"]
    rows.append({
        "ID": s["id"],
        "Vessel": s["vessel"],
        "Port": s["port"].split("(")[0].strip(),
        "Destination": s["destination"],
        "Cargo": s["cargo"],
        "Truck": s["truck_type"],
        "Priority": s["priority"],
        "Status": s["status"],
        "Progress": f'{s["progress"]:.0f}%',
        "ETA": s["truck_eta"].strftime("%b %d, %H:%M"),
        "Deadline": s["deadline"].strftime("%b %d, %H:%M"),
        "Buffer": f'{rec["buffer_hrs"]:.1f}h',
        "Delivery": s["time_status"],
        "Verdict": rec["dispatch_verdict"],
        "Action": rec["recovery_action"] or "On track",
    })

df = pd.DataFrame(rows)


def _style_delivery(val):
    colors = {"On Time": "#166534", "At Risk": "#78350f", "Delayed": "#7f1d1d"}
    bgs = {"On Time": "rgba(34,197,94,0.15)", "At Risk": "rgba(245,158,11,0.15)", "Delayed": "rgba(239,68,68,0.15)"}
    if val in colors:
        return f"color: {colors[val]}; background: {bgs[val]}; border-radius: 4px; padding: 2px 8px; font-weight: 600;"
    return ""


def _style_priority(val):
    if val == "Critical":
        return "color: #fca5a5; background: rgba(239,68,68,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"
    if val == "High":
        return "color: #fcd34d; background: rgba(245,158,11,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"
    return "color: #c4b5fd; background: rgba(139,92,246,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"


def _style_truck(val):
    if val == "Cooled":
        return "color: #93c5fd; background: rgba(59,130,246,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"
    return "color: #c4b5fd; background: rgba(139,92,246,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"


def _style_verdict(val):
    if val == "Optimal":
        return "color: #86efac; background: rgba(34,197,94,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"
    if val in ("Late", "Critical"):
        return "color: #fca5a5; background: rgba(239,68,68,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"
    return "color: #fcd34d; background: rgba(245,158,11,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"


if not df.empty:
    styled = (
        df.style
        .map(_style_delivery, subset=["Delivery"])
        .map(_style_priority, subset=["Priority"])
        .map(_style_truck, subset=["Truck"])
        .map(_style_verdict, subset=["Verdict"])
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=480)
else:
    st.markdown(
        '<div class="panel" style="text-align:center;color:var(--text-2);padding:40px;">No shipments match the current filters.</div>',
        unsafe_allow_html=True,
    )
