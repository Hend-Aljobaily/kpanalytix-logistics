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

from config import PORTS, ALL_DESTINATIONS, COLORS, DEST_COUNTRY_MAP, DEST_COUNTRIES, DEFAULT_COST_PARAMS, CARGO_TYPES
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
    st.session_state.shipments = generate_shipments(42)
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = _now()
if "selected_shipment_id" not in st.session_state:
    st.session_state.selected_shipment_id = None
if "company_data" not in st.session_state:
    st.session_state.company_data = None
if "analytics_data" not in st.session_state:
    st.session_state.analytics_data = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "Home"
if "cost_params" not in st.session_state:
    st.session_state.cost_params = dict(DEFAULT_COST_PARAMS)
st.session_state.dashboard_focus = "Overview"
if "micro_kpi_filter" not in st.session_state:
    st.session_state.micro_kpi_filter = None
if "macro_kpi_filter" not in st.session_state:
    st.session_state.macro_kpi_filter = None

if (_now() - st.session_state.last_refresh).seconds > 3600:
    st.session_state.shipments = generate_shipments(42)
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
    """Render a Folium map for the given shipments (filter-aware)."""
    m = create_base_map()

    # Only show ports and cities referenced by filtered shipments
    active_ports = {s["port"] for s in ship_list} if ship_list else set()
    active_dests = {s["destination"] for s in ship_list} if ship_list else set()
    visible_ports = {k: v for k, v in PORTS.items() if k in active_ports}
    visible_dests = {k: v for k, v in ALL_DESTINATIONS.items() if k in active_dests}

    port_summary = get_port_summary(ship_list)
    add_port_markers(m, visible_ports, port_summary=port_summary)
    add_city_markers(m, visible_dests)

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
    _view_options = ["Home", "Macro", "Micro", "Planner"]
    _view_idx = _view_options.index(st.session_state.view_mode) if st.session_state.view_mode in _view_options else 0
    view_mode = st.radio(
        "View",
        _view_options,
        index=_view_idx,
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
    # Planner inputs
    planner_company = None
    planner_origin = None
    planner_dest = None
    planner_cargo = None
    planner_priority = None
    planner_deadline_date = None
    planner_deadline_time = None
    planner_focus = "Balanced"
    w_urgency = 70
    w_revenue = 60
    w_priority = 80
    w_perishable = 50
    w_ontime = 40
    plan_base_margin = 15
    plan_urgency_premium = True
    plan_profit_floor = 0
    plan_max_drive_hrs = 10.0
    plan_loading_hrs = 2.0
    plan_multi_load = True

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

    elif view_mode == "Micro":
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

    else:
        # ── Planner — Decision Parameters ──
        st.markdown("""
        <div style="padding:4px 0 12px 0;">
            <div style="font-size:0.92rem;font-weight:700;color:var(--text-0);margin-bottom:2px;">Shipment Planner</div>
            <div style="font-size:0.72rem;color:var(--text-2);">Auto-optimize dispatch for all pending shipments</div>
        </div>
        """, unsafe_allow_html=True)

        _plan_company_names = {c["id"]: c["name"] for c in company_data["companies"]}
        _plan_company_ids = list(_plan_company_names.keys())
        planner_company = st.selectbox(
            "Company",
            options=_plan_company_ids,
            format_func=lambda x: _plan_company_names[x],
            key="planner_company",
        )

        # ── Company Focus ──
        st.markdown('<div style="font-size:0.72rem;color:var(--text-2);margin:12px 0 4px 0;text-transform:uppercase;letter-spacing:0.5px;">Company Focus</div>', unsafe_allow_html=True)
        _focus_options = ["Balanced", "Profit Maximization", "Reputation (On-Time)"]
        planner_focus = st.select_slider("Focus", options=_focus_options, value="Balanced", key="planner_focus")

        # ── Decision Weights ──
        st.markdown('<div style="font-size:0.72rem;color:var(--text-2);margin:12px 0 4px 0;text-transform:uppercase;letter-spacing:0.5px;">Decision Weights</div>', unsafe_allow_html=True)
        w_urgency = st.slider("Time Urgency", 0, 100, 70 if planner_focus != "Profit Maximization" else 40, 5, key="plan_w_urgency")
        w_revenue = st.slider("Revenue Value", 0, 100, 80 if planner_focus == "Profit Maximization" else 60, 5, key="plan_w_revenue")
        w_priority = st.slider("Priority Level", 0, 100, 90 if planner_focus == "Reputation (On-Time)" else 80, 5, key="plan_w_priority")
        w_perishable = st.slider("Perishability", 0, 100, 50, 5, key="plan_w_perishable")
        w_ontime = st.slider("On-Time Bonus", 0, 100, 90 if planner_focus == "Reputation (On-Time)" else 40, 5, key="plan_w_ontime",
                             help="Extra weight for shipments close to deadline — prioritize reputation")

        # ── Pricing Parameters ──
        st.markdown('<div style="font-size:0.72rem;color:var(--text-2);margin:12px 0 4px 0;text-transform:uppercase;letter-spacing:0.5px;">Pricing</div>', unsafe_allow_html=True)
        plan_base_margin = st.slider("Base Margin %", 5, 40, 15 if planner_focus != "Profit Maximization" else 25, 1, key="plan_base_margin")
        plan_urgency_premium = st.toggle("Urgency Premium", value=True if planner_focus != "Reputation (On-Time)" else False, key="plan_urgency_premium",
                                         help="Dynamic pricing multiplier based on deadline buffer")
        plan_profit_floor = st.slider("Min Profit (SAR)", 0, 5000, 500 if planner_focus == "Profit Maximization" else 0, 100, key="plan_profit_floor",
                                      help="Reject shipments below this profit threshold")

        # ── Cost Parameters ──
        with st.expander("Cost Parameters", expanded=False):
            st.session_state.cost_params["fuel_cost_per_km"] = st.slider(
                "Fuel Cost (SAR/km)", 0.20, 1.00, st.session_state.cost_params["fuel_cost_per_km"], 0.05, key="plan_fuel")
            st.session_state.cost_params["driver_cost_per_hr"] = st.slider(
                "Driver Cost (SAR/hr)", 15.0, 80.0, st.session_state.cost_params["driver_cost_per_hr"], 5.0, key="plan_driver_cost")
            st.session_state.cost_params["maintenance_per_km"] = st.slider(
                "Maintenance (SAR/km)", 0.02, 0.20, st.session_state.cost_params["maintenance_per_km"], 0.01, key="plan_maint")
            st.session_state.cost_params["toll_flat_rate"] = st.slider(
                "Toll Rate (SAR)", 0.0, 150.0, st.session_state.cost_params["toll_flat_rate"], 10.0, key="plan_toll")
            st.session_state.cost_params["cooled_surcharge_per_km"] = st.slider(
                "Cooled Surcharge (SAR/km)", 0.05, 0.50, st.session_state.cost_params["cooled_surcharge_per_km"], 0.05, key="plan_cooled")

        # ── Dispatch Constraints ──
        with st.expander("Dispatch Constraints", expanded=False):
            plan_max_drive_hrs = st.slider("Max Drive Hours/Driver", 4.0, 14.0, 10.0, 0.5, key="plan_max_drive")
            plan_loading_hrs = st.slider("Loading/Prep Time (hrs)", 0.5, 4.0, 2.0, 0.5, key="plan_loading_hrs")
            plan_multi_load = st.toggle("Allow Multi-Load", value=True, key="plan_multi_load",
                                        help="Let drivers handle sequential deliveries")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.72rem;color:var(--text-2);padding:4px 0;">Last refresh &mdash; {st.session_state.last_refresh.strftime("%H:%M:%S")}</div>',
        unsafe_allow_html=True,
    )
    if st.button("Refresh Data", type="primary", use_container_width=True):
        st.session_state.shipments = generate_shipments(42)
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

# Apply KPI click filter (Macro)
_maf = st.session_state.get("macro_kpi_filter")
if _maf:
    _maf_type, _maf_val = _maf
    if _maf_type == "delivery":
        filtered = [s for s in filtered if s["time_status"] == _maf_val]
    elif _maf_type == "status":
        filtered = [s for s in filtered if s["status"] == _maf_val]
    elif _maf_type == "truck_type":
        filtered = [s for s in filtered if s["truck_type"] == _maf_val]

f_summary = get_shipment_summary(filtered)

