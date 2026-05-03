import streamlit as st
import pandas as pd
from weather_logic import WeatherLogic, load_config
import os
import io
import datetime
import math
from dotenv import load_dotenv
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import requests
import folium
from streamlit_folium import st_folium

load_dotenv()

def resource_path(relative_path):
    """Get absolute path to resource, works for local and Streamlit Cloud."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_base64_image(image_path):
    abs_path = resource_path(image_path)
    if os.path.exists(abs_path):
        with open(abs_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

st.set_page_config(page_title="Weather Reporter", layout="wide")

# ─── UI Styling ──────────────────────────────────────────────────────────────
STYLE_CODE = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
    .stApp {
        background: linear-gradient(135deg, #000000, #000B58);
        color: #d1d9e6;
        font-family: 'Inter', sans-serif;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #e8f0fe;
    }
    div.stButton > button, div.stDownloadButton > button {
        background: linear-gradient(135deg, #0072ff, #00c6ff);
        color: white;
        border: 1px solid transparent;
        border-radius: 10px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        transition: all 0.2s ease-out;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background: linear-gradient(135deg, #005bcc, #00a3cc) !important;
        border: 1px solid #00c6ff !important;
        color: white !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(0, 114, 255, 0.35);
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 22px 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0, 114, 255, 0.12);
        border-color: rgba(0, 198, 255, 0.15);
    }
    .glass-card .card-icon {
        font-size: 28px;
        margin-bottom: 4px;
        display: block;
        text-align: center;
    }
    .glass-card .card-label {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #8fa6c0;
        text-align: center;
        margin-bottom: 4px;
    }
    .glass-card .card-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 22px;
        font-weight: 700;
        color: #e8f0fe;
        text-align: center;
    }
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 1.4rem;
        font-weight: 700;
        color: #e8f0fe;
        margin-top: 40px;
        margin-bottom: 16px;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(0, 114, 255, 0.25);
    }
    .section-header svg {
        width: 26px;
        height: 26px;
        color: #00c6ff;
        flex-shrink: 0;
    }
    .gradient-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 198, 255, 0.3), transparent);
        margin: 36px 0;
        border: none;
    }
    div[data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 4px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    button[data-baseweb="tab"] {
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
        color: #8fa6c0 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #0072ff, #00c6ff) !important;
        color: white !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #e8f0fe !important;
    }
    .weather-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 18px;
        border-radius: 24px;
        background: rgba(0, 200, 255, 0.08);
        border: 1px solid rgba(0, 200, 255, 0.18);
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 500;
        color: #a0d8ff;
    }
    .weather-badge .live-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #00c6ff;
        animation: dot-blink 2s ease-in-out infinite;
    }
    @keyframes dot-blink {
        0%, 100% { opacity: 1; box-shadow: 0 0 4px #00c6ff; }
        50% { opacity: 0.3; box-shadow: none; }
    }
    .export-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px;
    }
    .export-card-title {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 16px;
        color: #e8f0fe;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .export-card-title svg {
        width: 20px; height: 20px;
        color: #00c6ff;
    }
    button:focus-visible, input:focus-visible, select:focus-visible {
        outline: 2px solid #00c6ff !important;
        outline-offset: 2px !important;
    }
    .skeleton-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 22px 20px;
        animation: pulse 1.5s ease-in-out infinite;
        height: 104px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 12px;
    }
    .skeleton-line {
        height: 12px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 6px;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
    }
    button[data-baseweb="tab"] {
        flex: 1 !important;
        justify-content: center !important;
        min-width: 150px !important;
        white-space: nowrap !important;
    }
</style>
"""
st.markdown(STYLE_CODE, unsafe_allow_html=True)


st.title("Weather Reporter")

@st.cache_resource
def get_weather_logic():
    # Increment this dummy variable to force Streamlit to clear cache and reload logic
    _force_cache_reload_v5 = 45
    api_key_owm = os.environ.get("OPENWEATHERMAP_API_KEY")
    if not api_key_owm:
        try:
            api_key_owm = st.secrets.get("OPENWEATHERMAP_API_KEY", "")
        except Exception:
            pass
    config = load_config()
    if not api_key_owm:
        api_key_owm = config.get("api_keys", {}).get("openweathermap", "") or config.get("api_key_openweathermap", "")
    return WeatherLogic(api_key=api_key_owm), config

