# input_file_2.py
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QRadioButton,
                             QMessageBox, QFrame)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image
import matplotlib.pyplot as plt
import requests
import json
from datetime import datetime, timedelta, date, time  # Added date, time
import pytz
from timezonefinder import TimezoneFinder
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import math
from collections import defaultdict
from io import BytesIO  # Use BytesIO for charts
from datetime import datetime, timedelta, date, time, timezone
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- Matplotlib Configuration for Background Execution ---
import matplotlib
matplotlib.use('Agg')
# --------------------------------------------------------


class WeatherCrawlerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather Reporter")
        # Increased height for third button
        self.setGeometry(200, 200, 560, 350)

        # --- API Keys ---
        # IMPORTANT: Replace placeholders with your actual API keys
        self.owm_api_key = "e1a69775e0d7c149a4e2bdb69bb59a82"  # Your OpenWeatherMap Key
        # <<< ADD YOUR WEATHERAPI.COM KEY HERE
        self.weatherapi_key = "2e0e72f89ca04e66b9c151853253003"
        # ----------------

        # Add window icon
        icon_path = "weather_icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file '{icon_path}' not found.")

        # Initialize timezone finder instance
        self._tf_instance = None

        # Define locations
        self.locations = {
            'Lan Tay Platform': (7.5783, 108.8694),
            'Rong Doi Platform': (7.7925, 108.2021),
            'An Phu Office': (10.809427, 106.736553),
            'Vung Tau Airport': (10.376001, 107.093239)
        }

        self.initUI()

        if not self.owm_api_key or self.owm_api_key == "YOUR_OPENWEATHERMAP_API_KEY":
            QMessageBox.critical(
                self, "API Key Error",
                "OpenWeatherMap API key not set.\nPlease edit the script and add your API key."
            )

        if not self.weatherapi_key or self.weatherapi_key == "YOUR_WEATHERAPI_KEY":
            QMessageBox.critical(
                self, "API Key Error",
                "WeatherAPI.com key not set.\nPlease edit the script and add your API key."
            )

    # def get_timezone_finder(self):
    #     if self._tf_instance is None:
    #         self._tf_instance = TimezoneFinder()
    #     return self._tf_instance

    def get_timezone_finder(self):
        """Initialize TimezoneFinder instance if not already created"""
        if self._tf_instance is None:
            try:
                self._tf_instance = TimezoneFinder()
            except Exception as e:
                print(f"Error initializing TimezoneFinder: {e}")
                # Fallback to Asia/Ho_Chi_Minh timezone for Vietnam locations
                return pytz.timezone('Asia/Ho_Chi_Minh')
        return self._tf_instance

    def get_location_timezone(self, lat, lon):
        """Get timezone for given coordinates with fallback"""
        try:
            tf = self.get_timezone_finder()
            timezone_str = tf.timezone_at(lat=lat, lng=lon)
            if timezone_str:
                return pytz.timezone(timezone_str)
            else:
                print(
                    f"Warning: Could not determine timezone for {lat}, {lon}")
                # Fallback to Vietnam timezone since all locations are in Vietnam
                return pytz.timezone('Asia/Ho_Chi_Minh')
        except Exception as e:
            print(f"Error getting timezone: {e}")
            return pytz.timezone('Asia/Ho_Chi_Minh')

    def initUI(self):
        main_layout = QVBoxLayout()

    # --- Location Input Section ---
        location_group_box = QFrame()
        location_group_box.setFrameShape(QFrame.StyledPanel)
        location_layout = QVBoxLayout(location_group_box)
        input_label = QLabel("Select Location:")
        input_label.setFont(QFont("Arial", 12, QFont.Bold))
        location_layout.addWidget(input_label)

        # Initialize location radios dictionary and GPS input components first
        self.location_radios = {}
        self.gps_radio = QRadioButton("Enter Custom GPS Coordinates:")
        self.lat_label = QLabel("Latitude:")
        self.lat_input = QLineEdit()
        self.lon_label = QLabel("Longitude:")
        self.lon_input = QLineEdit()

        # Add predefined locations
        first_radio = True
        for name, coords in self.locations.items():
            radio_text = f"{name:<20} ({coords[0]:.4f}, {coords[1]:.4f})"
            radio = QRadioButton(radio_text)
            radio.setFont(QFont("Arial", 10))
            self.location_radios[name] = radio
            location_layout.addWidget(radio)
            if first_radio:
                radio.setChecked(True)
                first_radio = False
            radio.toggled.connect(self.toggle_gps_input)

            # Create GPS input layout
        gps_input_layout = QHBoxLayout()
        gps_input_layout.addWidget(self.lat_label)
        gps_input_layout.addWidget(self.lat_input)
        gps_input_layout.addWidget(self.lon_label)
        gps_input_layout.addWidget(self.lon_input)

        # Add GPS components
        location_layout.addWidget(self.gps_radio)
        location_layout.addLayout(gps_input_layout)

        # Set initial state
        self.lat_input.setEnabled(False)
        self.lon_input.setEnabled(False)
        # Connect signals after all widgets are created
        self.gps_radio.toggled.connect(self.toggle_gps_input)
        for radio in self.location_radios.values():
            radio.toggled.connect(self.toggle_gps_input)

        # Add location section to main layout
        main_layout.addWidget(location_group_box)

        # --- Report Generation Section ---
        report_group_box = QFrame()
        report_group_box.setFrameShape(QFrame.StyledPanel)
        report_layout = QVBoxLayout(report_group_box)
        report_label = QLabel("Generate Report:")
        report_label.setFont(QFont("Arial", 11, QFont.Bold))
        report_label.setAlignment(Qt.AlignCenter)
        report_layout.addWidget(report_label)

        # OWM Buttons
        owm_daily_button = QPushButton("OWM: Generate 5-Day Daily Summary PDF")
        owm_daily_button.clicked.connect(self.crawl_owm_daily_forecast)
        report_layout.addWidget(owm_daily_button)

        owm_3hourly_button = QPushButton(
            "OWM: Generate 5-Day / 3-Hourly Forecast PDF")
        owm_3hourly_button.clicked.connect(self.crawl_owm_3hourly_forecast)
        report_layout.addWidget(owm_3hourly_button)

        # WeatherAPI Button
        weatherapi_hourly_button = QPushButton(
            "WeatherAPI: Generate 3-Day Hourly Forecast PDF")
        weatherapi_hourly_button.clicked.connect(
            self.crawl_weatherapi_hourly_forecast)
        report_layout.addWidget(weatherapi_hourly_button)

        main_layout.addWidget(report_group_box)
        self.setLayout(main_layout)

    def toggle_gps_input(self):
        self.lat_input.setEnabled(self.gps_radio.isChecked())
        self.lon_input.setEnabled(self.gps_radio.isChecked())

    def get_coordinates(self):
        if self.gps_radio.isChecked():
            try:
                lat = float(self.lat_input.text())
                lon = float(self.lon_input.text())
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Latitude/Longitude out of range.")
                return lat, lon
            except ValueError as e:
                QMessageBox.warning(
                    self, "Input Error", f"Invalid Latitude or Longitude.\nError: {e}")
                return None, None
        else:
            for name, radio in self.location_radios.items():
                if radio.isChecked():
                    return self.locations[name]
        QMessageBox.warning(self, "Input Error", "No location selected.")
        return None, None

    # --- Button Click Handlers ---
    def crawl_owm_daily_forecast(self):
        self._crawl_and_generate(api_source="owm", report_type="daily_summary")

    def crawl_owm_3hourly_forecast(self):
        self._crawl_and_generate(
            api_source="owm", report_type="3hourly_detail")

    def crawl_weatherapi_hourly_forecast(self):
        self._crawl_and_generate(
            api_source="weatherapi", report_type="hourly_detail")
    # ---------------------------

    def _crawl_and_generate(self, api_source, report_type):
        """Handles fetching, processing, and generating for the specified API and report."""
        lat, lon = self.get_coordinates()
        if lat is None or lon is None:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            # --- Fetch Data based on API Source ---
            if api_source == "owm":
                # OWM requires separate current and forecast calls
                current_data, forecast_data, location_info = self.fetch_owm_data(
                    lat, lon)
                if not forecast_data or 'list' not in forecast_data or not forecast_data['list']:
                    QMessageBox.warning(
                        self, "OWM Error", "Failed to fetch/parse OWM forecast data.")
                    return
                forecast_list = forecast_data['list']

            elif api_source == "weatherapi":
                api_data, location_info = self.fetch_weatherapi_data(lat, lon)
                if not api_data or 'forecast' not in api_data or 'forecastday' not in api_data['forecast']:
                    QMessageBox.warning(
                        self, "WeatherAPI Error", "Failed to fetch/parse WeatherAPI forecast data.")
                    return
                # Extract hourly data from all forecast days
                forecast_list = []
                for day in api_data['forecast']['forecastday']:
                    forecast_list.extend(day.get('hour', []))
                if not forecast_list:
                    QMessageBox.warning(
                        self, "WeatherAPI Error", "No hourly forecast data found in WeatherAPI response.")
                    return
            else:
                QMessageBox.critical(self, "Internal Error",
                                     "Invalid API source specified.")
                return

            # --- Process and Generate Report ---
            tf = self.get_timezone_finder()
            timezone_str = tf.timezone_at(lat=lat, lng=lon)
            local_tz = pytz.timezone(
                timezone_str) if timezone_str else pytz.UTC

            if api_source == "owm":
                if report_type == "daily_summary":
                    processed_data = self.process_owm_daily_data(
                        forecast_list, local_tz)
                    if not processed_data:
                        raise ValueError("Could not aggregate OWM daily data.")
                    self.generate_owm_daily_pdf(
                        lat, lon, processed_data, location_info)
                    QMessageBox.information(
                        self, "Success", "OWM 5-Day Daily Summary PDF generated!")
                elif report_type == "3hourly_detail":
                    processed_data = self.process_owm_3hourly_data(
                        forecast_list, local_tz)
                    if not processed_data:
                        raise ValueError(
                            "Could not process OWM 3-hourly data.")
                    self.generate_owm_3hourly_pdf(
                        lat, lon, processed_data, location_info)
                    QMessageBox.information(
                        self, "Success", "OWM 5-Day / 3-Hourly Forecast PDF generated!")

            elif api_source == "weatherapi":
                if report_type == "hourly_detail":
                    processed_data = self.process_weatherapi_hourly_data(
                        forecast_list, local_tz)
                    if not processed_data:
                        raise ValueError(
                            "Could not process WeatherAPI hourly data.")
                    self.generate_weatherapi_hourly_pdf(
                        lat, lon, processed_data, location_info)
                    QMessageBox.information(
                        self, "Success", "WeatherAPI 3-Day Hourly Forecast PDF generated!")

        except requests.exceptions.RequestException as e:
            # Pass API source for context
            self._handle_api_error(e, api_source)
        except pytz.exceptions.UnknownTimeZoneError:
            QMessageBox.critical(
                self, "Timezone Error", f"Could not determine timezone for {lat}, {lon}.")
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred:\n{e}")
            import traceback
            print(f"--- Detailed Error ({api_source} / {report_type}) ---")
            traceback.print_exc()
            print("----------------------------------------------------")
        finally:
            QApplication.restoreOverrideCursor()

    def _format_value(self, value, decimal_places=1):
        """Helper method to format numeric values with proper decimal places"""
        try:
            if value in [None, 'N/A', '']:
                return 'N/A'
            if isinstance(value, str):
                value = float(value.replace('%', ''))
            return f"{float(value):.{decimal_places}f}"
        except (ValueError, TypeError):
            return 'N/A'

    def _handle_api_error(self, e, api_source="Unknown"):
        """Centralized handling for API request errors."""
        error_message = f"Error connecting to {api_source} service:\n{e}"
        print(error_message)
        status_code = None
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            print(f"{api_source} Response Status Code: {status_code}")
            # Limit long responses
            print(f"{api_source} Response Text: {e.response.text[:500]}...")

            if status_code == 401 or status_code == 403:  # Unauthorized/Forbidden
                error_message = f"{api_source} API Key Error: Invalid or unauthorized API Key."
            # Bad Request (often invalid location for WeatherAPI)
            elif status_code == 400:
                error_message = f"{api_source} API Error: Bad Request (check location validity)."
                # WeatherAPI specific error code for invalid location
                try:
                    error_json = e.response.json()
                    if error_json.get("error", {}).get("code") == 1006:
                        error_message = f"{api_source} API Error: Location not found or invalid query."
                except json.JSONDecodeError:
                    pass  # Ignore if response is not JSON
            elif status_code == 404:
                error_message = f"{api_source} API Error: Endpoint or Resource not found."
            elif status_code == 429:
                error_message = f"{api_source} API Error: Rate limit exceeded. Please wait."
            else:
                error_message = f"{api_source} API Error: Status Code {status_code}. See console."

        elif isinstance(e, requests.exceptions.Timeout):
            error_message = "Connection Error: The request timed out. Check network connection."
        elif isinstance(e, requests.exceptions.ConnectionError):
            error_message = "Connection Error: Could not connect. Check network/firewall/proxy."

        QMessageBox.critical(self, f"{api_source} API Error", error_message)

    def create_requests_session(self):
        # (No changes needed from previous version with proxy check)
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[
                        500, 502, 503, 504, 404, 408, 429], allowed_methods=["GET"])
        proxies = {}
        http_proxy = os.environ.get(
            'HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get(
            'HTTPS_PROXY') or os.environ.get('https_proxy')
        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        # Manual override:
        # proxies = {'http': '...', 'https': '...'}
        if proxies:
            print(f"Using proxies: {proxies}")
            session.proxies = proxies
        adapter = HTTPAdapter(
            max_retries=retries, pool_connections=3, pool_maxsize=3, pool_block=True)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    # --- OWM Specific Fetching ---
    def fetch_owm_data(self, lat, lon):
        base_url = "https://api.openweathermap.org/data/2.5/"
        units = "metric"
        session = self.create_requests_session()
        timeout = (15, 30)
        current_data = None
        forecast_data = None
        location_info = {'name': 'N/A', 'country': 'N/A',
                         'sunrise': 'N/A', 'sunset': 'N/A', 'source': 'OpenWeatherMap'}

        try:
            # Fetch Current Weather
            current_url = f"{base_url}weather?lat={lat}&lon={lon}&appid={self.owm_api_key}&units={units}"
            print(f"Fetching OWM current: {current_url}")
            current_response = session.get(current_url, timeout=timeout)
            current_response.raise_for_status()
            current_data = current_response.json()

            # Fetch 5-Day/3-Hour Forecast
            forecast_url = f"{base_url}forecast?lat={lat}&lon={lon}&appid={self.owm_api_key}&units={units}"
            print(f"Fetching OWM forecast: {forecast_url}")
            forecast_response = session.get(forecast_url, timeout=timeout)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # --- Process Location Info ---
            tf = self.get_timezone_finder()
            timezone_str = tf.timezone_at(lat=lat, lng=lon)
            local_tz = pytz.timezone(
                timezone_str) if timezone_str else pytz.UTC

            if current_data:
                location_info['name'] = current_data.get(
                    'name', f"OWM ({lat:.4f}, {lon:.4f})")
                if 'sys' in current_data:
                    location_info['country'] = current_data['sys'].get(
                        'country', '')
                    if 'sunrise' in current_data['sys']:
                        location_info['sunrise'] = datetime.fromtimestamp(
                            current_data['sys']['sunrise'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M')
                    if 'sunset' in current_data['sys']:
                        location_info['sunset'] = datetime.fromtimestamp(
                            current_data['sys']['sunset'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M')
            # Fallback using forecast data if current failed but forecast succeeded (less likely)
            elif forecast_data and 'city' in forecast_data:
                location_info['name'] = forecast_data['city'].get(
                    'name', f"OWM ({lat:.4f}, {lon:.4f})")
                location_info['country'] = forecast_data['city'].get(
                    'country', '')
                # Sunrise/sunset might differ slightly if from forecast
                if 'sunrise' in forecast_data['city']:
                    location_info['sunrise'] = datetime.fromtimestamp(
                        forecast_data['city']['sunrise'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M')
                if 'sunset' in forecast_data['city']:
                    location_info['sunset'] = datetime.fromtimestamp(
                        forecast_data['city']['sunset'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M')

            return current_data, forecast_data, location_info

        finally:
            session.close()

    # --- WeatherAPI.com Specific Fetching ---
    def fetch_weatherapi_data(self, lat, lon):
        base_url = "https://api.weatherapi.com/v1/"
        # Free tier allows up to 3 days forecast
        forecast_days = 3
        # Include air quality data (aqi=yes) if needed, otherwise aqi=no
        api_url = f"{base_url}forecast.json?key={self.weatherapi_key}&q={lat},{lon}&days={forecast_days}&aqi=no&alerts=no"

        session = self.create_requests_session()
        timeout = (15, 30)
        api_data = None
        location_info = {'name': 'N/A', 'country': 'N/A',
                         'sunrise': 'N/A', 'sunset': 'N/A', 'source': 'WeatherAPI.com'}

        try:
            print(f"Fetching WeatherAPI: {api_url}")
            response = session.get(api_url, timeout=timeout)
            response.raise_for_status()  # Check for HTTP errors
            api_data = response.json()

            # --- Process Location Info ---
            tf = self.get_timezone_finder()
            timezone_str = tf.timezone_at(lat=lat, lng=lon)
            local_tz = pytz.timezone(
                timezone_str) if timezone_str else pytz.UTC

            if api_data and 'location' in api_data:
                loc = api_data['location']
                location_info['name'] = loc.get(
                    'name', f"WAPI ({lat:.4f}, {lon:.4f})")
                location_info['country'] = loc.get('country', '')
                # Get sunrise/sunset from the first forecast day's astro info
                if 'forecast' in api_data and 'forecastday' in api_data['forecast'] and api_data['forecast']['forecastday']:
                    astro = api_data['forecast']['forecastday'][0].get(
                        'astro', {})
                    # WeatherAPI times are usually local already, but convert for consistency just in case
                    # Need date context for parsing HH:MM AM/PM
                    day_date_str = api_data['forecast']['forecastday'][0].get(
                        'date')
                    if day_date_str:
                        try:
                            day_date = datetime.strptime(
                                day_date_str, '%Y-%m-%d').date()
                            if 'sunrise' in astro:
                                # Combine date with time string, assuming local time already
                                sunrise_dt_naive = datetime.strptime(
                                    f"{day_date_str} {astro['sunrise']}", '%Y-%m-%d %I:%M %p')
                                sunrise_dt_aware = local_tz.localize(
                                    sunrise_dt_naive)  # Make timezone aware
                                location_info['sunrise'] = sunrise_dt_aware.strftime(
                                    '%H:%M')
                            if 'sunset' in astro:
                                sunset_dt_naive = datetime.strptime(
                                    f"{day_date_str} {astro['sunset']}", '%Y-%m-%d %I:%M %p')
                                sunset_dt_aware = local_tz.localize(
                                    sunset_dt_naive)  # Make timezone aware
                                location_info['sunset'] = sunset_dt_aware.strftime(
                                    '%H:%M')
                        except ValueError as time_parse_error:
                            print(
                                f"Warning: Could not parse WeatherAPI sunrise/sunset time: {time_parse_error}")

            return api_data, location_info

        finally:
            session.close()

    def degrees_to_direction(self, degrees):
        # (No changes)
        if degrees is None:
            return 'N/A'
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE',
                      'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        try:
            index = round(float(degrees) / (360 / len(directions))
                          ) % len(directions)
            return directions[index]
        except (ValueError, TypeError):
            return 'N/A'

    # --- OWM Processing Functions ---
    def process_owm_daily_data(self, forecast_list, local_tz):
        # (Largely same as before, ensure no UVI processing)
        daily_aggregated = defaultdict(lambda: {'temps': [], 'feels_like': [], 'humidity': [], 'wind_speed': [
        ], 'wind_gust': [], 'rain': 0.0, 'pop': [], 'descriptions': defaultdict(int), 'wind_directions': []})
        for item in forecast_list:
            try:
                dt_utc = datetime.fromtimestamp(item['dt'], tz=timezone.utc)
                dt_local = dt_utc.astimezone(local_tz)
                local_date_obj = dt_local.date()
                agg = daily_aggregated[local_date_obj]
                if 'main' in item:
                    agg['temps'].append(item['main'].get('temp'))
                    agg['feels_like'].append(item['main'].get('feels_like'))
                    agg['humidity'].append(item['main'].get('humidity'))
                if 'wind' in item:
                    agg['wind_speed'].append(item['wind'].get('speed'))
                    agg['wind_gust'].append(item['wind'].get('gust'))
                    agg['wind_directions'].append(item['wind'].get('deg'))
                agg['rain'] += item.get('rain', {}).get('3h', 0.0)
                agg['pop'].append(item.get('pop'))
                if 'weather' in item and item['weather']:
                    desc = item['weather'][0].get('description', 'N/A')
                    agg['descriptions'][desc] += 1
            except Exception as e:
                print(f"Error OWM daily agg item: {item} -> {e}")
                continue
        processed_daily_list = []
        for day_date, agg_data in sorted(daily_aggregated.items()):
            try:
                temps = [t for t in agg_data['temps'] if t is not None]
                feels = [f for f in agg_data['feels_like'] if f is not None]
                humid = [h for h in agg_data['humidity'] if h is not None]
                wind_s = [w for w in agg_data['wind_speed'] if w is not None]
                wind_g = [g for g in agg_data['wind_gust'] if g is not None]
                pop = [p for p in agg_data['pop'] if p is not None]
                most_common_desc = max(
                    agg_data['descriptions'], key=agg_data['descriptions'].get) if agg_data['descriptions'] else 'N/A'
                peak_wind_dir = 'N/A'
                if wind_s:
                    max_wind_speed = max(wind_s)
                    idx = agg_data['wind_speed'].index(max_wind_speed)
                    peak_wind_dir_deg = agg_data['wind_directions'][idx]
                    peak_wind_dir = self.degrees_to_direction(
                        peak_wind_dir_deg)
                max_wind_knots = round(
                    max(wind_s) * 1.94384, 1) if wind_s else 'N/A'
                max_gust_knots = round(
                    max(wind_g) * 1.94384, 1) if wind_g else 'N/A'
                processed_daily_list.append({'date': day_date.strftime('%Y-%m-%d'), 'description': most_common_desc.title(), 'temp_min': f"{min(temps):.1f}" if temps else 'N/A', 'temp_max': f"{max(temps):.1f}" if temps else 'N/A', 'feels_like_max': f"{max(feels):.1f}" if feels else 'N/A',
                                            'humidity_avg': f"{sum(humid)/len(humid):.0f}" if humid else 'N/A', 'wind_speed': max_wind_knots, 'wind_gust': max_gust_knots, 'wind_direction': peak_wind_dir, 'rain': f"{agg_data['rain']:.1f}", 'pop': math.ceil(max(pop)*100) if pop else 0, })
            except Exception as e:
                print(f"Error OWM daily final agg date {day_date}: {e}")
                continue
        return processed_daily_list

    def process_owm_3hourly_data(self, forecast_list, local_tz):
        # (Largely same as before, remove UVI)
        processed_data = []
        for item in forecast_list:
            try:
                dt_utc = datetime.fromtimestamp(item['dt'], tz=timezone.utc)
                local_time = dt_utc.astimezone(local_tz)
                main = item.get('main', {})
                wind = item.get('wind', {})
                weather = item.get('weather', [{}])[0]
                temp = main.get('temp')
                feels_like = main.get('feels_like')
                humidity = main.get('humidity')
                wind_speed_mps = wind.get('speed')
                wind_gust_mps = wind.get('gust')
                wind_deg = wind.get('deg')
                wind_speed_knots = round(
                    wind_speed_mps * 1.94384, 1) if wind_speed_mps is not None else 'N/A'
                wind_gust_knots = round(
                    wind_gust_mps * 1.94384, 1) if wind_gust_mps is not None else 'N/A'
                wind_direction = self.degrees_to_direction(wind_deg)
                weather_desc = weather.get('description', 'N/A')
                rain_3h = item.get('rain', {}).get('3h', 0.0)
                pop = item.get('pop', 0.0)
                pop_percent = math.ceil(pop * 100)
                visibility = item.get('visibility', 'N/A')
                processed_data.append({'datetime': local_time.strftime('%Y-%m-%d %H:%M'), 'description': weather_desc.title(), 'temperature': f"{temp:.1f}" if temp is not None else 'N/A', 'feels_like': f"{feels_like:.1f}" if feels_like is not None else 'N/A',
                                      'humidity': humidity if humidity is not None else 'N/A', 'wind_speed': wind_speed_knots, 'wind_gust': wind_gust_knots, 'wind_direction': wind_direction, 'rain_3h': f"{rain_3h:.1f}", 'pop': pop_percent, 'visibility': visibility if visibility is not None else 'N/A'})  # No UVI
            except Exception as e:
                print(f"Error processing OWM 3hourly item: {item} -> {e}")
                continue
        return processed_data

    # --- WeatherAPI.com Processing Functions ---
    def process_weatherapi_hourly_data(self, hourly_forecast_list, local_tz):
        """Processes the hourly list from WeatherAPI response."""
        processed_data = []
        for item in hourly_forecast_list:
            try:
                # WeatherAPI timestamp is usually local, parse it and make it aware
                dt_str = item.get('time')  # e.g., "2023-10-27 00:00"
                if not dt_str:
                    continue  # Skip if time is missing

                try:
                    # Attempt to parse assuming local time - this might need adjustment if API format changes
                    dt_naive = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
                    # Assign the determined local timezone
                    dt_aware_local = local_tz.localize(dt_naive)
                    datetime_str = dt_aware_local.strftime('%Y-%m-%d %H:%M')
                except ValueError as time_parse_error:
                    print(
                        f"Warning: Could not parse WeatherAPI time '{dt_str}': {time_parse_error}")
                    # Include raw time with error notice
                    datetime_str = dt_str + " (Time Parsing Error)"

                temp = item.get('temp_c')
                feels_like = item.get('feelslike_c')
                humidity = item.get('humidity')
                condition = item.get('condition', {})
                weather_desc = condition.get('text', 'N/A')

                # WeatherAPI provides wind in kph, convert to knots
                wind_kph = item.get('wind_kph')
                wind_gust_kph = item.get('gust_kph')
                wind_deg = item.get('wind_degree')

                # Conversion: 1 kph = 0.539957 knots
                wind_speed_knots = round(
                    wind_kph * 0.539957, 1) if wind_kph is not None else 'N/A'
                wind_gust_knots = round(
                    wind_gust_kph * 0.539957, 1) if wind_gust_kph is not None else 'N/A'

                wind_direction = self.degrees_to_direction(wind_deg)

                # WeatherAPI provides rain in mm (precip_mm) - likely per hour
                rain_mm = item.get('precip_mm', 0.0)
                pop = item.get('chance_of_rain', 0)  # Already percentage
                visibility_km = item.get('vis_km')
                visibility_m = round(
                    visibility_km * 1000) if visibility_km is not None else 'N/A'

                processed_data.append({
                    'datetime': datetime_str,
                    'description': weather_desc.title(),
                    'temperature': f"{temp:.1f}" if temp is not None else 'N/A',
                    'feels_like': f"{feels_like:.1f}" if feels_like is not None else 'N/A',
                    'humidity': humidity if humidity is not None else 'N/A',
                    'wind_speed': wind_speed_knots,
                    'wind_gust': wind_gust_knots,
                    'wind_direction': wind_direction,
                    'rain_hourly': f"{rain_mm:.1f}",  # Rain per hour
                    'pop': int(pop),  # Already %
                    'visibility': visibility_m
                })
            except Exception as e:
                print(
                    f"Error processing WeatherAPI hourly item: {item} -> {e}")
                continue
        return processed_data

    # --- Chart and PDF Base Functions ---
    # create_chart (Use version with BytesIO from previous answer - no changes needed)

    def create_chart(self, dates, values, param_name, ylabel, title):
        if not dates or not values or len(dates) != len(values):
            return None
        valid_indices = [i for i, v in enumerate(
            values) if isinstance(v, (int, float))]
        if not valid_indices:
            return None
        chart_dates = [dates[i] for i in valid_indices]
        chart_values = [values[i] for i in valid_indices]
        if not chart_dates:
            return None
        plt.figure(figsize=(10, 3))
        plt.plot(chart_dates, chart_values, marker='.', linestyle='-')
        plt.title(title)
        plt.xlabel('Date/Time')
        plt.ylabel(ylabel)
        plt.xticks(rotation=30, ha='right')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        img_buffer = BytesIO()
        try:
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)
            img = Image(img_buffer, width=7 * inch, height=2.5 * inch)
            img.hAlign = 'CENTER'
            return img
        except Exception as e:
            print(f"Error creating chart image for {title}: {e}")
            plt.close()
            return None

    def _generate_base_pdf_elements(self, lat, lon, location_info, report_title_suffix):
        # (Add API source)
        elements = []
        styles = getSampleStyleSheet()

    # Add custom 'small' style
        styles.add(
            ParagraphStyle(
                name='small',
                parent=styles['Normal'],
                fontSize=8,
                leading=10,
                textColor=colors.grey
            )
        )

        title_style = styles['h1']
        title_style.alignment = Qt.AlignCenter
        normal_style = styles['Normal']
        normal_style.leading = 14
        italic_style = styles['Italic']

        elements.append(
            Paragraph(f"Weather Forecast Report - {report_title_suffix}", title_style))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            f"<b>GPS Coordinates:</b> Latitude: {lat:.4f}, Longitude: {lon:.4f}", normal_style))
        loc_name = location_info.get('name', 'N/A')
        loc_country = location_info.get('country', '')
        elements.append(
            Paragraph(f"<b>Location:</b> {loc_name} {loc_country}", normal_style))
        elements.append(Paragraph(
            f"<b>Sunrise:</b> {location_info.get('sunrise', 'N/A')}, <b>Sunset:</b> {location_info.get('sunset', 'N/A')}", normal_style))
        elements.append(Paragraph(
            f"<i>Data Source: {location_info.get('source', 'Unknown API')}</i>", italic_style))
        elements.append(Spacer(1, 0.2*inch))
        return elements, styles

    def _apply_min_max_highlighting(self, table_data, style, param_columns):
        # (No changes needed)
        for param, col_idx in param_columns.items():
            col_values = []
            for row_idx, row in enumerate(table_data[1:], 1):
                try:
                    value_str = str(row[col_idx]).replace('%', '').strip()
                    if value_str not in ['N/A', '']:
                        value = float(value_str)
                        col_values.append((value, row_idx))
                except (ValueError, TypeError, IndexError):
                    continue
            if col_values:
                try:
                    min_val_tuple = min(col_values, key=lambda x: x[0])
                    max_val_tuple = max(col_values, key=lambda x: x[0])
                    style.add(
                        'BACKGROUND', (col_idx, min_val_tuple[1]), (col_idx, min_val_tuple[1]), colors.lightblue)
                    style.add(
                        'BACKGROUND', (col_idx, max_val_tuple[1]), (col_idx, max_val_tuple[1]), colors.pink)
                except Exception as e:
                    print(
                        f"Warning: Could not highlight min/max for col {col_idx} ({param}): {e}")

    # --- OWM PDF Generation Functions (Remove UVI) ---
    def generate_owm_daily_pdf(self, lat, lon, weather_data, location_info):
        location_name_safe = location_info.get('name', 'Unknown').replace(' ', '_').replace(
            '/', '_').replace('\\', '_').replace('(', '').replace(')', '').replace(',', '')
        file_name = f"OWM_Report_DailySummary_{location_name_safe}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        doc = SimpleDocTemplate(file_name, pagesize=landscape(
            letter), topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
        elements, styles = self._generate_base_pdf_elements(
            lat, lon, location_info, "OWM 5-Day Daily Summary")
        normal_style = styles['Normal']
        # Headers without UV
        headers = ["Date", "Description", "Temp\nMin/Max\n(°C)", "Feels Like\nMax (°C)", "Humidity\nAvg (%)",
                   "Wind Max\n(knots)", "Gust Max\n(knots)", "Wind\nDir", "Rain Total\n(mm)", "POP Max\n(%)"]
        table_data = [headers]
        for item in weather_data:
            row = [item['date'], item['description'], f"{item['temp_min']} / {item['temp_max']}", str(item['feels_like_max']), str(
                item['humidity_avg']), str(item['wind_speed']), str(item['wind_gust']), str(item['wind_direction']), str(item['rain']), f"{item['pop']}%"]
            table_data.append(row)
        # Col widths adjusted
        col_widths = [75, 120, 75, 75, 75, 75, 75, 50, 70, 70]
        table = Table(table_data, repeatRows=1, colWidths=col_widths)
        style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 10), ('FONTNAME', (0, 1),
                           (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 1), (-1, -1), 4), ('BOTTOMPADDING', (0, 1), (-1, -1), 4), ('GRID', (0, 0), (-1, -1), 1, colors.black), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightblue])])
        # Highlight columns (adjust indices)
        daily_param_columns = {'temp_max': 2, 'feels_like_max': 3,
                               'humidity_avg': 4, 'wind_speed': 5, 'wind_gust': 6, 'rain': 8, 'pop': 9}
        self._apply_min_max_highlighting(
            table_data, style, daily_param_columns)
        table.setStyle(style)
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        # Charts (No UVI chart)
        chart_heading_style = styles['h2']
        chart_heading_style.alignment = 1
        elements.append(
            Paragraph("<b>OWM Daily Trends</b>", chart_heading_style))
        elements.append(Spacer(1, 0.1*inch))
        daily_chart_params = [('temp_max', '°C', 'Max Temperature Trend'), ('humidity_avg', '%', 'Average Humidity Trend'), ('wind_speed',
                                                                                                                             'knots', 'Max Wind Speed Trend'), ('pop', '%', 'Max Precipitation Probability Trend'), ('rain', 'mm', 'Total Daily Rainfall Trend'), ]
        chart_dates = [datetime.strptime(
            item['date'], '%Y-%m-%d') for item in weather_data]
        charts_created = 0
        for param, unit, title in daily_chart_params:
            values = [float(item[param]) if item.get(param) not in [
                None, 'N/A'] else None for item in weather_data]
            chart = self.create_chart(
                chart_dates, values, f"owm_daily_{param}", unit, title)
            if chart:
                elements.append(chart)
                elements.append(Spacer(1, 0.1*inch))
                charts_created += 1
            else:
                print(f"Could not create OWM daily chart for: {param}")
        if charts_created == 0:
            elements.append(
                Paragraph("No chart data available.", normal_style))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['small']))
        try:
            doc.build(elements)
            print(f"OWM Daily PDF generated: {file_name}")
        except Exception as e:
            QMessageBox.critical(
                self, "PDF Error", f"Failed to build OWM Daily PDF:\n{e}")
            print(f"Error OWM Daily PDF: {e}")

    def generate_owm_3hourly_pdf(self, lat, lon, weather_data, location_info):
        location_name_safe = location_info.get('name', 'Unknown').replace(' ', '_').replace(
            '/', '_').replace('\\', '_').replace('(', '').replace(')', '').replace(',', '')
        file_name = f"OWM_Report_3Hourly_{location_name_safe}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        doc = SimpleDocTemplate(file_name, pagesize=landscape(
            letter), topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
        elements, styles = self._generate_base_pdf_elements(
            lat, lon, location_info, "OWM 5-Day / 3-Hourly Detail")
        normal_style = styles['Normal']
        # Headers without UV
        headers = ["Date/Time", "Desc.", "Temp\n(°C)", "Feels\nLike(°C)", "Humid\n(%)", "Wind\n(knots)",
                   "Gust\n(knots)", "Dir", "Rain\n(Last 3h)", "POP\n(%)", "Visibility\n(m)"]

        # Define decimal places for different parameters
        dp = {
            'temperature': 1,
            'feels_like': 1,
            'humidity': 0,
            'wind_speed': 1,
            'wind_gust': 1,
            'rain_3h': 1,
            'visibility': 0
        }

        table_data = [headers]
        for item in weather_data:
            # Format numeric values with proper decimal places
            row = [
                item['datetime'],
                item['description'],
                self._format_value(item['temperature'], dp['temperature']),
                self._format_value(item['feels_like'], dp['feels_like']),
                self._format_value(item['humidity'], dp['humidity']),
                self._format_value(item['wind_speed'], dp['wind_speed']),
                self._format_value(item['wind_gust'], dp['wind_gust']),
                str(item['wind_direction']),
                self._format_value(item['rain_3h'], dp['rain_3h']),
                f"{item['pop']}%",
                self._format_value(item['visibility'], dp['visibility'])
            ]
            table_data.append(row)

        # Col widths adjusted
        col_widths = [95, 90, 50, 50, 50, 60, 60, 35, 65, 50, 70]
        table = Table(table_data, repeatRows=1, colWidths=col_widths)
        style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 9), ('FONTNAME', (0, 1),
                           (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, 0), 6), ('TOPPADDING', (0, 1), (-1, -1), 3), ('BOTTOMPADDING', (0, 1), (-1, -1), 3), ('GRID', (0, 0), (-1, -1), 1, colors.black), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightblue])])
        # Highlight columns (adjust indices)
        hourly_param_columns = {'temperature': 2, 'feels_like': 3, 'humidity': 4,
                                'wind_speed': 5, 'wind_gust': 6, 'rain_3h': 8, 'pop': 9, 'visibility': 10, }
        self._apply_min_max_highlighting(
            table_data, style, hourly_param_columns)
        table.setStyle(style)
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        # Charts (No UVI)
        chart_heading_style = styles['h2']
        chart_heading_style.alignment = 1
        elements.append(
            Paragraph("<b>OWM 3-Hourly Trends</b>", chart_heading_style))
        elements.append(Spacer(1, 0.1*inch))
        hourly_chart_params = [('temperature', '°C', 'Temperature Trend'), ('humidity', '%', 'Humidity Trend'), ('wind_speed', 'knots', 'Wind Speed Trend'), (
            'pop', '%', 'Precipitation Probability Trend'), ('rain_3h', 'mm', 'Rainfall (in previous 3h) Trend'), ('visibility', 'm', 'Visibility Trend'), ]
        chart_dates = [datetime.strptime(
            item['datetime'], '%Y-%m-%d %H:%M') for item in weather_data]
        charts_created = 0
        for param, unit, title in hourly_chart_params:
            values = []
            for item in weather_data:
                val = item.get(param, 'N/A')
                try:
                    values.append(float(val.replace('%', '')) if val not in [
                                  None, 'N/A'] else None)  # Handle pop %
                except:
                    values.append(None)
            chart = self.create_chart(
                chart_dates, values, f"owm_3hourly_{param}", unit, title)
            if chart:
                elements.append(chart)
                elements.append(Spacer(1, 0.1*inch))
                charts_created += 1
            else:
                print(f"Could not create OWM 3h chart for: {param}")
        if charts_created == 0:
            elements.append(
                Paragraph("No chart data available.", normal_style))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['small']))
        try:
            doc.build(elements)
            print(f"OWM 3-Hourly PDF generated: {file_name}")
        except Exception as e:
            QMessageBox.critical(
                self, "PDF Error", f"Failed to build OWM 3-Hourly PDF:\n{e}")
            print(f"Error OWM 3h PDF: {e}")

    # --- WeatherAPI.com PDF Generation Function (Remove UVI) ---
    def generate_weatherapi_hourly_pdf(self, lat, lon, weather_data, location_info):
        location_name_safe = location_info.get('name', 'Unknown').replace(' ', '_').replace(
            '/', '_').replace('\\', '_').replace('(', '').replace(')', '').replace(',', '')
        file_name = f"WeatherAPI_Report_Hourly_{location_name_safe}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        doc = SimpleDocTemplate(file_name, pagesize=landscape(
            letter), topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
        elements, styles = self._generate_base_pdf_elements(
            lat, lon, location_info, "WeatherAPI 3-Day Hourly Detail")
        normal_style = styles['Normal']
        # Headers without UV
        headers = ["Date/Time", "Desc.", "Temp\n(°C)", "Feels\nLike(°C)", "Humid\n(%)",
                   "Wind\n(knots)", "Gust\n(knots)", "Dir", "Rain\n(Hrly)", "POP\n(%)", "Visibility\n(m)"]
        table_data = [headers]
        for item in weather_data:
            row = [item['datetime'], item['description'], str(item['temperature']), str(item['feels_like']), str(item['humidity']), str(
                item['wind_speed']), str(item['wind_gust']), str(item['wind_direction']), str(item['rain_hourly']), f"{item['pop']}%", str(item['visibility'])]
            table_data.append(row)
        # Col widths adjusted
        col_widths = [95, 90, 50, 50, 50, 60, 60, 35,
                      60, 50, 70]  # Adjusted rain col width
        table = Table(table_data, repeatRows=1, colWidths=col_widths)
        style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.darkcyan), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 9), ('FONTNAME', (0, 1),
                           (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, 0), 6), ('TOPPADDING', (0, 1), (-1, -1), 3), ('BOTTOMPADDING', (0, 1), (-1, -1), 3), ('GRID', (0, 0), (-1, -1), 1, colors.black), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightcyan])])
        # Highlight columns (adjust indices)
        hourly_param_columns = {'temperature': 2, 'feels_like': 3, 'humidity': 4,
                                'wind_speed': 5, 'wind_gust': 6, 'rain_hourly': 8, 'pop': 9, 'visibility': 10, }
        self._apply_min_max_highlighting(
            table_data, style, hourly_param_columns)
        table.setStyle(style)
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        # Charts (No UVI)
        chart_heading_style = styles['h2']
        chart_heading_style.alignment = 1
        elements.append(
            Paragraph("<b>WeatherAPI Hourly Trends</b>", chart_heading_style))
        elements.append(Spacer(1, 0.1*inch))
        hourly_chart_params = [('temperature', '°C', 'Temperature Trend'), ('humidity', '%', 'Humidity Trend'), ('wind_speed', 'knots', 'Wind Speed Trend'), (
            'pop', '%', 'Precipitation Probability Trend'), ('rain_hourly', 'mm', 'Hourly Rainfall Trend'), ('visibility', 'm', 'Visibility Trend'), ]
        # Need robust date parsing for charts as errors might exist
        chart_dates = []
        for item in weather_data:
            try:
                # Re-parse the processed datetime string for chart plotting
                dt_str_processed = item['datetime'].split(
                    " (")[0]  # Remove error string if present
                chart_dates.append(datetime.strptime(
                    dt_str_processed, '%Y-%m-%d %H:%M'))
            except ValueError:
                chart_dates.append(None)  # Append None if date parsing fails

        charts_created = 0
        for param, unit, title in hourly_chart_params:
            values = []
            dates_for_chart = []  # Use only dates corresponding to valid values
            for i, item in enumerate(weather_data):
                if chart_dates[i] is None:
                    continue  # Skip if date failed parsing
                val = item.get(param, 'N/A')
                try:
                    val_float = float(val.replace('%', '')) if val not in [
                        None, 'N/A'] else None
                    if val_float is not None:
                        values.append(val_float)
                        dates_for_chart.append(chart_dates[i])
                except:
                    continue  # Skip if value conversion fails

            if dates_for_chart and values:  # Ensure we have data to plot
                chart = self.create_chart(
                    dates_for_chart, values, f"wapi_hourly_{param}", unit, title)
                if chart:
                    elements.append(chart)
                    elements.append(Spacer(1, 0.1*inch))
                    charts_created += 1
                else:
                    print(f"Could not create WeatherAPI chart for: {param}")
            else:
                print(
                    f"No valid data/dates to plot WeatherAPI chart for: {param}")

        if charts_created == 0:
            elements.append(
                Paragraph("No chart data available.", normal_style))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['small']))
        try:
            doc.build(elements)
            print(f"WeatherAPI Hourly PDF generated: {file_name}")
        except Exception as e:
            QMessageBox.critical(
                self, "PDF Error", f"Failed to build WeatherAPI Hourly PDF:\n{e}")
            print(f"Error WeatherAPI PDF: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Perform API key checks after app object is created but before showing window
    weather_app = WeatherCrawlerApp()
    keys_ok = True
    if not weather_app.owm_api_key or weather_app.owm_api_key == "YOUR_OPENWEATHERMAP_API_KEY":
        QMessageBox.critical(
            None, "API Key Error", "OpenWeatherMap API key not set. Please edit the script and restart.")
        keys_ok = False
    if not weather_app.weatherapi_key or weather_app.weatherapi_key == "YOUR_WEATHERAPI_COM_KEY":
        QMessageBox.critical(
            None, "API Key Error", "WeatherAPI.com key not set. Please edit the script and restart.")
        keys_ok = False

    if keys_ok:
        weather_app.show()
        sys.exit(app.exec_())
    else:
        sys.exit()  # Exit if keys are missing
