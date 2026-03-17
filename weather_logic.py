import os
import re
import sys
import json
import math
import pytz
import traceback
import requests
from datetime import datetime, timedelta, timezone
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet

# --- Constants ---
DEFAULT_TIMEZONE = "Asia/Bangkok"
OPENMETEO_API_URL = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"
OPENMETEO_MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
DEFAULT_LOCATIONS_FILE = "locations.json"

# WMO Weather Codes mapping
WMO_WEATHER_CODES_EN = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 66: "Light freezing rain",
    67: "Heavy freezing rain", 71: "Slight snow fall", 73: "Moderate snow fall",
    75: "Heavy snow fall", 77: "Snow grains", 80: "Slight rain showers",
    81: "Moderate rain showers", 82: "Violent rain showers", 85: "Slight snow showers",
    86: "Heavy snow showers", 95: "Thunderstorm", 96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

def load_config(path='config.json'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {"owm_api_key": ""}

def save_config(config_data, path='config.json'):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

def degrees_to_direction(degrees):
    if degrees is None or degrees == 'N/A':
        return 'N/A'
    try:
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE',
                      'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        return directions[round(float(degrees) / (360 / len(directions))) % len(directions)]
    except (ValueError, TypeError):
        return 'N/A'

def fetch_weather_openmeteo(lat, lon, timezone_str=DEFAULT_TIMEZONE, session=None):
    if session is None:
        session = requests.Session()
    
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,rain,showers,snowfall,weather_code,pressure_msl,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,uv_index_max,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant",
        "timezone": timezone_str, "forecast_days": 14
    }
    try:
        response = session.get(OPENMETEO_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        hourly = data.get('hourly', {})
        processed_hourly = []
        local_tz = pytz.timezone(timezone_str)
        
        times = hourly.get('time', [])
        for i in range(len(times)):
            local_time = datetime.fromisoformat(times[i]).astimezone(local_tz)
            rain = (hourly.get('rain', [])[i] or 0) + (hourly.get('showers', [])[i] or 0) + (hourly.get('snowfall', [])[i] or 0)
            processed_hourly.append({
                'datetime_obj': local_time,
                'datetime': local_time.strftime('%Y-%m-%d %H:%M'),
                'description': WMO_WEATHER_CODES_EN.get(hourly.get('weather_code', [])[i], 'N/A'),
                'temperature': hourly.get('apparent_temperature', [])[i],
                'humidity': hourly.get('relative_humidity_2m', [])[i],
                'pressure': hourly.get('pressure_msl', [])[i],
                'wind_speed': hourly.get('wind_speed_10m', [])[i],
                'wind_gust': hourly.get('wind_gusts_10m', [])[i],
                'wind_direction': degrees_to_direction(hourly.get('wind_direction_10m', [])[i]),
                'rain': rain,
                'uv_index': hourly.get('uv_index', [])[i],
                'pop': hourly.get('precipitation_probability', [])[i],
                'cloud_cover': hourly.get('cloud_cover', [])[i]
            })
            
        location_info = {
            'lat': data.get('latitude'),
            'lon': data.get('longitude'),
            'timezone': data.get('timezone'),
            'elevation': data.get('elevation'),
            'sunrise': data.get('daily', {}).get('sunrise', ['N/A'])[0],
            'sunset': data.get('daily', {}).get('sunset', ['N/A'])[0]
        }
        
        return processed_hourly, location_info
    except Exception as e:
        print(f"Error fetching OpenMeteo weather: {e}")
        return None, None

def fetch_marine_data_openmeteo(lat, lon, timezone_str=DEFAULT_TIMEZONE, session=None):
    if session is None:
        session = requests.Session()
        
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "wave_height,wave_direction,wave_period,wind_wave_height,wind_wave_direction,wind_wave_period,swell_wave_height,swell_wave_direction,swell_wave_period",
        "timezone": timezone_str, "forecast_days": 14
    }
    try:
        response = session.get(OPENMETEO_MARINE_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json().get('hourly', {})
        
        processed_data = []
        local_tz = pytz.timezone(timezone_str)
        times = data.get('time', [])
        for i in range(len(times)):
            dt_obj = datetime.fromisoformat(times[i]).astimezone(local_tz)
            processed_data.append({
                'datetime_obj': dt_obj,
                'datetime': dt_obj.strftime('%Y-%m-%d %H:%M'),
                'wave_height': data.get('wave_height', [])[i],
                'wave_direction': degrees_to_direction(data.get('wave_direction', [])[i]),
                'wave_period': data.get('wave_period', [])[i],
                'wind_wave_height': data.get('wind_wave_height', [])[i],
                'wind_wave_direction': degrees_to_direction(data.get('wind_wave_direction', [])[i]),
                'wind_wave_period': data.get('wind_wave_period', [])[i],
                'swell_wave_height': data.get('swell_wave_height', [])[i],
                'swell_wave_direction': degrees_to_direction(data.get('swell_wave_direction', [])[i]),
                'swell_wave_period': data.get('swell_wave_period', [])[i],
            })
        return processed_data
    except Exception as e:
        print(f"Error fetching marine data: {e}")
        return None

def fetch_historical_data_openmeteo(lat, lon, start_date, end_date, timezone_str=DEFAULT_TIMEZONE, session=None):
    if session is None:
        session = requests.Session()
        
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": start_date, "end_date": end_date,
        "hourly": "apparent_temperature,temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m,cloud_cover,pressure_msl,uv_index",
        "timezone": timezone_str, "temperature_unit": "celsius", "wind_speed_unit": "kn", "precipitation_unit": "mm"
    }
    try:
        response = session.get(OPENMETEO_ARCHIVE_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json().get('hourly', {})
        
        processed = []
        local_tz = pytz.timezone(timezone_str)
        times = data.get('time', [])
        
        for i in range(len(times)):
            dt_obj = datetime.fromisoformat(times[i]).astimezone(local_tz)
            
            # Simple helper to get value or 'N/A'
            def get_val(key, idx):
                val = data.get(key, [])[idx]
                return val if val is not None else 'N/A'
                
            processed.append({
                'datetime_obj': dt_obj,
                'datetime': dt_obj.strftime('%Y-%m-%d %H:%M'),
                'description': WMO_WEATHER_CODES_EN.get(get_val('weather_code', i), 'N/A'),
                'temperature': get_val('apparent_temperature', i) if get_val('apparent_temperature', i) != 'N/A' else get_val('temperature_2m', i),
                'humidity': get_val('relative_humidity_2m', i),
                'wind_speed': get_val('wind_speed_10m', i),
                'wind_gust': get_val('wind_gusts_10m', i),
                'wind_direction': degrees_to_direction(get_val('wind_direction_10m', i)),
                'rain': get_val('precipitation', i),
                'cloud_cover': get_val('cloud_cover', i),
                'pressure': get_val('pressure_msl', i),
                'uv_index': get_val('uv_index', i),
                'pop': 'N/A'
            })
        return processed
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return None

# --- Visualization Logic ---

def create_chart(data, param_name, ylabel, title, date_key='datetime_obj', xlabel_text='Date/Time', color='tab:blue'):
    if not data:
        return None
    plt.figure(figsize=(9.0, 2.8))
    dates, values = [], []
    for item in data:
        val = item.get(param_name)
        if val is not None and val != 'N/A' and isinstance(item.get(date_key), datetime):
            dates.append(item[date_key])
            values.append(float(val))
    if not dates or not values:
        plt.close()
        return None
    plt.plot(dates, values, marker='.', linestyle='-', markersize=4, linewidth=1, color=color)
    plt.title(title, fontsize=10)
    plt.xlabel(xlabel_text, fontsize=9)
    plt.ylabel(ylabel, fontsize=9)
    plt.xticks(rotation=30, ha='right', fontsize=9)
    plt.yticks(fontsize=9)
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(byhour=[7], tz=dates[0].tzinfo if dates else None))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))
    plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
    plt.tight_layout(pad=0.5)
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close()
    buf.seek(0)
    return buf