@st.cache_data
def load_locations():
    """Load location list from config_LDC.json when present, otherwise fall back to locations.json."""
    import json
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "config_LDC.json"),
        os.path.join(base_dir, "locations.json")
    ]
    for loc_file in candidates:
        if os.path.exists(loc_file):
            try:
                with open(loc_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "locations" in data:
                    return data
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                continue
    return {"locations": {}, "default_location": "", "dashboard_locations": []}

logic, config_data = get_weather_logic()
locations_data = load_locations()


# ─── Session state init ───────────────────────────────────────────────────────
if "weather_data" not in st.session_state:
    st.session_state.weather_data = None
    st.session_state.location_info = None
    st.session_state.marine_data = None
    st.session_state.lat = None
    st.session_state.lon = None
    st.session_state.api_source = None
    st.session_state.ui_location_name = None
    st.session_state.fetch_error = False
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
    st.session_state.selected_lon = None
    st.session_state.selected_location_name = None
if "geocode_results" not in st.session_state:
    st.session_state.geocode_results = []


# ─── Location Section ─────────────────────────────────────────────────────────
st.header("Search Location")

locations_dict = locations_data.get("locations", {})
loc_names = list(locations_dict.keys())

if "map_clicked_lat" not in st.session_state:
    st.session_state.map_clicked_lat = None
    st.session_state.map_clicked_lon = None

tab1, tab2, tab3, tab4 = st.tabs(["📋 Saved Locations", "🔍 Search", "🗺️ Map", "📍 Coordinates"])

# ── Tab 1: Dropdown ────────────────────────────────────────────────────────────
with tab1:
    default_loc = locations_data.get("default_location", loc_names[0] if loc_names else "")
    default_idx = loc_names.index(default_loc) if default_loc in loc_names else 0
    selected_from_list = st.selectbox("Select location:", loc_names, index=default_idx)
    if st.button("Use this location", key="btn_list", use_container_width=True):
        coords = locations_dict[selected_from_list]['coords']
        st.session_state.selected_lat = coords[0]
        st.session_state.selected_lon = coords[1]
        st.session_state.selected_location_name = selected_from_list
        st.success(f"✅ Selected: **{selected_from_list}** ({coords[0]:.4f}, {coords[1]:.4f})")

    # Auto-select default on very first load (no location chosen yet)
    if st.session_state.selected_lat is None and loc_names:
        fallback = default_loc if default_loc in locations_dict else loc_names[0]
        coords = locations_dict[fallback]['coords']
        st.session_state.selected_lat = coords[0]
        st.session_state.selected_lon = coords[1]
        st.session_state.selected_location_name = fallback

# ── Tab 2: Geocoding Search ────────────────────────────────────────────────────
with tab2:
    search_query = st.text_input("Enter location name:", placeholder="e.g. Vung Tau, Ha Noi, Ho Chi Minh City...")
    if st.button("🔍 Search", key="btn_search", use_container_width=True):
        if search_query.strip():
            with st.spinner("Searching..."):
                try:
                    resp = requests.get(
                        "https://geocoding-api.open-meteo.com/v1/search",
                        params={"name": search_query, "count": 5, "language": "en", "format": "json"},
                        timeout=8
                    )
                    data = resp.json()
                    st.session_state.geocode_results = data.get("results", [])
                except Exception as e:
                    st.error(f"Search error: {e}")
                    st.session_state.geocode_results = []
        else:
            st.warning("Please enter a location name.")

    if st.session_state.geocode_results:
        options = [
            f"{r.get('name', '')}, {r.get('admin1', '')}, {r.get('country', '')} "
            f"({r['latitude']:.4f}, {r['longitude']:.4f})"
            for r in st.session_state.geocode_results
        ]
        chosen_idx = st.radio("Select a result:", range(len(options)), format_func=lambda i: options[i])
        if st.button("✅ Confirm this location", key="btn_confirm_search", use_container_width=True):
            r = st.session_state.geocode_results[chosen_idx]
            st.session_state.selected_lat = r["latitude"]
            st.session_state.selected_lon = r["longitude"]
            place_name = f"{r.get('name','')}, {r.get('country','')}"
            st.session_state.selected_location_name = place_name
            st.success(f"✅ Selected: **{place_name}** ({r['latitude']:.4f}, {r['longitude']:.4f})")

# ── Tab 3: Interactive Map ─────────────────────────────────────────────────────
with tab3:
    st.caption("Click anywhere on the map to get coordinates. Then confirm to use that location.")
    init_lat = st.session_state.selected_lat or 10.8
    init_lon = st.session_state.selected_lon or 106.7
    m = folium.Map(location=[init_lat, init_lon], zoom_start=6, tiles="OpenStreetMap")
    # Red marker = currently confirmed location
    if st.session_state.selected_lat:
        folium.Marker(
            [st.session_state.selected_lat, st.session_state.selected_lon],
            tooltip=f"✅ Confirmed: {st.session_state.selected_location_name or 'Selected location'}",
            icon=folium.Icon(color="red", icon="ok-sign")
        ).add_to(m)
    # Blue marker = last clicked point (pending confirmation)
    if st.session_state.map_clicked_lat:
        folium.Marker(
            [st.session_state.map_clicked_lat, st.session_state.map_clicked_lon],
            tooltip=f"📍 Clicked: {st.session_state.map_clicked_lat}, {st.session_state.map_clicked_lon}",
            icon=folium.Icon(color="blue", icon="map-marker")
        ).add_to(m)

    map_result = st_folium(m, height=420, width="100%", returned_objects=["last_clicked"])

    # ── Detect new click → persist in session_state → rerun to show blue marker ──
    if map_result and map_result.get("last_clicked"):
        clicked = map_result["last_clicked"]
        clat = round(clicked["lat"], 5)
        clon = round(clicked["lng"], 5)
        if (clat, clon) != (st.session_state.map_clicked_lat, st.session_state.map_clicked_lon):
            st.session_state.map_clicked_lat = clat
            st.session_state.map_clicked_lon = clon
            st.rerun()

    # ── Coordinate summary + confirm button (reads from session_state, survives rerun) ──
    if st.session_state.map_clicked_lat:
        clat = st.session_state.map_clicked_lat
        clon = st.session_state.map_clicked_lon
        st.markdown("---")
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.info(
                f"📍 **Clicked:** Lat `{clat}` | Lon `{clon}`\n\n"
                f"✅ **Confirmed:** {st.session_state.selected_location_name or '—'} "
                f"(Lat `{st.session_state.selected_lat}`, Lon `{st.session_state.selected_lon}`)"
            )
        with col_btn:
            if st.button(f"✅ Use this location", key="btn_confirm_map", use_container_width=True):
                st.session_state.selected_lat = clat
                st.session_state.selected_lon = clon
                st.session_state.selected_location_name = f"Custom ({clat}, {clon})"
                st.session_state.map_clicked_lat = None
                st.session_state.map_clicked_lon = None
                st.success("✅ Location saved from map!")
    elif st.session_state.selected_lat:
        st.markdown("---")
        st.info(
            f"✅ **Confirmed location:** {st.session_state.selected_location_name} "
            f"| Lat `{st.session_state.selected_lat}` | Lon `{st.session_state.selected_lon}`"
        )


# ── Tab 4: Manual Coordinates ──────────────────────────────────────────────────
with tab4:
    st.caption("Enter coordinates manually — useful for offshore platforms or technical locations.")
    mc1, mc2 = st.columns(2)
    with mc1:
        manual_lat = st.number_input("Latitude:", min_value=-90.0, max_value=90.0,
                                     value=float(st.session_state.selected_lat or 10.8),
                                     step=0.0001, format="%.5f")
    with mc2:
        manual_lon = st.number_input("Longitude:", min_value=-180.0, max_value=180.0,
                                     value=float(st.session_state.selected_lon or 106.7),
                                     step=0.0001, format="%.5f")
    manual_name = st.text_input("Location name (optional):", placeholder="e.g. Platform X, Block Y...")
    if st.button("✅ Confirm coordinates", key="btn_manual", use_container_width=True):
        st.session_state.selected_lat = manual_lat
        st.session_state.selected_lon = manual_lon
        st.session_state.selected_location_name = manual_name.strip() or f"({manual_lat:.5f}, {manual_lon:.5f})"
        st.success(f"✅ Confirmed: **{st.session_state.selected_location_name}**")

# ── Confirmed location display + Fetch ────────────────────────────────────────
st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
if st.session_state.selected_lat:
    st.markdown(
        f"📍 **Selected location:** {st.session_state.selected_location_name} "
        f"| Lat: `{st.session_state.selected_lat}` | Lon: `{st.session_state.selected_lon}`"
    )

col_ds, col_btn = st.columns([2, 1])
with col_ds:
    data_source = st.radio("Select Data Source:",
                       ["Open-Meteo", "OpenWeatherMap", "MET Norway"],
                       index=0, horizontal=True)
with col_btn:
    fetch_btn = st.button("Fetch Data")

# ── Smart Hourly Caching ───────────────────────────────────────────────────────
# Open-Meteo updates forecasts on the hour. Instead of a fixed TTL, we include
# the current UTC hour in the cache key so data is automatically invalidated
# when the clock ticks to the next hour.  The TTL=3600 acts as a safety net.

def _current_hour_key():
    """Return a string like '2026-03-23T22' that changes every hour (UTC).
    Used as a cache-key component so Streamlit auto-invalidates at each hour."""
    now = datetime.datetime.utcnow()
    return now.strftime("%Y-%m-%dT%H")

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_weather(lat, lon, source, _hour_key):
    """Fetch weather data; _hour_key ensures cache refreshes every hour."""
    return logic.fetch_weather(lat, lon, source=source)

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_marine(lat, lon, timezone_str, _hour_key):
    """Fetch marine data; _hour_key ensures cache refreshes every hour."""
    return logic._fetch_marine_data_openmeteo(lat, lon, timezone_str)

# ── Fetch Logic ────────────────────────────────────────────────────────────────
if fetch_btn or (not st.session_state.weather_data and st.session_state.selected_lat and not st.session_state.fetch_error):
    lat = st.session_state.selected_lat
    lon = st.session_state.selected_lon
    location = st.session_state.selected_location_name
    with st.spinner("Fetching data..."):
        _ph = st.empty()
        with _ph.container():
            cols_ph = st.columns(4)
            for c in cols_ph:
                c.markdown("""
                <div class="skeleton-card">
                    <div class="skeleton-line" style="width: 70%;"></div>
                    <div class="skeleton-line" style="width: 40%;"></div>
                </div>
                """, unsafe_allow_html=True)
                
        try:
            w_data, l_info = get_cached_weather(lat, lon, data_source, _current_hour_key())
            st.session_state.fetch_error = False
        except Exception as fetch_err:
            import traceback
            st.error(f"Exception during fetch: {fetch_err}")
            print(f"FETCH EXCEPTION: {traceback.format_exc()}")
            w_data, l_info = None, None
            st.session_state.fetch_error = True
        
        m_data = None
        if w_data and l_info and l_info.get('timezone'):
            try:
                m_data = get_cached_marine(lat, lon, l_info['timezone'], _current_hour_key())
            except Exception as e:
                print(f"Marine data fetch failed: {e}")
                
        _ph.empty()
        
        if lat and lon and w_data:
            st.session_state.weather_data = w_data
            st.session_state.location_info = l_info
            st.session_state.marine_data = m_data
            st.session_state.lat = lat
            st.session_state.lon = lon
            st.session_state.api_source = data_source
            st.session_state.ui_location_name = location
            st.success("Data fetched successfully!")
        else:
            st.session_state.fetch_error = True
            err_detail = f"lat={lat}, lon={lon}, w_data type={type(w_data).__name__}"
            if w_data is not None:
                err_detail += f", w_data len={len(w_data) if hasattr(w_data, '__len__') else 'N/A'}"
            if l_info is not None and isinstance(l_info, dict):
                if '_error' in l_info:
                    err_msg = l_info['_error']
                    if '429' in err_msg or 'Too Many Requests' in err_msg:
                        st.warning("⚠️ **Open-Meteo API Rate Limit Exceeded** \n\nStreamlit Cloud shares IP addresses, so the free Open-Meteo limit (10,000 calls/day per IP) is often reached by other users. \n\n**Solution:** Please select '**OpenWeatherMap**' or '**MET Norway**' as your Data Source above.")
                    else:
                        st.error(f"Failed to fetch data from {data_source}. Error: {err_msg}")
                    err_detail += f", ERROR: {err_msg}"
                else:
                    err_detail += f", l_info keys={list(l_info.keys())}"
            else:
                err_detail += ", l_info=None"
            print(f"FETCH FAILED: {err_detail}")
            if "Rate Limit Exceeded" not in err_detail and "429" not in err_detail:
                st.error(f"Failed to fetch data. Debug: {err_detail}")




if st.session_state.weather_data:
    w_data = st.session_state.weather_data
    l_info = st.session_state.location_info
    
    # Middle Section
    # ── Current Weather Condition ──────────────────────────────────────────────────
    st.markdown('<div class="section-header"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.7-9h1.8a4.5 4.5 0 1 1 0 9Z"/></svg>Current Weather Condition</div>', unsafe_allow_html=True)
    
    # find closest hourly data to now
    import pytz
    try:
        local_tz = pytz.timezone(l_info.get('timezone', 'UTC'))
    except:
        local_tz = pytz.UTC
    now_local = datetime.datetime.now(local_tz)
    current_point = min(w_data, key=lambda x: abs(x['datetime_obj'] - now_local))

    # --- Local time display ---
    tz_name = l_info.get('timezone', 'UTC')
    utc_offset = now_local.strftime('%z')  # e.g. +0700
    utc_label = f"UTC{utc_offset[:3]}:{utc_offset[3:]}"  # e.g. UTC+07:00
    local_time_str = now_local.strftime("%H:%M, %d %b %Y")
    st.markdown(
        f'<div class="weather-badge"><span class="live-dot"></span>Local time: '
        f'<strong>{local_time_str}</strong> · {tz_name} ({utc_label})</div>',
        unsafe_allow_html=True
    )

    location_name = st.session_state.selected_location_name or l_info.get('name', 'Unknown Location')
    current_desc = current_point.get('description', '')
    if current_desc:
        st.markdown(
            f"<h4 style='color:#ffffff; margin-top:5px;'>{location_name} - {current_desc}</h4>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<h4 style='color:#ffffff; margin-top:5px;'>{location_name}</h4>",
            unsafe_allow_html=True
        )

    colC1, colC2, colC3, colC4 = st.columns(4)
    
    # 1. Temperature
    curr_temp = current_point.get('temperature')
    temp_val = f"{curr_temp:.1f}°C" if curr_temp is not None else "N/A"
    colC1.markdown(f'<div class="glass-card"><span class="card-icon"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ff6b6b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/></svg></span><div class="card-label">Temperature</div><div class="card-value">{temp_val}</div></div>', unsafe_allow_html=True)
    
    # 2. Wind Speed
    curr_wind = current_point.get('wind_speed')
    wind_val = f"{curr_wind:.1f} kt" if curr_wind is not None else "N/A"
    colC2.markdown(f'<div class="glass-card"><span class="card-icon"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#00c6ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/></svg></span><div class="card-label">Wind Speed</div><div class="card-value">{wind_val}</div></div>', unsafe_allow_html=True)
    
    # 3. Rain
    curr_rain = current_point.get('rain')
    rain_val = f"{curr_rain:.1f} mm" if curr_rain is not None else "N/A"
    colC3.markdown(f'<div class="glass-card"><span class="card-icon"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4dabf7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M16 14v6"/><path d="M8 14v6"/><path d="M12 16v6"/></svg></span><div class="card-label">Rain</div><div class="card-value">{rain_val}</div></div>', unsafe_allow_html=True)
    
    # 4. UV Index
    curr_uv = current_point.get('uv_index')
    uv_val = f"{curr_uv:.1f}" if curr_uv is not None else "N/A"
    colC4.markdown(f'<div class="glass-card"><span class="card-icon"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ffd43b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg></span><div class="card-label">UV Index</div><div class="card-value">{uv_val}</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    # ── Precipitation Map ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.106 5.553a2 2 0 0 0 1.788 0l3.659-1.83A1 1 0 0 1 21 4.619v12.764a1 1 0 0 1-.553.894l-4.553 2.277a2 2 0 0 1-1.788 0l-4.212-2.106a2 2 0 0 0-1.788 0l-3.659 1.83A1 1 0 0 1 3 19.381V6.618a1 1 0 0 1 .553-.894l4.553-2.277a2 2 0 0 1 1.788 0z"/><path d="M15 5.764v15"/><path d="M9 3.236v15"/></svg>Precipitation Map</div>', unsafe_allow_html=True)
    windy_url = f"https://embed.windy.com/embed2.html?lat={st.session_state.lat}&lon={st.session_state.lon}&zoom=5&level=surface&overlay=rain&product=ecmwf&menu=&message=&marker=1&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=default&metricTemp=default&radarRange=-1"
    
    logo_b64 = get_base64_image("Pictures/weather-report-logo.png")
    if logo_b64:
        windy_html = f"""
        <div style="position: relative; width: 100%; height: 500px; overflow: hidden; border-radius: 4px;">
            <iframe src="{windy_url}" width="100%" height="100%" frameborder="0" style="border:0; pointer-events: auto;"></iframe>
            <div style="position: absolute; top: 0; left: 50%; transform: translateX(-50%); z-index: 9999; display: flex; justify-content: center; align-items: center; pointer-events: none;">
                <img src="data:image/png;base64,{logo_b64}" style="width: 150px; height: 67.5px; object-fit: contain; border: none; background: none; display: block;">
            </div>
        </div>
        """
        st.components.v1.html(windy_html, height=500, scrolling=False)
    else:
        st.components.v1.iframe(windy_url, height=500, scrolling=True)
    
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    # ── Weather Forecast Summary ──────────────────────────────────────────────────
    if st.session_state.api_source == "Open-Meteo":
        summary_title = "Weather Forecast Summary - For Next 14 Days"
    elif st.session_state.api_source == "OpenWeatherMap":
        summary_title = "Weather Forecast Summary - For Next 05 Days"
    elif st.session_state.api_source == "MET Norway":
        summary_title = "Weather Forecast Summary - For Next 10 Days"
    else:
        summary_title = "Weather Forecast Summary"
        
    st.markdown(f'<div class="section-header"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="m19 9-5 5-4-4-3 3"/></svg>{summary_title}</div>', unsafe_allow_html=True)
    
    # Calculate summary from forecast data
    temp_vals = [item.get('temperature') for item in w_data if isinstance(item.get('temperature'), (int, float))]
    wind_vals = [item.get('wind_speed') for item in w_data if isinstance(item.get('wind_speed'), (int, float))]
    rain_vals = [item.get('rain') for item in w_data if isinstance(item.get('rain'), (int, float))]
    uv_vals = [item.get('uv_index') for item in w_data if isinstance(item.get('uv_index'), (int, float))]
    
    temp_min = f"{min(temp_vals):.1f}°C" if temp_vals else "N/A"
    temp_max = f"{max(temp_vals):.1f}°C" if temp_vals else "N/A"
    wind_min = f"{min(wind_vals):.1f}" if wind_vals else "N/A"
    wind_max = f"{max(wind_vals):.1f}" if wind_vals else "N/A"
    rain_max = f"{max(rain_vals):.1f} mm" if rain_vals else "N/A"
    uv_max = f"{max(uv_vals):.1f}" if uv_vals else "N/A"
    
    colS1, colS2, colS3, colS4 = st.columns(4)
    
    colS1.markdown(f'<div class="glass-card"><span class="card-icon"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ff6b6b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/></svg></span><div class="card-label">Temp (Min–Max)</div><div class="card-value">{temp_min} – {temp_max}</div></div>', unsafe_allow_html=True)
    
    colS2.markdown(f'<div class="glass-card"><span class="card-icon"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#00c6ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/></svg></span><div class="card-label">Wind (Min–Max)</div><div class="card-value">{wind_min} – {wind_max} kt</div></div>', unsafe_allow_html=True)
    
    colS3.markdown(f'<div class="glass-card"><span class="card-icon"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4dabf7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M16 14v6"/><path d="M8 14v6"/><path d="M12 16v6"/></svg></span><div class="card-label">Rain (Max)</div><div class="card-value">{rain_max}</div></div>', unsafe_allow_html=True)
    
    colS4.markdown(f'<div class="glass-card"><span class="card-icon"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ffd43b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg></span><div class="card-label">UV Index (Max)</div><div class="card-value">{uv_max}</div></div>', unsafe_allow_html=True)
    
    current_time_str = now_local.strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"**Location Info:** {l_info.get('name')} | **Timezone:** {l_info.get('timezone')} | **Sunrise:** {l_info.get('sunrise')} | **Sunset:** {l_info.get('sunset')} | **Local Time:** {current_time_str}")

    # Sidebar Table
    # Bottom Section
    st.markdown('<div class="section-header"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>Charts</div>', unsafe_allow_html=True)
    df = pd.DataFrame(w_data)

    def plot_custom_chart(df_plot, title, cols, colors, units=None, descriptions=None, use_secondary_y=False):
        # Ensure datetime is parsed
        if not pd.api.types.is_datetime64_any_dtype(df_plot.index):
            df_plot.index = pd.to_datetime(df_plot.index)
        
        if units is None:
            units = [''] * len(cols)
            
        if use_secondary_y and len(cols) == 2:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
        else:
            fig = go.Figure()
        
        # Build traces list, then sort by descending mean y so the highest
        # line on the chart always appears first in the unified hover tooltip
        traces = []
        max_val = -float('inf')
        for col, color, unit in zip(cols, colors, units):
            if col in df_plot.columns:
                unit_str = f' {unit}' if unit else ''
                mean_y = df_plot[col].mean()
                traces.append(dict(
                    col=col, color=color, mean_y=mean_y,
                    unit_str=unit_str, data=df_plot[col]
                ))
                local_max = df_plot[col].max()
                if local_max > max_val:
                    max_val = local_max
        
        # Sort descending by mean value so hover label order matches visual order
        traces.sort(key=lambda t: t['mean_y'], reverse=True)
        
        for t in traces:
            hex_color = t['color']
            
            # Helper to quickly make a semi-transparent version of the hex color
            def make_rgba(hex_str, alpha):
                hex_str = hex_str.lstrip('#')
                if len(hex_str) == 3:
                     hex_str = ''.join(c + c for c in hex_str)
                # Map some color names used in the app safely if not hex
                color_map = {'cyan': '#00FFFF', 'green': '#008000', 'orange': '#FFA500', 'blue': '#0000FF', 'purple': '#800080', 'hotpink': '#FF69B4', '#FF00FF': '#FF00FF'}
                if hex_str in color_map:
                    hex_str = color_map[hex_str].lstrip('#')
                try:
                    rgb = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
                    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"
                except:
                    return f"rgba(255, 255, 255, {alpha})" # Fallback white glow
                    
            glow_color_1 = make_rgba(hex_color, 0.15) # Inner glow
            glow_color_2 = make_rgba(hex_color, 0.03) # Faint outer glow
            fill_color   = make_rgba(hex_color, 0.05) # Very subtle fill

            scatter_kwargs = dict(
                x=df_plot.index,
                y=t['data'],
                mode='lines',
                name=t['col'],
                line=dict(color=t['color'], width=2, shape='spline'),
                showlegend=True
            )
            
            is_secondary = (use_secondary_y and len(cols) == 2 and t['col'] == cols[1])
            trace_kwargs = {}
            if use_secondary_y and len(cols) == 2:
                trace_kwargs['secondary_y'] = is_secondary

            # Subtle fill below curve
            fig.add_trace(go.Scatter(
                x=df_plot.index, y=t['data'], mode='lines',
                line=dict(width=0, shape='spline'),
                fill='tozeroy',
                fillcolor=fill_color,
                hoverinfo='skip', showlegend=False
            ), **trace_kwargs)
            
            # Add outer glow
            fig.add_trace(go.Scatter(
                x=df_plot.index, y=t['data'], mode='lines',
                line=dict(color=glow_color_2, width=8, shape='spline'),
                hoverinfo='skip', showlegend=False
            ), **trace_kwargs)
            
            # Add inner glow
            fig.add_trace(go.Scatter(
                x=df_plot.index, y=t['data'], mode='lines',
                line=dict(color=glow_color_1, width=4, shape='spline'),
                hoverinfo='skip', showlegend=False
            ), **trace_kwargs)
            
            if descriptions is not None:
                scatter_kwargs['customdata'] = descriptions
                scatter_kwargs['hovertemplate'] = f'%{{y:.1f}}{t["unit_str"]} (%{{customdata}})<extra></extra>'
            else:
                scatter_kwargs['hovertemplate'] = f'%{{y:.1f}}{t["unit_str"]}<extra></extra>'
                
            fig.add_trace(go.Scatter(**scatter_kwargs), **trace_kwargs)
                    
        y_max_range = max_val * 1.1 if max_val != -float('inf') else None
        
        tickvals = df_plot.index[df_plot.index.hour.isin([7, 19])]
        ticktext = tickvals.strftime('%m-%d %H:%M')
        
        layout_kwargs = dict(
            title=dict(text=title, font=dict(size=18, color='#E0E0E0')),
            xaxis=dict(
                tickmode='array',
                tickvals=tickvals,
                ticktext=ticktext,
                tickangle=-45,
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.05)',
                tickfont=dict(size=14, color='#A0A0B0'),
                title_font=dict(size=14, color='#E0E0E0')
            ),
            legend=dict(font=dict(size=14, color='#E0E0E0')),
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
            paper_bgcolor='rgba(0,0,0,0)', # Transparent background
            hovermode="x unified",
            margin=dict(l=40, r=20, t=40, b=40)
        )

        if use_secondary_y and len(cols) == 2:
            y1_dict = dict(
                title=f"{cols[0]} ({units[0]})",
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.05)',
                tickfont=dict(size=14, color='#A0A0B0'),
                title_font=dict(size=14, color='#E0E0E0')
            )
            # Center the line for temperature or rain to make it clearer
            if cols[0] in ['temperature', 'rain']:
                t_min = df_plot[cols[0]].min()
                t_max = df_plot[cols[0]].max()
                t_span = t_max - t_min if t_max > t_min else 5
                y1_dict['range'] = [t_min - t_span, t_max + t_span]
            
            layout_kwargs['yaxis'] = y1_dict
            layout_kwargs['yaxis2'] = dict(
                title=f"{cols[1]} ({units[1]})",
                showgrid=False,
                tickfont=dict(size=14, color='#A0A0B0'),
                title_font=dict(size=14, color='#E0E0E0')
            )
        else:
            layout_kwargs['yaxis'] = dict(
                range=[None, y_max_range] if y_max_range is not None else None,
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.05)',
                tickfont=dict(size=14, color='#A0A0B0'),
                title_font=dict(size=14, color='#E0E0E0')
            )

        fig.update_layout(**layout_kwargs)
        
        # Chart Enhancements
        try:
            days = pd.Series(df_plot.index).dt.floor('D').unique()
            for day in days:
                fig.add_vline(x=day, line_width=1, line_dash="dash", line_color="rgba(255,255,255,0.15)")
                
            if 'now_local' in globals():
                if df_plot.index.tzinfo is None:
                    current_time = now_local.replace(tzinfo=None)
                else:
                    current_time = now_local
                if df_plot.index.min() <= current_time <= df_plot.index.max():
                    fig.add_vline(x=current_time, line_width=2, line_dash="solid", line_color="#00c6ff", annotation_text="Now", annotation_position="top left", annotation_font_size=10, annotation_font_color="#00c6ff")
        except Exception:
            pass
        
        st.plotly_chart(fig, width="stretch")

    # Swapped colors so Temperature is hotpink (#FF00FF) and Humidity is cyan
    plot_custom_chart(df.set_index('datetime'), "Temperature & Humidity",
        ['temperature', 'humidity'], ['#FF00FF', 'cyan'],
        units=['°C', '%'], use_secondary_y=True)
    
    # Wind: show combined chart only if gust has valid data, else just Wind Speed
    if 'wind_gust' in df.columns and df['wind_gust'].dropna().any():
        plot_custom_chart(df.set_index('datetime'), "Wind Speed & Gust",
            ['wind_speed', 'wind_gust'], ['cyan', '#FF00FF'],
            units=['knots', 'knots'])
    else:
        plot_custom_chart(df.set_index('datetime'), "Wind Speed",
            ['wind_speed'], ['cyan'],
            units=['knots'])
    
    # Rain & PoP: show combined only if pop has valid data
    if 'pop' in df.columns and df['pop'].dropna().any():
        rain_cols = ['rain', 'pop'] if 'rain' in df.columns else ['pop']
        rain_units = ['mm/h', '%'] if 'rain' in df.columns else ['%']
        plot_custom_chart(df.set_index('datetime'), "Rain & PoP",
            rain_cols, ['cyan', '#FF00FF'] if 'rain' in df.columns else ['cyan'],
            units=rain_units, use_secondary_y=True)
        st.caption("Note: PoP = Probability of Precipitation")
    elif 'rain' in df.columns:
        plot_custom_chart(df.set_index('datetime'), "Rain",
            ['rain'], ['cyan'],
            units=['mm/h'])
    
    if 'cloud_cover' in df.columns:
        plot_custom_chart(df.set_index('datetime'), "Cloud Cover & Weather Description",
            ['cloud_cover'], ['cyan'], units=['%'], 
            descriptions=df['description'].tolist())
        
    if 'dew_point' in df.columns and df['dew_point'].dropna().any():
        plot_custom_chart(df.set_index('datetime'), "Dew Point Temperature",
            ['dew_point'], ['cyan'], units=['°C'])
        
    if 'uv_index' in df.columns and df['uv_index'].dropna().any():
        plot_custom_chart(df.set_index('datetime'), "UV Index",
            ['uv_index'], ['#FF00FF'], units=[''])
        
    if st.session_state.api_source == "Open-Meteo" and st.session_state.marine_data:
        df_marine = pd.DataFrame(st.session_state.marine_data)
        plot_custom_chart(df_marine.set_index('datetime'), "Wave Height",
            ['wave_height', 'swell_wave_height'], ['cyan', '#FF00FF'],
            units=['m', 'm'])
        
        plot_custom_chart(df_marine.set_index('datetime'), "Wave Period",
            ['wave_period', 'swell_wave_period'], ['cyan', '#FF00FF'],
            units=['s', 's'])

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/></svg>Forecast Data Table</div>', unsafe_allow_html=True)
    if st.session_state.api_source == "Open-Meteo":
        cols = ['datetime', 'description', 'temperature', 'humidity', 'wind_speed', 'wind_gust', 'wind_direction', 'rain', 'pop', 'dew_point', 'uv_index']
    else:
        cols = ['datetime', 'description', 'temperature', 'humidity', 'wind_speed', 'wind_gust', 'wind_direction', 'pop', 'dew_point', 'uv_index']
    df_display = df[[c for c in cols if c in df.columns]].copy()
    df_display.fillna('N/A', inplace=True)
    
    # Add units to headers
    col_map = {
        'datetime': 'Date/Time',
        'description': 'Description',
        'temperature': 'Temp (°C)',
        'humidity': 'Hum (%)',
        'wind_speed': 'Wind (knots)',
        'wind_gust': 'Gust (knots)',
        'wind_direction': 'Wind Dir',
        'rain': 'Rain (mm)',
        'pop': 'PoP (%)',
        'dew_point': 'Dewpoint (°C)',
        'uv_index': 'UV'
    } 
    df_display.rename(columns=col_map, inplace=True)
    
    def highlight_extremes(s):
        styles = [''] * len(s)
        extreme_style = 'background-color: rgba(255, 107, 107, 0.25); color: #ffa0a0; font-weight: 600;'
        try:
            if s.name == 'Temp (°C)':
                styles = [extreme_style if type(v) in (int, float) and v > 37 else '' for v in s]
            elif s.name == 'Wind (knots)':
                styles = [extreme_style if type(v) in (int, float) and v > 25 else '' for v in s]
            elif s.name == 'Rain (mm)':
                styles = [extreme_style if type(v) in (int, float) and v > 0.5 else '' for v in s]
            elif s.name == 'UV':
                styles = [extreme_style if type(v) in (int, float) and v > 10 else '' for v in s]
        except Exception:
            pass
        return styles

    format_dict = {}
    for col in ['Temp (°C)', 'Wind (knots)', 'Gust (knots)', 'Rain (mm)', 'UV', 'Dewpoint (°C)']:
        if col in df_display.columns:
            format_dict[col] = lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else x
    for col in ['Hum (%)', 'PoP (%)']:
        if col in df_display.columns:
            format_dict[col] = lambda x: f"{int(round(x))}" if isinstance(x, (int, float)) else x

    styled_df = df_display.style.format(format_dict).apply(highlight_extremes, axis=0)
    if hasattr(styled_df, 'hide'):
        styled_df = styled_df.hide(axis="index")
    else:
        styled_df = styled_df.hide_index()
        
    # Render table via HTML for complete styling control (font size + lightblue hover)
    html_table = styled_df.to_html(table_attributes='class="custom-table"', justify='left', escape=False)
    
    html_template = f"""
<style>
.table-container {{
    max-height: 500px;
    overflow-y: auto;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(8px);
}}
.custom-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    font-family: 'JetBrains Mono', monospace;
    color: #d1d9e6;
}}
.custom-table thead th {{
    position: sticky;
    top: 0;
    background: rgba(0, 114, 255, 0.15);
    color: #e8f0fe;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    z-index: 10;
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.06);
}}
.custom-table th, .custom-table td {{
    padding: 10px 14px;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    text-align: left;
}}
.custom-table tbody tr:nth-child(even) {{
    background: rgba(255, 255, 255, 0.02);
}}
.custom-table th:nth-child(2), .custom-table td:nth-child(2) {{
    min-width: 180px;
}}
.custom-table th:nth-child(7), .custom-table td:nth-child(7) {{
    min-width: 60px;
    max-width: 80px;
}}
.custom-table tr:hover {{
    background-color: rgba(0, 198, 255, 0.08) !important;
}}
</style>
<div class="table-container">
{html_table}
</div>
"""
    st.markdown(html_template, unsafe_allow_html=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>Export Reports</div>', unsafe_allow_html=True)
    colA, colB = st.columns(2)
    
    with colA:
        st.markdown('<div class="export-card"><div class="export-card-title"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>Weather Forecast Report - PDF</div></div>', unsafe_allow_html=True)
        pdf_lang = st.radio("PDF Language", ["English", "Vietnamese"], horizontal=True)
        if st.button("Generate PDF Report"):
            with st.spinner("Generating PDF Report..."):
                if pdf_lang == "Vietnamese":
                    filename = logic.generate_vietnamese_pdf_report(
                        st.session_state.lat, st.session_state.lon, w_data, l_info, 
                        st.session_state.ui_location_name, st.session_state.api_source, st.session_state.marine_data
                    )
                else:
                    filename = logic.generate_pdf_report(
                        st.session_state.lat, st.session_state.lon, w_data, l_info, 
                        st.session_state.ui_location_name, st.session_state.api_source, st.session_state.marine_data
                    )
                
                if filename and os.path.exists(filename):
                    with open(filename, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(f"Download {pdf_lang} PDF", data=pdf_bytes, file_name=filename, mime="application/pdf")
                    st.success(f"✅ {pdf_lang} PDF generated!")
                else:
                    st.error("❌ Failed to generate PDF.")
                    
    with colB:
        st.markdown('<div class="export-card"><div class="export-card-title"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M7 16h8"/><path d="M7 11h12"/><path d="M7 6h3"/></svg>Historical Data Export</div></div>', unsafe_allow_html=True)
        
        export_col1, export_col2 = st.columns(2)
        current_date = datetime.date.today()
        default_from = current_date - datetime.timedelta(days=7)
        
        with export_col1:
            hist_from = st.date_input("History From", max_value=current_date, value=default_from)
        with export_col2:
            hist_to = st.date_input("History To", max_value=current_date, value=current_date)
            
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            if st.button("Historical Excel Report"):
                with st.spinner("Fetching Historical Data & Generating Excel..."):
                    hist_data, hist_l_info = logic.fetch_open_meteo_historical_weather(
                        st.session_state.lat, st.session_state.lon, 
                        hist_from, hist_to
                    )
                    if hist_data:
                        filename = logic.generate_historical_excel_report(
                            st.session_state.lat, st.session_state.lon, hist_data, hist_l_info,
                            st.session_state.ui_location_name, hist_from, hist_to
                        )
                        if filename and os.path.exists(filename):
                            with open(filename, "rb") as f:
                                excel_bytes = f.read()
                            st.download_button("Download Historical Excel (.xlsx)", data=excel_bytes, file_name=filename, 
                                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                            st.success("✅ Historical Excel generated!")
                            st.info("💡 Preview of Historical Data (First 5 rows):")
                            df_hist_preview = pd.DataFrame(hist_data).head(5)
                            st.dataframe(df_hist_preview)
                        else:
                            st.error("❌ Failed to generate Excel.")
                        
        with col_ex2:
            if st.button("Historical PDF Report"):
                with st.spinner("Fetching Historical Data & Generating PDF..."):
                    # Fetch historical data first
                    hist_data, hist_l_info = logic.fetch_open_meteo_historical_weather(
                        st.session_state.lat, st.session_state.lon, 
                        hist_from, hist_to
                    )
                    if hist_data:
                        filename = logic.generate_historical_pdf_report(
                            st.session_state.lat, st.session_state.lon, hist_data, hist_l_info,
                            st.session_state.ui_location_name, hist_from, hist_to
                        )
                        if filename and os.path.exists(filename):
                            with open(filename, "rb") as f:
                                pdf_bytes = f.read()
                            st.download_button("Download Historical PDF", data=pdf_bytes, file_name=filename, mime="application/pdf")
                            st.success("✅ Historical PDF generated!")
                            st.info("💡 Preview of Historical Data (First 5 rows):")
                            df_hist_preview = pd.DataFrame(hist_data).head(5)
                            st.dataframe(df_hist_preview)
                        else:
                            st.error("❌ Failed to generate historical PDF.")
                    else:
                        st.error("❌ Failed to fetch historical data.")

    # Additional export for raw CSV
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    if st.button("Export Raw CSV Data"):
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"Weather_Data_{st.session_state.ui_location_name}.csv",
            mime="text/csv"
        )
    st.info("💡 Tip: You can change the forecast range in the sidebar to export more or less data.")

