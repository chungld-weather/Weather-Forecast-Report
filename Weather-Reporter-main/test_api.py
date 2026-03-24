import requests
print('OpenMeteo 14 days:', len(requests.get('https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&hourly=temperature_2m&forecast_days=14').json().get('hourly', {}).get('time', []))/24)
print('OpenMeteo 16 days:', len(requests.get('https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&hourly=temperature_2m&forecast_days=16').json().get('hourly', {}).get('time', []))/24)
print('Marine 14 days:', len(requests.get('https://marine-api.open-meteo.com/v1/marine?latitude=52.52&longitude=13.41&hourly=wave_height&forecast_days=14').json().get('hourly', {}).get('time', []))/24)