def create_wind_chart(data, date_key='datetime_obj'):
    if not data:
        return None
    plt.figure(figsize=(9.0, 2.8))
    dates, speeds, gusts = [], [], []
    for item in data:
        dt = item.get(date_key)
        if isinstance(dt, datetime):
            dates.append(dt)
            s = item.get('wind_speed')
            g = item.get('wind_gust')
            speeds.append(float(s) if s not in [None, 'N/A'] else math.nan)
            gusts.append(float(g) if g not in [None, 'N/A'] else math.nan)
    
    if not dates:
        plt.close()
        return None
    
    plt.plot(dates, speeds, marker='.', label='Speed')
    plt.plot(dates, gusts, marker='.', label='Gust', color='orange')
    plt.title("Wind Speed and Gust Trend", fontsize=10)
    plt.legend(fontsize=8)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close()
    buf.seek(0)
    return buf

def create_temp_humidity_chart(data, date_key='datetime_obj'):
    if not data:
        return None
    fig, ax1 = plt.subplots(figsize=(9.0, 2.8))
    dates, temps, hums = [], [], []
    for item in data:
        dt = item.get(date_key)
        if isinstance(dt, datetime):
            dates.append(dt)
            t = item.get('temperature')
            h = item.get('humidity')
            temps.append(float(t) if t not in [None, 'N/A'] else math.nan)
            hums.append(float(h) if h not in [None, 'N/A'] else math.nan)
            
    ax1.plot(dates, temps, color='tab:blue', label='Temp (°C)')
    ax1.set_ylabel('Temp (°C)', color='tab:blue')
    ax2 = ax1.twinx()
    ax2.plot(dates, hums, color='orange', label='Humidity (%)')
    ax2.set_ylabel('Humidity (%)', color='orange')
    plt.title("Temperature and Humidity Trend")
    fig.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf

