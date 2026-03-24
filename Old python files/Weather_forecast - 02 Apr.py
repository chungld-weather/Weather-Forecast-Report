# -*- coding: utf-8 -*-
# Add this line at the top for better Unicode handling

import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QRadioButton,
                             QMessageBox)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm  # Add cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, letter
import requests
import json
from datetime import datetime, timedelta, timezone
import pytz
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image
from bs4 import BeautifulSoup  # Import BeautifulSoup
import re  # Import re for potential regex use
from urllib.parse import urljoin  # Import urljoin

# Remove this line:
# from timezonefinder import TimezoneFinder

# Update LOCATION_TIMEZONES dictionary with 100 popular countries
LOCATION_TIMEZONES = {
    # Southeast Asia (existing)
    'VN': 'Asia/Ho_Chi_Minh',    # Vietnam
    'ID': 'Asia/Jakarta',        # Indonesia
    'MY': 'Asia/Kuala_Lumpur',   # Malaysia
    'SG': 'Asia/Singapore',      # Singapore
    'TH': 'Asia/Bangkok',        # Thailand
    'PH': 'Asia/Manila',         # Philippines

    # East Asia
    'CN': 'Asia/Shanghai',       # China
    'JP': 'Asia/Tokyo',          # Japan
    'KR': 'Asia/Seoul',          # South Korea
    'TW': 'Asia/Taipei',         # Taiwan
    'HK': 'Asia/Hong_Kong',      # Hong Kong

    # South Asia
    'IN': 'Asia/Kolkata',        # India
    'PK': 'Asia/Karachi',        # Pakistan
    'BD': 'Asia/Dhaka',          # Bangladesh
    'LK': 'Asia/Colombo',        # Sri Lanka
    'NP': 'Asia/Kathmandu',      # Nepal

    # Middle East
    'AE': 'Asia/Dubai',          # United Arab Emirates
    'SA': 'Asia/Riyadh',         # Saudi Arabia
    'QA': 'Asia/Qatar',          # Qatar
    'IL': 'Asia/Jerusalem',      # Israel
    'TR': 'Europe/Istanbul',     # Turkey

    # Europe
    'GB': 'Europe/London',       # United Kingdom
    'DE': 'Europe/Berlin',       # Germany
    'FR': 'Europe/Paris',        # France
    'IT': 'Europe/Rome',         # Italy
    'ES': 'Europe/Madrid',       # Spain
    'PT': 'Europe/Lisbon',       # Portugal
    'NL': 'Europe/Amsterdam',    # Netherlands
    'BE': 'Europe/Brussels',     # Belgium
    'CH': 'Europe/Zurich',       # Switzerland
    'SE': 'Europe/Stockholm',    # Sweden
    'NO': 'Europe/Oslo',         # Norway
    'DK': 'Europe/Copenhagen',   # Denmark
    'FI': 'Europe/Helsinki',     # Finland
    'PL': 'Europe/Warsaw',       # Poland
    'AT': 'Europe/Vienna',       # Austria
    'GR': 'Europe/Athens',       # Greece
    'IE': 'Europe/Dublin',       # Ireland
    'RU': 'Europe/Moscow',       # Russia

    # North America
    'US': 'America/New_York',    # United States
    'CA': 'America/Toronto',     # Canada
    'MX': 'America/Mexico_City',  # Mexico

    # Central America
    'PA': 'America/Panama',      # Panama
    'CR': 'America/Costa_Rica',  # Costa Rica
    'GT': 'America/Guatemala',   # Guatemala

    # South America
    'BR': 'America/Sao_Paulo',   # Brazil
    'AR': 'America/Buenos_Aires',  # Argentina
    'CL': 'America/Santiago',    # Chile
    'CO': 'America/Bogota',      # Colombia
    'PE': 'America/Lima',        # Peru
    'VE': 'America/Caracas',     # Venezuela

    # Oceania
    'AU': 'Australia/Sydney',    # Australia
    'NZ': 'Pacific/Auckland',    # New Zealand
    'FJ': 'Pacific/Fiji',        # Fiji

    # Africa
    'ZA': 'Africa/Johannesburg',  # South Africa
    'EG': 'Africa/Cairo',        # Egypt
    'MA': 'Africa/Casablanca',   # Morocco
    'NG': 'Africa/Lagos',        # Nigeria
    'KE': 'Africa/Nairobi',      # Kenya
    'ET': 'Africa/Addis_Ababa',  # Ethiopia

    # Additional European countries
    'UA': 'Europe/Kiev',         # Ukraine
    'RO': 'Europe/Bucharest',    # Romania
    'CZ': 'Europe/Prague',       # Czech Republic
    'HU': 'Europe/Budapest',     # Hungary
    'BG': 'Europe/Sofia',        # Bulgaria
    'SK': 'Europe/Bratislava',   # Slovakia
    'HR': 'Europe/Zagreb',       # Croatia
    'RS': 'Europe/Belgrade',     # Serbia

    # Additional Asian countries
    'KZ': 'Asia/Almaty',         # Kazakhstan
    'UZ': 'Asia/Tashkent',       # Uzbekistan
    'MM': 'Asia/Yangon',         # Myanmar
    'KH': 'Asia/Phnom_Penh',     # Cambodia
    'LA': 'Asia/Vientiane',      # Laos

    # Additional American countries
    'EC': 'America/Guayaquil',   # Ecuador
    'BO': 'America/La_Paz',      # Bolivia
    'PY': 'America/Asuncion',    # Paraguay
    'UY': 'America/Montevideo',  # Uruguay

    # Additional African countries
    'DZ': 'Africa/Algiers',      # Algeria
    'TN': 'Africa/Tunis',        # Tunisia
    'GH': 'Africa/Accra',        # Ghana
    'CI': 'Africa/Abidjan',      # Ivory Coast
    'CM': 'Africa/Douala',       # Cameroon
    'SN': 'Africa/Dakar',        # Senegal
    'UG': 'Africa/Kampala',      # Uganda
    'TZ': 'Africa/Dar_es_Salaam',  # Tanzania

    # Additional Middle Eastern countries
    'IQ': 'Asia/Baghdad',        # Iraq
    'IR': 'Asia/Tehran',         # Iran
    'JO': 'Asia/Amman',          # Jordan
    'KW': 'Asia/Kuwait',         # Kuwait
    'LB': 'Asia/Beirut',         # Lebanon
    'OM': 'Asia/Muscat',         # Oman
    'BH': 'Asia/Bahrain',        # Bahrain

    # Additional Pacific countries
    'PG': 'Pacific/Port_Moresby',  # Papua New Guinea
    'NC': 'Pacific/Noumea',      # New Caledonia
    'VU': 'Pacific/Efate',       # Vanuatu

    # Caribbean countries
    'CU': 'America/Havana',      # Cuba
    'DO': 'America/Santo_Domingo',  # Dominican Republic
    'JM': 'America/Jamaica',     # Jamaica
    'BS': 'America/Nassau',      # Bahamas
    'BB': 'America/Barbados',    # Barbados
    'TT': 'America/Port_of_Spain'  # Trinidad and Tobago
}