# ══════════════════════════════════════════════════════════════════
# VIEW: HOME — Solution Selection Landing Page
# ══════════════════════════════════════════════════════════════════
if view_mode == "Home":
    st.markdown("""
    <div style="text-align:center;padding:40px 0 20px 0;">
        <div style="font-size:2rem;font-weight:800;color:var(--text-0);letter-spacing:-0.5px;">Logistics Optimizer</div>
        <div style="font-size:0.95rem;color:var(--text-2);margin-top:6px;">Automated Operations Center &mdash; Select a solution to get started</div>
    </div>
    """, unsafe_allow_html=True)

    _home_cols = st.columns(3, gap="large")

    with _home_cols[0]:
        st.markdown("""
        <div class="panel" style="text-align:center;padding:32px 20px;min-height:320px;display:flex;flex-direction:column;justify-content:space-between;">
            <div>
                <div style="font-size:2.5rem;margin-bottom:12px;">&#127758;</div>
                <div style="font-size:1.15rem;font-weight:800;color:var(--text-0);margin-bottom:6px;">Macro Dashboard</div>
                <div style="font-size:0.75rem;color:var(--accent);font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">National Operations View</div>
                <div style="font-size:0.82rem;color:var(--text-1);line-height:1.6;">
                    Government-level shipment intelligence across all ports, routes, and companies.
                    Real-time KPIs, delay analytics, port throughput, and national fleet monitoring.
                </div>
            </div>
            <div style="margin-top:16px;">
                <div style="font-size:0.72rem;color:var(--text-2);margin-bottom:8px;">Best for: Ministry of Transport, Customs Authority, Regulatory Bodies</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Macro Dashboard", key="home_macro", use_container_width=True):
            st.session_state.view_mode = "Macro"
            st.rerun()

    with _home_cols[1]:
        st.markdown("""
        <div class="panel" style="text-align:center;padding:32px 20px;min-height:320px;display:flex;flex-direction:column;justify-content:space-between;">
            <div>
                <div style="font-size:2.5rem;margin-bottom:12px;">&#128666;</div>
                <div style="font-size:1.15rem;font-weight:800;color:var(--text-0);margin-bottom:6px;">Micro Dashboard</div>
                <div style="font-size:0.75rem;color:var(--blue);font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Company Fleet Monitoring</div>
                <div style="font-size:0.82rem;color:var(--text-1);line-height:1.6;">
                    Per-company live monitoring of trucks, drivers, shipments, and delivery performance.
                    Track individual shipments, driver efficiency, and fleet utilization.
                </div>
            </div>
            <div style="margin-top:16px;">
                <div style="font-size:0.72rem;color:var(--text-2);margin-bottom:8px;">Best for: Fleet Managers, Logistics Coordinators, Operations Teams</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Micro Dashboard", key="home_micro", use_container_width=True):
            st.session_state.view_mode = "Micro"
            st.rerun()

    with _home_cols[2]:
        st.markdown("""
        <div class="panel" style="text-align:center;padding:32px 20px;min-height:320px;display:flex;flex-direction:column;justify-content:space-between;">
            <div>
                <div style="font-size:2.5rem;margin-bottom:12px;">&#9881;</div>
                <div style="font-size:1.15rem;font-weight:800;color:var(--text-0);margin-bottom:6px;">Shipment Planner</div>
                <div style="font-size:0.75rem;color:var(--green);font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Dispatch Optimization Engine</div>
                <div style="font-size:0.82rem;color:var(--text-1);line-height:1.6;">
                    AI-driven dispatch planner that ranks all pending orders by criticality,
                    auto-assigns trucks &amp; drivers, computes dynamic pricing, and recommends hiring.
                </div>
            </div>
            <div style="margin-top:16px;">
                <div style="font-size:0.72rem;color:var(--text-2);margin-bottom:8px;">Best for: Dispatch Managers, Pricing Analysts, Capacity Planners</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Shipment Planner", key="home_planner", use_container_width=True):
            st.session_state.view_mode = "Planner"
            st.rerun()

    # Quick stats bar
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Platform Overview</div>', unsafe_allow_html=True)

    _home_kpi_cols = st.columns(5)
    _home_kpi = [
        ("Active Shipments", f'{f_summary["total"]}', "var(--accent)"),
        ("In Transit", f'{f_summary["in_transit"]}', "var(--blue)"),
        ("On Time", f'{f_summary["on_time"]}', "var(--green)"),
        ("At Risk", f'{f_summary["at_risk"]}', "var(--amber)"),
        ("Delayed", f'{f_summary["delayed"]}', "var(--red)"),
    ]
    for _hcol, (_hl, _hv, _hc) in zip(_home_kpi_cols, _home_kpi):
        with _hcol:
            st.markdown(f"""
            <div class="panel" style="text-align:center;">
                <div style="font-size:0.68rem;color:var(--text-2);text-transform:uppercase;letter-spacing:1px;">{_hl}</div>
                <div style="font-size:1.6rem;font-weight:800;color:{_hc};">{_hv}</div>
            </div>""", unsafe_allow_html=True)

    # Companies overview
    st.markdown('<div class="sec-title">Registered Companies</div>', unsafe_allow_html=True)
    _comp_cols = st.columns(3)
    for _ci, _comp in enumerate(company_data["companies"]):
        with _comp_cols[_ci % 3]:
            _comp_shps = len([s for s in shipments if s.get("company_id") == _comp["id"]])
            _comp_drvs = len(company_data["drivers"].get(_comp["id"], []))
            _comp_trks = len(company_data["trucks"].get(_comp["id"], []))
            st.markdown(f"""
            <div class="panel" style="margin-bottom:10px;">
                <div style="font-weight:700;color:var(--text-0);margin-bottom:4px;">{_comp["name"]}</div>
                <div style="font-size:0.78rem;color:var(--text-2);margin-bottom:8px;">{_comp.get("specialization", "")} &bull; {_comp["hq_city"]}</div>
                <div style="display:flex;gap:16px;font-size:0.78rem;">
                    <span style="color:var(--accent);">{_comp_shps} orders</span>
                    <span style="color:var(--text-1);">{_comp_drvs} drivers</span>
                    <span style="color:var(--text-1);">{_comp_trks} trucks</span>
                    <span style="color:var(--text-2);">{_comp.get("erp_system", "")}</span>
                </div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# VIEW: MACRO or MICRO (controlled by sidebar)
# ══════════════════════════════════════════════════════════════════
elif view_mode == "Macro":
    pct_on_time = round(f_summary["on_time"] / f_summary["total"] * 100) if f_summary["total"] else 0

    # Active KPI filter indicator
    _maf = st.session_state.get("macro_kpi_filter")
    if _maf:
        _ftype, _fval = _maf
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
            f'<span style="font-size:0.78rem;color:var(--accent);font-weight:600;">Filtered: {_fval}</span>'
            f'</div>', unsafe_allow_html=True)

    # Clickable KPI cards — Row 1
    _macro_kpis_r1 = [
        ("Total Shipments", f_summary["total"], "var(--text-0)", "&#9776;", None),
        ("On Time", f'{pct_on_time}%', "var(--green)", "&#10003;", ("delivery", "On Time")),
        ("At Risk", f_summary["at_risk"], "var(--amber)", "&#9888;", ("delivery", "At Risk")),
        ("Delayed", f_summary["delayed"], "var(--red)", "&#10006;", ("delivery", "Delayed")),
        ("Avg Buffer", f'{f_summary["avg_buffer_hrs"]}h', "var(--amber)" if f_summary["avg_buffer_hrs"] < 4 else "var(--green)", "&#9201;", None),
    ]
    _macro_kpis_r2 = [
        ("Cooled Fleet", f_summary["cooled"], "var(--blue)", "&#10052;", ("truck_type", "Cooled")),
        ("Regular Fleet", f_summary["regular"], "var(--accent)", "&#9951;", ("truck_type", "Regular")),
        ("In Transit", f_summary["in_transit"], "var(--accent)", "&#10132;", ("status", "In Transit")),
        ("At Port", f_summary["at_port"], "var(--blue)", "&#9875;", ("status", "At Port")),
        ("Delivered", f_summary["delivered"], "var(--green)", "&#10003;", ("status", "Delivered")),
    ]

    for _row_idx, _kpi_row in enumerate([_macro_kpis_r1, _macro_kpis_r2]):
        _cols = st.columns(len(_kpi_row))
        for _ki, (_col, (_label, _val, _color, _icon, _filter)) in enumerate(zip(_cols, _kpi_row)):
            with _col:
                _is_active = _maf == _filter if _filter else False
                _border = f"border:2px solid #4285F4;background:rgba(66,133,244,0.08);" if _is_active else ""
                st.markdown(
                    f'<div class="kpi" style="{_border}">'
                    f'<div class="kpi-accent" style="background:{_color};"></div>'
                    f'<div class="kpi-icon" style="color:{_color};">{_icon}</div>'
                    f'<div class="kpi-label">{_label}</div>'
                    f'<div class="kpi-value" style="color:{_color};">{_val}</div>'
                    f'</div>', unsafe_allow_html=True)
                if _filter:
                    _btn_label = "Clear" if _is_active else _label
                    if st.button(_btn_label, key=f"maf_{_row_idx}_{_ki}", use_container_width=True):
                        if _is_active:
                            st.session_state.macro_kpi_filter = None
                        else:
                            st.session_state.macro_kpi_filter = _filter
                        st.rerun()

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
elif view_mode == "Micro":
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

    # Apply KPI click filter (toggle filter from clicking KPI cards)
    _mkf = st.session_state.get("micro_kpi_filter")
    if _mkf:
        _mkf_type, _mkf_val = _mkf
        if _mkf_type == "delivery":
            micro_filtered = [s for s in micro_filtered if s["time_status"] == _mkf_val]
        elif _mkf_type == "status":
            micro_filtered = [s for s in micro_filtered if s["status"] == _mkf_val]
        elif _mkf_type == "truck_type":
            micro_filtered = [s for s in micro_filtered if s["truck_type"] == _mkf_val]

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
        # Active KPI filter indicator
        _mkf = st.session_state.get("micro_kpi_filter")
        if _mkf:
            _ftype, _fval = _mkf
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                f'<span style="font-size:0.78rem;color:var(--accent);font-weight:600;">Filtered: {_fval}</span>'
                f'</div>', unsafe_allow_html=True)

        # Clickable KPI cards — Row 1
        _micro_kpis_r1 = [
            ("Total Shipments", mf_summary["total"], "var(--text-0)", "&#9776;", None),
            ("On Time", f'{mf_on_time_pct}%', "var(--green)", "&#10003;", ("delivery", "On Time")),
            ("At Risk", mf_summary["at_risk"], "var(--amber)", "&#9888;", ("delivery", "At Risk")),
            ("Delayed", mf_summary["delayed"], "var(--red)", "&#10006;", ("delivery", "Delayed")),
            ("Avg Buffer", f'{mf_summary["avg_buffer_hrs"]}h', "var(--amber)" if mf_summary["avg_buffer_hrs"] < 4 else "var(--green)", "&#9201;", None),
        ]
        _micro_kpis_r2 = [
            ("Cooled Fleet", mf_summary["cooled"], "var(--blue)", "&#10052;", ("truck_type", "Cooled")),
            ("Regular Fleet", mf_summary["regular"], "var(--accent)", "&#9951;", ("truck_type", "Regular")),
            ("In Transit", mf_summary["in_transit"], "var(--accent)", "&#10132;", ("status", "In Transit")),
            ("At Port", mf_summary["at_port"], "var(--blue)", "&#9875;", ("status", "At Port")),
            ("Delivered", mf_summary["delivered"], "var(--green)", "&#10003;", ("status", "Delivered")),
        ]

        for _row_idx, _kpi_row in enumerate([_micro_kpis_r1, _micro_kpis_r2]):
            _cols = st.columns(len(_kpi_row))
            for _ki, (_col, (_label, _val, _color, _icon, _filter)) in enumerate(zip(_cols, _kpi_row)):
                with _col:
                    _is_active = _mkf == _filter if _filter else False
                    _border = f"border:2px solid #4285F4;background:rgba(66,133,244,0.08);" if _is_active else ""
                    st.markdown(
                        f'<div class="kpi" style="{_border}">'
                        f'<div class="kpi-accent" style="background:{_color};"></div>'
                        f'<div class="kpi-icon" style="color:{_color};">{_icon}</div>'
                        f'<div class="kpi-label">{_label}</div>'
                        f'<div class="kpi-value" style="color:{_color};">{_val}</div>'
                        f'</div>', unsafe_allow_html=True)
                    if _filter:
                        _btn_label = "Clear" if _is_active else _label
                        if st.button(_btn_label, key=f"mkpi_{_row_idx}_{_ki}", use_container_width=True):
                            if _is_active:
                                st.session_state.micro_kpi_filter = None
                            else:
                                st.session_state.micro_kpi_filter = _filter
                            st.rerun()

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

        # Driver route map — full route with clickable alternatives
        if sel_driver["assigned_shipment_id"]:
            _drv_ship = next((s for s in comp_shipments if s["id"] == sel_driver["assigned_shipment_id"]), None)
        else:
            _drv_ship = None

        if _drv_ship and _drv_ship["route"]["waypoints"]:
            _drv_hotspots = analytics_data["location_hotspots"].get(selected_company_id, [])

            # Fetch OSRM route alternatives for this driver's shipment
            from routing import get_route_alternatives as _drv_get_alts
            _drv_port_coords = _drv_ship["port_coords"]
            _drv_dest_coords = _drv_ship["dest_coords"]
            _drv_osrm_alts = _drv_get_alts(
                {"lat": _drv_port_coords["lat"], "lon": _drv_port_coords["lon"]},
                {"lat": _drv_dest_coords["lat"], "lon": _drv_dest_coords["lon"]},
                num_alternatives=3,
            )

            # Build route alternatives list from OSRM
            _drv_route_alts = []
            if _drv_osrm_alts:
                for _ai, _alt in enumerate(_drv_osrm_alts):
                    _drv_route_alts.append({
                        "geometry": _alt["geometry"],
                        "distance_km": round(_alt["distance_km"], 1),
                        "duration_hrs": round(_alt["duration_hrs"], 1),
                        "label": "Recommended" if _ai == 0 else f"Route {chr(65 + _ai)}",
                    })

            # Fallback — use the shipment's own route
            if not _drv_route_alts:
                _drv_route_alts.append({
                    "geometry": _drv_ship["route"]["waypoints"],
                    "distance_km": _drv_ship["route"]["distance_km"],
                    "duration_hrs": _drv_ship["route"]["duration_hrs"],
                    "label": "Recommended",
                })

            # Selected route — stored in session state, reset when driver changes
            _drv_route_key = f"drv_route_{sel_driver['id']}"
            if _drv_route_key not in st.session_state:
                st.session_state[_drv_route_key] = 0
            _sel_route_idx = st.session_state[_drv_route_key]
            if _sel_route_idx >= len(_drv_route_alts):
                _sel_route_idx = 0

            # Route info cards — clickable Google Maps style
            if len(_drv_route_alts) > 1:
                _route_cols = st.columns(len(_drv_route_alts))
                for _ri, (_rcol, _ralt) in enumerate(zip(_route_cols, _drv_route_alts)):
                    with _rcol:
                        _rh = int(_ralt["duration_hrs"])
                        _rm = int((_ralt["duration_hrs"] % 1) * 60)
                        _is_sel = (_ri == _sel_route_idx)
                        _border_color = "#4285F4" if _is_sel else "var(--border)"
                        _text_color = "#4285F4" if _is_sel else "var(--text-2)"
                        _bg = "rgba(66,133,244,0.08)" if _is_sel else "transparent"
                        _dot = "&#9679;" if _is_sel else "&#9675;"
                        st.markdown(f"""
                        <div style="border:2px solid {_border_color};border-radius:8px;padding:10px;
                                    background:{_bg};text-align:center;cursor:pointer;">
                            <div style="font-size:0.9rem;font-weight:700;color:{_text_color};">
                                {_dot} {_ralt["label"]}
                            </div>
                            <div style="font-size:1.1rem;font-weight:700;color:var(--text-0);margin:4px 0;">
                                {_rh}h {_rm}m
                            </div>
                            <div style="font-size:0.78rem;color:var(--text-2);">
                                {_ralt["distance_km"]:.0f} km
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(
                            "Select" if not _is_sel else "Selected",
                            key=f"drv_route_btn_{_ri}",
                            disabled=_is_sel,
                            use_container_width=True,
                        ):
                            st.session_state[_drv_route_key] = _ri
                            st.rerun()

                # Legend
                st.markdown(
                    '<div style="display:flex;gap:16px;margin:4px 0 4px 0;">'
                    '<span style="font-size:0.75rem;color:#4285F4;font-weight:600;">&#9473;&#9473; Selected Route</span>'
                    '<span style="font-size:0.75rem;color:#9AA0A6;font-weight:600;">&#9473;&#9473; Alternatives</span>'
                    '</div>', unsafe_allow_html=True,
                )

            drv_map = create_driver_route_map(
                sel_driver, _drv_ship,
                hotspots=_drv_hotspots,
                route_alternatives=_drv_route_alts,
                selected_route_idx=_sel_route_idx,
            )

            # Render map — capture clicks on grey routes
            _map_data = st_folium(drv_map, use_container_width=True, height=400, returned_objects=["last_object_clicked"], key="drv_location_map")

            # Click detection — switch to nearest route when clicking on map
            if len(_drv_route_alts) > 1 and _map_data and _map_data.get("last_object_clicked"):
                _click = _map_data["last_object_clicked"]
                _click_key = (round(_click["lat"], 5), round(_click["lng"], 5))
                if _click_key != st.session_state.get("_drv_last_click"):
                    st.session_state["_drv_last_click"] = _click_key
                    # Find nearest route to click point
                    import math
                    _best_idx = _sel_route_idx
                    _best_dist = float("inf")
                    for _ri, _ralt in enumerate(_drv_route_alts):
                        # Sample every 50th point for performance
                        for _pt in _ralt["geometry"][::50]:
                            _d = math.sqrt((_pt[0] - _click["lat"])**2 + (_pt[1] - _click["lng"])**2)
                            if _d < _best_dist:
                                _best_dist = _d
                                _best_idx = _ri
                    # Only switch if click is reasonably close to a route (~0.3 degrees)
                    if _best_dist < 0.3 and _best_idx != _sel_route_idx:
                        st.session_state[_drv_route_key] = _best_idx
                        st.rerun()
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
        # Section 0: Unified Delay & Route Overview Map
        # ════════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Delay &amp; Route Overview</div>', unsafe_allow_html=True)

        # Pre-compute route options so they can be drawn on the unified map
        route_options = generate_route_options(a_incidents, st.session_state.cost_params) if a_incidents else []

        # Session state for selected route per incident
        for _ii in range(len(a_incidents)):
            _sel_key = f"opt_route_sel_{selected_company_id}_{_ii}"
            if _sel_key not in st.session_state:
                st.session_state[_sel_key] = "Balanced"

        if comp_shipments:
            unified_map = create_base_map()

            # Layer 1: Delay-colored routes + truck positions
            add_delay_colored_routes(unified_map, comp_shipments)

            # Layer 2: Hotspot markers
            if a_hotspots:
                add_hotspot_markers(unified_map, a_hotspots)

            # Layer 3: Incident markers + route alternatives (with selection)
            for inc_idx, inc in enumerate(a_incidents):
                _route_opts = route_options[inc_idx]["options"] if inc_idx < len(route_options) else []
                _sel_name = st.session_state.get(f"opt_route_sel_{selected_company_id}_{inc_idx}", "Balanced")
                add_optimization_routes(unified_map, _route_opts, incident=inc,
                                        original_route=inc["original_route"], selected_name=_sel_name)

            # Fit bounds to all visible features
            all_map_pts = []
            for _s in comp_shipments:
                all_map_pts.extend(_s["route"]["waypoints"])
            for _h in a_hotspots:
                all_map_pts.append([_h["lat"], _h["lon"]])
            for inc_idx, inc in enumerate(a_incidents):
                all_map_pts.extend(inc.get("original_route", []))
                for _opt in (route_options[inc_idx]["options"] if inc_idx < len(route_options) else []):
                    all_map_pts.extend(_opt.get("waypoints", []))
            if all_map_pts:
                fit_map_bounds(unified_map, all_map_pts)

            # Combined legend
            legend_parts = [
                '<span style="font-size:0.75rem;color:#4285F4;font-weight:600;">&#9473; Routes</span>',
                '<span style="font-size:0.75rem;color:#2ECC71;font-weight:600;">&#9679; On Time</span>',
                '<span style="font-size:0.75rem;color:#F39C12;font-weight:600;">&#9679; At Risk</span>',
                '<span style="font-size:0.75rem;color:#E74C3C;font-weight:600;">&#9679; Delayed</span>',
            ]
            if a_hotspots:
                legend_parts.append('<span style="font-size:0.75rem;color:#f59e0b;font-weight:600;">&#11044; Hotspots</span>')
            if a_incidents:
                legend_parts.extend([
                    '<span style="font-size:0.75rem;color:#9AA0A6;font-weight:600;">&#9473;&#9473; Alternatives (click to select)</span>',
                    '<span style="font-size:0.75rem;color:#ef4444;font-weight:600;">&#9888; Incidents</span>',
                ])
            st.markdown(
                '<div style="display:flex;flex-wrap:wrap;gap:16px;margin-bottom:8px;">'
                + ''.join(legend_parts) + '</div>', unsafe_allow_html=True,
            )
            _map_data = st_folium(unified_map, use_container_width=True, height=480,
                                  returned_objects=["last_object_clicked"], key="analytics_unified_map")

            # Click detection — switch to nearest route alternative
            if a_incidents and route_options and _map_data and _map_data.get("last_object_clicked"):
                import math as _math
                _click = _map_data["last_object_clicked"]
                _click_key = (round(_click["lat"], 5), round(_click["lng"], 5))
                if _click_key != st.session_state.get("_analytics_last_click"):
                    st.session_state["_analytics_last_click"] = _click_key
                    _best_inc = None
                    _best_name = None
                    _best_dist = float("inf")
                    for _ii, _inc in enumerate(a_incidents):
                        _opts = route_options[_ii]["options"] if _ii < len(route_options) else []
                        for _opt in _opts:
                            _wps = _opt.get("waypoints", [])
                            for _pt in _wps[::50]:
                                _d = _math.sqrt((_pt[0] - _click["lat"])**2 + (_pt[1] - _click["lng"])**2)
                                if _d < _best_dist:
                                    _best_dist = _d
                                    _best_inc = _ii
                                    _best_name = _opt["name"]
                    if _best_dist < 0.3 and _best_inc is not None:
                        _cur_sel = st.session_state.get(f"opt_route_sel_{selected_company_id}_{_best_inc}", "Balanced")
                        if _best_name != _cur_sel:
                            st.session_state[f"opt_route_sel_{selected_company_id}_{_best_inc}"] = _best_name
                            st.rerun()
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
            # Hotspot table (map is shown in unified overview above)
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

        if a_incidents and route_options:
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

                # 3-option route comparison cards with selection
                opts = route_options[inc_idx]["options"] if inc_idx < len(route_options) else []
                _cur_sel = st.session_state.get(f"opt_route_sel_{selected_company_id}_{inc_idx}", "Balanced")
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
                            _is_sel = (opt["name"] == _cur_sel)
                            _border = f"2px solid #4285F4" if _is_sel else f"none"
                            _bg = "rgba(66,133,244,0.08)" if _is_sel else "transparent"
                            _dot = "&#9679;" if _is_sel else "&#9675;"
                            st.markdown(f"""
                            <div class="panel" style="border-left:3px solid {_color};border:{_border};background:{_bg};">
                                <div style="font-size:0.82rem;font-weight:700;color:{_color};margin-bottom:8px;">
                                    <span style="color:#4285F4;">{_dot}</span> {_icon} {opt["name"]}
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
                            if st.button(
                                "Selected" if _is_sel else "Select",
                                key=f"opt_btn_{inc_idx}_{opt['name']}",
                                disabled=_is_sel,
                                use_container_width=True,
                            ):
                                st.session_state[f"opt_route_sel_{selected_company_id}_{inc_idx}"] = opt["name"]
                                st.rerun()

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

        a_fleet_data = analytics_data.get("fleet_recommendations", {}).get(selected_company_id, {})
        # Support both old list format and new dict format
        if isinstance(a_fleet_data, list):
            a_fleet_recs = a_fleet_data
            cooled_table = []
            driver_opt = []
            reassign_actions = []
        else:
            a_fleet_recs = a_fleet_data.get("recommendations", [])
            cooled_table = a_fleet_data.get("cooled_priority_table", [])
            driver_opt = a_fleet_data.get("driver_optimization", [])
            reassign_actions = a_fleet_data.get("reassignment_actions", [])

        # ── Revenue KPI Strip ──
        comp_ships_for_rev = [s for s in shipments if s.get("company_id") == selected_company_id]
        total_rev = sum(s.get("estimated_revenue", 0) for s in comp_ships_for_rev)
        cooled_rev = sum(s.get("estimated_revenue", 0) for s in comp_ships_for_rev if s.get("truck_type") == "Cooled")
        risk_rev = sum(s.get("estimated_revenue", 0) for s in comp_ships_for_rev if s.get("time_status") in ("Delayed", "At Risk"))

        kpi_cols = st.columns(3)
        with kpi_cols[0]:
            st.markdown(f"""
            <div class="panel" style="text-align:center;">
                <div style="font-size:0.72rem;color:var(--text-1);text-transform:uppercase;letter-spacing:1px;">Total Est. Revenue</div>
                <div style="font-size:1.5rem;font-weight:800;color:var(--accent);">{total_rev:,.0f} <span style="font-size:0.7rem;">SAR</span></div>
            </div>""", unsafe_allow_html=True)
        with kpi_cols[1]:
            st.markdown(f"""
            <div class="panel" style="text-align:center;">
                <div style="font-size:0.72rem;color:var(--text-1);text-transform:uppercase;letter-spacing:1px;">Cooled Cargo Value</div>
                <div style="font-size:1.5rem;font-weight:800;color:var(--blue);">{cooled_rev:,.0f} <span style="font-size:0.7rem;">SAR</span></div>
            </div>""", unsafe_allow_html=True)
        with kpi_cols[2]:
            st.markdown(f"""
            <div class="panel" style="text-align:center;">
                <div style="font-size:0.72rem;color:var(--text-1);text-transform:uppercase;letter-spacing:1px;">Revenue at Risk</div>
                <div style="font-size:1.5rem;font-weight:800;color:var(--red);">{risk_rev:,.0f} <span style="font-size:0.7rem;">SAR</span></div>
            </div>""", unsafe_allow_html=True)

        # ── Cooled Fleet Priority Ranking Table ──
        if cooled_table:
            st.markdown('<div style="font-weight:700;color:var(--text-0);font-size:0.88rem;margin:16px 0 8px;">Cooled Fleet Priority Ranking</div>', unsafe_allow_html=True)
            header = """<div class="panel" style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:0.78rem;">
            <thead><tr style="border-bottom:1px solid var(--border);">
                <th style="padding:6px 8px;text-align:left;color:var(--text-1);">Rank</th>
                <th style="padding:6px 8px;text-align:left;color:var(--text-1);">Shipment</th>
                <th style="padding:6px 8px;text-align:left;color:var(--text-1);">Cargo</th>
                <th style="padding:6px 8px;text-align:left;color:var(--text-1);">Priority</th>
                <th style="padding:6px 8px;text-align:right;color:var(--text-1);">Revenue (SAR)</th>
                <th style="padding:6px 8px;text-align:left;color:var(--text-1);">Driver</th>
                <th style="padding:6px 8px;text-align:left;color:var(--text-1);">Status</th>
            </tr></thead><tbody>"""
            rows = ""
            for ct in cooled_table:
                row_color = "rgba(46,204,113,0.08)" if ct["optimally_ranked"] else "rgba(243,156,18,0.08)"
                status_color = {"On Time": "var(--green)", "At Risk": "var(--amber)", "Delayed": "var(--red)"}.get(ct["time_status"], "var(--text-1)")
                priority_color = {"Critical": "var(--red)", "High": "var(--amber)", "Standard": "var(--text-1)"}.get(ct["priority"], "var(--text-1)")
                rows += f"""<tr style="background:{row_color};border-bottom:1px solid rgba(46,37,69,0.3);">
                    <td style="padding:6px 8px;color:var(--text-0);font-weight:700;">#{ct['rank']}</td>
                    <td style="padding:6px 8px;color:var(--accent);">{ct['shipment_id']}</td>
                    <td style="padding:6px 8px;color:var(--text-0);">{ct['cargo']}</td>
                    <td style="padding:6px 8px;color:{priority_color};font-weight:600;">{ct['priority']}</td>
                    <td style="padding:6px 8px;text-align:right;color:var(--text-0);font-weight:700;">{ct['revenue']:,.0f}</td>
                    <td style="padding:6px 8px;color:var(--text-1);">{ct['assigned_driver']}</td>
                    <td style="padding:6px 8px;color:{status_color};font-weight:600;">{ct['time_status']}</td>
                </tr>"""
            st.markdown(header + rows + "</tbody></table></div>", unsafe_allow_html=True)

        # ── Driver-Shipment Optimization ──
        if driver_opt:
            st.markdown('<div style="font-weight:700;color:var(--text-0);font-size:0.88rem;margin:16px 0 8px;">Driver-Shipment Optimization</div>', unsafe_allow_html=True)
            drv_cols = st.columns(min(3, len(driver_opt)))
            for idx, dopt in enumerate(driver_opt[:6]):
                col = drv_cols[idx % len(drv_cols)]
                score = dopt["efficiency_score"]
                if score >= 85:
                    score_color = "var(--green)"
                elif score >= 70:
                    score_color = "var(--amber)"
                else:
                    score_color = "var(--red)"
                ship_label = f"{dopt['assigned_shipment_id']} ({dopt['shipment_revenue']:,.0f} SAR)" if dopt["assigned_shipment_id"] else "No active shipment"
                suggestion_color = "var(--green)" if "Optimal" in dopt["suggestion"] else "var(--amber)"
                with col:
                    st.markdown(f"""
                    <div class="panel" style="margin-bottom:10px;">
                        <div style="font-weight:700;color:var(--text-0);font-size:0.82rem;margin-bottom:6px;">{dopt['driver_name']}</div>
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                            <span style="font-size:1.3rem;font-weight:800;color:{score_color};">{score}</span>
                            <span style="font-size:0.7rem;color:var(--text-1);">/ 100 efficiency</span>
                        </div>
                        <div style="font-size:0.72rem;color:var(--text-1);margin-bottom:4px;">
                            OT: {dopt['stats']['on_time_pct']}% &middot; Rating: {dopt['stats']['avg_rating']:.1f} &middot; {dopt['stats']['km_per_month']:,} km/mo
                        </div>
                        <div style="font-size:0.75rem;color:var(--accent);margin-bottom:6px;">{ship_label}</div>
                        <div style="font-size:0.72rem;color:{suggestion_color};font-weight:600;">{dopt['suggestion']}</div>
                    </div>""", unsafe_allow_html=True)

        # ── Recommended Reassignments ──
        if reassign_actions:
            st.markdown('<div style="font-weight:700;color:var(--text-0);font-size:0.88rem;margin:16px 0 8px;">Recommended Reassignments</div>', unsafe_allow_html=True)
            for ra in reassign_actions:
                st.markdown(f"""
                <div class="panel" style="margin-bottom:10px;border-left:3px solid var(--amber);">
                    <div style="font-size:0.82rem;color:var(--text-0);margin-bottom:6px;">
                        <b>Swap</b> {ra['from_driver']} <span style="color:var(--green);">(score {ra['from_score']})</span>
                        &#10132; <span style="color:var(--accent);">{ra['to_shipment']}</span> ({ra['to_revenue']:,.0f} SAR)
                        &nbsp;with&nbsp;
                        {ra['to_driver']} <span style="color:var(--red);">(score {ra['to_score']})</span>
                        &#10132; <span style="color:var(--accent);">{ra['from_shipment']}</span> ({ra['from_revenue']:,.0f} SAR)
                    </div>
                    <div style="font-size:0.72rem;color:var(--text-1);">{ra['reason']}</div>
                </div>""", unsafe_allow_html=True)

        # ── Existing Recommendation Cards ──
        if a_fleet_recs:
            st.markdown('<div style="font-weight:700;color:var(--text-0);font-size:0.88rem;margin:16px 0 8px;">Optimization Recommendations</div>', unsafe_allow_html=True)
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
        elif not cooled_table and not driver_opt:
            st.markdown(
                '<div class="panel" style="text-align:center;color:var(--green);padding:30px;">'
                '&#10003; Fleet is operating at optimal capacity.</div>',
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════
# PLANNER VIEW — Time-Critical Multi-Shipment Optimizer
# ══════════════════════════════════════════════════════════════════
elif view_mode == "Planner":
    from routing import calculate_cost as _plan_calc_cost
    from config import COOLED_CARGO, CARGO_REVENUE_MAP, PRIORITY_REVENUE_MULTIPLIER

    _plan_company = next(c for c in company_data["companies"] if c["id"] == planner_company)
    _plan_drivers = [dict(d) for d in company_data["drivers"].get(planner_company, [])]
    _plan_trucks = [dict(t) for t in company_data["trucks"].get(planner_company, [])]
    _cost_params = dict(st.session_state.cost_params)

    # ── Gather all non-delivered shipments for this company ──
    _comp_shipments = [
        s for s in shipments
        if s.get("company_id") == planner_company and s.get("status") != "Delivered"
    ]

    _now_dt = _now()

    # ── Focus label & icon ──
    _focus_icon = {"Balanced": "&#9878;", "Profit Maximization": "&#9733;", "Reputation (On-Time)": "&#9201;"}.get(planner_focus, "&#9878;")
    _focus_pill = {"Balanced": "pill-purple", "Profit Maximization": "pill-green", "Reputation (On-Time)": "pill-blue"}.get(planner_focus, "pill-purple")

    # ── Header ──
    st.markdown(f"""
    <div class="company-header">
        <div>
            <div class="ch-name">Shipment Dispatch Planner</div>
            <div class="ch-detail">{_plan_company["name"]} &bull; {_plan_company.get("specialization", "")} &bull; {len(_comp_shipments)} pending orders &bull; via {_plan_company.get("erp_system", "ERP")}</div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;">
            <span class="pill {_focus_pill}">{_focus_icon} {planner_focus}</span>
            <span class="pill pill-purple">{len(_plan_drivers)} Drivers &bull; {len(_plan_trucks)} Trucks</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not _comp_shipments:
        st.markdown(
            '<div class="panel" style="text-align:center;padding:40px;color:var(--text-2);">'
            'No pending shipments for this company. All deliveries are complete.</div>',
            unsafe_allow_html=True)
    else:
        # ══════════════════════════════════════════════════════════
        # CRITICALITY SCORING ENGINE
        # ══════════════════════════════════════════════════════════
        _priority_factor_map = {"Critical": 100, "High": 60, "Standard": 30}

        # Collect revenues for normalization
        _all_revs = [s.get("estimated_revenue", 0) for s in _comp_shipments]
        _min_rev = min(_all_revs) if _all_revs else 0
        _max_rev = max(_all_revs) if _all_revs else 1
        _rev_range = _max_rev - _min_rev if _max_rev > _min_rev else 1

        # Max buffer for normalization (hrs)
        _max_buffer = 48.0

        _scored = []
        for _s in _comp_shipments:
            # Buffer hours
            _deadline_dt = _s.get("deadline")
            if _deadline_dt and hasattr(_deadline_dt, "replace"):
                _deadline_naive = _deadline_dt.replace(tzinfo=None) if _deadline_dt.tzinfo else _deadline_dt
            else:
                _deadline_naive = _now_dt.replace(tzinfo=None) + timedelta(hours=24)
            _now_naive = _now_dt.replace(tzinfo=None) if _now_dt.tzinfo else _now_dt

            _route = _s.get("route", {})
            _dur_hrs = _route.get("duration_hrs", 6)
            _dist_km = _route.get("distance_km", 400)
            _dispatch_time = _now_naive + timedelta(hours=plan_loading_hrs)
            _eta = _dispatch_time + timedelta(hours=_dur_hrs)
            _buffer_hrs = (_deadline_naive - _eta).total_seconds() / 3600

            # Urgency factor: 0 (lots of buffer) to 100 (no buffer / late)
            _urgency_f = max(0, min(100, (_max_buffer - _buffer_hrs) / _max_buffer * 100))

            # Revenue factor
            _est_rev = _s.get("estimated_revenue", 0)
            _revenue_f = ((_est_rev - _min_rev) / _rev_range) * 100

            # Priority factor
            _priority_f = _priority_factor_map.get(_s.get("priority", "Standard"), 30)

            # Perishable factor
            _is_cooled = _s.get("cargo", "") in COOLED_CARGO
            _perishable_f = 100 if _is_cooled else 0

            # On-time reputation bonus: extra urgency for tight buffers
            _ontime_f = max(0, min(100, (8 - _buffer_hrs) / 8 * 100)) if _buffer_hrs < 8 else 0

            # Weighted average
            _total_w = w_urgency + w_revenue + w_priority + w_perishable + w_ontime
            if _total_w > 0:
                _score = (
                    _urgency_f * w_urgency
                    + _revenue_f * w_revenue
                    + _priority_f * w_priority
                    + _perishable_f * w_perishable
                    + _ontime_f * w_ontime
                ) / _total_w
            else:
                _score = 50

            # ── Dynamic Pricing ──
            if plan_urgency_premium:
                if _buffer_hrs < 0:
                    _urg_mult = 1.50
                elif _buffer_hrs < 2:
                    _urg_mult = 1.35
                elif _buffer_hrs < 4:
                    _urg_mult = 1.25
                elif _buffer_hrs < 8:
                    _urg_mult = 1.15
                else:
                    _urg_mult = 1.0 + plan_base_margin / 100
            else:
                _urg_mult = 1.0 + plan_base_margin / 100

            # Cost calculation
            _base_cost = _plan_calc_cost(_dist_km, _dur_hrs, _cost_params)
            _cooled_extra = _dist_km * _cost_params["cooled_surcharge_per_km"] if _is_cooled else 0
            _total_cost = _base_cost["total"] + _cooled_extra
            _price = round(_total_cost * _urg_mult, 2)
            _profit = round(_price - _total_cost, 2)

            _scored.append({
                "shipment": _s,
                "id": _s["id"],
                "order_ref": _s.get("order_ref", ""),
                "customer_ref": _s.get("customer_ref", ""),
                "customer_name": _s.get("customer_name", ""),
                "cargo": _s.get("cargo", "Unknown"),
                "priority": _s.get("priority", "Standard"),
                "origin": _s.get("port", "Unknown"),
                "destination": _s.get("destination", "Unknown"),
                "distance_km": _dist_km,
                "duration_hrs": _dur_hrs,
                "buffer_hrs": round(_buffer_hrs, 1),
                "score": round(_score, 1),
                "urgency_mult": round(_urg_mult, 2),
                "cost": round(_total_cost, 2),
                "price": _price,
                "profit": _profit,
                "est_revenue": _est_rev,
                "is_cooled": _is_cooled,
                "truck_type": "Cooled" if _is_cooled else "Regular",
                "dispatch_time": _dispatch_time,
                "eta": _eta,
                "deadline": _deadline_naive,
                "meets_deadline": _buffer_hrs >= 0,
                "origin_coords": _s.get("port_coords", {}),
                "dest_coords": _s.get("dest_coords", {}),
                "route_geom": _route.get("waypoints", []),
                "status": _s.get("status", "Unknown"),
                # Individual factor scores for tooltip
                "_urgency_f": round(_urgency_f, 1),
                "_revenue_f": round(_revenue_f, 1),
                "_priority_f": _priority_f,
                "_perishable_f": _perishable_f,
                "_ontime_f": round(_ontime_f, 1),
            })

        # Sort by criticality score (highest first)
        _scored.sort(key=lambda x: x["score"], reverse=True)

        # ══════════════════════════════════════════════════════════
        # TRUCK / DRIVER AUTO-ASSIGNMENT
        # ══════════════════════════════════════════════════════════
        _used_trucks = set()
        _used_drivers = set()
        _assigned = []
        _unassigned = []

        # Score drivers for ranking
        for _d in _plan_drivers:
            _d["_eff_score"] = round(
                _d["stats"]["on_time_pct"] * 0.4
                + (_d["stats"]["avg_rating"] / 5) * 100 * 0.3
                + min(100, _d["stats"]["km_per_month"] / 100) * 0.3, 1
            )

        for _si, _item in enumerate(_scored):
            # Find best truck: correct type, lowest mileage, not used
            _cand_trucks = [
                t for t in _plan_trucks
                if t["id"] not in _used_trucks
                and t["status"] != "maintenance"
                and t["type"] == _item["truck_type"]
            ]
            if not _cand_trucks:
                # Fallback: any available truck
                _cand_trucks = [
                    t for t in _plan_trucks
                    if t["id"] not in _used_trucks and t["status"] != "maintenance"
                ]
            _sel_truck = min(_cand_trucks, key=lambda t: t["mileage_km"]) if _cand_trucks else None

            # Find best driver: idle first, highest efficiency, not used
            _cand_drivers = [
                d for d in _plan_drivers
                if d["id"] not in _used_drivers
                and d["status"] != "off_duty"
            ]
            if not _cand_drivers:
                _cand_drivers = [
                    d for d in _plan_drivers
                    if d["id"] not in _used_drivers
                ]
            _cand_drivers.sort(key=lambda d: d.get("_eff_score", 0), reverse=True)
            _sel_driver = _cand_drivers[0] if _cand_drivers else None

            if _sel_truck and _sel_driver:
                _used_trucks.add(_sel_truck["id"])
                _used_drivers.add(_sel_driver["id"])
                _item["assigned_truck"] = _sel_truck
                _item["assigned_driver"] = _sel_driver
                _item["rank"] = len(_assigned) + 1
                _assigned.append(_item)
            else:
                _item["assigned_truck"] = None
                _item["assigned_driver"] = None
                _item["rank"] = None
                _item["_missing_truck"] = _sel_truck is None
                _item["_missing_driver"] = _sel_driver is None
                _unassigned.append(_item)

        # Profit-floor filter
        _below_floor = [a for a in _assigned if a["profit"] < plan_profit_floor]

        # ══════════════════════════════════════════════════════════
        # 0. PRICING SUMMARY KPI STRIP
        # ══════════════════════════════════════════════════════════
        _total_revenue = sum(a["price"] for a in _assigned)
        _total_cost = sum(a["cost"] for a in _assigned)
        _total_margin = _total_revenue - _total_cost
        _avg_mult = sum(a["urgency_mult"] for a in _assigned) / len(_assigned) if _assigned else 0
        _on_time_count = sum(1 for a in _assigned if a["meets_deadline"])
        _on_time_pct = (_on_time_count / len(_assigned) * 100) if _assigned else 0

        _margin_pct_total = (_total_margin / _total_cost * 100) if _total_cost > 0 else 0
        _kpi_cols = st.columns(6)
        _kpi_data = [
            ("Your Cost", f"{_total_cost:,.0f}", "SAR", "var(--red)"),
            ("Client Price", f"{_total_revenue:,.0f}", "SAR", "var(--green)"),
            ("Your Profit", f"{_total_margin:,.0f}", "SAR", "var(--accent)"),
            ("Margin %", f"{_margin_pct_total:.1f}%", "", "var(--amber)"),
            ("On-Time Rate", f"{_on_time_pct:.0f}%", "", "var(--blue)"),
            ("Unassigned", f"{len(_unassigned)}", "shipments", "var(--red)" if _unassigned else "var(--green)"),
        ]
        for _ki, (_kl, _kv, _ku, _kc) in enumerate(zip(_kpi_cols, _kpi_data)):
            with _kl:
                st.markdown(f"""
                <div class="panel" style="text-align:center;padding:12px 8px;">
                    <div style="font-size:0.68rem;color:var(--text-2);text-transform:uppercase;letter-spacing:1px;">{_kv[0]}</div>
                    <div style="font-size:1.3rem;font-weight:800;color:{_kv[3]};">{_kv[1]} <span style="font-size:0.65rem;color:var(--text-2);">{_kv[2]}</span></div>
                </div>""", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════
        # 1. DISPATCH PRIORITY RANKING TABLE
        # ══════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Dispatch Priority Ranking</div>', unsafe_allow_html=True)

        _table_header = """<div class="panel" style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:0.76rem;">
        <thead><tr style="border-bottom:2px solid var(--border);">
            <th style="padding:8px 6px;text-align:center;color:var(--text-2);width:40px;">Rank</th>
            <th style="padding:8px 6px;text-align:left;color:var(--text-2);">Order Ref</th>
            <th style="padding:8px 6px;text-align:left;color:var(--text-2);">Customer</th>
            <th style="padding:8px 6px;text-align:left;color:var(--text-2);">Cargo</th>
            <th style="padding:8px 6px;text-align:center;color:var(--text-2);">Priority</th>
            <th style="padding:8px 6px;text-align:left;color:var(--text-2);">Route</th>
            <th style="padding:8px 6px;text-align:right;color:var(--text-2);">Buffer</th>
            <th style="padding:8px 6px;text-align:right;color:var(--text-2);">Score</th>
            <th style="padding:8px 6px;text-align:right;color:var(--text-2);">Your Cost</th>
            <th style="padding:8px 6px;text-align:right;color:var(--text-2);">Client Price</th>
            <th style="padding:8px 6px;text-align:right;color:var(--text-2);">Profit</th>
            <th style="padding:8px 6px;text-align:right;color:var(--text-2);">Mult</th>
            <th style="padding:8px 6px;text-align:left;color:var(--text-2);">Driver</th>
        </tr></thead><tbody>"""

        _table_rows = ""
        for _item in _assigned:
            _sc = _item["score"]
            if _sc > 75:
                _row_bg = "rgba(239,68,68,0.08)"
                _score_color = "var(--red)"
            elif _sc > 50:
                _row_bg = "rgba(245,158,11,0.08)"
                _score_color = "var(--amber)"
            else:
                _row_bg = "transparent"
                _score_color = "var(--green)"

            _pri_pill = {"Critical": "pill-red", "High": "pill-amber", "Standard": "pill-green"}.get(_item["priority"], "pill-green")
            _buf_color = "var(--green)" if _item["buffer_hrs"] > 4 else ("var(--amber)" if _item["buffer_hrs"] > 0 else "var(--red)")
            _drv = _item.get("assigned_driver", {})
            _trk = _item.get("assigned_truck", {})

            _table_rows += f"""<tr style="background:{_row_bg};border-bottom:1px solid var(--border);">
                <td style="padding:8px 6px;text-align:center;font-weight:800;color:var(--accent);font-size:0.9rem;">{_item["rank"]}</td>
                <td style="padding:8px 6px;color:var(--text-0);font-weight:600;font-size:0.72rem;">{_item["order_ref"] or _item["id"]}</td>
                <td style="padding:8px 6px;color:var(--text-1);font-size:0.72rem;">{_item["customer_name"]}</td>
                <td style="padding:8px 6px;color:var(--text-1);font-size:0.74rem;">{"&#10052; " if _item["is_cooled"] else ""}{_item["cargo"]}</td>
                <td style="padding:8px 6px;text-align:center;"><span class="pill {_pri_pill}" style="font-size:0.65rem;">{_item["priority"]}</span></td>
                <td style="padding:8px 6px;color:var(--text-1);font-size:0.72rem;">{_item["origin"].split("(")[0].strip()} &#10132; {_item["destination"]}</td>
                <td style="padding:8px 6px;text-align:right;color:{_buf_color};font-weight:700;">{_item["buffer_hrs"]:.1f}h</td>
                <td style="padding:8px 6px;text-align:right;color:{_score_color};font-weight:800;font-size:0.85rem;">{_sc:.0f}</td>
                <td style="padding:8px 6px;text-align:right;color:var(--text-0);">{_item["cost"]:,.0f}</td>
                <td style="padding:8px 6px;text-align:right;color:var(--green);font-weight:700;">{_item["price"]:,.0f}</td>
                <td style="padding:8px 6px;text-align:right;color:var(--accent);font-weight:700;">{_item["profit"]:,.0f}</td>
                <td style="padding:8px 6px;text-align:right;color:var(--amber);font-weight:600;">{_item["urgency_mult"]:.2f}x</td>
                <td style="padding:8px 6px;color:var(--text-1);font-size:0.72rem;">{_drv.get("name", "—")}</td>
            </tr>"""

        st.markdown(_table_header + _table_rows + "</tbody></table></div>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════
        # 2. DISPATCH ROUTE MAP
        # ══════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Dispatch Route Map</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="display:flex;gap:16px;margin-bottom:8px;">'
            '<span style="font-size:0.75rem;color:#ef4444;font-weight:600;">&#9473;&#9473; Rank 1-3 (Immediate)</span>'
            '<span style="font-size:0.75rem;color:#f59e0b;font-weight:600;">&#9473;&#9473; Rank 4-6 (Soon)</span>'
            '<span style="font-size:0.75rem;color:#3b82f6;font-weight:600;">&#9473;&#9473; Rank 7+ (Standard)</span>'
            '</div>', unsafe_allow_html=True,
        )

        _plan_map = create_base_map()
        _plan_all_pts = []

        for _item in _assigned:
            _rank = _item["rank"]
            if _rank <= 3:
                _rcolor = "#ef4444"
            elif _rank <= 6:
                _rcolor = "#f59e0b"
            else:
                _rcolor = "#3b82f6"

            _geom = _item["route_geom"]
            if _geom and len(_geom) >= 2:
                folium.PolyLine(
                    locations=_geom,
                    color=_rcolor,
                    weight=3 if _rank <= 3 else 2,
                    opacity=0.8 if _rank <= 6 else 0.5,
                    tooltip=f'#{_rank} {_item["id"]} — {_item["origin"].split("(")[0].strip()} &#10132; {_item["destination"]} — Score: {_item["score"]:.0f}',
                ).add_to(_plan_map)
                _plan_all_pts.extend(_geom)

            # Numbered circle marker at origin
            _oc = _item.get("origin_coords", {})
            if _oc.get("lat") and _oc.get("lon"):
                folium.CircleMarker(
                    location=[_oc["lat"], _oc["lon"]],
                    radius=12 if _rank <= 3 else 9,
                    color=_rcolor,
                    fill=True,
                    fill_color=_rcolor,
                    fill_opacity=0.9,
                    tooltip=f'#{_rank} {_item["id"]} — {_item["cargo"]} — Score: {_item["score"]:.0f}',
                ).add_to(_plan_map)
                folium.Marker(
                    location=[_oc["lat"], _oc["lon"]],
                    icon=folium.DivIcon(html=f'<div style="font-size:10px;font-weight:900;color:#fff;text-align:center;line-height:24px;">{_rank}</div>'),
                ).add_to(_plan_map)

        if _plan_all_pts:
            fit_map_bounds(_plan_map, _plan_all_pts)

        st_folium(_plan_map, use_container_width=True, height=420, key="planner_dispatch_map")

        # ══════════════════════════════════════════════════════════
        # 3. DRIVER DELIVERY SCHEDULE
        # ══════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Driver Delivery Schedule</div>', unsafe_allow_html=True)

        # Group assignments by driver
        _driver_schedule = {}
        for _item in _assigned:
            _drv = _item.get("assigned_driver")
            if _drv:
                _did = _drv["id"]
                if _did not in _driver_schedule:
                    _driver_schedule[_did] = {"driver": _drv, "loads": []}
                _driver_schedule[_did]["loads"].append(_item)

        _sched_html = ""
        for _did, _info in _driver_schedule.items():
            _drv = _info["driver"]
            _eff = _drv.get("_eff_score", 0)
            _eff_color = "var(--green)" if _eff >= 85 else ("var(--amber)" if _eff >= 70 else "var(--red)")
            _loads = _info["loads"]

            _load_items = ""
            for _li, _load in enumerate(_loads):
                _buf_c = "var(--green)" if _load["buffer_hrs"] > 4 else ("var(--amber)" if _load["buffer_hrs"] > 0 else "var(--red)")
                _pri_c = {"Critical": "var(--red)", "High": "var(--amber)", "Standard": "var(--text-1)"}.get(_load["priority"], "var(--text-1)")
                _depart_str = _load["dispatch_time"].strftime("%H:%M")
                _load_items += (
                    f'<div style="display:flex;align-items:center;gap:12px;padding:6px 0;'
                    f'border-bottom:1px solid var(--border);">'
                    f'<span style="font-weight:800;color:var(--accent);width:20px;">{_li+1}.</span>'
                    f'<span style="color:var(--text-0);font-weight:600;min-width:140px;">{_load["order_ref"] or _load["id"]}</span>'
                    f'<span style="color:var(--text-1);font-size:0.78rem;">&#10132; {_load["destination"]}</span>'
                    f'<span style="color:{_pri_c};font-size:0.72rem;font-weight:600;">{_load["priority"]}</span>'
                    f'<span style="color:{_buf_c};font-size:0.78rem;font-weight:600;">{_load["buffer_hrs"]:.1f}h buffer</span>'
                    f'<span style="color:var(--text-2);font-size:0.78rem;margin-left:auto;">Depart {_depart_str}</span>'
                    f'</div>'
                )

            _sched_html += (
                f'<div class="panel" style="margin-bottom:10px;">'
                f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">'
                f'<span style="font-weight:700;color:var(--text-0);">{_drv["name"]}</span>'
                f'<span style="font-size:0.75rem;color:{_eff_color};font-weight:700;">Score: {_eff}</span>'
                f'<span style="font-size:0.72rem;color:var(--text-2);">{_drv.get("phone", "")}</span>'
                f'<span style="font-size:0.72rem;color:var(--text-2);margin-left:auto;">{len(_loads)} load{"s" if len(_loads) != 1 else ""}</span>'
                f'</div>{_load_items}</div>'
            )

        if _sched_html:
            st.markdown(_sched_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="panel" style="text-align:center;color:var(--text-2);padding:20px;">No drivers assigned.</div>', unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════
        # 4. FLEET ASSIGNMENT SUMMARY TABLE
        # ══════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Fleet Assignment Summary</div>', unsafe_allow_html=True)

        _fleet_header = """<div class="panel" style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:0.76rem;">
        <thead><tr style="border-bottom:2px solid var(--border);">
            <th style="padding:8px 6px;text-align:left;color:var(--text-2);">Driver</th>
            <th style="padding:8px 6px;text-align:left;color:var(--text-2);">Truck</th>
            <th style="padding:8px 6px;text-align:left;color:var(--text-2);">Order Ref</th>
            <th style="padding:8px 6px;text-align:left;color:var(--text-2);">Customer</th>
            <th style="padding:8px 6px;text-align:left;color:var(--text-2);">Cargo</th>
            <th style="padding:8px 6px;text-align:left;color:var(--text-2);">Route</th>
            <th style="padding:8px 6px;text-align:right;color:var(--text-2);">Depart</th>
            <th style="padding:8px 6px;text-align:right;color:var(--text-2);">ETA</th>
            <th style="padding:8px 6px;text-align:right;color:var(--text-2);">Price (SAR)</th>
        </tr></thead><tbody>"""

        _fleet_rows = ""
        for _item in _assigned:
            _drv = _item.get("assigned_driver", {})
            _trk = _item.get("assigned_truck", {})
            _dep_str = _item["dispatch_time"].strftime("%b %d, %H:%M")
            _eta_str = _item["eta"].strftime("%b %d, %H:%M")

            _fleet_rows += f"""<tr style="border-bottom:1px solid var(--border);">
                <td style="padding:8px 6px;color:var(--text-0);font-weight:600;">{_drv.get("name", "—")}</td>
                <td style="padding:8px 6px;color:var(--text-1);font-size:0.74rem;">{_trk.get("id", "—")} <span style="color:var(--text-2);">({_trk.get("type", "")})</span></td>
                <td style="padding:8px 6px;color:var(--accent);font-weight:600;font-size:0.72rem;">{_item["order_ref"] or _item["id"]}</td>
                <td style="padding:8px 6px;color:var(--text-1);font-size:0.72rem;">{_item["customer_name"]}</td>
                <td style="padding:8px 6px;color:var(--text-1);">{"&#10052; " if _item["is_cooled"] else ""}{_item["cargo"]}</td>
                <td style="padding:8px 6px;color:var(--text-1);font-size:0.72rem;">{_item["origin"].split("(")[0].strip()} &#10132; {_item["destination"]}</td>
                <td style="padding:8px 6px;text-align:right;color:var(--text-0);">{_dep_str}</td>
                <td style="padding:8px 6px;text-align:right;color:var(--text-0);">{_eta_str}</td>
                <td style="padding:8px 6px;text-align:right;color:var(--green);font-weight:700;">{_item["price"]:,.0f}</td>
            </tr>"""

        st.markdown(_fleet_header + _fleet_rows + "</tbody></table></div>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════
        # 5. HIRING / CAPACITY RECOMMENDATIONS
        # ══════════════════════════════════════════════════════════
        if _unassigned:
            st.markdown('<div class="sec-title">Capacity Recommendations</div>', unsafe_allow_html=True)

            _need_cooled_trucks = sum(1 for u in _unassigned if u.get("_missing_truck") and u["is_cooled"])
            _need_regular_trucks = sum(1 for u in _unassigned if u.get("_missing_truck") and not u["is_cooled"])
            _need_drivers = sum(1 for u in _unassigned if u.get("_missing_driver"))
            _at_risk_rev = sum(u["est_revenue"] for u in _unassigned)

            _rec_html = '<div class="panel">'
            _rec_html += (
                f'<div class="alert-strip critical" style="margin-bottom:12px;">'
                f'<span class="alert-icon">&#9888;</span>'
                f'<span><strong>{len(_unassigned)} shipment{"s" if len(_unassigned) != 1 else ""} unassigned</strong> '
                f'due to insufficient capacity. Estimated revenue at risk: <strong>{_at_risk_rev:,.0f} SAR</strong></span></div>'
            )

            if _need_drivers > 0:
                _rec_html += (
                    f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border);">'
                    f'<span style="font-size:1.1rem;">&#9823;</span>'
                    f'<span style="color:var(--text-0);font-weight:600;">Hire {_need_drivers} additional driver{"s" if _need_drivers != 1 else ""}</span>'
                    f'</div>'
                )
            if _need_cooled_trucks > 0:
                _rec_html += (
                    f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border);">'
                    f'<span style="font-size:1.1rem;">&#10052;</span>'
                    f'<span style="color:var(--text-0);font-weight:600;">Acquire {_need_cooled_trucks} Cooled truck{"s" if _need_cooled_trucks != 1 else ""}</span>'
                    f'</div>'
                )
            if _need_regular_trucks > 0:
                _rec_html += (
                    f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border);">'
                    f'<span style="font-size:1.1rem;">&#9951;</span>'
                    f'<span style="color:var(--text-0);font-weight:600;">Acquire {_need_regular_trucks} Regular truck{"s" if _need_regular_trucks != 1 else ""}</span>'
                    f'</div>'
                )

            # List unassigned shipments
            _rec_html += '<div style="margin-top:12px;font-size:0.72rem;color:var(--text-2);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Unassigned Shipments</div>'
            for _u in _unassigned:
                _ubuf_c = "var(--red)" if _u["buffer_hrs"] < 0 else ("var(--amber)" if _u["buffer_hrs"] < 4 else "var(--green)")
                _rec_html += (
                    f'<div style="display:flex;align-items:center;gap:10px;padding:4px 0;font-size:0.78rem;">'
                    f'<span style="color:var(--accent);font-weight:600;">{_u["id"]}</span>'
                    f'<span style="color:var(--text-1);">{_u["cargo"]}</span>'
                    f'<span style="color:var(--text-1);">{_u["origin"].split("(")[0].strip()} &#10132; {_u["destination"]}</span>'
                    f'<span style="color:{_ubuf_c};font-weight:600;">{_u["buffer_hrs"]:.1f}h buffer</span>'
                    f'<span style="color:var(--text-2);margin-left:auto;">Score: {_u["score"]:.0f}</span>'
                    f'</div>'
                )
            _rec_html += '</div>'
            st.markdown(_rec_html, unsafe_allow_html=True)

        # ── Profit floor warnings ──
        if _below_floor and plan_profit_floor > 0:
            st.markdown(
                f'<div class="alert-strip critical" style="margin-top:8px;">'
                f'<span class="alert-icon">&#9733;</span>'
                f'<span><strong>{len(_below_floor)} shipment{"s" if len(_below_floor) != 1 else ""} below minimum profit floor</strong> '
                f'of {plan_profit_floor:,} SAR. Consider raising prices or declining these loads.</span></div>',
                unsafe_allow_html=True,
            )

        # ══════════════════════════════════════════════════════════
        # 6. FOCUS-AWARE RECOMMENDATIONS
        # ══════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Strategy Recommendations</div>', unsafe_allow_html=True)

        _late_count = sum(1 for a in _assigned if not a["meets_deadline"])
        _high_margin = [a for a in _assigned if a["profit"] > 1000]

        _strat_html = '<div class="panel">'
        if planner_focus == "Profit Maximization":
            _strat_html += (
                f'<div style="margin-bottom:8px;font-weight:700;color:var(--green);">&#9733; Profit Maximization Mode</div>'
                f'<div style="font-size:0.82rem;color:var(--text-1);margin-bottom:6px;">'
                f'Total margin: <strong style="color:var(--green);">{_total_margin:,.0f} SAR</strong> across {len(_assigned)} shipments. '
                f'{len(_high_margin)} shipment{"s" if len(_high_margin) != 1 else ""} exceed 1,000 SAR profit.</div>'
            )
            if _late_count > 0:
                _strat_html += (
                    f'<div style="font-size:0.82rem;color:var(--amber);">'
                    f'&#9888; {_late_count} shipment{"s" if _late_count != 1 else ""} may miss deadline. '
                    f'Accepting late delivery risk for higher margin.</div>'
                )
        elif planner_focus == "Reputation (On-Time)":
            _strat_html += (
                f'<div style="margin-bottom:8px;font-weight:700;color:var(--blue);">&#9201; Reputation / On-Time Mode</div>'
                f'<div style="font-size:0.82rem;color:var(--text-1);margin-bottom:6px;">'
                f'On-time delivery rate: <strong style="color:{"var(--green)" if _on_time_pct >= 90 else "var(--amber)"};">{_on_time_pct:.0f}%</strong>. '
                f'Prioritizing deadline compliance over margin.</div>'
            )
            if _late_count > 0:
                _strat_html += (
                    f'<div style="font-size:0.82rem;color:var(--red);">'
                    f'&#9888; {_late_count} shipment{"s" if _late_count != 1 else ""} still at risk despite priority ordering. '
                    f'Consider additional capacity or route changes.</div>'
                )
        else:
            _strat_html += (
                f'<div style="margin-bottom:8px;font-weight:700;color:var(--accent);">&#9878; Balanced Mode</div>'
                f'<div style="font-size:0.82rem;color:var(--text-1);margin-bottom:6px;">'
                f'Balancing margin ({_total_margin:,.0f} SAR) with on-time delivery ({_on_time_pct:.0f}%). '
                f'{len(_assigned)} dispatched, {len(_unassigned)} pending capacity.</div>'
            )

        _strat_html += '</div>'
        st.markdown(_strat_html, unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════
        # 7. MONITOR IN MICRO VIEW BUTTON
        # ══════════════════════════════════════════════════════════
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        _mon_cols = st.columns([3, 1])
        with _mon_cols[1]:
            if st.button("Monitor Live in Micro View", key="planner_to_micro", use_container_width=True):
                st.session_state.view_mode = "Micro"
                st.session_state.micro_sb_company = planner_company
                st.rerun()
