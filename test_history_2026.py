import sys
import datetime
import pytz
from weather_logic import WeatherLogic

logic = WeatherLogic()
lat = 52.52
lon = 13.41
start_date = datetime.date(2026, 3, 15)
end_date = datetime.date(2026, 3, 22)

res, tz_info = logic.fetch_open_meteo_historical_weather(lat, lon, start_date, end_date)
if res:
    print(f"Num items: {len(res)}")
    if len(res) > 0:
        print(f"First item: {res[0]}")
        print(f"Last item: {res[-1]}")
else:
    print("No result")