DEFAULT_TIMEZONE = 'Asia/Ho_Chi_Minh'  # Default to Vietnam timezone


class WeatherCrawlerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather Reporter")
        self.setGeometry(200, 200, 540, 255)  # Adjust window size

        # Add window icon
        icon_path = "weather_icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file {icon_path} not found")

        self.default_lat = 7.5783
        self.default_lon = 108.8694

        # Replace with your API key - DONE
        self.api_key = "e1a69775e0d7c149a4e2bdb69bb59a82"

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Input Options Section
        input_layout = QVBoxLayout()
        input_label = QLabel("Locations:")
        input_label.setFont(QFont("Arial", 12, QFont.Bold))
        input_layout.addWidget(input_label)

        self.gps_radio = QRadioButton("Enter GPS Coordinates:")
        self.default_radio = QRadioButton(
            "Lan Tay Platform - Default Location")
        self.default_radio.setChecked(True)  # Default selected

        self.lat_label = QLabel("Latitude:")
        self.lat_input = QLineEdit()
        self.lon_label = QLabel("Longitude:")
        self.lon_input = QLineEdit()
        self.lat_input.setEnabled(False)  # Disabled by default
        self.lon_input.setEnabled(False)

        gps_input_layout = QHBoxLayout()
        gps_input_layout.addWidget(self.lat_label)
        gps_input_layout.addWidget(self.lat_input)
        gps_input_layout.addWidget(self.lon_label)
        gps_input_layout.addWidget(self.lon_input)

        input_layout.addWidget(self.gps_radio)
        input_layout.addLayout(gps_input_layout)
        input_layout.addWidget(self.default_radio)

        self.gps_radio.toggled.connect(self.toggle_gps_input)
        self.default_radio.toggled.connect(self.toggle_gps_input)

        # Define locations
        self.locations = {
            'Lan Tay Platform': (7.5783, 108.8694),
            'Rong Doi Platform': (7.7925, 108.2021),
            'An Phu Office': (10.809427, 106.736553),
            'Vung Tau Airport': (10.376001, 107.093239)
        }

        # Input Options Section
        input_layout = QVBoxLayout()
        input_label = QLabel("Locations:")
        input_label.setFont(QFont("Arial", 12, QFont.Bold))
        input_layout.addWidget(input_label)

        # GPS Radio button group
        self.gps_radio = QRadioButton("Enter GPS Coordinates:")
        gps_input_layout = QHBoxLayout()
        gps_input_layout.addWidget(self.lat_label)
        gps_input_layout.addWidget(self.lat_input)
        gps_input_layout.addWidget(self.lon_label)
        gps_input_layout.addWidget(self.lon_input)

        # Add predefined locations
        self.location_radios = {}
        for name, coords in self.locations.items():
            radio = QRadioButton(
                f"{name}      ({coords[0]}, {coords[1]})")
            self.location_radios[name] = radio
            input_layout.addWidget(radio)
            radio.toggled.connect(self.toggle_gps_input)

        # Set default selection
        self.location_radios['Lan Tay Platform'].setChecked(True)

        input_layout.addWidget(self.gps_radio)
        input_layout.addLayout(gps_input_layout)

        # Result Options Section
        result_layout = QVBoxLayout()
        result_layout.setSpacing(0)  # Reduce spacing between widgets

        # Result Options Section
        result_label_layout = QHBoxLayout()
        result_label = QLabel("Create Report")
        result_label.setFont(QFont("Arial", 12, QFont.Bold))
        result_label.setAlignment(Qt.AlignCenter)  # Center align the text
        result_label_layout.addStretch()
        result_label_layout.addWidget(result_label)
        result_label_layout.addStretch()

        # Add the result_label_layout to result_layout
        result_layout.addLayout(result_label_layout)

        # Crawl Button
        crawl_button = QPushButton("Crawl Weather Data - Generate PDF")
        crawl_button.clicked.connect(self.crawl_weather_data)

        main_layout.addLayout(input_layout)
        main_layout.addLayout(result_layout)
        main_layout.addWidget(crawl_button)

        self.setLayout(main_layout)

    def toggle_gps_input(self):
        # if self.gps_radio.isChecked():
        #     self.lat_input.setEnabled(True)
        #     self.lon_input.setEnabled(True)
        # else:
        #     self.lat_input.setEnabled(False)
        #     self.lon_input.setEnabled(False)
        self.lat_input.setEnabled(self.gps_radio.isChecked())
        self.lon_input.setEnabled(self.gps_radio.isChecked())

    def get_coordinates(self):
        if self.gps_radio.isChecked():
            try:
                lat = float(self.lat_input.text())
                lon = float(self.lon_input.text())
                return lat, lon
            except ValueError:
                QMessageBox.warning(
                    self, "Input Error", "Invalid Latitude or Longitude. Please enter numbers.")
                return None, None
        else:
            # Check which location is selected
            for name, radio in self.location_radios.items():
                if radio.isChecked():
                    return self.locations[name]
        return None, None

    def crawl_weather_data(self):
        lat, lon = self.get_coordinates()
        if lat is None:  # Error already shown in get_coordinates
            return

        data_type = "forecast"  # Only one option now

        try:
            weather_data, location_info = self.fetch_weather_data(
                lat, lon, data_type)
            if weather_data:
                self.generate_pdf_report(
                    lat, lon, weather_data, data_type, location_info)
                QMessageBox.information(
                    self, "Success", "Weather data crawled and PDF report generated successfully!")
            else:
                QMessageBox.warning(
                    self, "Error", "Failed to fetch weather data.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def create_requests_session(self):
        session = requests.Session()
        retries = Retry(
            total=5,  # Increased from 3 to 5 retries
            backoff_factor=1,  # Increased from 0.5 to 1 second
            # Added timeout (408) and rate limit (429)
            status_forcelist=[500, 502, 503, 504, 404, 408, 429],
            allowed_methods=["GET"],  # Explicitly allow GET methods
        )
        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=3,
            pool_maxsize=3,
            pool_block=True
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def fetch_weather_data(self, lat, lon, data_type):
        base_url = "https://api.openweathermap.org/data/2.5/"
        units = "metric"
        session = self.create_requests_session()
        timeout = (15, 30)  # (connection timeout, read timeout)

        try:
            # Get current weather for location info and sun times
            try:
                current_url = f"{base_url}weather?lat={lat}&lon={lon}&appid={self.api_key}&units={units}"
                current_response = session.get(current_url, timeout=timeout)
                current_response.raise_for_status()
                current_data = current_response.json()

                forecast_url = f"{base_url}forecast?lat={lat}&lon={lon}&appid={self.api_key}&units={units}&cnt=40"
                forecast_response = session.get(forecast_url, timeout=timeout)
                forecast_response.raise_for_status()
                forecast_data = forecast_response.json()

                # Get timezone based on country code
                country_code = current_data.get('sys', {}).get('country', 'VN')
                timezone_str = LOCATION_TIMEZONES.get(
                    country_code, DEFAULT_TIMEZONE)
                local_tz = pytz.timezone(timezone_str)

                # Handle cases where country code might be missing
                location_info = {
                    'name': current_data.get('name', 'Unknown Location'),
                    'country': current_data.get('sys', {}).get('country', 'N/A'),
                    'sunrise': datetime.fromtimestamp(
                        current_data['sys']['sunrise'],
                        tz=timezone.utc
                    ).astimezone(local_tz).strftime('%H:%M') if 'sunrise' in current_data.get('sys', {}) else 'N/A',
                    'sunset': datetime.fromtimestamp(
                        current_data['sys']['sunset'],
                        tz=timezone.utc
                    ).astimezone(local_tz).strftime('%H:%M') if 'sunset' in current_data.get('sys', {}) else 'N/A'
                }

                result = self.process_forecast_data(
                    forecast_data), location_info
                return result

            except requests.exceptions.Timeout as e:
                QMessageBox.warning(
                    self, "Timeout", "Request timed out. Retrying...")
                raise e

        except requests.exceptions.Timeout:
            QMessageBox.critical(self, "Connection Error",
                                 "The connection timed out. Please check your internet connection and try again.")
            return None, None
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Connection Error",
                                 "Failed to connect to the weather service. Please check your network connection.")
            return None, None
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error",
                                 f"An error occurred while fetching weather data:\n{str(e)}")
            return None, None
        finally:
            session.close()

    def process_forecast_data(self, data):
        def degrees_to_direction(degrees):
            directions = [
                'N', 'NNE', 'NE', 'ENE',
                'E', 'ESE', 'SE', 'SSE',
                'S', 'SSW', 'SW', 'WSW',
                'W', 'WNW', 'NW', 'NNW'
            ]
            index = round(degrees / (360 / len(directions))) % len(directions)
            return directions[index]

        processed_data = []

        # Get timezone based on country code
        country_code = data['city'].get(
            'country', 'VN')  # Default to VN if not found
        timezone_str = LOCATION_TIMEZONES.get(country_code, DEFAULT_TIMEZONE)
        local_tz = pytz.timezone(timezone_str)

        for item in data['list']:
            try:
                dt_txt = item['dt_txt']
                # Parse UTC time
                dt_object = datetime.strptime(dt_txt, '%Y-%m-%d %H:%M:%S')
                dt_object = dt_object.replace(tzinfo=timezone.utc)
                # Convert to local time
                local_time = dt_object.astimezone(local_tz)

                if local_time > datetime.now(local_tz) and local_time <= datetime.now(local_tz) + timedelta(days=5):
                    weather_desc = item['weather'][0]['description']
                    temp = float(item['main']['temp'])
                    humidity = float(item['main']['humidity'])
                    # Convert to knots
                    wind_speed = float(item['wind']['speed']) * 1.94384

                    # Handle wind gust more carefully
                    wind_gust = item['wind'].get('gust', 'N/A')
                    if wind_gust != 'N/A':
                        try:
                            wind_gust = float(wind_gust) * \
                                1.94384449  # Convert to knots
                        except (ValueError, TypeError):
                            wind_gust = 'N/A'

                    wind_deg = item['wind']['deg']
                    wind_direction = degrees_to_direction(wind_deg)
                    rain = float(item.get('rain', {}).get('3h', 0))

                    # Handle visibility
                    try:
                        visibility = float(item.get('visibility', 0))
                    except (ValueError, TypeError):
                        visibility = 'N/A'

                    # Add precipitation probability (multiply by 100 to get percentage)
                    pop = float(item.get('pop', 0)) * 100

                    processed_data.append({
                        'datetime': local_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'description': weather_desc,
                        'temperature': temp,
                        'humidity': humidity,
                        'wind_speed': round(wind_speed, 1),
                        'wind_gust': round(wind_gust, 1) if wind_gust != 'N/A' else 'N/A',
                        'wind_direction': wind_direction,
                        'rain': rain,
                        'visibility': visibility,
                        'pop': pop
                    })
            except Exception as e:
                print(f"Error processing item: {e}")
                continue

        return processed_data

    # def create_chart(self, data, param_name, ylabel, title):
    #     plt.figure(figsize=(8, 3))
    #     dates = [datetime.strptime(
    #         item['datetime'], '%Y-%m-%d %H:%M:%S') for item in data]
    #     values = [item[param_name] for item in data]
    #     plt.plot(dates, values)
    #     plt.title(title)
    #     plt.xlabel('Date/Time')
    #     plt.ylabel(ylabel)
    #     plt.xticks(rotation=45)
    #     plt.tight_layout()

    #     # Save to temporary file instead of BytesIO
    #     temp_image = f'temp_chart_{param_name}.png'
    #     plt.savefig(temp_image, format='png', dpi=300, bbox_inches='tight')
    #     plt.close()

    #     # Create Image object with specific width
    #     img = Image(temp_image, width=600, height=210)
    #     return img

    def create_chart(self, data, param_name, ylabel, title, date_key='datetime', date_format='%Y-%m-%d %H:%M:%S'):
        """Generates a chart and returns a ReportLab Image object."""
        plt.figure(figsize=(8.5, 2.8))  # Adjusted size slightly
        dates = []
        values = []

        # Extract data, skipping 'N/A' or invalid entries
        for item in data:
            item_val = item.get(param_name)
            item_date = item.get(date_key)
            if item_val != 'N/A' and item_date is not None:  # Ensure date exists
                try:
                    # Use stored datetime object if available, otherwise parse
                    current_date = None
                    if isinstance(item_date, datetime):
                        current_date = item_date
                    else:
                        # str() handles non-string types
                        current_date = datetime.strptime(
                            str(item_date), date_format)

                    dates.append(current_date)
                    values.append(float(item_val))
                except (ValueError, TypeError, AttributeError) as e:
                    print(
                        f"Skipping chart point due to error: {e} - Param: {param_name}, Date: {item_date}, Value: {item_val}")
                    continue  # Skip if date parsing or value conversion fails

        if not dates or not values:
            print(f"Warning: No valid data found for chart: {title}")
            plt.close()  # Close the empty figure
            return None

        plt.plot(dates, values, marker='.', linestyle='-')  # Add markers
        plt.title(title, fontsize=10)
        plt.xlabel('Date/Time', fontsize=8)
        plt.ylabel(ylabel, fontsize=8)
        # Adjust rotation and alignment
        plt.xticks(rotation=30, ha='right', fontsize=7)
        plt.yticks(fontsize=7)
        plt.grid(True, linestyle='--', alpha=0.6)  # Add grid
        plt.tight_layout()

        # Save to BytesIO instead of temporary file
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        img_buffer.seek(0)

        # Create Image object with specific width
        img = Image(img_buffer, width=7.5*inch, height=2.5*inch)
        img.hAlign = 'CENTER'
        return img

    def generate_pdf_report(self, lat, lon, weather_data, data_type, location_info):

        # Modify page size to be narrower
        page_width = letter[0] * 0.91  # 90% of standard letter width
        page_height = letter[1] * 0.99  # 95% of standard letter height
        custom_page_size = (page_width, page_height)

        # Create a safe filename by removing invalid characters
        location_name = location_info['name'].replace(
            ' ', '_').replace('/', '_').replace('\\', '_')
        file_name = f"weather_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{location_name}.pdf"

        # file_name = f"weather_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(
            file_name,
            pagesize=landscape(custom_page_size),
            topMargin=25,        # Reduce top margin
            bottomMargin=10,     # Reduce bottom margin
            leftMargin=30,       # Adjust left margin
            rightMargin=30       # Adjust right margin
        )

        elements = []

        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        normal_style = styles['Normal']

        # --- Define Styles ---
        title_style = styles['h1']
        title_style.alignment = 1

        sub_title_style = styles['h2']
        sub_title_style.spaceBefore = 10
        sub_title_style.spaceAfter = 2  # Reduced space after subtitle

        normal_style = styles['Normal']
        normal_style.leading = 14

        small_note_style = styles['Normal'].clone('SmallNote')
        small_note_style.fontSize = 8
        small_note_style.leading = 10

        # Increase line spacing
        normal_style.leading = 16  # Increase from default 12

        # Title and info
        elements.append(Paragraph("Weather Forecast Report", title_style))
        elements.append(Paragraph("<br/>", normal_style))
        elements.append(Paragraph(
            f"GPS Coordinates: Latitude: {lat:.4f}, Longitude: {lon:.4f}", normal_style))
        elements.append(Paragraph(
            f"Location: {location_info['name']}, {location_info['country']}", normal_style))
        elements.append(Paragraph(
            f"Sunrise: {location_info['sunrise']}, Sunset: {location_info['sunset']}", normal_style))
        elements.append(Paragraph(
            "Data Type: 03 Hourly forecast for next 05 days", normal_style))
        elements.append(Paragraph("<br/>", normal_style))

        # Update table headers to include PoP
        headers = ["Date/Time", "Description", "Temp\n(°C)", "Humidity\n(%)",
                   "Wind Speed\n(knots)", "Wind Gust\n(knots)", "Wind\nDir",
                   "Rain\n(mm)", "PoP\n(%)", "Visibility\n(m)"]

        table_data = [headers]

        # Update data rows to include PoP
        for item in weather_data:
            wind_speed = round(item['wind_speed'])
            wind_gust = round(
                float(item['wind_gust'])) if item['wind_gust'] != 'N/A' else 'N/A'

            row = [
                item['datetime'],
                item['description'],
                f"{item['temperature']:.1f}",
                str(item['humidity']),
                str(wind_speed),
                str(wind_gust),
                str(item['wind_direction']),
                f"{item['rain']:.1f}",
                f"{item['pop']:.0f}",  # Add PoP column
                str(item['visibility'])
            ]
            table_data.append(row)

        # Find min/max values for highlighting
        params = ['temperature', 'humidity', 'wind_speed',
                  'wind_gust', 'visibility', 'rain', 'pop']
        # Update param_columns dictionary to include pop
        param_columns = {
            'temperature': 2,
            'humidity': 3,
            'wind_speed': 4,
            'wind_gust': 5,
            'visibility': 9,  # Updated index
            'rain': 7,
            'pop': 8  # Add PoP column index
        }
        min_max = {}
        for param in params:
            try:
                values = []
                for item in weather_data:
                    value = item[param]
                    if value != 'N/A':
                        try:
                            values.append(float(value))
                        except (ValueError, TypeError):
                            continue
                if values:
                    min_max[param] = {'min': min(values), 'max': max(values)}
            except Exception as e:
                print(f"Warning: Could not process {param} values: {e}")
                continue

        # Update column widths to accommodate new column
        col_widths = [108, 100, 60, 60, 72, 72, 60, 60, 60, 60]
        table = Table(table_data, repeatRows=1, colWidths=col_widths)

        # Base table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ])

       # Find and highlight min/max values
        for param, col_idx in param_columns.items():
            col_values = []
            # Skip header row
            for row_idx, row in enumerate(table_data[1:], 1):
                try:
                    if row[col_idx] != 'N/A':
                        # Strip any formatting and convert to float
                        clean_value = row[col_idx].replace(',', '').strip()
                        if isinstance(clean_value, str):
                            if clean_value.endswith('.0'):
                                clean_value = clean_value[:-2]
                        value = float(clean_value)
                        col_values.append((value, row_idx))
                except (ValueError, TypeError):
                    continue

            if col_values:
                min_val = min(col_values, key=lambda x: x[0])
                max_val = max(col_values, key=lambda x: x[0])

                # Highlight min value
                style.add('BACKGROUND', (col_idx, min_val[1]),
                          (col_idx, min_val[1]), colors.cyan)
                # Highlight max value
                style.add('BACKGROUND', (col_idx, max_val[1]),
                          (col_idx, max_val[1]), colors.pink)

        table.setStyle(style)
        elements.append(table)

        # Add explanatory notes below the table
        note_style = styles['Normal'].clone('Note')
        note_style.fontSize = 10
        note_style.leading = 11
        elements.append(Paragraph("<br/>", note_style))
        elements.append(Paragraph(
            "<br/>Note: 1 Knot = 1.852 km/h = 0.514 m/s ; Wind Dir = Wind Direction ;  PoP = Probability of Precipitation, the likelihood of rain or snow.", note_style))

        # Create a custom style for the chart section heading
        chart_heading_style = styles['Heading1'].clone('ChartHeading')
        chart_heading_style.fontSize = 16  # Larger font size
        chart_heading_style.alignment = 1  # 1 means center alignment
        chart_heading_style.spaceAfter = 20  # Add some space after the heading
        chart_heading_style.spaceBefore = 5  # Add some space before the heading

        # Add space before charts section
        elements.append(Paragraph("<br/><br/>", normal_style))
        elements.append(
            Paragraph("<b>Weather Parameter Charts</b>", chart_heading_style))
        elements.append(Paragraph("<br/>", normal_style))

        # Create charts
        chart_params = [
            ('temperature', '°C', 'Temperature'),
            ('humidity', '%', 'Humidity'),
            ('wind_speed', 'knots', 'Wind Speed'),
            ('visibility', 'm', 'Visibility'),
            ('rain', 'mm', 'Rainfall')
        ]

        # Create and add charts
        for param, unit, title in chart_params:
            if any(item[param] != 'N/A' for item in weather_data):
                elements.append(
                    Paragraph(f"<b>{title} Chart</b>", normal_style))
                chart = self.create_chart(weather_data, param, unit, title)
                elements.append(chart)
                elements.append(Paragraph("<br/>", normal_style))

        # elements.append(
        #     Paragraph("\n *** 2025 © TungTT ***\n", normal_style))
        # # Build the PDF
        # doc.build(elements)
        # print(f"PDF report generated: {file_name}")

         # --- Footer ---
        elements.append(Spacer(1, 0.2*inch))
        footer_style = small_note_style.clone('Footer')
        footer_style.alignment = 1
        elements.append(Paragraph("--- Report End ---", footer_style))
        elements.append(Paragraph(
            "Weather data from OpenWeatherMap.", footer_style))
        elements.append(Paragraph("2025 © TungTT", footer_style))

        # Build the PDF
        doc.build(elements)
        print(f"PDF report generated: {file_name}")

        # Cleanup temporary chart files
        for param, _, _ in chart_params:
            temp_file = f'temp_chart_{param}.png'
            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    weather_app = WeatherCrawlerApp()
    weather_app.show()
    sys.exit(app.exec_())