def create_combined_wave_chart(data, date_key='datetime_obj'):
    if not data:
        return None, None
    
    dates, wh, sh, wp, sp = [], [], [], [], []
    for item in data:
        dt = item.get(date_key)
        if isinstance(dt, datetime):
            dates.append(dt)
            wh.append(float(item.get('wave_height', 0)) if item.get('wave_height') != 'N/A' else math.nan)
            sh.append(float(item.get('swell_wave_height', 0)) if item.get('swell_wave_height') != 'N/A' else math.nan)
            wp.append(float(item.get('wave_period', 0)) if item.get('wave_period') != 'N/A' else math.nan)
            sp.append(float(item.get('swell_wave_period', 0)) if item.get('swell_wave_period') != 'N/A' else math.nan)

    # Height Chart
    plt.figure(figsize=(9.0, 2.8))
    plt.plot(dates, wh, label='Wave Height')
    plt.plot(dates, sh, label='Swell Height')
    plt.title("Wave & Swell Height Trend")
    plt.legend()
    h_buf = BytesIO()
    plt.savefig(h_buf, format='png', dpi=150)
    plt.close()
    h_buf.seek(0)

    # Period Chart
    plt.figure(figsize=(9.0, 2.8))
    plt.plot(dates, wp, label='Wave Period')
    plt.plot(dates, sp, label='Swell Period')
    plt.title("Wave & Swell Period Trend")
    plt.legend()
    p_buf = BytesIO()
    plt.savefig(p_buf, format='png', dpi=150)
    plt.close()
    p_buf.seek(0)
    
    return h_buf, p_buf

def generate_pdf_report(ui_location_name, lat, lon, location_info, weather_data, api_source="OpenMeteo"):
    file_name = f"Weather_Report_{api_source}_{ui_location_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"Weather Forecast for {ui_location_name}", styles['Title']))
    elements.append(Paragraph(f"Coordinates: {lat:.4f}, {lon:.4f} | Timezone: {location_info.get('timezone')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Simple table for current weather
    if weather_data:
        curr = weather_data[0]
        data = [
            ["Parameter", "Value"],
            ["Temperature", f"{curr.get('temperature')}°C"],
            ["Wind", f"{curr.get('wind_speed')} knots {curr.get('wind_direction')}"],
            ["Humidity", f"{curr.get('humidity')}%"],
            ["Conditions", curr.get('description')]
        ]
        t = Table(data)
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey), ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke)]))
        elements.append(t)
        
    doc.build(elements)
    return file_name
