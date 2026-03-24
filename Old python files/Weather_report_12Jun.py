import requests
import json

# Platform coordinates
LAT, LON = 52.52, 13.41

# Open-Meteo: Marine and weather data
open_meteo_url = f"https://api.open-meteo.com/v1/marine?latitude={LAT}&longitude={LON}&hourly=wave_height,wave_period,wind_speed_10m"
open_meteo_response = requests.get(open_meteo_url).json()

# Google Weather API (requires API key)
google_api_key = "AIzaSyCCIVftff_mmEJ8XBQ251tsLIk3tS9pj6g"
google_url = f"https://weather.googleapis.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=temperature,precipitation,wind_speed&key={google_api_key}"
google_response = requests.get(google_url).json()

# Combine and process data
combined_data = []
for i, time in enumerate(open_meteo_response["hourly"]["time"]):
    entry = {
        "time": time,
        "wave_height": open_meteo_response["hourly"]["wave_height"][i],
        "wind_speed": open_meteo_response["hourly"]["wind_speed_10m"][i],
        "temperature": google_response["hourly"]["temperature"][i],
        "precipitation": google_response["hourly"]["precipitation"][i]
    }
    # Alert for critical conditions
    if entry["wave_height"] > 3 or entry["wind_speed"] > 20:
        entry["alert"] = "Warning: Unsafe conditions for vessel ops"
    combined_data.append(entry)

# Save to file or database
with open("weather_data.json", "w") as f:
    json.dump(combined_data, f, indent=2)
