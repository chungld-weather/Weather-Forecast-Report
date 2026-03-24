"""Quick test script to debug marine data fetch and PDF generation flow."""
from weather_logic import WeatherLogic

logic = WeatherLogic(api_key='')

# Fetch weather for Rong Doi Platform coordinates
print("=== Fetching weather data ===")
w_data, l_info = logic.fetch_weather(9.78, 107.05, source='Open-Meteo')
print(f"Weather: {len(w_data) if w_data else 0} records")
print(f"Timezone: {l_info.get('timezone') if l_info else None}")

# Fetch marine data
print("\n=== Fetching marine data ===")
m_data = logic._fetch_marine_data_openmeteo(9.78, 107.05, l_info.get('timezone', 'Asia/Ho_Chi_Minh'))
print(f"Marine: type={type(m_data).__name__}, len={len(m_data) if m_data else 0}")

if m_data and len(m_data) > 0:
    print(f"First record keys: {list(m_data[0].keys())}")
    print(f"First record sample: wave_height={m_data[0].get('wave_height')}, wave_period={m_data[0].get('wave_period')}")
else:
    print("WARNING: No marine data returned!")

# Test PDF generation with marine data
print("\n=== Testing PDF generation ===")
try:
    pdf_bytes = logic.generate_pdf_report(
        lat=9.78, lon=107.05,
        weather_data=w_data, location_info=l_info,
        ui_location_name="Rong Doi Platform",
        api_source="Open-Meteo",
        marine_data=m_data
    )
    print(f"PDF generated: {len(pdf_bytes)} bytes")
except Exception as e:
    print(f"PDF generation failed: {e}")
    import traceback
    traceback.print_exc()
