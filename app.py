"""
Logistics Optimizer
Automated Government Operations Center — Live Shipment Intelligence.
"""

import streamlit as st
import pandas as pd
import folium
from datetime import datetime, timezone, timedelta

# Saudi Arabia timezone (UTC+3)
_TZ_SA = timezone(timedelta(hours=3))

def _now():
    """Current time in Saudi Arabia timezone."""
    return datetime.now(_TZ_SA)
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

from config import PORTS, ALL_DESTINATIONS, COLORS, DEST_COUNTRY_MAP, DEST_COUNTRIES, DEFAULT_COST_PARAMS
from map_utils import (
    create_base_map,
    add_port_markers,
    add_city_markers,
    add_all_routes,
    add_shipment_trucks,
    add_vessel_markers,
    fit_map_bounds,
    simulate_truck_position,
    add_hotspot_markers,
    add_incident_marker,
    add_alternate_route,
    add_delay_colored_routes,
    create_driver_route_map,
    add_optimization_routes,
)
from mock_data import generate_shipments, get_shipment_summary, get_port_summary
from company_data import generate_company_data, get_company_summary, COMPANIES
from delay_analytics_data import generate_analytics_data, generate_route_options

# ── Page Config ──
st.set_page_config(
    page_title="Logistics Optimizer",
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
    header[data-testid="stHeader"] { background: var(--bg-0) !important; }
    footer { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
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

    /* ── Tab styling (dark theme) ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--bg-1);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border);
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-2) !important;
        border: none !important;
        border-radius: var(--radius) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 8px 24px !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--bg-3) !important;
        color: var(--text-0) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    .stTabs [data-baseweb="tab-border"] { display: none !important; }

    /* ── Company Header ── */
    .company-header {
        background: var(--bg-1);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 18px 24px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .company-header .ch-name {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text-0);
    }
    .company-header .ch-detail {
        font-size: 0.78rem;
        color: var(--text-2);
        margin-top: 3px;
    }

    /* ── Driver Card ── */
    .driver-card {
        background: var(--bg-1);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 18px 22px;
        margin-bottom: 12px;
    }
    .driver-card .drv-name {
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-0);
        margin-bottom: 4px;
    }
    .driver-card .drv-info {
        font-size: 0.78rem;
        color: var(--text-2);
        margin-bottom: 10px;
    }

    /* ── Analytics: Cause Card ── */
    .cause-card {
        background: var(--bg-2);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 14px 16px;
        margin-bottom: 8px;
        border-left: 3px solid var(--amber);
    }
    .cause-card.severe { border-left-color: var(--red); }
    .cause-card.moderate { border-left-color: var(--amber); }
    .cause-card.minor { border-left-color: var(--blue); }
    .cause-card .cc-cause {
        font-size: 0.82rem; font-weight: 700; color: var(--text-0); margin-bottom: 4px;
    }
    .cause-card .cc-desc {
        font-size: 0.78rem; color: var(--text-1); margin-bottom: 4px;
    }
    .cause-card .cc-meta {
        font-size: 0.72rem; color: var(--text-2);
    }

    /* ── Analytics: Trip Row ── */
    .trip-row {
        display: grid;
        grid-template-columns: 90px 1fr 80px 80px 80px 65px 80px 1fr;
        gap: 8px;
        padding: 8px 12px;
        font-size: 0.78rem;
        border-bottom: 1px solid var(--border);
        align-items: center;
    }
    .trip-row:hover { background: rgba(255,255,255,0.02); }
    .trip-row.header {
        font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.5px; color: var(--text-2); border-bottom: 1px solid var(--border);
    }
    .trip-row .trip-val { color: var(--text-0); font-variant-numeric: tabular-nums; }
    .trip-row .trip-delayed { color: var(--red); }
    .trip-row .trip-ontime { color: var(--green); }

    /* ── Analytics: Hotspot Badge ── */
    .hotspot-badge {
        display: inline-block; padding: 2px 8px; border-radius: 10px;
        font-size: 0.72rem; font-weight: 600;
    }
    .hotspot-badge.high { background: var(--red-dim); color: var(--red); }
    .hotspot-badge.medium { background: var(--amber-dim); color: var(--amber); }
    .hotspot-badge.low { background: var(--blue-dim); color: var(--blue); }

    /* ── Analytics: Incident Card ── */
    .incident-card {
        background: var(--bg-1);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 18px 22px;
        margin-bottom: 14px;
        border-left: 4px solid var(--red);
    }
    .incident-card .ic-type {
        font-size: 0.9rem; font-weight: 700; color: var(--red); margin-bottom: 4px;
    }
    .incident-card .ic-desc {
        font-size: 0.82rem; color: var(--text-1); margin-bottom: 10px;
    }

    /* ── Analytics: Pattern Alert ── */
    .pattern-alert {
        padding: 10px 14px;
        border-radius: var(--radius);
        font-size: 0.82rem;
        margin-bottom: 8px;
        font-weight: 500;
        background: var(--amber-dim);
        border: 1px solid rgba(245,158,11,0.2);
        color: #fcd34d;
    }
    .pattern-alert.info {
        background: var(--blue-dim);
        border-color: rgba(59,130,246,0.2);
        color: #93c5fd;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
if "shipments" not in st.session_state:
    st.session_state.shipments = generate_shipments(15)
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = _now()
if "selected_shipment_id" not in st.session_state:
    st.session_state.selected_shipment_id = None
if "company_data" not in st.session_state:
    st.session_state.company_data = None
if "analytics_data" not in st.session_state:
    st.session_state.analytics_data = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "Macro"
if "cost_params" not in st.session_state:
    st.session_state.cost_params = dict(DEFAULT_COST_PARAMS)
if "dashboard_focus" not in st.session_state:
    st.session_state.dashboard_focus = "Overview"

if (_now() - st.session_state.last_refresh).seconds > 3600:
    st.session_state.shipments = generate_shipments(15)
    st.session_state.company_data = None
    st.session_state.analytics_data = None
    st.session_state.last_refresh = _now()

shipments = st.session_state.shipments
summary = get_shipment_summary(shipments)

# Generate company data (once per refresh)
if st.session_state.company_data is None:
    st.session_state.company_data = generate_company_data(shipments)
company_data = st.session_state.company_data

if st.session_state.analytics_data is None:
    st.session_state.analytics_data = generate_analytics_data(shipments, company_data)
analytics_data = st.session_state.analytics_data


# ══════════════════════════════════════════════════════════════════
# REUSABLE RENDERING HELPERS
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


def render_alert_strip(ship_list):
    """Render delay/action alert strip for a list of shipments."""
    delayed_ships = [s for s in ship_list if s["time_status"] == "Delayed"]
    needs_act = [s for s in ship_list if s["recommendation"]["recovery_action"]]
    if delayed_ships:
        ids = ", ".join(s["id"] for s in delayed_ships[:5])
        more = f" +{len(delayed_ships)-5} more" if len(delayed_ships) > 5 else ""
        st.markdown(f"""
        <div class="alert-strip critical">
            <span class="alert-icon">&#9888;</span>
            <span><strong>{len(delayed_ships)} shipment(s)</strong> projected to miss deadline &mdash; {ids}{more}</span>
        </div>
        """, unsafe_allow_html=True)
    elif needs_act:
        st.markdown(f"""
        <div class="alert-strip warn">
            <span class="alert-icon">&#9888;</span>
            <span><strong>{len(needs_act)} shipment(s)</strong> require monitoring or intervention</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alert-strip ok">
            <span class="alert-icon">&#10003;</span>
            <span>All shipments operating within schedule</span>
        </div>
        """, unsafe_allow_html=True)


def render_shipment_detail(ship_list, key_prefix):
    """Render shipment detail panel with selectbox."""
    if not ship_list:
        return
    st.markdown('<div class="sec-title">Shipment Detail</div>', unsafe_allow_html=True)
    shipment_options = {
        s["id"]: f'{s["id"]}  |  {s["vessel"]}  |  {s["port"].split("(")[0].strip()} -> {s["destination"]}  |  {s["time_status"]}'
        for s in ship_list
    }
    selected_id = st.selectbox(
        "Select shipment",
        options=list(shipment_options.keys()),
        format_func=lambda x: shipment_options[x],
        key=f"{key_prefix}_shipment_selector",
    )
    if key_prefix == "macro":
        st.session_state.selected_shipment_id = selected_id

    ship = next(s for s in ship_list if s["id"] == selected_id)
    rec = ship["recommendation"]
    route = ship["route"]
    drive_h = int(route["duration_hrs"])
    drive_m = int((route["duration_hrs"] % 1) * 60)
    buf = rec["buffer_hrs"]

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


def render_shipments_table(ship_list, key_prefix, extra_cols=None):
    """Render styled DataFrame of shipments."""
    st.markdown('<div class="sec-title">All Shipments</div>', unsafe_allow_html=True)
    rows = []
    for s in ship_list:
        rec = s["recommendation"]
        row = {
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
        }
        if extra_cols:
            row.update(extra_cols.get(s["id"], {}))
        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        styled = (
            df.style
            .map(_style_delivery, subset=["Delivery"])
            .map(_style_priority, subset=["Priority"])
            .map(_style_truck, subset=["Truck"])
            .map(_style_verdict, subset=["Verdict"])
        )
        st.dataframe(styled, use_container_width=True, hide_index=True, height=480, key=f"{key_prefix}_table")
    else:
        st.markdown(
            '<div class="panel" style="text-align:center;color:var(--text-2);padding:40px;">No shipments match the current filters.</div>',
            unsafe_allow_html=True,
        )


def render_map(ship_list, all_shipments, height=540, selected_id=None, map_key="map"):
    """Render a Folium map for the given shipments."""
    m = create_base_map()
    port_summary = get_port_summary(all_shipments)
    add_port_markers(m, PORTS, port_summary=port_summary)
    add_city_markers(m, ALL_DESTINATIONS)

    route_colors = COLORS["route_colors"]
    add_all_routes(m, ship_list, route_colors, selected_id=selected_id)
    add_vessel_markers(m, ship_list)
    add_shipment_trucks(m, ship_list)

    all_wps = []
    for s in ship_list:
        all_wps.extend(s["route"]["waypoints"])
    if all_wps:
        fit_map_bounds(m, all_wps)

    st_folium(m, use_container_width=True, height=height, returned_objects=[], key=map_key)


# ══════════════════════════════════════════════════════════════════
# TOP BAR (with logo)
# ══════════════════════════════════════════════════════════════════
import base64, pathlib
_logo_b64 = base64.b64encode(pathlib.Path("assets/logo.png").read_bytes()).decode()
refresh_str = st.session_state.last_refresh.strftime("%b %d, %Y  %H:%M")
st.markdown(f"""
<div class="top-bar">
    <div style="display:flex;align-items:center;gap:18px;">
        <img src="data:image/png;base64,{_logo_b64}" style="height:30px;">
        <div>
            <div class="top-bar-title">Logistics Optimizer</div>
            <div class="top-bar-sub">Automated Delivery Intelligence</div>
        </div>
    </div>
    <div class="top-bar-right">
        <div><span class="live-dot"></span><span class="live-label">Live</span></div>
        <div class="top-bar-time">{refresh_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    # View selector
    view_mode = st.radio(
        "View",
        ["Macro", "Micro"],
        index=0 if st.session_state.view_mode == "Macro" else 1,
        horizontal=True,
        key="view_mode_radio",
    )
    st.session_state.view_mode = view_mode

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Macro Filters ──
    filter_ports = []
    filter_country = []
    filter_city = []
    filter_status = []
    filter_priority = []
    filter_delivery = []
    micro_sb_company = None
    micro_sb_country = []
    micro_sb_city = []
    micro_sb_status = []
    micro_sb_priority = []
    micro_sb_delivery = []

    if view_mode == "Macro":
        st.markdown("""
        <div style="padding:4px 0 12px 0;">
            <div style="font-size:0.92rem;font-weight:700;color:var(--text-0);margin-bottom:2px;">Filters</div>
            <div style="font-size:0.72rem;color:var(--text-2);">Narrow down shipment data</div>
        </div>
        """, unsafe_allow_html=True)

        filter_ports = st.multiselect("Port", list(PORTS.keys()), default=[], key="macro_port")
        filter_country = st.multiselect("Destination Country", DEST_COUNTRIES, default=[], key="macro_country")
        # City options filtered by selected countries
        if filter_country:
            _macro_city_opts = sorted(c for c, co in DEST_COUNTRY_MAP.items() if co in filter_country)
        else:
            _macro_city_opts = sorted(ALL_DESTINATIONS.keys())
        filter_city = st.multiselect("Destination City", _macro_city_opts, default=[], key="macro_city")
        filter_status = st.multiselect("Status", ["Vessel En Route", "At Port", "In Transit", "Delivered"], default=[], key="macro_status")
        filter_priority = st.multiselect("Priority", ["Critical", "High", "Standard"], default=[], key="macro_priority")
        filter_delivery = st.multiselect("Delivery Status", ["On Time", "At Risk", "Delayed"], default=[], key="macro_delivery")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.session_state.dashboard_focus = st.radio(
            "Dashboard Focus",
            ["Overview", "Delays & Risk", "Fleet & Drivers", "Performance"],
            index=["Overview", "Delays & Risk", "Fleet & Drivers", "Performance"].index(st.session_state.dashboard_focus),
            key="macro_dashboard_focus",
        )

        with st.expander("Optimization Parameters"):
            st.session_state.cost_params["fuel_cost_per_km"] = st.slider(
                "Fuel Cost (SAR/km)", 0.20, 1.00, st.session_state.cost_params["fuel_cost_per_km"], 0.05, key="macro_fuel")
            st.session_state.cost_params["driver_cost_per_hr"] = st.slider(
                "Driver Cost (SAR/hr)", 15.0, 80.0, st.session_state.cost_params["driver_cost_per_hr"], 5.0, key="macro_driver_cost")
            st.session_state.cost_params["maintenance_per_km"] = st.slider(
                "Maintenance (SAR/km)", 0.02, 0.20, st.session_state.cost_params["maintenance_per_km"], 0.01, key="macro_maint")
            st.session_state.cost_params["toll_flat_rate"] = st.slider(
                "Toll Rate (SAR)", 0.0, 150.0, st.session_state.cost_params["toll_flat_rate"], 10.0, key="macro_toll")
            st.session_state.cost_params["cooled_surcharge_per_km"] = st.slider(
                "Cooled Surcharge (SAR/km)", 0.05, 0.50, st.session_state.cost_params["cooled_surcharge_per_km"], 0.05, key="macro_cooled")

    else:
        # ── Micro Filters ──
        st.markdown("""
        <div style="padding:4px 0 12px 0;">
            <div style="font-size:0.92rem;font-weight:700;color:var(--text-0);margin-bottom:2px;">Company Filters</div>
            <div style="font-size:0.72rem;color:var(--text-2);">Filter by company & shipment data</div>
        </div>
        """, unsafe_allow_html=True)

        company_names_sb = {c["id"]: c["name"] for c in company_data["companies"]}
        company_ids_sb = list(company_names_sb.keys())
        micro_sb_company = st.selectbox(
            "Company",
            options=company_ids_sb,
            format_func=lambda x: company_names_sb[x],
            key="micro_sb_company",
        )
        micro_sb_country = st.multiselect("Destination Country", DEST_COUNTRIES, default=[], key="micro_sb_country")
        if micro_sb_country:
            _micro_city_opts = sorted(c for c, co in DEST_COUNTRY_MAP.items() if co in micro_sb_country)
        else:
            _micro_city_opts = sorted(ALL_DESTINATIONS.keys())
        micro_sb_city = st.multiselect("Destination City", _micro_city_opts, default=[], key="micro_sb_city")
        micro_sb_status = st.multiselect("Status", ["Vessel En Route", "At Port", "In Transit", "Delivered"], default=[], key="micro_sb_status")
        micro_sb_priority = st.multiselect("Priority", ["Critical", "High", "Standard"], default=[], key="micro_sb_priority")
        micro_sb_delivery = st.multiselect("Delivery Status", ["On Time", "At Risk", "Delayed"], default=[], key="micro_sb_delivery")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.session_state.dashboard_focus = st.radio(
            "Dashboard Focus",
            ["Overview", "Delays & Risk", "Fleet & Drivers", "Performance"],
            index=["Overview", "Delays & Risk", "Fleet & Drivers", "Performance"].index(st.session_state.dashboard_focus),
            key="micro_dashboard_focus",
        )

        with st.expander("Optimization Parameters"):
            st.session_state.cost_params["fuel_cost_per_km"] = st.slider(
                "Fuel Cost (SAR/km)", 0.20, 1.00, st.session_state.cost_params["fuel_cost_per_km"], 0.05, key="micro_fuel")
            st.session_state.cost_params["driver_cost_per_hr"] = st.slider(
                "Driver Cost (SAR/hr)", 15.0, 80.0, st.session_state.cost_params["driver_cost_per_hr"], 5.0, key="micro_driver_cost")
            st.session_state.cost_params["maintenance_per_km"] = st.slider(
                "Maintenance (SAR/km)", 0.02, 0.20, st.session_state.cost_params["maintenance_per_km"], 0.01, key="micro_maint")
            st.session_state.cost_params["toll_flat_rate"] = st.slider(
                "Toll Rate (SAR)", 0.0, 150.0, st.session_state.cost_params["toll_flat_rate"], 10.0, key="micro_toll")
            st.session_state.cost_params["cooled_surcharge_per_km"] = st.slider(
                "Cooled Surcharge (SAR/km)", 0.05, 0.50, st.session_state.cost_params["cooled_surcharge_per_km"], 0.05, key="micro_cooled")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.72rem;color:var(--text-2);padding:4px 0;">Last refresh &mdash; {st.session_state.last_refresh.strftime("%H:%M:%S")}</div>',
        unsafe_allow_html=True,
    )
    if st.button("Refresh Data", type="primary", use_container_width=True):
        st.session_state.shipments = generate_shipments(15)
        st.session_state.company_data = None
        st.session_state.analytics_data = None
        st.session_state.last_refresh = _now()
        st.rerun()
    st.markdown(
        '<div style="font-size:0.68rem;color:var(--text-2);margin-top:6px;">Data auto-refreshes every hour.</div>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════
# APPLY FILTERS (for Macro)
# ══════════════════════════════════════════════════════════════════
filtered = shipments
if filter_ports:
    filtered = [s for s in filtered if s["port"] in filter_ports]
if filter_country:
    filtered = [s for s in filtered if DEST_COUNTRY_MAP.get(s["destination"]) in filter_country]
if filter_city:
    filtered = [s for s in filtered if s["destination"] in filter_city]
if filter_status:
    filtered = [s for s in filtered if s["status"] in filter_status]
if filter_priority:
    filtered = [s for s in filtered if s["priority"] in filter_priority]
if filter_delivery:
    filtered = [s for s in filtered if s["time_status"] in filter_delivery]

f_summary = get_shipment_summary(filtered)

# ══════════════════════════════════════════════════════════════════
# VIEW: MACRO or MICRO (controlled by sidebar)
# ══════════════════════════════════════════════════════════════════
if view_mode == "Macro":
    # Dynamic KPI Rendering based on Dashboard Focus
    pct_on_time = round(f_summary["on_time"] / f_summary["total"] * 100) if f_summary["total"] else 0
    _focus = st.session_state.dashboard_focus

    if _focus == "Delays & Risk":
        _critical_count = sum(1 for s in filtered if s["priority"] == "Critical" and s["time_status"] == "Delayed")
        _recovery_count = sum(1 for s in filtered if s["recommendation"]["recovery_action"])
        _delayed_hrs = [s["recommendation"]["buffer_hrs"] for s in filtered if s["time_status"] == "Delayed"]
        _avg_delay = round(abs(sum(_delayed_hrs) / len(_delayed_hrs)), 1) if _delayed_hrs else 0
        st.markdown(f"""
        <div class="kpi-grid">
            {kpi_html("Delayed", f_summary["delayed"], "var(--red)", "&#10006;")}
            {kpi_html("At Risk", f_summary["at_risk"], "var(--amber)", "&#9888;")}
            {kpi_html("Avg Delay", f'{_avg_delay}h', "var(--red)", "&#9201;")}
            {kpi_html("Critical", _critical_count, "var(--red)", "&#9888;", "Delayed + Critical priority")}
            {kpi_html("Recovery Needed", _recovery_count, "var(--amber)", "&#9881;", "Shipments needing action")}
        </div>
        """, unsafe_allow_html=True)
    elif _focus == "Fleet & Drivers":
        st.markdown(f"""
        <div class="kpi-grid">
            {kpi_html("Cooled Fleet", f_summary["cooled"], "var(--blue)", "&#10052;")}
            {kpi_html("Regular Fleet", f_summary["regular"], "var(--accent)", "&#9951;")}
            {kpi_html("In Transit", f_summary["in_transit"], "var(--accent)", "&#10132;")}
            {kpi_html("At Port", f_summary["at_port"], "var(--blue)", "&#9875;")}
            {kpi_html("Vessels Inbound", f_summary["vessel_enroute"], "var(--text-1)", "&#9973;")}
        </div>
        """, unsafe_allow_html=True)
    elif _focus == "Performance":
        _avg_dist = round(sum(s["route"]["distance_km"] for s in filtered) / len(filtered)) if filtered else 0
        _avg_drive = round(sum(s["route"]["duration_hrs"] for s in filtered) / len(filtered), 1) if filtered else 0
        st.markdown(f"""
        <div class="kpi-grid">
            {kpi_html("On-Time %", f'{pct_on_time}%', "var(--green)", "&#10003;")}
            {kpi_html("Avg Buffer", f'{f_summary["avg_buffer_hrs"]}h', "var(--amber)" if f_summary["avg_buffer_hrs"] < 4 else "var(--green)", "&#9201;")}
            {kpi_html("Delivered", f_summary["delivered"], "var(--green)", "&#10003;")}
            {kpi_html("Avg Distance", f'{_avg_dist} km', "var(--accent)", "&#10132;")}
            {kpi_html("Avg Drive Time", f'{_avg_drive}h', "var(--accent)", "&#9201;")}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Overview (default) — original 10-card layout
        st.markdown(f"""
        <div class="kpi-grid">
            {kpi_html("Total Shipments", f_summary["total"], "var(--text-0)", "&#9776;", f'{f_summary["delivered"]} delivered')}
            {kpi_html("In Transit", f_summary["in_transit"], "var(--accent)", "&#10132;", f'{f_summary["vessel_enroute"]} vessels inbound')}
            {kpi_html("At Port", f_summary["at_port"], "var(--blue)", "&#9875;", f'{f_summary["cooled"]} cooled &bull; {f_summary["regular"]} regular')}
            {kpi_html("On Time", f"{pct_on_time}%", "var(--green)", "&#10003;", f'{f_summary["on_time"]} of {f_summary["total"]} shipments')}
            {kpi_html("Avg Buffer", f'{f_summary["avg_buffer_hrs"]}h', "var(--amber)" if f_summary["avg_buffer_hrs"] < 4 else "var(--green)", "&#9201;", f'{f_summary["needs_action"]} need action')}
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="kpi-grid">
            {kpi_html("At Risk", f_summary["at_risk"], "var(--amber)", "&#9888;")}
            {kpi_html("Delayed", f_summary["delayed"], "var(--red)", "&#10006;")}
            {kpi_html("Cooled Fleet", f_summary["cooled"], "var(--blue)", "&#10052;")}
            {kpi_html("Regular Fleet", f_summary["regular"], "var(--accent)", "&#9951;")}
            {kpi_html("Vessels Inbound", f_summary["vessel_enroute"], "var(--text-1)", "&#9973;")}
        </div>
        """, unsafe_allow_html=True)

    # Critical warnings
    critical_delayed = [s for s in filtered if s["priority"] == "Critical" and s["time_status"] == "Delayed"]
    needs_action = [s for s in filtered if s["recommendation"]["recovery_action"]]

    if critical_delayed:
        details = "".join(
            f'<div class="sb-detail">{s["id"]} &mdash; {s["port"].split("(")[0].strip()} &rarr; {s["destination"]}</div>'
            for s in critical_delayed
        )
        st.markdown(
            f'<div class="alert-strip critical"><span class="alert-icon">&#9888;</span>'
            f'<span><strong>{len(critical_delayed)} critical shipment(s) delayed</strong>{details}</span></div>',
            unsafe_allow_html=True,
        )

    if needs_action:
        st.markdown(
            f'<div class="alert-strip warn"><span class="alert-icon">&#9888;</span>'
            f'<span><strong>{len(needs_action)} shipment(s)</strong> require attention</span></div>',
            unsafe_allow_html=True,
        )

    if not critical_delayed and not needs_action:
        st.markdown(
            '<div class="alert-strip ok"><span class="alert-icon">&#10003;</span>'
            '<span>No critical delays &mdash; all shipments operating normally</span></div>',
            unsafe_allow_html=True,
        )

    # Alert strip
    render_alert_strip(filtered)

    # Live Map
    st.markdown('<div class="sec-title">Live Operations Map</div>', unsafe_allow_html=True)
    render_map(filtered, shipments, height=540, selected_id=st.session_state.selected_shipment_id, map_key="macro_map")

    # Port Operations Table
    st.markdown('<div class="sec-title">Port Operations</div>', unsafe_allow_html=True)
    port_summary = get_port_summary(shipments)
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

    # Shipment Detail
    render_shipment_detail(filtered, "macro")

    # All Shipments Table
    render_shipments_table(filtered, "macro")


# ══════════════════════════════════════════════════════════════════
# MICRO VIEW — Company Dashboard
# ══════════════════════════════════════════════════════════════════
else:
    selected_company_id = micro_sb_company
    sel_company = next(c for c in company_data["companies"] if c["id"] == selected_company_id)
    comp_shipments = [s for s in shipments if s.get("company_id") == selected_company_id]
    comp_drivers = company_data["drivers"].get(selected_company_id, [])
    comp_trucks = company_data["trucks"].get(selected_company_id, [])

    # Apply sidebar micro filters to company shipments
    micro_filtered = comp_shipments
    if micro_sb_country:
        micro_filtered = [s for s in micro_filtered if DEST_COUNTRY_MAP.get(s["destination"]) in micro_sb_country]
    if micro_sb_city:
        micro_filtered = [s for s in micro_filtered if s["destination"] in micro_sb_city]
    if micro_sb_status:
        micro_filtered = [s for s in micro_filtered if s["status"] in micro_sb_status]
    if micro_sb_priority:
        micro_filtered = [s for s in micro_filtered if s["priority"] in micro_sb_priority]
    if micro_sb_delivery:
        micro_filtered = [s for s in micro_filtered if s["time_status"] in micro_sb_delivery]

    # Compute summary from filtered shipments
    mf_summary = get_shipment_summary(micro_filtered)

    # Company Header
    st.markdown(f"""
    <div class="company-header">
        <div>
            <div class="ch-name">{sel_company["name"]}</div>
            <div class="ch-detail">HQ: {sel_company["hq_city"]} &bull; {sel_company["specialization"]}</div>
        </div>
        <div>
            <span class="pill pill-purple">{sel_company["id"]}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Company warnings
    micro_critical = [s for s in micro_filtered if s["priority"] == "Critical" and s["time_status"] == "Delayed"]
    micro_needs_action = [s for s in micro_filtered if s["recommendation"]["recovery_action"]]

    if micro_critical:
        details = "".join(
            f'<div class="sb-detail">{s["id"]} &mdash; {s["port"].split("(")[0].strip()} &rarr; {s["destination"]}</div>'
            for s in micro_critical
        )
        st.markdown(
            f'<div class="alert-strip critical"><span class="alert-icon">&#9888;</span>'
            f'<span><strong>{len(micro_critical)} critical shipment(s) delayed</strong>{details}</span></div>',
            unsafe_allow_html=True,
        )

    if micro_needs_action:
        st.markdown(
            f'<div class="alert-strip warn"><span class="alert-icon">&#9888;</span>'
            f'<span><strong>{len(micro_needs_action)} shipment(s)</strong> require attention</span></div>',
            unsafe_allow_html=True,
        )

    if not micro_critical and not micro_needs_action:
        st.markdown(
            '<div class="alert-strip ok"><span class="alert-icon">&#10003;</span>'
            '<span>No critical delays &mdash; all shipments operating normally</span></div>',
            unsafe_allow_html=True,
        )

    # Sub-tabs
    overview_tab, drivers_tab, shipments_tab, analytics_tab = st.tabs(["Overview", "Drivers", "Shipments", "Delays Deep-Dive"])

    # ── Overview Sub-Tab ──
    with overview_tab:
        # Dynamic KPIs based on Dashboard Focus
        mf_on_time_pct = round(mf_summary["on_time"] / mf_summary["total"] * 100) if mf_summary["total"] else 0
        active_drv = sum(1 for d in comp_drivers if d["status"] == "active")
        idle_drv = sum(1 for d in comp_drivers if d["status"] == "idle")
        fleet_in_use = sum(1 for t in comp_trucks if t["status"] == "in_use")
        fleet_util = round(fleet_in_use / len(comp_trucks) * 100) if comp_trucks else 0
        _focus = st.session_state.dashboard_focus

        if _focus == "Delays & Risk":
            _micro_critical_cnt = sum(1 for s in micro_filtered if s["priority"] == "Critical" and s["time_status"] == "Delayed")
            _micro_recovery = sum(1 for s in micro_filtered if s["recommendation"]["recovery_action"])
            _micro_del_hrs = [s["recommendation"]["buffer_hrs"] for s in micro_filtered if s["time_status"] == "Delayed"]
            _micro_avg_delay = round(abs(sum(_micro_del_hrs) / len(_micro_del_hrs)), 1) if _micro_del_hrs else 0
            st.markdown(f"""
            <div class="kpi-grid">
                {kpi_html("Delayed", mf_summary["delayed"], "var(--red)", "&#10006;")}
                {kpi_html("At Risk", mf_summary["at_risk"], "var(--amber)", "&#9888;")}
                {kpi_html("Avg Delay", f'{_micro_avg_delay}h', "var(--red)", "&#9201;")}
                {kpi_html("Critical", _micro_critical_cnt, "var(--red)", "&#9888;")}
                {kpi_html("Recovery Needed", _micro_recovery, "var(--amber)", "&#9881;")}
            </div>
            """, unsafe_allow_html=True)
        elif _focus == "Fleet & Drivers":
            _cooled_pct = round(mf_summary["cooled"] / mf_summary["total"] * 100) if mf_summary["total"] else 0
            _maint_trucks = sum(1 for t in comp_trucks if t["status"] == "maintenance")
            st.markdown(f"""
            <div class="kpi-grid">
                {kpi_html("Active Drivers", active_drv, "var(--green)", "&#9823;")}
                {kpi_html("Idle Drivers", idle_drv, "var(--amber)", "&#9202;")}
                {kpi_html("Fleet Utilization", f'{fleet_util}%', "var(--accent)", "&#9951;")}
                {kpi_html("Cooled Fleet %", f'{_cooled_pct}%', "var(--blue)", "&#10052;")}
                {kpi_html("In Maintenance", _maint_trucks, "var(--text-2)", "&#9881;")}
            </div>
            """, unsafe_allow_html=True)
        elif _focus == "Performance":
            _m_avg_dist = round(sum(s["route"]["distance_km"] for s in micro_filtered) / len(micro_filtered)) if micro_filtered else 0
            _m_avg_drive = round(sum(s["route"]["duration_hrs"] for s in micro_filtered) / len(micro_filtered), 1) if micro_filtered else 0
            st.markdown(f"""
            <div class="kpi-grid">
                {kpi_html("On-Time %", f'{mf_on_time_pct}%', "var(--green)", "&#10003;")}
                {kpi_html("Avg Buffer", f'{mf_summary["avg_buffer_hrs"]}h', "var(--amber)" if mf_summary["avg_buffer_hrs"] < 4 else "var(--green)", "&#9201;")}
                {kpi_html("Delivered", mf_summary["delivered"], "var(--green)", "&#10003;")}
                {kpi_html("Avg Distance", f'{_m_avg_dist} km', "var(--accent)", "&#10132;")}
                {kpi_html("Avg Drive Time", f'{_m_avg_drive}h', "var(--accent)", "&#9201;")}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Overview (default)
            st.markdown(f"""
            <div class="kpi-grid">
                {kpi_html("Total Shipments", mf_summary["total"], "var(--text-0)", "&#9776;", f'{mf_summary["delivered"]} delivered')}
                {kpi_html("Active Drivers", active_drv, "var(--green)", "&#9823;")}
                {kpi_html("Fleet Utilization", f'{fleet_util}%', "var(--accent)", "&#9951;")}
                {kpi_html("On-Time Rate", f'{mf_on_time_pct}%', "var(--green)", "&#10003;")}
                {kpi_html("Avg Buffer", f'{mf_summary["avg_buffer_hrs"]}h', "var(--amber)" if mf_summary["avg_buffer_hrs"] < 4 else "var(--green)", "&#9201;")}
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="kpi-grid">
                {kpi_html("Cooled Fleet", mf_summary["cooled"], "var(--blue)", "&#10052;")}
                {kpi_html("Regular Fleet", mf_summary["regular"], "var(--accent)", "&#9951;")}
                {kpi_html("In Transit", mf_summary["in_transit"], "var(--accent)", "&#10132;")}
                {kpi_html("At Port", mf_summary["at_port"], "var(--blue)", "&#9875;")}
                {kpi_html("Delivered", mf_summary["delivered"], "var(--green)", "&#10003;")}
            </div>
            """, unsafe_allow_html=True)

        # Company Map — always show, use filtered shipments for routes if any
        st.markdown('<div class="sec-title">Company Routes</div>', unsafe_allow_html=True)
        map_shipments = micro_filtered if micro_filtered else comp_shipments
        render_map(map_shipments, shipments, height=400, map_key="micro_overview_map")

        # Fleet Summary Table
        st.markdown('<div class="sec-title">Fleet Summary</div>', unsafe_allow_html=True)
        fleet_rows = []
        for t in comp_trucks:
            driver_name = ""
            if t["assigned_driver_id"]:
                drv = next((d for d in comp_drivers if d["id"] == t["assigned_driver_id"]), None)
                if drv:
                    driver_name = drv["name"]
            fleet_rows.append({
                "Truck ID": t["id"],
                "Plate": t["plate"],
                "Type": t["type"],
                "Model": t["model"],
                "Year": t["year"],
                "Status": t["status"].replace("_", " ").title(),
                "Driver": driver_name or "-",
                "Mileage": f'{t["mileage_km"]:,} km',
            })
        fleet_df = pd.DataFrame(fleet_rows)
        if not fleet_df.empty:
            st.dataframe(fleet_df, use_container_width=True, hide_index=True, key="micro_fleet_table")

    # ── Drivers Sub-Tab ──
    with drivers_tab:
        # Driver Status KPIs
        drv_active = sum(1 for d in comp_drivers if d["status"] == "active")
        drv_idle = sum(1 for d in comp_drivers if d["status"] == "idle")
        drv_off = sum(1 for d in comp_drivers if d["status"] == "off_duty")
        st.markdown(f"""
        <div class="kpi-grid" style="grid-template-columns: repeat(3, 1fr);">
            {kpi_html("Active", drv_active, "var(--green)", "&#9823;", "Currently driving")}
            {kpi_html("Idle", drv_idle, "var(--amber)", "&#9202;", "Awaiting assignment")}
            {kpi_html("Off Duty", drv_off, "var(--text-2)", "&#9790;", "Not on shift")}
        </div>
        """, unsafe_allow_html=True)

        # Drivers Table
        st.markdown('<div class="sec-title">Driver Roster</div>', unsafe_allow_html=True)
        drv_rows = []
        for d in comp_drivers:
            status_pill_cls = {"active": "pill-green", "idle": "pill-amber", "off_duty": "pill-purple"}.get(d["status"], "pill-purple")
            assignment = "-"
            truck_id = d.get("assigned_truck_id", "") or "-"
            if d["assigned_shipment_id"]:
                ship_match = next((s for s in comp_shipments if s["id"] == d["assigned_shipment_id"]), None)
                if ship_match:
                    assignment = f'{ship_match["id"]} ({ship_match["destination"]})'

            drv_rows.append({
                "Name": d["name"],
                "Status": d["status"].replace("_", " ").title(),
                "Assignment": assignment,
                "Truck": truck_id,
                "Deliveries": d["stats"]["total_deliveries"],
                "On-Time %": f'{d["stats"]["on_time_pct"]}%',
                "Rating": f'{d["stats"]["avg_rating"]}/5.0',
                "KM/Month": f'{d["stats"]["km_per_month"]:,}',
            })
        drv_df = pd.DataFrame(drv_rows)
        if not drv_df.empty:
            def _style_driver_status(val):
                if val == "Active":
                    return "color: #86efac; background: rgba(34,197,94,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"
                if val == "Idle":
                    return "color: #fcd34d; background: rgba(245,158,11,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"
                return "color: #c4b5fd; background: rgba(139,92,246,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"

            styled_drv = drv_df.style.map(_style_driver_status, subset=["Status"])
            st.dataframe(styled_drv, use_container_width=True, hide_index=True, key="micro_drivers_table")

        # Driver Detail Panel
        st.markdown('<div class="sec-title">Driver Detail</div>', unsafe_allow_html=True)
        driver_options = {d["id"]: d["name"] for d in comp_drivers}
        selected_driver_id = st.selectbox(
            "Select driver",
            options=list(driver_options.keys()),
            format_func=lambda x: driver_options[x],
            key="drv_selector",
        )
        sel_driver = next(d for d in comp_drivers if d["id"] == selected_driver_id)
        drv_status_pill = {"active": "pill-green", "idle": "pill-amber", "off_duty": "pill-purple"}.get(sel_driver["status"], "pill-purple")

        # Driver info card
        shipment_info = ""
        if sel_driver["assigned_shipment_id"]:
            ship_match = next((s for s in comp_shipments if s["id"] == sel_driver["assigned_shipment_id"]), None)
            if ship_match:
                _ts = ship_match["time_status"]
                _ts_pill = "pill-green" if _ts == "On Time" else ("pill-amber" if _ts == "At Risk" else "pill-red")
                _port_short = ship_match["port"].split("(")[0].strip()
                shipment_info = (
                    '<div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border);">'
                    '<div style="font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-2);margin-bottom:8px;">Current Assignment</div>'
                    f'<div style="font-size:0.85rem;color:var(--text-0);">'
                    f'<b>{ship_match["id"]}</b> &mdash; {_port_short} &rarr; {ship_match["destination"]}'
                    f' <span class="pill {_ts_pill}" style="margin-left:8px;">{_ts}</span>'
                    '</div></div>'
                )

        st.markdown(f"""
        <div class="driver-card">
            <div class="drv-name">{sel_driver["name"]} <span class="pill {drv_status_pill}" style="margin-left:8px;">{sel_driver["status"].replace("_"," ").title()}</span></div>
            <div class="drv-info">{sel_driver["phone"]} &bull; License: {sel_driver["license_type"]} &bull; Location: {sel_driver["current_city"]}</div>
            <div class="detail-grid" style="grid-template-columns: repeat(4, 1fr);">
                <div class="detail-card">
                    <div class="dc-label">Deliveries</div>
                    <div class="dc-value">{sel_driver["stats"]["total_deliveries"]}</div>
                </div>
                <div class="detail-card">
                    <div class="dc-label">On-Time</div>
                    <div class="dc-value">{sel_driver["stats"]["on_time_pct"]}%</div>
                </div>
                <div class="detail-card">
                    <div class="dc-label">Rating</div>
                    <div class="dc-value">{sel_driver["stats"]["avg_rating"]}/5</div>
                </div>
                <div class="detail-card">
                    <div class="dc-label">KM/Month</div>
                    <div class="dc-value">{sel_driver["stats"]["km_per_month"]:,}</div>
                </div>
            </div>
            {shipment_info}
        </div>
        """, unsafe_allow_html=True)

        # Driver route map — full route if assigned, or simple location pin
        if sel_driver["assigned_shipment_id"]:
            _drv_ship = next((s for s in comp_shipments if s["id"] == sel_driver["assigned_shipment_id"]), None)
        else:
            _drv_ship = None

        if _drv_ship and _drv_ship["route"]["waypoints"]:
            _drv_hotspots = analytics_data["location_hotspots"].get(selected_company_id, [])
            drv_map = create_driver_route_map(sel_driver, _drv_ship, hotspots=_drv_hotspots)
            st_folium(drv_map, use_container_width=True, height=350, returned_objects=[], key="drv_location_map")
        else:
            drv_lat, drv_lon = sel_driver["current_location"]
            drv_map = folium.Map(
                location=[drv_lat, drv_lon],
                zoom_start=8,
                tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                attr="Google",
            )
            folium.Marker(
                location=[drv_lat, drv_lon],
                popup=f'{sel_driver["name"]} - {sel_driver["current_city"]}',
                tooltip=sel_driver["name"],
                icon=folium.Icon(color="purple", icon="user", prefix="fa"),
            ).add_to(drv_map)
            st_folium(drv_map, use_container_width=True, height=350, returned_objects=[], key="drv_location_map")

    # ── Shipments Sub-Tab ──
    with shipments_tab:
        # Alert strip
        render_alert_strip(micro_filtered)

        # Shipment Detail
        if micro_filtered:
            # Build driver column mapping
            driver_col = {}
            for s in micro_filtered:
                drv = next((d for d in comp_drivers if d.get("assigned_shipment_id") == s["id"]), None)
                driver_col[s["id"]] = {"Driver": drv["name"] if drv else "-"}

            render_shipment_detail(micro_filtered, "micro")
            render_shipments_table(micro_filtered, "micro", extra_cols=driver_col)
        else:
            st.markdown(
                '<div class="panel" style="text-align:center;color:var(--text-2);padding:40px;">No shipments match the current filters.</div>',
                unsafe_allow_html=True,
            )

    # ── Analytics Sub-Tab ──
    with analytics_tab:
        from collections import Counter

        a_delay_causes = analytics_data["delay_causes"]
        a_driver_history = analytics_data["driver_history"]
        a_hotspots = analytics_data["location_hotspots"].get(selected_company_id, [])
        a_incidents = analytics_data["active_incidents"].get(selected_company_id, [])

        # ════════════════════════════════════════════════════════════
        # Section 0: Delay Overview Map
        # ════════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Delay Overview Map</div>', unsafe_allow_html=True)
        if comp_shipments:
            delay_map = create_base_map()
            add_delay_colored_routes(delay_map, comp_shipments)
            all_delay_wps = []
            for _s in comp_shipments:
                all_delay_wps.extend(_s["route"]["waypoints"])
            if all_delay_wps:
                fit_map_bounds(delay_map, all_delay_wps)
            st.markdown(
                '<div style="display:flex;gap:16px;margin-bottom:8px;">'
                '<span style="font-size:0.75rem;color:#2ECC71;font-weight:600;">&#9679; On Time</span>'
                '<span style="font-size:0.75rem;color:#F39C12;font-weight:600;">&#9679; At Risk</span>'
                '<span style="font-size:0.75rem;color:#E74C3C;font-weight:600;">&#9679; Delayed</span>'
                '</div>', unsafe_allow_html=True,
            )
            st_folium(delay_map, use_container_width=True, height=400, returned_objects=[], key="analytics_delay_map")
        else:
            st.markdown(
                '<div class="panel" style="text-align:center;color:var(--text-2);padding:30px;">'
                'No shipments to display.</div>', unsafe_allow_html=True,
            )

        # ════════════════════════════════════════════════════════════
        # Section 1: Root Cause Analysis
        # ════════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Root Cause Analysis</div>', unsafe_allow_html=True)

        delayed_shipments = [s for s in comp_shipments if s["time_status"] in ("Delayed", "At Risk")]

        if delayed_shipments:
            # Summary bar chart of cause categories
            all_causes_flat = []
            for s in delayed_shipments:
                causes = a_delay_causes.get(s["id"], [])
                all_causes_flat.extend(causes)

            if all_causes_flat:
                cause_counts = Counter(c["cause"] for c in all_causes_flat)
                sorted_causes = cause_counts.most_common()

                # Horizontal bar chart via HTML
                max_count = max(cause_counts.values()) if cause_counts else 1
                bars_html = ""
                bar_colors = {
                    "Port Congestion": "var(--blue)", "Customs Clearance": "var(--accent)",
                    "Driver Break": "var(--amber)", "Road Congestion": "var(--red)",
                    "Weather": "#f59e0b", "Mechanical Issue": "var(--red)",
                    "Checkpoint Delay": "var(--amber)", "Loading Delay": "var(--blue)",
                }
                for cause_name, count in sorted_causes:
                    pct = count / max_count * 100
                    color = bar_colors.get(cause_name, "var(--accent)")
                    bars_html += (
                        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
                        f'<div style="width:140px;font-size:0.78rem;color:var(--text-1);text-align:right;">{cause_name}</div>'
                        f'<div style="flex:1;background:var(--bg-2);border-radius:4px;height:20px;overflow:hidden;">'
                        f'<div style="width:{pct}%;height:100%;background:{color};border-radius:4px;"></div></div>'
                        f'<div style="width:30px;font-size:0.78rem;color:var(--text-0);font-weight:600;">{count}</div>'
                        f'</div>'
                    )
                st.markdown(f'<div class="panel">{bars_html}</div>', unsafe_allow_html=True)

            # Per-shipment cause cards
            for s in delayed_shipments:
                causes = a_delay_causes.get(s["id"], [])
                if not causes:
                    continue

                ts_pill = "pill-red" if s["time_status"] == "Delayed" else "pill-amber"
                port_short = s["port"].split("(")[0].strip()
                total_delay = sum(c["delay_hrs"] for c in causes)

                st.markdown(f"""
                <div class="panel" style="margin-bottom:10px;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                        <span style="font-weight:700;color:var(--text-0);">{s["id"]}</span>
                        <span class="pill {ts_pill}">{s["time_status"]}</span>
                        <span style="font-size:0.78rem;color:var(--text-2);">{port_short} &rarr; {s["destination"]}</span>
                        <span style="margin-left:auto;font-size:0.78rem;color:var(--red);font-weight:600;">Total: +{total_delay:.1f}h</span>
                    </div>
                """, unsafe_allow_html=True)

                for c in causes:
                    severity = "severe" if c["delay_hrs"] >= 3 else ("moderate" if c["delay_hrs"] >= 1.5 else "minor")
                    st.markdown(f"""
                    <div class="cause-card {severity}">
                        <div class="cc-cause">{c["cause"]} <span style="color:var(--red);font-size:0.78rem;">+{c["delay_hrs"]}h</span></div>
                        <div class="cc-desc">{c["description"]}</div>
                        <div class="cc-meta">{c["location"]} &bull; {c["timestamp"].strftime("%H:%M")}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="panel" style="text-align:center;color:var(--green);padding:30px;">'
                '&#10003; All shipments on schedule &mdash; no delay causes to report.</div>',
                unsafe_allow_html=True,
            )

        # ════════════════════════════════════════════════════════════
        # Section 2: Driver Patterns
        # ════════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Driver Patterns</div>', unsafe_allow_html=True)

        analytics_driver_options = {d["id"]: d["name"] for d in comp_drivers}
        analytics_sel_driver_id = st.selectbox(
            "Select driver to analyze",
            options=list(analytics_driver_options.keys()),
            format_func=lambda x: analytics_driver_options[x],
            key="analytics_driver_selector",
        )
        sel_drv = next(d for d in comp_drivers if d["id"] == analytics_sel_driver_id)
        trips = a_driver_history.get(analytics_sel_driver_id, [])

        if trips:
            # Driver summary KPIs
            total_trips = len(trips)
            on_time_trips = sum(1 for t in trips if t["on_time"])
            ot_pct = round(on_time_trips / total_trips * 100, 1) if total_trips else 0
            delayed_trips = [t for t in trips if not t["on_time"]]
            avg_delay = round(sum(t["delay_hrs"] for t in delayed_trips) / len(delayed_trips), 1) if delayed_trips else 0

            # Most common cause
            delay_reasons = [t["delay_reason"] for t in delayed_trips if t["delay_reason"]]
            most_common_cause = Counter(delay_reasons).most_common(1)[0][0] if delay_reasons else "N/A"

            st.markdown(f"""
            <div class="detail-grid" style="grid-template-columns: repeat(4, 1fr);">
                <div class="detail-card">
                    <div class="dc-label">Total Trips</div>
                    <div class="dc-value">{total_trips}</div>
                </div>
                <div class="detail-card">
                    <div class="dc-label">On-Time Rate</div>
                    <div class="dc-value" style="color:{"var(--green)" if ot_pct >= 85 else "var(--red)"};">{ot_pct}%</div>
                </div>
                <div class="detail-card">
                    <div class="dc-label">Avg Delay</div>
                    <div class="dc-value" style="color:var(--amber);">{avg_delay}h</div>
                </div>
                <div class="detail-card">
                    <div class="dc-label">Top Cause</div>
                    <div class="dc-value" style="font-size:0.85rem;">{most_common_cause}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Pattern detection
            if delayed_trips:
                route_delays = Counter(t["route_name"] for t in delayed_trips)
                reason_delays = Counter(t["delay_reason"] for t in delayed_trips if t["delay_reason"])

                # Company avg on-time rate
                all_drv_ot = [d["stats"]["on_time_pct"] for d in comp_drivers]
                company_avg_ot = sum(all_drv_ot) / len(all_drv_ot) if all_drv_ot else 90

                patterns_html = ""
                for route_name, cnt in route_delays.most_common(2):
                    if cnt >= 3:
                        patterns_html += (
                            f'<div class="pattern-alert">'
                            f'&#9888; This driver has <b>{cnt} delays</b> on the <b>{route_name}</b> route'
                            f'</div>'
                        )
                for reason, cnt in reason_delays.most_common(2):
                    if cnt >= 3:
                        pct = round(cnt / len(delayed_trips) * 100)
                        patterns_html += (
                            f'<div class="pattern-alert">'
                            f'&#9888; <b>{reason}</b> accounts for <b>{pct}%</b> of this driver\'s delays ({cnt} occurrences)'
                            f'</div>'
                        )
                if ot_pct < company_avg_ot - 5:
                    diff = round(company_avg_ot - ot_pct, 1)
                    patterns_html += (
                        f'<div class="pattern-alert info">'
                        f'&#8505; Driver performs <b>{diff}%</b> below company average on-time rate ({company_avg_ot:.1f}%)'
                        f'</div>'
                    )
                if patterns_html:
                    st.markdown(patterns_html, unsafe_allow_html=True)

            # Trip history table
            st.markdown(
                '<div style="font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;'
                'color:var(--text-2);margin:14px 0 8px 0;">Trip History (Last 30 Trips)</div>',
                unsafe_allow_html=True,
            )

            trip_rows = []
            for t in trips:
                trip_rows.append({
                    "Date": t["date"].strftime("%b %d"),
                    "Route": t["route_name"],
                    "Cargo": t["cargo"],
                    "Distance": f'{t["distance_km"]} km',
                    "Expected": f'{t["expected_hrs"]}h',
                    "Actual": f'{t["actual_hrs"]}h',
                    "Delay": f'+{t["delay_hrs"]}h' if t["delay_hrs"] > 0 else "-",
                    "Status": "On Time" if t["on_time"] else "Delayed",
                    "Reason": t["delay_reason"] or "-",
                })
            trip_df = pd.DataFrame(trip_rows)

            def _style_trip_status(val):
                if val == "On Time":
                    return "color: #86efac; background: rgba(34,197,94,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"
                if val == "Delayed":
                    return "color: #fca5a5; background: rgba(239,68,68,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"
                return ""

            styled_trips = trip_df.style.map(_style_trip_status, subset=["Status"])
            st.dataframe(styled_trips, use_container_width=True, hide_index=True, height=400, key="analytics_trips_table")
        else:
            st.markdown(
                '<div class="panel" style="text-align:center;color:var(--text-2);padding:30px;">'
                'No trip history available for this driver.</div>',
                unsafe_allow_html=True,
            )

        # ════════════════════════════════════════════════════════════
        # Section 3: Location Hotspots
        # ════════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Location Hotspots</div>', unsafe_allow_html=True)

        if a_hotspots:
            # Hotspot map
            hs_map = create_base_map()
            add_hotspot_markers(hs_map, a_hotspots)
            # Fit to hotspot bounds
            hs_coords = [[h["lat"], h["lon"]] for h in a_hotspots]
            if len(hs_coords) >= 2:
                fit_map_bounds(hs_map, hs_coords)
            elif hs_coords:
                hs_map.location = hs_coords[0]
                hs_map.zoom_start = 7
            st_folium(hs_map, use_container_width=True, height=400, returned_objects=[], key="analytics_hotspot_map")

            # Hotspot table
            hs_rows = []
            for idx, h in enumerate(a_hotspots):
                severity_score = h["avg_delay_hrs"] * h["frequency"]
                if severity_score > 20:
                    badge_cls = "high"
                    badge_label = "High"
                elif severity_score > 10:
                    badge_cls = "medium"
                    badge_label = "Medium"
                else:
                    badge_cls = "low"
                    badge_label = "Low"

                highlight = ' style="background:rgba(239,68,68,0.05);"' if idx < 3 else ""
                hs_rows.append({
                    "Location": h["name"],
                    "Type": h["type"].replace("_", " ").title(),
                    "Avg Delay": f'{h["avg_delay_hrs"]}h',
                    "Frequency": h["frequency"],
                    "Impact": badge_label,
                    "Description": h["description"],
                })
            hs_df = pd.DataFrame(hs_rows)

            def _style_impact(val):
                if val == "High":
                    return "color: #fca5a5; background: rgba(239,68,68,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"
                if val == "Medium":
                    return "color: #fcd34d; background: rgba(245,158,11,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"
                return "color: #93c5fd; background: rgba(59,130,246,0.12); border-radius: 4px; padding: 2px 8px; font-weight: 600;"

            styled_hs = hs_df.style.map(_style_impact, subset=["Impact"])
            st.dataframe(styled_hs, use_container_width=True, hide_index=True, key="analytics_hotspot_table")
        else:
            st.markdown(
                '<div class="panel" style="text-align:center;color:var(--text-2);padding:30px;">'
                'No hotspot data available for this company.</div>',
                unsafe_allow_html=True,
            )

        # ════════════════════════════════════════════════════════════
        # Section 4: Route Optimization (Fastest / Cheapest / Balanced)
        # ════════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Route Optimization</div>', unsafe_allow_html=True)

        if a_incidents:
            route_options = generate_route_options(a_incidents, st.session_state.cost_params)

            for inc_idx, inc in enumerate(a_incidents):
                inc_type_label = inc["incident_type"].replace("_", " ").title()

                st.markdown(f"""
                <div class="incident-card">
                    <div class="ic-type">&#9888; {inc_type_label}</div>
                    <div class="ic-desc">{inc["description"]}</div>
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                        <span class="pill pill-red">{inc["shipment_id"]}</span>
                        <span style="font-size:0.78rem;color:var(--text-2);">
                            Reported at {inc["reported_at"].strftime("%H:%M")}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 3-option route comparison
                opts = route_options[inc_idx]["options"] if inc_idx < len(route_options) else []
                if opts:
                    opt_colors = {"Fastest": "var(--green)", "Cheapest": "var(--blue)", "Balanced": "var(--accent)"}
                    opt_icons = {"Fastest": "&#9889;", "Cheapest": "&#9733;", "Balanced": "&#9878;"}
                    col_f, col_c, col_b = st.columns(3)
                    for col_widget, opt in zip([col_f, col_c, col_b], opts):
                        with col_widget:
                            _oh = int(opt["duration_hrs"])
                            _om = int((opt["duration_hrs"] % 1) * 60)
                            _color = opt_colors.get(opt["name"], "var(--accent)")
                            _icon = opt_icons.get(opt["name"], "")
                            st.markdown(f"""
                            <div class="panel" style="border-left:3px solid {_color};">
                                <div style="font-size:0.82rem;font-weight:700;color:{_color};margin-bottom:8px;">
                                    {_icon} {opt["name"]}
                                </div>
                                <div class="detail-grid" style="grid-template-columns: 1fr 1fr;">
                                    <div class="detail-card">
                                        <div class="dc-label">Distance</div>
                                        <div class="dc-value" style="font-size:0.95rem;">{opt["distance_km"]} km</div>
                                    </div>
                                    <div class="detail-card">
                                        <div class="dc-label">Duration</div>
                                        <div class="dc-value" style="font-size:0.95rem;">{_oh}h {_om}m</div>
                                    </div>
                                </div>
                                <div class="detail-grid" style="grid-template-columns: 1fr 1fr;">
                                    <div class="detail-card">
                                        <div class="dc-label">Total Cost</div>
                                        <div class="dc-value" style="font-size:0.95rem;color:{_color};">{opt["cost"]["total"]:,.0f} SAR</div>
                                    </div>
                                    <div class="detail-card">
                                        <div class="dc-label">Fuel Cost</div>
                                        <div class="dc-value" style="font-size:0.85rem;">{opt["cost"]["fuel"]:,.0f} SAR</div>
                                    </div>
                                </div>
                                <div style="font-size:0.72rem;color:var(--green);margin-top:4px;">&#10003; {opt["pros"]}</div>
                                <div style="font-size:0.72rem;color:var(--amber);margin-top:2px;">&#9888; {opt["cons"]}</div>
                            </div>
                            """, unsafe_allow_html=True)

                # Map — Google Maps style: blue recommended, grey alternatives, red dashed original
                inc_map = create_base_map()
                _route_opts = route_options[inc_idx]["options"] if inc_idx < len(route_options) else []
                add_optimization_routes(inc_map, _route_opts, incident=inc, original_route=inc["original_route"])

                _all_map_pts = list(inc["original_route"])
                for _opt in _route_opts:
                    _all_map_pts.extend(_opt.get("waypoints", []))
                if len(_all_map_pts) >= 2:
                    fit_map_bounds(inc_map, _all_map_pts)

                st.markdown(
                    '<div style="display:flex;gap:16px;margin-bottom:4px;">'
                    '<span style="font-size:0.75rem;color:#4285F4;font-weight:600;">&#9473;&#9473; Recommended</span>'
                    '<span style="font-size:0.75rem;color:#9AA0A6;font-weight:600;">&#9473;&#9473; Alternatives</span>'
                    '<span style="font-size:0.75rem;color:#E74C3C;font-weight:600;">&#9476;&#9476; Original (Blocked)</span>'
                    '</div>', unsafe_allow_html=True,
                )
                st_folium(inc_map, use_container_width=True, height=380, returned_objects=[], key=f"analytics_incident_map_{inc_idx}")

                drv_for_ship = next((d for d in comp_drivers if d.get("assigned_shipment_id") == inc["shipment_id"]), None)
                drv_name = drv_for_ship["name"] if drv_for_ship else "driver"
                st.markdown(f"""
                <div class="recovery ok" style="margin-bottom:20px;">
                    <b>&#10003; Route Optimization Available:</b> Reroute recommendation sent to <b>{drv_name}</b>.
                    Alternate route via detour avoids {inc_type_label.lower()} zone.
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="panel" style="text-align:center;color:var(--green);padding:30px;">'
                '&#10003; No active incidents &mdash; all routes are clear.</div>',
                unsafe_allow_html=True,
            )

        # ════════════════════════════════════════════════════════════
        # Section 5: Fleet Optimization Recommendations
        # ════════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Fleet Optimization</div>', unsafe_allow_html=True)

        a_fleet_recs = analytics_data.get("fleet_recommendations", {}).get(selected_company_id, [])
        if a_fleet_recs:
            for rec_idx, rec in enumerate(a_fleet_recs):
                _impact_pill = {
                    "High": "pill-red", "Medium": "pill-amber", "Low": "pill-green"
                }.get(rec["impact"], "pill-purple")
                _cat_icon = {
                    "fleet": "&#9951;", "drivers": "&#9823;", "routes": "&#10132;", "general": "&#10003;"
                }.get(rec.get("category", "general"), "&#9881;")
                st.markdown(f"""
                <div class="panel" style="margin-bottom:10px;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                        <span style="font-size:1.1rem;">{_cat_icon}</span>
                        <span style="font-weight:700;color:var(--text-0);font-size:0.9rem;">{rec["title"]}</span>
                        <span class="pill {_impact_pill}" style="margin-left:auto;">{rec["impact"]} Impact</span>
                    </div>
                    <div style="font-size:0.82rem;color:var(--text-1);margin-bottom:8px;">{rec["description"]}</div>
                    <div style="font-size:0.75rem;color:var(--green);font-weight:600;">
                        Estimated Savings: {rec["estimated_savings"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="panel" style="text-align:center;color:var(--green);padding:30px;">'
                '&#10003; Fleet is operating at optimal capacity.</div>',
                unsafe_allow_html=True,
            )
