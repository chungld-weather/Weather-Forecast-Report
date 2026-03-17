import streamlit as st
import pandas as pd
import weather_logic as logic
import os
import io
import datetime
import math
from dotenv import load_dotenv
import plotly.graph_objects as go
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

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #2A0845, #1C0770);
    color: white; /* to ensure text remains readable on dark background */
}

/* Custom Button Styles */
div.stButton > button, div.stDownloadButton > button {
    background: linear-gradient(90deg, #0072ff, #00c6ff);
    color: white;
    border: 1px solid transparent;
    transition: 0.3s;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
    background: transparent !important;
    border: 1px solid #00c6ff !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Weather Reporter")

@st.cache_data
def load_locations():
    """Load location list from locations.json (committed to git — no secrets inside)."""
    import json
    loc_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locations.json")
    if os.path.exists(loc_file):
        with open(loc_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"locations": {}, "default_location": "", "dashboard_locations": []}

config_data = logic.load_config()
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
    if st.button("Use this location", key="btn_list"):
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
    if st.button("🔍 Search", key="btn_search"):
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
        if st.button("✅ Confirm this location", key="btn_confirm_search"):
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
            if st.button(f"✅ Use this location", key="btn_confirm_map"):
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
    if st.button("✅ Confirm coordinates", key="btn_manual"):
        st.session_state.selected_lat = manual_lat
        st.session_state.selected_lon = manual_lon
        st.session_state.selected_location_name = manual_name.strip() or f"({manual_lat:.5f}, {manual_lon:.5f})"
        st.success(f"✅ Confirmed: **{st.session_state.selected_location_name}**")

# ── Confirmed location display + Fetch ────────────────────────────────────────
st.markdown("---")
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

# ── Fetch Logic ────────────────────────────────────────────────────────────────
if fetch_btn or (not st.session_state.weather_data and st.session_state.selected_lat):
    lat = st.session_state.selected_lat
    lon = st.session_state.selected_lon
    location = st.session_state.selected_location_name
    with st.spinner("Fetching data..."):
        w_data, l_info = logic.fetch_weather(lat, lon, source=data_source)
        # marine data is only for Open-Meteo in this logic
        m_data = logic.fetch_marine_data(lat, lon, l_info['timezone']) if l_info and data_source == "Open-Meteo" else None
        
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
            st.error("Failed to fetch data or location not found.")


if st.session_state.weather_data:
    w_data = st.session_state.weather_data
    l_info = st.session_state.location_info
    
    # Middle Section
    # ── Current Weather Condition ──────────────────────────────────────────────────
    st.header("⚡ Current Weather Condition")
    
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
        f"<span style='font-size:14px; color:#a0d8ff;'>🕐 Local time at location: "
        f"<b>{local_time_str}</b> &nbsp;·&nbsp; {tz_name} ({utc_label})</span>",
        unsafe_allow_html=True
    )

    colC1, colC2, colC3, colC4 = st.columns(4)
    
    # 1. Temperature
    temp_b64 = get_base64_image("icons/temp.png")
    colC1.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{temp_b64}' width='55'></div>", unsafe_allow_html=True)
    curr_temp = current_point.get('temperature', 0)
    colC1.metric("Temperature", f"{curr_temp:.1f}°C")
    
    # 2. Wind Speed
    wind_b64 = get_base64_image("icons/wind.png")
    colC2.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{wind_b64}' width='55'></div>", unsafe_allow_html=True)
    curr_wind = current_point.get('wind_speed', 0)
    colC2.metric("Wind Speed", f"{curr_wind:.1f} knots")
    
    # 3. Rain
    rain_b64 = get_base64_image("icons/rain.png")
    colC3.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{rain_b64}' width='55'></div>", unsafe_allow_html=True)
    curr_rain = current_point.get('rain', 0)
    colC3.metric("Rain", f"{curr_rain:.1f} mm")
    
    # 4. UV Index
    uv_b64 = get_base64_image("icons/UV.png")
    colC4.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{uv_b64}' width='55'></div>", unsafe_allow_html=True)
    curr_uv = current_point.get('uv_index', 0)
    colC4.metric("UV Index", f"{curr_uv:.1f}")
    
    st.markdown("---")
    
    # ── Precipitation Map ──────────────────────────────────────────────────────────
    st.header("🗺️ Precipitation Map")
    windy_url = f"https://embed.windy.com/embed2.html?lat={st.session_state.lat}&lon={st.session_state.lon}&zoom=5&level=surface&overlay=rain&product=ecmwf&menu=&message=&marker=1&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=default&metricTemp=default&radarRange=-1"
    st.components.v1.iframe(windy_url, height=500, scrolling=True)
    
    st.markdown("---")
    
    # ── Weather Forecast Summary ──────────────────────────────────────────────────
    st.header("📊 Weather Forecast Summary")
    
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
    
    colS1.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{temp_b64}' width='55'></div>", unsafe_allow_html=True)
    colS1.metric("Temp (Min-Max)", f"{temp_min} - {temp_max}")
    
    colS2.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{wind_b64}' width='55'></div>", unsafe_allow_html=True)
    colS2.metric("Wind (Min-Max)", f"{wind_min} - {wind_max} knots")
    
    colS3.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{rain_b64}' width='55'></div>", unsafe_allow_html=True)
    colS3.metric("Rain (Max)", rain_max)
    
    colS4.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{uv_b64}' width='55'></div>", unsafe_allow_html=True)
    colS4.metric("UV Index (Max)", uv_max)
    
    current_time_str = now_local.strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"**Location Info:** {l_info.get('name')} | **Timezone:** {l_info.get('timezone')} | **Sunrise:** {l_info.get('sunrise')} | **Sunset:** {l_info.get('sunset')} | **Local Time:** {current_time_str}")

    # Sidebar Table
    # Bottom Section
    # Bottom Section
    st.header("Charts")
    
    st.subheader("Temperature & Humidity")
    temp_hum_chart = logic.create_temp_humidity_chart(w_data)
    if temp_hum_chart:
        st.image(temp_hum_chart)
    
    st.subheader("Wind Speed & Gust")
    wind_chart = logic.create_wind_chart(w_data)
    if wind_chart:
        st.image(wind_chart)
    
    st.subheader("Rain & Probability of Precipitation")
    rain_chart = logic.create_chart(w_data, 'rain', 'Rain (mm)', 'Rainfall Trend', color='blue')
    if rain_chart:
        st.image(rain_chart)
    
    pop_chart = logic.create_chart(w_data, 'pop', 'PoP (%)', 'Precipitation Probability', color='purple')
    if pop_chart:
        st.image(pop_chart)
        
    if 'cloud_cover' in pd.DataFrame(w_data).columns:
        st.subheader("Cloud Cover")
        cloud_chart = logic.create_chart(w_data, 'cloud_cover', 'Cloud (%)', 'Cloud Cover Trend', color='grey')
        if cloud_chart:
            st.image(cloud_chart)
        
    if 'uv_index' in pd.DataFrame(w_data).columns:
        st.subheader("UV Index")
        uv_chart = logic.create_chart(w_data, 'uv_index', 'UV Index', 'UV Index Trend', color='gold')
        if uv_chart:
            st.image(uv_chart)
        
    if st.session_state.api_source == "Open-Meteo" and st.session_state.marine_data:
        st.subheader("Marine Data (Wave & Swell)")
        h_chart, p_chart = logic.create_combined_wave_chart(st.session_state.marine_data)
        if h_chart:
            st.image(h_chart)
        if p_chart:
            st.image(p_chart)

    st.markdown("---")
    st.header("Data Table")
    if st.session_state.api_source == "Open-Meteo":
        cols = ['datetime', 'description', 'temperature', 'humidity', 'wind_speed', 'wind_gust', 'wind_direction', 'rain', 'pop', 'uv_index']
    else:
        cols = ['datetime', 'description', 'temperature', 'humidity', 'wind_speed', 'wind_gust', 'wind_direction', 'pop']
    df_display = df[[c for c in cols if c in df.columns]].copy()
    
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
        'uv_index': 'UV'
    }
    df_display.rename(columns=col_map, inplace=True)
    
    # Render table via HTML for complete styling control (font size + lightblue hover)
    html_table = df_display.to_html(classes="custom-table", index=False, justify='left', escape=False)
    
    html_template = f"""
<style>
.table-container {{
    max-height: 500px;
    overflow-y: auto;
    border: 1px solid #444;
    border-radius: 8px;
}}
.custom-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 15px; 
    color: white;
}}
.custom-table thead th {{
    position: sticky;
    top: 0;
    background-color: #333;
    z-index: 10;
    box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.4);
}}
.custom-table th, .custom-table td {{
    padding: 10px 14px;
    border: 1px solid #444;
    text-align: left;
}}
/* Adjust Description column width (2nd col) */
.custom-table th:nth-child(2), .custom-table td:nth-child(2) {{
    min-width: 180px;
}}
/* Adjust Wind Direction column width (7th col) */
.custom-table th:nth-child(7), .custom-table td:nth-child(7) {{
    min-width: 60px;
    max-width: 80px;
}}
.custom-table tr:hover {{
    background-color: rgba(0, 255, 255, 0.1) !important;
}}
</style>
<div class="table-container">
{html_table}
</div>
"""
    st.markdown(html_template, unsafe_allow_html=True)

    st.markdown("---")
    st.header("Export Reports")
    colA, colB = st.columns(2)
    
    with colA:
        st.subheader("PDF Report")
        pdf_lang = st.radio("PDF Language", ["English", "Vietnamese"], horizontal=True)
        if st.button("Generate PDF Report"):
            with st.spinner("Generating PDF..."):
                if pdf_lang == "Vietnamese":
                    logic.generate_vietnamese_pdf_report(
                        st.session_state.lat, st.session_state.lon, w_data, l_info, 
                        st.session_state.ui_location_name, st.session_state.api_source, st.session_state.marine_data
                    )
                else:
                    logic.generate_pdf_report(
                        st.session_state.lat, st.session_state.lon, w_data, l_info, 
                        st.session_state.ui_location_name, st.session_state.api_source, st.session_state.marine_data
                    )
                import glob
                pdfs = glob.glob("Weather_Report_*.pdf")
                if pdfs:
                    latest_pdf = max(pdfs, key=os.path.getctime)
                    with open(latest_pdf, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button("Download Current PDF", data=pdf_bytes, file_name=latest_pdf, mime="application/pdf")
                    st.success("PDF generated!")
                else:
                    st.error("Failed to generate PDF.")
                    
    with colB:
        st.subheader("Historical Data Export")
        
        df_datetime = pd.to_datetime(df['datetime'])
        import datetime
        current_date = datetime.date.today()
        default_from = current_date - datetime.timedelta(days=7)
        
        export_col1, export_col2 = st.columns(2)
        with export_col1:
            export_from = st.date_input("From (date)", max_value=current_date, value=default_from)
        with export_col2:
            export_to = st.date_input("To (date)", max_value=current_date, value=current_date)

        # Filter dataset by converting string datetimes
        mask = (df_datetime.dt.date >= export_from) & (df_datetime.dt.date <= export_to)
        export_df = df.loc[mask]
        
        export_marine_df = None
        if st.session_state.marine_data:
            marine_df = pd.DataFrame(st.session_state.marine_data)
            marine_mask = (pd.to_datetime(marine_df['datetime']).dt.date >= export_from) & (pd.to_datetime(marine_df['datetime']).dt.date <= export_to)
            export_marine_df = marine_df.loc[marine_mask]

        # Prepare Excel (remove timezones as Excel doesn't support them)
        export_df_excel = export_df.copy()
        export_df_excel['datetime'] = pd.to_datetime(export_df_excel['datetime']).dt.tz_localize(None)
        
        # Remove tzinfo from any other columns (like datetime_obj, sunrise, sunset)
        for col in export_df_excel.columns:
            if export_df_excel[col].apply(lambda x: hasattr(x, 'tzinfo') and x.tzinfo is not None).any():
                export_df_excel[col] = export_df_excel[col].apply(lambda x: x.replace(tzinfo=None) if hasattr(x, 'tzinfo') and x.tzinfo is not None else x)
        
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
            export_df_excel.to_excel(writer, index=False, sheet_name='Weather')
            if export_marine_df is not None:
                export_marine_df_excel = export_marine_df.copy()
                export_marine_df_excel['datetime'] = pd.to_datetime(export_marine_df_excel['datetime']).dt.tz_localize(None)
                
                for col in export_marine_df_excel.columns:
                    if export_marine_df_excel[col].apply(lambda x: hasattr(x, 'tzinfo') and x.tzinfo is not None).any():
                        export_marine_df_excel[col] = export_marine_df_excel[col].apply(lambda x: x.replace(tzinfo=None) if hasattr(x, 'tzinfo') and x.tzinfo is not None else x)
                
                export_marine_df_excel.to_excel(writer, index=False, sheet_name='Marine')
        
        # Prepare CSV
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.download_button(
                label="Download Excel (.xlsx)",
                data=excel_buf.getvalue(),
                file_name=f"Historical_Data_{st.session_state.ui_location_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with btn_col2:
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"Historical_Data_{st.session_state.ui_location_name}.csv",
                mime="text/csv"
            )

