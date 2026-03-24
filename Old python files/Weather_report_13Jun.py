import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QRadioButton,
                             QMessageBox, QDateEdit, QProgressBar, QSizePolicy,
                             QGroupBox, QTextEdit)  # Added QTextEdit for real-time display
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QDate, QTimer  # Import QDate, QTimer
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import ImageReader
import requests
import json
from datetime import datetime, timedelta, timezone, date, time
import pytz
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
# from bs4 import BeautifulSoup # REMOVED - not needed after tidal removal
import re  # KEPT - Used for safe filename generation
# from urllib.parse import urljoin # REMOVED - not needed after tidal removal
import io  # For handling PDF download in memory - KEPT for BytesIO
import traceback  # For better error printing
import math  # For isnan check
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# -*- coding: utf-8 -*-
# Add this line at the top for better Unicode handling


# Added date, time, make sure 'date' is imported from datetime
# Corrected import for newer urllib3 versions
# Removed tempfile, PyPDF2 - replaced by pdfplumber and io
# pdfplumber import removed as tidal removed

# --- ReportLab Font Registration for Vietnamese ---

VIETNAMESE_FONT_NAME = 'Helvetica'  # Default fallback
VIETNAMESE_FONT_NAME_BOLD = 'Helvetica-Bold'  # Default fallback
try:
    # --- Try Noto Sans ---
    font_path_regular = 'NotoSans-Regular.ttf'
    font_path_bold = 'NotoSans-Bold.ttf'  # Or the correct bold filename

    if os.path.exists(font_path_regular) and os.path.exists(font_path_bold):
        pdfmetrics.registerFont(TTFont('NotoSans', font_path_regular))
        # Register bold variant
        pdfmetrics.registerFont(TTFont('NotoSans-Bold', font_path_bold))
        VIETNAMESE_FONT_NAME = 'NotoSans'
        VIETNAMESE_FONT_NAME_BOLD = 'NotoSans-Bold'  # Use the registered bold name
        print("Registered NotoSans font for Vietnamese PDF reports.")
    else:
        # --- Fallback to UTM Neo Sans Intel ---
        font_path_utm = 'UTM Neo Sans Intel.ttf'
        if os.path.exists(font_path_utm):
            pdfmetrics.registerFont(
                TTFont('UTM Neo Sans Intel', font_path_utm))
            # Assuming UTM font handles bold internally or use a specific bold file if available
            # Try registering bold variant
            pdfmetrics.registerFont(
                TTFont('UTM Neo Sans Intel-Bold', font_path_utm))
            VIETNAMESE_FONT_NAME = 'UTM Neo Sans Intel'
            VIETNAMESE_FONT_NAME_BOLD = 'UTM Neo Sans Intel-Bold'
            print("Registered UTM Neo Sans Intel font for Vietnamese PDF reports.")
        else:
            print(f"Warning: Neither NotoSans nor UTM Neo Sans Intel found. Using default Helvetica (may cause character issues).")

except Exception as font_err:
    print(
        f"Warning: Could not register Vietnamese font. Using default Helvetica. Error: {font_err}")
    # Keep Helvetica as fallback
# --- End Font Registration ---

# pdfplumber import removed as tidal report is removed

# ... (Keep LOCATION_TIMEZONES and DEFAULT_TIMEZONE) ...
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
DEFAULT_TIMEZONE = 'Asia/Ho_Chi_Minh'

# --- Translation Mappings ---
WEATHER_DESC_VIET = {
    # Clouds
    'Clear sky': 'Trời quang',
    'Few clouds': 'Ít mây',
    'Scattered clouds': 'Mây rải rác',
    'Broken clouds': 'Nhiều mây',  # Often used for partly cloudy
    'Overcast clouds': 'Trời u ám',

    # Rain
    'Light rain': 'Mưa nhẹ',
    'Moderate rain': 'Mưa vừa',
    'Heavy intensity rain': 'Mưa to',
    'Very heavy rain': 'Mưa rất to',
    'Extreme rain': 'Mưa cực lớn',
    'Freezing rain': 'Mưa đông đá',
    'Light intensity shower rain': 'Mưa rào nhẹ',
    'Shower rain': 'Mưa rào',
    'Heavy intensity shower rain': 'Mưa rào nặng hạt',
    'Ragged shower rain': 'Mưa rào không đều',

    # Thunderstorm
    'Thunderstorm with light rain': 'Dông kèm mưa nhẹ',
    'Thunderstorm with rain': 'Dông kèm mưa',
    'Thunderstorm with heavy rain': 'Dông kèm mưa to',
    'Light thunderstorm': 'Dông nhẹ',
    'Thunderstorm': 'Dông',
    'Heavy thunderstorm': 'Dông mạnh',
    'Ragged thunderstorm': 'Dông không đều',
    'Thunderstorm with light drizzle': 'Dông kèm mưa phùn nhẹ',
    'Thunderstorm with drizzle': 'Dông kèm mưa phùn',
    'Thunderstorm with heavy drizzle': 'Dông kèm mưa phùn nặng hạt',

    # Drizzle
    'Light intensity drizzle': 'Mưa phùn nhẹ',
    'Drizzle': 'Mưa phùn',
    'Heavy intensity drizzle': 'Mưa phùn nặng hạt',
    'Light intensity drizzle rain': 'Mưa phùn/mưa nhẹ',
    'Drizzle rain': 'Mưa phùn/mưa',
    'Heavy intensity drizzle rain': 'Mưa phùn/mưa nặng hạt',
    'Shower rain and drizzle': 'Mưa rào và mưa phùn',
    'Heavy shower rain and drizzle': 'Mưa rào to và mưa phùn',
    'Shower drizzle': 'Mưa phùn dạng mưa rào',

    # Snow (Less common in target areas, but included)
    'Light snow': 'Tuyết nhẹ',
    'Snow': 'Tuyết',
    'Heavy snow': 'Tuyết dày',
    'Sleet': 'Mưa tuyết',
    'Light shower sleet': 'Mưa tuyết nhẹ',
    'Shower sleet': 'Mưa tuyết',
    'Light rain and snow': 'Mưa và tuyết nhẹ',
    'Rain and snow': 'Mưa và tuyết',
    'Light shower snow': 'Tuyết rơi nhẹ',
    'Shower snow': 'Tuyết rơi',
    'Heavy shower snow': 'Tuyết rơi dày',

    # Atmosphere
    'Mist': 'Sương mù nhẹ',
    'Smoke': 'Khói',
    'Haze': 'Bụi mù',
    'Sand/ dust whirls': 'Xoáy cát/bụi',
    'Fog': 'Sương mù',
    'Sand': 'Cát',
    'Dust': 'Bụi',
    'Volcanic ash': 'Tro núi lửa',
    'Squalls': 'Gió giật mạnh',
    'Tornado': 'Lốc xoáy',
    'N/A': 'Không xác định'
}

WIND_DIR_VIET = {
    'N': 'B',    # Bắc
    'NNE': 'BĐB',  # Bắc Đông Bắc
    'NE': 'ĐB',  # Đông Bắc
    'ENE': 'ĐĐB',  # Đông Đông Bắc
    'E': 'Đ',    # Đông
    'ESE': 'ĐĐN',  # Đông Đông Nam
    'SE': 'ĐN',  # Đông Nam
    'SSE': 'NĐN',  # Nam Đông Nam
    'S': 'N',    # Nam
    'SSW': 'NTN',  # Nam Tây Nam
    'SW': 'TN',  # Tây Nam
    'WSW': 'TTN',  # Tây Tây Nam
    'W': 'T',    # Tây
    'WNW': 'TTB',  # Tây Tây Bắc
    'NW': 'TB',  # Tây Bắc
    'NNW': 'BTB',  # Bắc Tây Bắc
    'N/A': 'N/A'  # Handle missing data
}

# --- WMO Weather Codes (Open-Meteo) ---
# Source: https://www.nodc.noaa.gov/archive/arc0021/0002196/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
# Simplified for common conditions
WMO_WEATHER_CODES_EN = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight showers",
    81: "Moderate showers",
    82: "Violent showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm (slight/moderate)",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

WMO_WEATHER_CODES_VIET = {
    0: "Trời quang",
    1: "Chủ yếu quang mây",
    2: "Mây rải rác",
    3: "Trời nhiều mây",
    45: "Sương mù",
    48: "Sương mù có sương giá",
    51: "Mưa phùn nhẹ",
    53: "Mưa phùn vừa",
    55: "Mưa phùn nặng hạt",
    56: "Mưa phùn nhẹ kèm đông đá",
    57: "Mưa phùn nặng hạt kèm đông đá",
    61: "Mưa nhẹ",
    63: "Mưa vừa",
    65: "Mưa to",
    66: "Mưa nhẹ kèm đông đá",
    67: "Mưa to kèm đông đá",
    71: "Tuyết rơi nhẹ",
    73: "Tuyết rơi vừa",
    75: "Tuyết rơi dày",
    77: "Hạt tuyết",
    80: "Mưa rào nhẹ",
    81: "Mưa rào vừa",
    82: "Mưa rào dữ dội",
    85: "Mưa tuyết nhẹ",
    86: "Mưa tuyết dày",
    95: "Dông (nhẹ/vừa)",
    96: "Dông kèm mưa đá nhỏ",
    99: "Dông kèm mưa đá lớn"
}
# --- End WMO Weather Codes ---


# --- Constants ---
# TIDAL_INDEX_URL = "http://www.kttv-nb.org.vn/index.php/thong-tin-kttv/thuy-van" # REMOVED
OPENMETEO_API_URL = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"  # NEW
OPENMETEO_ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"  # NEW

# --- Tidal PDF Scraping Function (Removed) ---
# def scrape_and_download_tidal_pdf_for_date(...) (REMOVED)


class WeatherCrawlerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather Reporter")
        # Increased height slightly for date edit
        # Increased height for new API selection and real-time/historical sections
        self.setGeometry(200, 100, 480, 900)  # Adjusted height

        icon_path = "weather_icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file {icon_path} not found")

        # Initialize real-time dashboard data and timer
        # Moved these initializations before initUI()
        self.realtime_locations = {
            'Lan Tay Platform': (7.5783, 108.8694),
            'Rong Doi Platform': (7.7925, 108.2021),
            'An Phu Office': (10.8094, 106.7366)
        }
        self.realtime_labels_data = {}  # Store labels for easy access, dict of dicts

        self.api_key = "e1a69775e0d7c149a4e2bdb69bb59a82"  # OpenWeatherMap API Key

        self.initUI()
        self.session = self.create_requests_session()

        # Removed pdfplumber warning here as tidal is removed

        self.realtime_timer = QTimer(self)
        self.realtime_timer.timeout.connect(self._update_realtime_display)
        self.realtime_timer.start(30 * 60 * 1000)  # 30 minutes in milliseconds
        self._update_realtime_display()  # Initial update on startup

    def initUI(self):
        main_layout = QVBoxLayout()

        # --- 0. API Selection Section ---
        api_group = QGroupBox("Select Weather API Source:")
        api_group.setFont(QFont("Arial", 10))
        api_layout = QVBoxLayout()

        self.api_radio_owm = QRadioButton("OpenWeatherMap (5-day forecast)")
        self.api_radio_owm.setFont(QFont("Arial", 10))

        self.api_radio_openmeteo = QRadioButton(
            "Open-Meteo (Up to 16-day forecast, Marine & Historical data)")  # Updated text
        self.api_radio_openmeteo.setFont(QFont("Arial", 10))

        # Change default selection to Open-Meteo (already done)
        self.api_radio_openmeteo.setChecked(True)
        self.api_radio_owm.setChecked(False)

        api_layout.addWidget(self.api_radio_openmeteo)  # Open-Meteo first
        api_layout.addWidget(self.api_radio_owm)
        api_group.setLayout(api_layout)
        main_layout.addWidget(api_group)
        main_layout.addSpacing(10)
        # --- END API Selection ---

        # --- 1. Location Input Section ---
        input_layout = QVBoxLayout()
        input_label = QLabel("Locations:")
        input_label.setFont(QFont("Arial", 12, QFont.Bold))
        input_layout.addWidget(input_label)

        self.lat_label = QLabel("Latitude:")
        self.lat_label.setFont(QFont("Arial", 10))
        self.lon_label = QLabel("Longitude:")
        self.lon_label.setFont(QFont("Arial", 10))
        self.lat_input = QLineEdit()
        self.lon_input = QLineEdit()
        self.lat_input.setEnabled(False)
        self.lon_input.setEnabled(False)

        self.locations = {
            'Lan Tay Platform': (7.5783, 108.8694),
            'Rong Doi Platform': (7.7925, 108.2021),
            'Home': (10.8317, 106.7327),
            'Ha Noi home': (21.0042, 105.8145),
            'An Phu Office': (10.8094, 106.7366),
            'Thao Dien Pitch': (10.8070, 106.7390),
            'Vung Tau Airport': (10.3760, 107.0932)
        }

        self.location_radios = {}
        location_font = QFont("Arial", 10)

        for name, coords in self.locations.items():
            location_hbox = QHBoxLayout()
            radio = QRadioButton(name)
            radio.setFont(location_font)
            self.location_radios[name] = radio
            radio.toggled.connect(self.toggle_gps_input)
            coord_label = QLabel(f"({coords[0]:.4f}, {coords[1]:.4f})")
            coord_label.setFont(location_font)
            coord_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            location_hbox.addWidget(radio)
            location_hbox.addWidget(coord_label)
            input_layout.addLayout(location_hbox)

        self.gps_radio = QRadioButton("Enter Custom GPS Coordinates:")
        self.gps_radio.setFont(location_font)
        self.gps_radio.toggled.connect(self.toggle_gps_input)
        input_layout.addWidget(self.gps_radio)

        gps_name_layout = QHBoxLayout()
        self.gps_name_label = QLabel("Custom Name (Optional):")
        self.gps_name_label.setFont(QFont("Arial", 10))
        self.gps_name_input = QLineEdit()
        self.gps_name_input.setPlaceholderText("e.g., My Offshore Site")
        self.gps_name_input.setEnabled(False)
        gps_name_layout.addWidget(self.gps_name_label)
        gps_name_layout.addWidget(self.gps_name_input)
        input_layout.addLayout(gps_name_layout)

        gps_coord_layout = QHBoxLayout()
        gps_coord_layout.addWidget(self.lat_label)
        gps_coord_layout.addWidget(self.lat_input)
        gps_coord_layout.addWidget(self.lon_label)
        gps_coord_layout.addWidget(self.lon_input)
        gps_coord_layout.addStretch()
        input_layout.addLayout(gps_coord_layout)

        default_location_key = 'An Phu Office'
        if default_location_key not in self.location_radios:
            default_location_key = next(iter(self.locations))
        if default_location_key in self.location_radios:
            self.location_radios[default_location_key].setChecked(True)

        main_layout.addLayout(input_layout)
        main_layout.addSpacing(20)

        # --- 2. Generate Weather Report Title ---
        weather_title_layout = QHBoxLayout()
        weather_title_label = QLabel("Generate Weather Forecast Report")
        weather_title_label.setFont(QFont("Arial", 11, QFont.Bold))
        weather_title_label.setAlignment(Qt.AlignCenter)
        weather_title_layout.addStretch()
        weather_title_layout.addWidget(weather_title_label)
        weather_title_layout.addStretch()
        main_layout.addLayout(weather_title_layout)
        main_layout.addSpacing(5)

        # --- 3. Generate Weather Report Button ---
        self.weather_button = QPushButton("Generate Report (English)")
        self.weather_button.setFont(QFont("Arial", 10))
        self.weather_button.clicked.connect(
            self.generate_weather_report_action)
        main_layout.addWidget(self.weather_button)

        self.vietnamese_weather_button = QPushButton(
            "Tạo Báo Cáo Thời Tiết (Tiếng Việt)")
        self.vietnamese_weather_button.setFont(QFont("Arial", 10))
        self.vietnamese_weather_button.clicked.connect(
            self.generate_vietnamese_weather_report_action)
        main_layout.addWidget(self.vietnamese_weather_button)
        main_layout.addSpacing(20)

        # --- NEW: Real-time Weather Dashboard Section ---
        realtime_group = QGroupBox(
            "Real-time Weather Dashboard (Refreshes every 30 mins)")
        realtime_group.setFont(QFont("Arial", 11, QFont.Bold))
        realtime_layout = QVBoxLayout()
        realtime_font = QFont("Arial", 10)
        realtime_bold_font = QFont("Arial", 10, QFont.Bold)

        # Labels for each specific real-time location
        for loc_name in self.realtime_locations.keys():
            loc_hbox = QHBoxLayout()
            name_label = QLabel(f"<b>{loc_name}:</b>")
            name_label.setFont(realtime_bold_font)
            loc_hbox.addWidget(name_label)

            temp_label = QLabel("Temp: N/A")
            temp_label.setFont(realtime_font)
            loc_hbox.addWidget(temp_label)

            wind_label = QLabel("Wind: N/A")
            wind_label.setFont(realtime_font)
            loc_hbox.addWidget(wind_label)

            desc_label = QLabel("Desc: N/A")
            desc_label.setFont(realtime_font)
            loc_hbox.addWidget(desc_label)

            self.realtime_labels_data[loc_name] = {
                'temp': temp_label,
                'wind': wind_label,
                'desc': desc_label
            }
            realtime_layout.addLayout(loc_hbox)

        self.rt_alert_label = QLabel("Wind Speed Alert: None")
        self.rt_alert_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.rt_alert_label.setStyleSheet("color: blue;")
        realtime_layout.addWidget(self.rt_alert_label)

        realtime_group.setLayout(realtime_layout)
        main_layout.addWidget(realtime_group)
        main_layout.addSpacing(20)
        # --- END NEW: Real-time Weather Dashboard Section ---

        # --- NEW: Historical Data Retrieval Section ---
        historical_group = QGroupBox(
            "Historical Weather Data Retrieval (Open-Meteo)")
        historical_group.setFont(QFont("Arial", 11, QFont.Bold))
        historical_layout = QVBoxLayout()

        # Date range selection
        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(QLabel("From Date:"))
        self.historical_from_date = QDateEdit(self)
        self.historical_from_date.setDate(
            QDate.currentDate().addDays(-7))  # Default to last 7 days
        self.historical_from_date.setCalendarPopup(True)
        self.historical_from_date.setDisplayFormat("dd/MM/yyyy")
        date_range_layout.addWidget(self.historical_from_date)

        date_range_layout.addWidget(QLabel("To Date:"))
        self.historical_to_date = QDateEdit(self)
        self.historical_to_date.setDate(QDate.currentDate())
        self.historical_to_date.setCalendarPopup(True)
        self.historical_to_date.setDisplayFormat("dd/MM/yyyy")
        date_range_layout.addWidget(self.historical_to_date)
        date_range_layout.addStretch()
        historical_layout.addLayout(date_range_layout)

        self.fetch_historical_button = QPushButton(
            "Fetch & Generate Historical Report (PDF)")
        self.fetch_historical_button.setFont(QFont("Arial", 10))
        self.fetch_historical_button.clicked.connect(
            self._fetch_historical_and_generate_report_action)
        historical_layout.addWidget(self.fetch_historical_button)

        historical_group.setLayout(historical_layout)
        main_layout.addWidget(historical_group)
        main_layout.addSpacing(15)
        # --- END NEW: Historical Data Retrieval Section ---

        # --- Progress Bar (remains the same position) ---
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFormat("")
        self.progress_bar.setVisible(False)
        self.progress_bar.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.progress_bar)

        # --- Status Label (remains the same position) ---
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setVisible(False)
        main_layout.addWidget(self.status_label)

        # --- Final Layout Setup ---
        main_layout.addStretch()
        self.setLayout(main_layout)
        self.toggle_gps_input()

        self.resize(self.width(), 750)  # Adjusted height for all new sections

    def toggle_gps_input(self):
        """Enables/disables the Latitude, Longitude, and Custom Name input fields based on GPS radio selection."""
        is_gps_selected = self.gps_radio.isChecked()
        self.lat_input.setEnabled(is_gps_selected)
        self.lon_input.setEnabled(is_gps_selected)
        self.gps_name_input.setEnabled(
            is_gps_selected)
        self.gps_name_label.setEnabled(
            is_gps_selected)

    def get_api_choice(self):
        """Returns the currently selected weather API source."""
        if self.api_radio_owm.isChecked():
            return "OWM"
        elif self.api_radio_openmeteo.isChecked():
            return "OpenMeteo"
        return None

    def generate_weather_report_action(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return

        api_choice = self.get_api_choice()
        if not api_choice:
            QMessageBox.warning(
                self, "API Selection Error", "Please select a weather API source.")
            return

        self._start_progress(
            f"Preparing to fetch weather data from {api_choice}...")

        QApplication.setOverrideCursor(Qt.WaitCursor)
        weather_data = None
        location_info = None
        marine_data = None  # NEW

        try:
            print(
                f"--- Starting Weather Data Fetch for Report ({api_choice}) ---")

            self._update_progress_status(
                f"Fetching weather data from {api_choice}... Please wait")

            if api_choice == "OWM":
                weather_data, location_info = self._fetch_weather_data_owm(
                    lat, lon)
            elif api_choice == "OpenMeteo":
                weather_data, location_info = self._fetch_weather_data_openmeteo(
                    lat, lon)
                # Fetch marine data for specific locations when OpenMeteo is selected
                if location_name_selected in ['Lan Tay Platform', 'Rong Doi Platform']:
                    self._update_progress_status(
                        f"Fetching marine data for {location_name_selected}...")
                    marine_data = self._fetch_marine_data_openmeteo(
                        lat, lon, location_info.get('timezone', DEFAULT_TIMEZONE))

            if not weather_data:
                if not location_info:
                    location_info = {'name': location_name_selected, 'country': 'N/A',
                                     'sunrise': 'N/A', 'sunset': 'N/A', 'timezone': DEFAULT_TIMEZONE}
                QMessageBox.warning(
                    self, "Weather Error", "Failed to fetch weather data. Report generation stopped.")
                return

            self._update_progress_status("Generating PDF report...")

            self.generate_pdf_report(
                lat, lon, weather_data, location_info, location_name_selected, api_choice, marine_data)

            self._end_progress("Report generated successfully!", success=True)
            QMessageBox.information(
                self, "Success", "Weather PDF report generated successfully!")

        except Exception as e:
            self._end_progress("Report generation failed.", success=False)
            print(f"An error occurred during weather report generation: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred generating the weather report:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    def generate_vietnamese_weather_report_action(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return

        api_choice = self.get_api_choice()
        if not api_choice:
            QMessageBox.warning(
                self, "API Selection Error", "Vui lòng chọn nguồn API thời tiết.")
            return

        self._start_progress(
            f"Đang chuẩn bị lấy dữ liệu thời tiết từ {api_choice}...")

        QApplication.setOverrideCursor(Qt.WaitCursor)
        weather_data = None
        location_info = None
        marine_data = None  # NEW

        try:
            print(
                f"--- Starting Weather Data Fetch for Vietnamese Report ({api_choice}) ---")

            self._update_progress_status(
                f"Đang lấy dữ liệu thời tiết từ {api_choice}... Vui lòng chờ")

            if api_choice == "OWM":
                weather_data, location_info = self._fetch_weather_data_owm(
                    lat, lon)
            elif api_choice == "OpenMeteo":
                weather_data, location_info = self._fetch_weather_data_openmeteo(
                    lat, lon)
                # Fetch marine data for specific locations when OpenMeteo is selected
                if location_name_selected in ['Lan Tay Platform', 'Rong Doi Platform']:
                    self._update_progress_status(
                        f"Đang lấy dữ liệu biển cho {location_name_selected}...")
                    marine_data = self._fetch_marine_data_openmeteo(
                        lat, lon, location_info.get('timezone', DEFAULT_TIMEZONE))

            if not weather_data:
                if not location_info:
                    location_info = {'name': location_name_selected, 'country': 'N/A',
                                     'sunrise': 'N/A', 'sunset': 'N/A', 'timezone': DEFAULT_TIMEZONE}
                QMessageBox.warning(
                    self, "Lỗi Dữ Liệu Thời Tiết", "Không thể lấy dữ liệu thời tiết. Đã dừng tạo báo cáo.")
                return

            self._update_progress_status(
                "Đang tạo báo cáo PDF (Tiếng Việt)...")

            self.generate_vietnamese_pdf_report(
                lat, lon, weather_data, location_info, location_name_selected, api_choice, marine_data)

            self._end_progress("Đã tạo báo cáo thành công!", success=True)
            QMessageBox.information(
                self, "Thành Công", "Đã tạo báo cáo thời tiết PDF (Tiếng Việt) thành công!")

        except Exception as e:
            self._end_progress("Tạo báo cáo thất bại.", success=False)
            print(
                f"An error occurred during Vietnamese weather report generation: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Lỗi", f"Đã xảy ra lỗi không mong muốn khi tạo báo cáo:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    # --- REMOVED download_tidal_report_action ---
    # def download_tidal_report_action(self): ... (REMOVED)

    def get_coordinates(self):
        if self.gps_radio.isChecked():
            try:
                lat_str = self.lat_input.text().strip()
                lon_str = self.lon_input.text().strip()
                if not lat_str or not lon_str:
                    QMessageBox.warning(
                        self, "Input Error", "Latitude and Longitude cannot be empty.")
                    return None, None, None
                lat = float(lat_str)
                lon = float(lon_str)
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Latitude/Longitude out of range.")

                custom_name = self.gps_name_input.text().strip()
                if custom_name:
                    location_name = custom_name
                else:
                    location_name = f"Custom GPS ({lat:.4f}, {lon:.4f})"

                return lat, lon, location_name
            except ValueError as e:
                QMessageBox.warning(self, "Input Error",
                                    f"Invalid Latitude or Longitude: {e}")
                return None, None, None
        else:
            for name, radio in self.location_radios.items():
                if radio.isChecked():
                    return self.locations[name][0], self.locations[name][1], name
        QMessageBox.warning(self, "Input Error",
                            "Please select a location option.")
        return None, None, None

    def create_requests_session(self):
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=10,
            pool_maxsize=10,
            pool_block=False
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
        })
        return session

    # --- Utility functions for progress bar ---
    def _start_progress(self, message):
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)
        self.status_label.setText(message)
        self.status_label.setVisible(True)
        QApplication.processEvents()

    def _update_progress_status(self, message):
        self.status_label.setText(message)
        QApplication.processEvents()

    def _end_progress(self, message, success=True):
        if success:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.status_label.setText(message)
            QApplication.processEvents()
            # Delay hiding for a better user experience on success
            QTimer.singleShot(1000, lambda: [self.status_label.setVisible(
                False), self.progress_bar.setVisible(False)])
        else:
            self.status_label.setVisible(False)
            self.progress_bar.setVisible(False)
        QApplication.processEvents()
    # --- End Utility functions for progress bar ---

    def _fetch_weather_data_owm(self, lat, lon):
        base_url = "https://api.openweathermap.org/data/2.5/"
        units = "metric"
        timeout = (15, 30)
        current_data = None
        forecast_data = None
        location_info = {
            'name': f"Coords ({lat:.4f}, {lon:.4f})",
            'country': 'N/A',
            'sunrise': 'N/A',
            'sunset': 'N/A',
            'timezone': DEFAULT_TIMEZONE
        }

        try:
            current_url = f"{base_url}weather?lat={lat}&lon={lon}&appid={self.api_key}&units={units}"
            print(f"Fetching OWM current: {current_url}")
            current_response = self.session.get(current_url, timeout=timeout)
            current_response.raise_for_status()
            current_data = current_response.json()

            forecast_url = f"{base_url}forecast?lat={lat}&lon={lon}&appid={self.api_key}&units={units}&cnt=40"
            print(f"Fetching OWM forecast: {forecast_url}")
            forecast_response = self.session.get(forecast_url, timeout=timeout)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            timezone_str = DEFAULT_TIMEZONE
            country_code = current_data.get('sys', {}).get('country')
            local_tz = None

            if country_code and country_code in LOCATION_TIMEZONES:
                timezone_str = LOCATION_TIMEZONES[country_code]
                print(
                    f"Using timezone from mapped country code '{country_code}': {timezone_str}")
            elif 'timezone' in current_data:
                try:
                    offset_sec = int(current_data['timezone'])
                    fixed_tz = timezone(timedelta(seconds=offset_sec))
                    now_utc = datetime.now(timezone.utc)
                    matching_tz_name = None
                    for tz_name in pytz.common_timezones:
                        tz = pytz.timezone(tz_name)
                        if now_utc.astimezone(tz).utcoffset() == timedelta(seconds=offset_sec):
                            matching_tz_name = tz_name
                            break
                    if matching_tz_name:
                        timezone_str = matching_tz_name
                        print(
                            f"Using timezone derived from OWM offset ({offset_sec}s): {timezone_str}")
                    else:
                        offset_hours = offset_sec / 3600
                        timezone_str = f"UTC{offset_hours:+03.0f}:00 (Offset)"
                        print(
                            f"Warning: Could not find exact pytz match for offset {offset_sec}s. Using fixed offset: {timezone_str}")
                        local_tz = fixed_tz

                except Exception as tz_offset_err:
                    print(
                        f"Warning: Could not process timezone offset {current_data.get('timezone')}. Using default {DEFAULT_TIMEZONE}. Error: {tz_offset_err}")
                    timezone_str = DEFAULT_TIMEZONE
            else:
                print(
                    f"Warning: No country code or timezone offset from OWM. Using default {DEFAULT_TIMEZONE}.")

            if local_tz is None:
                try:
                    local_tz = pytz.timezone(timezone_str)
                except pytz.exceptions.UnknownTimeZoneError:
                    print(
                        f"Error: pytz does not recognize timezone '{timezone_str}'. Falling back to {DEFAULT_TIMEZONE}.")
                    timezone_str = DEFAULT_TIMEZONE
                    local_tz = pytz.timezone(DEFAULT_TIMEZONE)

            print(f"Final timezone for processing: {timezone_str}")
            location_info['timezone'] = timezone_str

            location_info['name'] = current_data.get(
                'name', f"Coords ({lat:.4f}, {lon:.4f})")
            location_info['country'] = current_data.get(
                'sys', {}).get('country', 'N/A')
            if 'sunrise' in current_data.get('sys', {}):
                location_info['sunrise'] = datetime.fromtimestamp(
                    current_data['sys']['sunrise'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M')
            if 'sunset' in current_data.get('sys', {}):
                location_info['sunset'] = datetime.fromtimestamp(
                    current_data['sys']['sunset'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M')

            processed_forecast = self._process_forecast_data_owm(
                forecast_data, local_tz)
            return processed_forecast, location_info

        except requests.exceptions.Timeout:
            QMessageBox.critical(
                self, "Connection Error", "Weather API request timed out. Please check internet connection.")
            return None, location_info
        except requests.exceptions.HTTPError as e:
            err_msg = f"Weather API HTTP Error: {e}"
            if e.response is not None:
                status_code = e.response.status_code
                err_msg += f"\nStatus Code: {status_code}"
                try:
                    details = e.response.json()
                    err_msg += f"\nMessage: {details.get('message', e.response.text)}"
                except json.JSONDecodeError:
                    err_msg += f"\nResponse: {e.response.text[:200]}..."

                if status_code == 401:
                    err_msg = "Invalid OpenWeatherMap API Key. Please check the key in the script."
                elif status_code == 404:
                    err_msg = f"Location (Lat: {lat}, Lon: {lon}) not found by Weather API."
                elif status_code == 429:
                    err_msg = "Weather API rate limit exceeded. Please wait and try again later."

            QMessageBox.critical(self, "API Error", err_msg)
            return None, location_info
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error",
                                 f"Could not connect to weather service: {e}")
            return None, location_info
        except Exception as e:
            print(f"Unexpected error in _fetch_weather_data_owm: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Processing Error", f"An error occurred while processing weather data: {e}")
            return None, location_info

    def _fetch_weather_data_openmeteo(self, lat, lon):
        timeout = (15, 30)
        location_info = {
            'name': f"Coords ({lat:.4f}, {lon:.4f})",
            'country': 'N/A',
            'sunrise': 'N/A',
            'sunset': 'N/A',
            'timezone': DEFAULT_TIMEZONE
        }
        processed_data = []

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m,visibility,cloud_cover,pressure_msl,uv_index",
            "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,weather_code",
            "timezone": "auto",
            # Fetch up to 16 days of daily, Open-Meteo provides 7 days of hourly (168 hours)
            "forecast_days": 16,
            "temperature_unit": "celsius",
            "wind_speed_unit": "kn",
            "precipitation_unit": "mm"
        }

        try:
            print(
                f"Fetching Open-Meteo: {OPENMETEO_API_URL} with params: {params}")
            response = self.session.get(
                OPENMETEO_API_URL, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            location_info['timezone'] = data.get(
                'timezone', DEFAULT_TIMEZONE)

            try:
                local_tz = pytz.timezone(location_info['timezone'])
            except pytz.exceptions.UnknownTimeZoneError:
                print(
                    f"Error: pytz does not recognize timezone '{location_info['timezone']}'. Falling back to {DEFAULT_TIMEZONE}.")
                location_info['timezone'] = DEFAULT_TIMEZONE
                local_tz = pytz.timezone(DEFAULT_TIMEZONE)

            daily_data = data.get('daily', {})
            if daily_data.get('sunrise') and len(daily_data['sunrise']) > 0:
                sunrise_utc = datetime.fromisoformat(
                    daily_data['sunrise'][0].replace('Z', '+00:00'))
                location_info['sunrise'] = sunrise_utc.astimezone(
                    local_tz).strftime('%H:%M')
            if daily_data.get('sunset') and len(daily_data['sunset']) > 0:
                sunset_utc = datetime.fromisoformat(
                    daily_data['sunset'][0].replace('Z', '+00:00'))
                location_info['sunset'] = sunset_utc.astimezone(
                    local_tz).strftime('%H:%M')

            hourly_data = data.get('hourly', {})
            times = hourly_data.get('time', [])
            temperatures = hourly_data.get('temperature_2m', [])
            humidities = hourly_data.get('relative_humidity_2m', [])
            precipitations = hourly_data.get('precipitation', [])
            rain_amounts = hourly_data.get('rain', [])
            showers_amounts = hourly_data.get('showers', [])
            snowfall_amounts = hourly_data.get('snowfall', [])
            weather_codes = hourly_data.get('weather_code', [])
            wind_speeds = hourly_data.get('wind_speed_10m', [])
            wind_gusts = hourly_data.get('wind_gusts_10m', [])
            wind_directions = hourly_data.get('wind_direction_10m', [])
            visibilities = hourly_data.get('visibility', [])
            cloud_covers = hourly_data.get('cloud_cover', [])
            pressures = hourly_data.get('pressure_msl', [])
            uv_indices = hourly_data.get('uv_index', [])

            now_local = datetime.now(local_tz)

            for i in range(len(times)):
                try:
                    dt_obj = datetime.fromisoformat(
                        times[i]).astimezone(local_tz)

                    if dt_obj >= now_local - timedelta(hours=1) and dt_obj <= now_local + timedelta(days=7, hours=1):

                        wmo_code = weather_codes[i] if i < len(
                            weather_codes) and weather_codes[i] is not None else None
                        weather_desc_en = WMO_WEATHER_CODES_EN.get(
                            wmo_code, f"Unknown code {wmo_code}" if wmo_code is not None else 'N/A')

                        temp = temperatures[i] if i < len(
                            temperatures) and temperatures[i] is not None else None
                        humidity = humidities[i] if i < len(
                            humidities) and humidities[i] is not None else None

                        wind_speed = wind_speeds[i] if i < len(
                            wind_speeds) and wind_speeds[i] is not None else None
                        wind_gust = wind_gusts[i] if i < len(
                            wind_gusts) and wind_gusts[i] is not None else None
                        wind_deg = wind_directions[i] if i < len(
                            wind_directions) and wind_directions[i] is not None else None
                        wind_direction = self._degrees_to_direction(wind_deg)

                        total_rain_hourly = (rain_amounts[i] if i < len(rain_amounts) and rain_amounts[i] is not None else 0.0) + \
                            (showers_amounts[i] if i < len(showers_amounts) and showers_amounts[i] is not None else 0.0) + \
                            (snowfall_amounts[i] if i < len(
                                snowfall_amounts) and snowfall_amounts[i] is not None else 0.0)

                        pop = 100 if total_rain_hourly > 0.0 else 0

                        visibility = visibilities[i] if i < len(
                            visibilities) and visibilities[i] is not None else 'N/A'
                        cloud_cover = cloud_covers[i] if i < len(
                            cloud_covers) and cloud_covers[i] is not None else 'N/A'
                        pressure = pressures[i] if i < len(
                            pressures) and pressures[i] is not None else 'N/A'
                        uv_index = uv_indices[i] if i < len(
                            uv_indices) and uv_indices[i] is not None else 'N/A'

                        processed_data.append({
                            'datetime_obj': dt_obj,
                            'datetime': dt_obj.strftime('%Y-%m-%d %H:%M'),
                            'description': weather_desc_en,
                            'temperature': float(temp) if temp is not None else 'N/A',
                            'humidity': float(humidity) if humidity is not None else 'N/A',
                            'wind_speed': float(wind_speed) if wind_speed is not None else 'N/A',
                            'wind_gust': float(wind_gust) if wind_gust is not None else 'N/A',
                            'wind_direction': wind_direction,
                            'rain': float(total_rain_hourly),
                            'visibility': int(visibility) if isinstance(visibility, (int, float)) else 'N/A',
                            'pop': pop,
                            'cloud_cover': float(cloud_cover) if cloud_cover is not None else 'N/A',
                            'pressure': float(pressure) if pressure is not None else 'N/A',
                            'uv_index': float(uv_index) if uv_index is not None else 'N/A'
                        })
                except Exception as e:
                    print(
                        f"Error processing Open-Meteo hourly item at index {i}: {e}")
                    print(traceback.format_exc())
                    continue

            return processed_data, location_info

        except requests.exceptions.Timeout:
            QMessageBox.critical(
                self, "Connection Error", "Open-Meteo API request timed out. Please check internet connection.")
            return None, location_info
        except requests.exceptions.HTTPError as e:
            err_msg = f"Open-Meteo API HTTP Error: {e}"
            if e.response is not None:
                status_code = e.response.status_code
                err_msg += f"\nStatus Code: {status_code}"
                try:
                    details = e.response.json()
                    err_msg += f"\nMessage: {details.get('reason', e.response.text)}"
                except json.JSONDecodeError:
                    err_msg += f"\nResponse: {e.response.text[:200]}..."

            QMessageBox.critical(self, "API Error", err_msg)
            return None, location_info
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error",
                                 f"Could not connect to weather service: {e}")
            return None, location_info
        except Exception as e:
            print(f"Unexpected error in _fetch_weather_data_openmeteo: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Processing Error", f"An error occurred while processing weather data: {e}")
            return None, location_info

    # --- NEW: _fetch_marine_data_openmeteo ---
    def _fetch_marine_data_openmeteo(self, lat, lon, timezone_str):
        timeout = (15, 30)
        processed_data = []
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wave_height,wave_direction,wave_period,wind_wave_height,wind_wave_direction,wind_wave_period,swell_wave_height,swell_wave_direction,swell_wave_period",
            "timezone": timezone_str,  # Use the determined timezone
            "forecast_days": 7  # 7 days of hourly marine data
        }

        try:
            print(
                f"Fetching Open-Meteo Marine: {OPENMETEO_MARINE_API_URL} with params: {params}")
            response = self.session.get(
                OPENMETEO_MARINE_API_URL, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            hourly_data = data.get('hourly', {})
            times = hourly_data.get('time', [])
            wave_heights = hourly_data.get('wave_height', [])
            wave_directions = hourly_data.get('wave_direction', [])
            wave_periods = hourly_data.get('wave_period', [])

            local_tz = pytz.timezone(timezone_str)
            now_local = datetime.now(local_tz)

            for i in range(len(times)):
                try:
                    dt_obj = datetime.fromisoformat(
                        times[i]).astimezone(local_tz)

                    # Only include data for the next 7 days
                    if dt_obj >= now_local - timedelta(hours=1) and dt_obj <= now_local + timedelta(days=7, hours=1):
                        height = wave_heights[i] if i < len(
                            wave_heights) and wave_heights[i] is not None else 'N/A'
                        direction_deg = wave_directions[i] if i < len(
                            wave_directions) and wave_directions[i] is not None else 'N/A'
                        period = wave_periods[i] if i < len(
                            wave_periods) and wave_periods[i] is not None else 'N/A'

                        processed_data.append({
                            'datetime_obj': dt_obj,
                            'datetime': dt_obj.strftime('%Y-%m-%d %H:%M'),
                            'wave_height': float(height) if isinstance(height, (int, float)) else 'N/A',
                            'wave_direction_deg': float(direction_deg) if isinstance(direction_deg, (int, float)) else 'N/A',
                            'wave_direction': self._degrees_to_direction(direction_deg),
                            'wave_period': float(period) if isinstance(period, (int, float)) else 'N/A'
                        })
                except Exception as e:
                    print(
                        f"Error processing Open-Meteo marine hourly item at index {i}: {e}")
                    print(traceback.format_exc())
                    continue

            return processed_data

        except requests.exceptions.Timeout:
            QMessageBox.critical(self, "Connection Error",
                                 "Marine API request timed out.")
            return None
        except requests.exceptions.HTTPError as e:
            err_msg = f"Marine API HTTP Error: {e}"
            if e.response is not None:
                status_code = e.response.status_code
                err_msg += f"\nStatus Code: {status_code}"
                try:
                    details = e.response.json()
                    err_msg += f"\nMessage: {details.get('reason', e.response.text)}"
                except json.JSONDecodeError:
                    err_msg += f"\nResponse: {e.response.text[:200]}..."
            QMessageBox.critical(self, "API Error", err_msg)
            return None
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error",
                                 f"Could not connect to marine service: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in _fetch_marine_data_openmeteo: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Processing Error", f"An error occurred while processing marine data: {e}")
            return None
    # --- END NEW: _fetch_marine_data_openmeteo ---

    # --- NEW: _fetch_historical_data_openmeteo ---
    def _fetch_historical_data_openmeteo(self, lat, lon, start_date_str, end_date_str, timezone_str):
        timeout = (15, 30)
        processed_data = []

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m,cloud_cover,pressure_msl,visibility",
            "timezone": timezone_str,
            "temperature_unit": "celsius",
            "wind_speed_unit": "kn",
            "precipitation_unit": "mm"
        }

        try:
            print(
                f"Fetching Open-Meteo Historical: {OPENMETEO_ARCHIVE_API_URL} with params: {params}")
            response = self.session.get(
                OPENMETEO_ARCHIVE_API_URL, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            hourly_data = data.get('hourly', {})
            times = hourly_data.get('time', [])
            temperatures = hourly_data.get('temperature_2m', [])
            humidities = hourly_data.get('relative_humidity_2m', [])
            precipitations = hourly_data.get('precipitation', [])
            weather_codes = hourly_data.get('weather_code', [])
            wind_speeds = hourly_data.get('wind_speed_10m', [])
            wind_gusts = hourly_data.get('wind_gusts_10m', [])
            wind_directions = hourly_data.get('wind_direction_10m', [])
            cloud_covers = hourly_data.get('cloud_cover', [])
            pressures = hourly_data.get('pressure_msl', [])
            visibilities = hourly_data.get('visibility', [])

            local_tz = pytz.timezone(timezone_str)

            for i in range(len(times)):
                try:
                    dt_obj = datetime.fromisoformat(
                        times[i]).astimezone(local_tz)

                    wmo_code = weather_codes[i] if i < len(
                        weather_codes) and weather_codes[i] is not None else None
                    weather_desc_en = WMO_WEATHER_CODES_EN.get(
                        wmo_code, f"Unknown code {wmo_code}" if wmo_code is not None else 'N/A')

                    temp = temperatures[i] if i < len(
                        temperatures) and temperatures[i] is not None else None
                    humidity = humidities[i] if i < len(
                        humidities) and humidities[i] is not None else None

                    wind_speed = wind_speeds[i] if i < len(
                        wind_speeds) and wind_speeds[i] is not None else None
                    wind_gust = wind_gusts[i] if i < len(
                        wind_gusts) and wind_gusts[i] is not None else None
                    wind_deg = wind_directions[i] if i < len(
                        wind_directions) and wind_directions[i] is not None else None
                    wind_direction = self._degrees_to_direction(wind_deg)

                    rain_amount = precipitations[i] if i < len(
                        precipitations) and precipitations[i] is not None else 0.0

                    cloud_cover = cloud_covers[i] if i < len(
                        cloud_covers) and cloud_covers[i] is not None else 'N/A'
                    pressure = pressures[i] if i < len(
                        pressures) and pressures[i] is not None else 'N/A'
                    visibility = visibilities[i] if i < len(
                        visibilities) and visibilities[i] is not None else 'N/A'

                    processed_data.append({
                        'datetime_obj': dt_obj,
                        'datetime': dt_obj.strftime('%Y-%m-%d %H:%M'),
                        'description': weather_desc_en,
                        'temperature': float(temp) if temp is not None else 'N/A',
                        'humidity': float(humidity) if humidity is not None else 'N/A',
                        'wind_speed': float(wind_speed) if wind_speed is not None else 'N/A',
                        'wind_gust': float(wind_gust) if wind_gust is not None else 'N/A',
                        'wind_direction': wind_direction,
                        'rain': float(rain_amount),
                        'cloud_cover': float(cloud_cover) if cloud_cover is not None else 'N/A',
                        'pressure': float(pressure) if pressure is not None else 'N/A',
                        'visibility': int(visibility) if isinstance(visibility, (int, float)) else 'N/A',
                        'pop': 'N/A'  # PoP not available in historical hourly data
                    })
                except Exception as e:
                    print(
                        f"Error processing Open-Meteo historical item at index {i}: {e}")
                    print(traceback.format_exc())
                    continue

            return processed_data

        except requests.exceptions.Timeout:
            QMessageBox.critical(self, "Connection Error",
                                 "Historical API request timed out.")
            return None
        except requests.exceptions.HTTPError as e:
            err_msg = f"Historical API HTTP Error: {e}"
            if e.response is not None:
                status_code = e.response.status_code
                err_msg += f"\nStatus Code: {status_code}"
                try:
                    details = e.response.json()
                    err_msg += f"\nMessage: {details.get('reason', e.response.text)}"
                except json.JSONDecodeError:
                    err_msg += f"\nResponse: {e.response.text[:200]}..."
            QMessageBox.critical(self, "API Error", err_msg)
            return None
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error",
                                 f"Could not connect to historical service: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in _fetch_historical_data_openmeteo: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Processing Error", f"An error occurred while processing historical data: {e}")
            return None
    # --- END NEW: _fetch_historical_data_openmeteo ---

    def _process_forecast_data_owm(self, data, local_tz):
        processed_data = []
        if not data or 'list' not in data:
            print("Warning: Forecast data is missing or invalid.")
            return processed_data

        now_local = datetime.now(local_tz)

        for item in data.get('list', []):
            try:
                dt_utc = datetime.fromtimestamp(item['dt'], tz=timezone.utc)
                local_time = dt_utc.astimezone(local_tz)

                if local_time >= now_local - timedelta(hours=3) and local_time <= now_local + timedelta(days=5, hours=3):

                    weather_desc = item.get('weather', [{}])[0].get(
                        'description', 'N/A').capitalize()
                    main_data = item.get('main', {})
                    temp = main_data.get('temp')
                    humidity = main_data.get('humidity')
                    pressure = main_data.get('pressure')  # ADDED for OWM chart

                    wind_data = item.get('wind', {})
                    wind_speed_mps = wind_data.get('speed')
                    wind_speed_knots = round(
                        wind_speed_mps * 1.94384, 1) if wind_speed_mps is not None else 'N/A'

                    wind_gust_mps = wind_data.get('gust')
                    wind_gust_knots = round(
                        wind_gust_mps * 1.94384, 1) if wind_gust_mps is not None else 'N/A'

                    wind_deg = wind_data.get('deg')
                    wind_direction = self._degrees_to_direction(wind_deg)

                    rain_3h = item.get('rain', {}).get(
                        '3h', 0.0)
                    visibility = item.get('visibility', 'N/A')
                    pop = round(item.get('pop', 0.0) * 100)
                    cloud_cover = item.get('clouds', {}).get(
                        'all', 'N/A')  # ADDED for OWM chart

                    processed_data.append({
                        'datetime_obj': local_time,
                        'datetime': local_time.strftime('%Y-%m-%d %H:%M'),
                        'description': weather_desc,
                        'temperature': float(temp) if temp is not None else 'N/A',
                        'humidity': float(humidity) if humidity is not None else 'N/A',
                        'wind_speed': wind_speed_knots,
                        'wind_gust': wind_gust_knots,
                        'wind_direction': wind_direction,
                        'rain': float(rain_3h),
                        'visibility': int(visibility) if isinstance(visibility, (int, float)) else 'N/A',
                        'pop': pop,
                        # ADDED
                        'cloud_cover': float(cloud_cover) if cloud_cover is not None else 'N/A',
                        # ADDED
                        'pressure': float(pressure) if pressure is not None else 'N/A'
                    })
            except Exception as e:
                print(
                    f"Error processing OWM forecast item: {item}. Error: {e}")
                continue

        return processed_data

    def _degrees_to_direction(self, degrees):
        if degrees is None:
            return 'N/A'
        try:
            deg_float = float(degrees)
            directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE',
                          'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
            index = round(deg_float / (360 / len(directions))
                          ) % len(directions)
            return directions[index]
        except (ValueError, TypeError):
            return 'N/A'

    def create_chart(self, data, param_name, ylabel, title, date_key='datetime_obj',
                     xlabel_text='Date/Time'):
        if not data:
            print(f"Warning: No data provided for chart: {title}")
            return None

        plt.figure(figsize=(9.0, 2.8))
        dates = []
        values = []
        for item in data:
            item_val = item.get(param_name)
            item_date = item.get(date_key)
            if item_val not in [None, 'N/A'] and isinstance(item_date, datetime):
                try:
                    dates.append(item_date)
                    values.append(float(item_val))
                except (ValueError, TypeError):
                    continue

        if not dates or not values:
            print(
                f"Warning: No valid numeric data points found for chart: {title}")
            plt.close()
            return None

        try:
            plt.plot(dates, values, marker='.',
                     linestyle='-', markersize=4, linewidth=1)
            plt.title(title, fontsize=10)
            plt.xlabel(xlabel_text, fontsize=9)
            plt.ylabel(ylabel, fontsize=9)
            plt.xticks(rotation=30, ha='right', fontsize=9)
            plt.yticks(fontsize=9)

            plt.gca().xaxis.set_major_locator(mdates.HourLocator(
                byhour=[1, 7, 13, 19], tz=dates[0].tzinfo if dates else None))
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(
                '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))

            plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
            plt.tight_layout(pad=0.5)

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)

            img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
            img.hAlign = 'CENTER'
            return img

        except Exception as chart_err:
            print(f"Error during chart plotting for '{title}': {chart_err}")
            print(traceback.format_exc())
            plt.close()
            return None

    def create_wind_chart(self, data, date_key='datetime_obj',
                          xlabel_text='Date/Time', ylabel_text='Speed (knots)',
                          title_text='Wind Speed and Gust Trend',
                          speed_label='Wind Speed', gust_label='Wind Gust'):
        if not data:
            print("Warning: No data provided for wind chart.")
            return None

        plt.figure(figsize=(9.0, 2.8))
        dates = []
        speeds = []
        gusts = []

        for item in data:
            item_date = item.get(date_key)
            speed_val = item.get('wind_speed')
            gust_val = item.get('wind_gust')

            if isinstance(item_date, datetime):
                dates.append(item_date)
                try:
                    speeds.append(float(speed_val) if speed_val not in [
                                  None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    speeds.append(math.nan)
                try:
                    gusts.append(float(gust_val) if gust_val not in [
                                 None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    gusts.append(math.nan)

        if not dates or (all(math.isnan(s) for s in speeds) and all(math.isnan(g) for g in gusts)):
            print("Warning: No valid numeric data points found for wind chart.")
            plt.close()
            return None

        try:
            line1, = plt.plot(dates, speeds, marker='.', linestyle='-',
                              markersize=4, linewidth=1, label=speed_label)
            line2, = plt.plot(dates, gusts, marker='.', linestyle='-', markersize=4,
                              linewidth=1, color='orange', label=gust_label)

            plt.title(title_text, fontsize=10)
            plt.xlabel(xlabel_text, fontsize=9)
            plt.ylabel(ylabel_text, fontsize=9)
            plt.xticks(rotation=30, ha='right', fontsize=9)
            plt.yticks(fontsize=9)
            plt.legend(fontsize=8)

            plt.gca().xaxis.set_major_locator(mdates.HourLocator(
                byhour=[1, 7, 13, 19], tz=dates[0].tzinfo if dates else None))
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(
                '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))

            plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
            plt.tight_layout(pad=0.5)

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)

            img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
            img.hAlign = 'CENTER'
            return img

        except Exception as chart_err:
            print(f"Error during wind chart plotting: {chart_err}")
            print(traceback.format_exc())
            plt.close()
            return None

    def create_temp_humidity_chart(self, data, date_key='datetime_obj',
                                   xlabel_text='Date/Time', temp_ylabel='Temperature (°C)',
                                   hum_ylabel='Humidity (%)', title_text='Temperature and Humidity Trend',
                                   temp_label='Temperature', hum_label='Humidity'):
        if not data:
            print("Warning: No data provided for Temp/Humidity chart.")
            return None

        fig, ax1 = plt.subplots(figsize=(9.0, 2.8))

        dates = []
        temps = []
        humidity = []

        for item in data:
            item_date = item.get(date_key)
            temp_val = item.get('temperature')
            hum_val = item.get('humidity')

            if isinstance(item_date, datetime):
                dates.append(item_date)
                try:
                    temps.append(float(temp_val) if temp_val not in [
                                 None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    temps.append(math.nan)
                try:
                    humidity.append(float(hum_val) if hum_val not in [
                                    None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    humidity.append(math.nan)

        if not dates or (all(math.isnan(t) for t in temps) and
                         all(math.isnan(h) for h in humidity)):
            print("Warning: No valid numeric data points found for Temp/Humidity chart.")
            plt.close(fig)
            return None

        try:
            color_temp = 'tab:blue'
            ax1.set_xlabel(xlabel_text, fontsize=9)
            ax1.set_ylabel(temp_ylabel, color=color_temp,
                           fontsize=9)
            ax1.tick_params(axis='x', rotation=30, labelsize=9)

            ax1.xaxis.set_major_locator(mdates.HourLocator(
                byhour=[1, 7, 13, 19], tz=dates[0].tzinfo if dates else None))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter(
                '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))

            line1, = ax1.plot(dates, temps, marker='.', linestyle='-',
                              markersize=4, linewidth=1, color=color_temp, label=temp_label)

            ax2 = ax1.twinx()
            color_hum = 'orange'
            ax2.set_ylabel(hum_ylabel, color=color_hum,
                           fontsize=9)
            line2, = ax2.plot(dates, humidity, marker='.', linestyle='-',
                              markersize=4, linewidth=1, color=color_hum, label=hum_label)
            ax2.tick_params(axis='y', labelcolor=color_hum, labelsize=9)

            lines = [line1, line2]
            ax1.legend(lines, [l.get_label()
                       for l in lines], loc='upper left', fontsize=8)

            plt.title(title_text, fontsize=10)
            ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)

            fig.tight_layout(pad=0.5)

            for label in ax1.get_xticklabels():
                label.set_horizontalalignment('right')

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            img_buffer.seek(0)

            img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
            img.hAlign = 'CENTER'
            return img

        except Exception as chart_err:
            print(f"Error during Temp/Humidity chart plotting: {chart_err}")
            print(traceback.format_exc())
            plt.close(fig)
            return None

    def create_rain_pop_chart(self, data, date_key='datetime_obj',
                              xlabel_text='Date/Time', rain_ylabel='Rainfall (mm/h)',
                              pop_ylabel='Probability of Precipitation (%)',
                              title_text='Rainfall and Precipitation Probability Trend',
                              rain_label='Rainfall', pop_label='PoP'):
        if not data:
            print("Warning: No data provided for Rain/PoP chart.")
            return None

        fig, ax1 = plt.subplots(figsize=(9.0, 2.8))

        dates = []
        rains = []
        pops = []

        for item in data:
            item_date = item.get(date_key)
            rain_val = item.get('rain')
            pop_val = item.get('pop')

            if isinstance(item_date, datetime):
                dates.append(item_date)
                try:
                    rains.append(float(rain_val) if rain_val not in [
                                 None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    rains.append(math.nan)
                try:
                    pops.append(float(pop_val) if pop_val not in [
                                None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    pops.append(math.nan)

        if not dates or (all(math.isnan(r) for r in rains) and all(math.isnan(p) for p in pops)):
            print("Warning: No valid numeric data points found for Rain/PoP chart.")
            plt.close(fig)
            return None

        try:
            color_rain = 'tab:blue'
            ax1.set_xlabel(xlabel_text, fontsize=9)
            ax1.set_ylabel(rain_ylabel, color=color_rain,
                           fontsize=9)
            ax1.tick_params(axis='y', labelcolor=color_rain, labelsize=9)
            ax1.tick_params(axis='x', rotation=30, labelsize=9)

            ax1.xaxis.set_major_locator(mdates.HourLocator(
                byhour=[1, 7, 13, 19], tz=dates[0].tzinfo if dates else None))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter(
                '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))

            line1, = ax1.plot(dates, rains, marker='.', linestyle='-',
                              markersize=4, linewidth=1, color=color_rain, label=rain_label)

            ax2 = ax1.twinx()
            color_pop = 'orange'
            ax2.set_ylabel(pop_ylabel, color=color_pop,
                           fontsize=9)
            line2, = ax2.plot(dates, pops, marker='.', linestyle='-',
                              markersize=4, linewidth=1, color=color_pop, label=pop_label)
            ax2.tick_params(axis='y', labelcolor=color_pop, labelsize=9)
            ax2.set_ylim(0, 105)

            lines = [line1, line2]
            ax1.legend(lines, [l.get_label()
                       for l in lines], loc='upper left', fontsize=8)

            plt.title(title_text, fontsize=10)
            ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)

            fig.tight_layout(pad=0.5)

            for label in ax1.get_xticklabels():
                label.set_horizontalalignment('right')

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            img_buffer.seek(0)

            img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
            img.hAlign = 'CENTER'
            return img

        except Exception as chart_err:
            print(f"Error during Rain/PoP chart plotting: {chart_err}")
            print(traceback.format_exc())
            plt.close(fig)
            return None

    # --- NEW: create_wave_chart ---
    def create_wave_chart(self, data, param_name, ylabel, title, date_key='datetime_obj',
                          xlabel_text='Date/Time'):
        if not data:
            print(f"Warning: No data provided for wave chart: {title}")
            return None

        plt.figure(figsize=(9.0, 2.8))
        dates = []
        values = []
        for item in data:
            item_val = item.get(param_name)
            item_date = item.get(date_key)
            if item_val not in [None, 'N/A'] and isinstance(item_date, datetime):
                try:
                    dates.append(item_date)
                    values.append(float(item_val))
                except (ValueError, TypeError):
                    continue

        if not dates or not values:
            print(
                f"Warning: No valid numeric data points found for wave chart: {title}")
            plt.close()
            return None

        try:
            plt.plot(dates, values, marker='.',
                     linestyle='-', markersize=4, linewidth=1, color='teal')
            plt.title(title, fontsize=10)
            plt.xlabel(xlabel_text, fontsize=9)
            plt.ylabel(ylabel, fontsize=9)
            plt.xticks(rotation=30, ha='right', fontsize=9)
            plt.yticks(fontsize=9)

            plt.gca().xaxis.set_major_locator(mdates.HourLocator(
                byhour=[1, 7, 13, 19], tz=dates[0].tzinfo if dates else None))
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(
                '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))

            plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
            plt.tight_layout(pad=0.5)

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)

            img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
            img.hAlign = 'CENTER'
            return img

        except Exception as chart_err:
            print(
                f"Error during wave chart plotting for '{title}': {chart_err}")
            print(traceback.format_exc())
            plt.close()
            return None
    # --- END NEW: create_wave_chart ---

    # --- NEW: _fetch_realtime_data_openmeteo ---

    def _fetch_realtime_data_openmeteo(self, lat, lon, location_name):
        timeout = (10, 20)
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "timezone": "auto",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kn"
        }
        try:
            response = self.session.get(
                OPENMETEO_API_URL, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            current_weather = data.get('current_weather', {})
            weather_code = current_weather.get('weather_code')
            temperature = current_weather.get('temperature')
            wind_speed = current_weather.get('wind_speed')
            wind_direction = current_weather.get('wind_direction')  # degrees

            description_en = WMO_WEATHER_CODES_EN.get(weather_code, 'N/A')
            wind_dir_compass = self._degrees_to_direction(wind_direction)

            # Get local timezone from API response
            timezone_api = data.get('timezone', DEFAULT_TIMEZONE)
            try:
                local_tz = pytz.timezone(timezone_api)
            except pytz.exceptions.UnknownTimeZoneError:
                local_tz = pytz.timezone(DEFAULT_TIMEZONE)

            # Get current time in local timezone for accurate "as of"
            current_time_str = datetime.now(local_tz).strftime('%H:%M')

            return {
                'name': location_name,
                'temperature': f"{temperature:.1f}°C" if temperature is not None else "N/A",
                'wind_speed': f"{wind_speed:.1f} knots" if wind_speed is not None else "N/A",
                # for alert
                'wind_speed_value': float(wind_speed) if wind_speed is not None else 0.0,
                'weather_description': description_en,
                'wind_direction': wind_dir_compass,
                'time_as_of': current_time_str
            }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching real-time data for {location_name}: {e}")
            return None
        except Exception as e:
            print(
                f"Unexpected error in _fetch_realtime_data_openmeteo for {location_name}: {e}")
            print(traceback.format_exc())
            return None

    # --- NEW: _update_realtime_display ---
    def _update_realtime_display(self):
        print("\n--- Updating Real-time Weather Dashboard ---")
        self.rt_alert_label.setStyleSheet("color: blue;")  # Reset alert
        self.rt_alert_label.setText("Wind Speed Alert: None")
        max_wind_speed_overall = 0.0

        for name, coords in self.realtime_locations.items():
            lat, lon = coords
            data = self._fetch_realtime_data_openmeteo(lat, lon, name)
            labels = self.realtime_labels_data.get(name)

            if data and labels:
                labels['temp'].setText(f"Temp: {data['temperature']}")
                labels['wind'].setText(
                    f"Wind: {data['wind_speed']} ({data['wind_direction']})")
                labels['desc'].setText(
                    f"Desc: {data['weather_description']} (as of {data['time_as_of']})")

                # Update max wind speed for alert check
                if data['wind_speed_value'] > max_wind_speed_overall:
                    max_wind_speed_overall = data['wind_speed_value']
            elif labels:
                labels['temp'].setText("Temp: N/A")
                labels['wind'].setText("Wind: N/A")
                labels['desc'].setText("Desc: Failed to load")

        # Check for high wind alert
        if max_wind_speed_overall > 30.0:  # Threshold for alert
            self.rt_alert_label.setText(
                f"HIGH WIND ALERT! ({max_wind_speed_overall:.1f} knots detected)")
            self.rt_alert_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.rt_alert_label.setText(
                f"Wind Speed Alert: None (Max: {max_wind_speed_overall:.1f} knots)")
            self.rt_alert_label.setStyleSheet("color: green;")

        QApplication.processEvents()
        print("--- Real-time Weather Dashboard Updated ---")
    # --- END NEW: _update_realtime_display ---

    # --- NEW: _fetch_historical_and_generate_report_action ---
    def _fetch_historical_and_generate_report_action(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return

        from_date_qdate = self.historical_from_date.date()
        to_date_qdate = self.historical_to_date.date()

        from_date = from_date_qdate.toPyDate()
        to_date = to_date_qdate.toPyDate()

        if from_date > to_date:
            QMessageBox.warning(self, "Date Error",
                                "From Date cannot be after To Date.")
            return

        # Open-Meteo historical API limit (approx 2000 days or so, but let's limit for practical use)
        if (to_date - from_date).days > 365 * 2:  # Limit to 2 years for a single query
            QMessageBox.warning(self, "Date Range Warning",
                                "Please select a date range of up to 2 years for historical data.")
            return

        # Determine timezone for the location (Open-Meteo uses 'auto' in forecast, but for historical
        # it's better to provide an explicit IANA timezone if possible, or let it auto-detect then extract)
        # For simplicity, we'll fetch current data to get timezone if not already known, or default.
        # A more robust solution might use Open-Meteo's GeoCoding API first.

        # Small hack: make a quick forecast request to get the timezone for the location
        # This is not ideal but gets the local timezone from Open-Meteo's auto-detection.
        temp_forecast_data, location_info = self._fetch_weather_data_openmeteo(
            lat, lon)
        timezone_for_historical = location_info.get(
            'timezone', DEFAULT_TIMEZONE)

        self._start_progress(
            f"Fetching historical weather data for {location_name_selected} from {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}...")

        QApplication.setOverrideCursor(Qt.WaitCursor)
        historical_data = None

        try:
            historical_data = self._fetch_historical_data_openmeteo(
                lat, lon, from_date.strftime(
                    '%Y-%m-%d'), to_date.strftime('%Y-%m-%d'),
                timezone_for_historical
            )

            if not historical_data:
                QMessageBox.warning(
                    self, "Historical Data Error", "Failed to fetch historical weather data. Report generation stopped.")
                return

            self._update_progress_status("Generating historical PDF report...")

            self.generate_historical_pdf_report(
                lat, lon, historical_data, location_info, location_name_selected,
                from_date, to_date
            )

            self._end_progress(
                "Historical report generated successfully!", success=True)
            QMessageBox.information(
                self, "Success", "Historical Weather PDF report generated successfully!")

        except Exception as e:
            self._end_progress(
                "Historical report generation failed.", success=False)
            print(
                f"An error occurred during historical report generation: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred generating the historical report:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    # --- MODIFIED generate_pdf_report (now accepts marine_data) ---
    def generate_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source, marine_data=None):

        page_width, page_height = landscape(letter)

        file_name_location = re.sub(
            r'[\\/*?:"<>|()]+', "", ui_location_name).replace(' ', '_')
        file_name = f"Weather_Report_{api_source}_{file_name_location}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

        doc = SimpleDocTemplate(
            file_name,
            pagesize=(page_width, page_height),
            topMargin=0.5*inch, bottomMargin=0.4*inch,
            leftMargin=0.5*inch, rightMargin=0.5*inch
        )

        elements = []
        styles = getSampleStyleSheet()

        title_style = styles['h1']
        title_style.alignment = 1
        title_style.fontSize = 16
        h2_style = styles['h2']
        h2_style.alignment = 0
        h2_style.fontSize = 14
        h2_style.spaceBefore = 15
        h2_style.spaceAfter = 4
        normal_style = styles['Normal']
        normal_style.leading = 15
        normal_style.fontSize = 11
        small_note_style = styles['Normal'].clone('SmallNote')
        small_note_style.fontSize = 9
        small_note_style.leading = 10
        small_note_style.textColor = colors.dimgray
        footer_style = small_note_style.clone('Footer')
        footer_style.alignment = 1
        footer_style.fontSize = 8

        elements.append(Paragraph("Weather Forecast Report", title_style))
        elements.append(Spacer(1, 0.1*inch))

        api_name = location_info.get('name', '')
        country_code = location_info.get('country', 'N/A')

        api_details_parts = []
        if api_name and api_name != ui_location_name and not api_name.startswith("Coords ("):
            api_details_parts.append(api_name)
        if country_code and country_code != 'N/A':
            api_details_parts.append(country_code)

        location_string = f"<b>Location:</b> {ui_location_name}"
        if api_details_parts:
            api_details = ", ".join(api_details_parts)
            location_string += f" ({api_details})"

        elements.append(Paragraph(location_string, normal_style))
        elements.append(
            Paragraph(f"<b>Coordinates:</b> Lat: {lat:.4f}, Lon: {lon:.4f}", normal_style))
        elements.append(Paragraph(
            f"<b>Timezone:</b> {location_info.get('timezone', DEFAULT_TIMEZONE)}", normal_style))
        elements.append(Paragraph(
            f"<b>Sunrise:</b> {location_info.get('sunrise', 'N/A')}, <b>Sunset:</b> {location_info.get('sunset', 'N/A')}", normal_style))
        elements.append(Paragraph(
            f"<b>Report Generated:</b> {datetime.now(pytz.timezone(location_info.get('timezone', DEFAULT_TIMEZONE))).strftime('%Y-%m-%d %H:%M:%S %Z')}", normal_style))
        elements.append(
            Paragraph(f"<b>Data Source:</b> {api_source}", normal_style))
        elements.append(Spacer(1, 0.2*inch))

        if weather_data:
            elements.append(
                Paragraph("Weather Forecast (Next 5-7 Days Hourly)", h2_style))

            col_params = {
                'datetime': {'header': "Date/Time", 'format': lambda x: x, 'width': 1.28*inch, 'align': 'CENTER'},
                'description': {'header': "Description", 'format': lambda x: x, 'width': 1.88*inch, 'align': 'CENTER'},
                'temperature': {'header': "Temp\n(°C)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
                'humidity': {'header': "Humidity\n(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.8*inch, 'align': 'RIGHT'},
                'wind_speed': {'header': "Wind Speed\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'wind_gust': {'header': "Wind Gust\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'wind_direction': {'header': "Wind\nDir", 'format': lambda x: x, 'width': 0.72*inch, 'align': 'CENTER'},
                'rain': {'header': "Rain\n(mm/h)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.75*inch, 'align': 'RIGHT'},
                'pop': {'header': "PoP\n(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
                'visibility': {'header': "Visibility\n(m)", 'format': lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.88*inch, 'align': 'RIGHT'},
            }

            weather_headers = ["Date/Time", "Description", "Temp\n(°C)", "Humidity\n(%)",
                               "Wind Speed\n(knots)", "Wind Gust\n(knots)", "Wind\nDir",
                               "Rain\n(mm/h)", "PoP\n(%)", "Visibility\n(m)"]
            weather_col_widths = [1.28*inch, 1.88*inch, 0.72*inch, 0.8*inch,
                                  1*inch, 1*inch, 0.72*inch, 0.75*inch, 0.72*inch, 0.88*inch]

            param_to_col_index = {
                'temperature': 2, 'humidity': 3, 'wind_speed': 4, 'wind_gust': 5,
                'rain': 7, 'pop': 8, 'visibility': 9
            }
            numeric_data_for_highlight = {p: []
                                          for p in param_to_col_index.keys()}

            weather_table_data = [weather_headers]

            max_entries_for_table = 7 * 24

            for row_idx, item in enumerate(weather_data[:max_entries_for_table]):
                vis_formatted = col_params['visibility']['format'](
                    item.get('visibility'))
                temp_formatted = col_params['temperature']['format'](
                    item.get('temperature'))
                hum_formatted = col_params['humidity']['format'](
                    item.get('humidity'))
                wind_formatted = col_params['wind_speed']['format'](
                    item.get('wind_speed'))
                gust_formatted = col_params['wind_gust']['format'](
                    item.get('wind_gust'))
                rain_formatted = col_params['rain']['format'](item.get('rain'))
                pop_formatted = col_params['pop']['format'](item.get('pop'))

                row = [
                    item['datetime'],
                    item['description'],
                    temp_formatted,
                    hum_formatted,
                    wind_formatted,
                    gust_formatted,
                    item['wind_direction'],
                    rain_formatted,
                    pop_formatted,
                    vis_formatted
                ]
                weather_table_data.append(row)

                table_row_index = row_idx + 1
                for param, value in [('temperature', item.get('temperature')),
                                     ('humidity', item.get('humidity')),
                                     ('wind_speed', item.get('wind_speed')),
                                     ('wind_gust', item.get('wind_gust')),
                                     ('rain', item.get('rain')),
                                     ('pop', item.get('pop')),
                                     ('visibility', item.get('visibility'))]:
                    if param in numeric_data_for_highlight and isinstance(value, (int, float)) and not math.isnan(value):
                        numeric_data_for_highlight[param].append(
                            (value, table_row_index))

            weather_table = Table(weather_table_data,
                                  repeatRows=1, colWidths=weather_col_widths)
            weather_style_cmds = [('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 10.5), ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 6), ('FONTNAME',
                                                                                                                                                                                                                                                                                                                                                                                        (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 9.5), ('TOPPADDING', (0, 1), (-1, -1), 5), ('BOTTOMPADDING', (0, 1), (-1, -1), 5), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ALIGN', (2, 1), (3, -1), 'RIGHT'), ('ALIGN', (4, 1), (5, -1), 'RIGHT'), ('ALIGN', (7, 1), (9, -1), 'RIGHT'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightblue])]
            for param, data_points in numeric_data_for_highlight.items():
                if data_points:
                    col_idx = param_to_col_index[param]
                    min_val, min_row_idx = min(data_points, key=lambda x: x[0])
                    max_val, max_row_idx = max(data_points, key=lambda x: x[0])
                    weather_style_cmds.append(
                        ('BACKGROUND', (col_idx, min_row_idx), (col_idx, min_row_idx), colors.cyan))
                    weather_style_cmds.append(
                        ('BACKGROUND', (col_idx, max_row_idx), (col_idx, max_row_idx), colors.pink))
            weather_table.setStyle(TableStyle(weather_style_cmds))
            elements.append(weather_table)
            elements.append(Spacer(1, 0.1*inch))
            note_text = "Note: 1 knot = 1.85 km/h; Wind Dir = Wind Direction; PoP = Probability of Precipitation (hourly derived based on presence of rain/snow for Open-Meteo). Rainfall values are per hour for Open-Meteo, per 3 hours for OpenWeatherMap."
            elements.append(Paragraph(note_text, small_note_style))
            elements.append(Spacer(1, 0.15*inch))
        else:
            elements.append(
                Paragraph("Weather Forecast Data Not Available", h2_style))
            elements.append(Spacer(1, 0.15*inch))

        if weather_data:
            elements.append(Paragraph("Weather Parameter Charts", h2_style))

            temp_hum_chart = self.create_temp_humidity_chart(
                weather_data)
            if temp_hum_chart:
                elements.append(temp_hum_chart)
                elements.append(Spacer(1, 0.1*inch))

            wind_chart = self.create_wind_chart(weather_data)
            if wind_chart:
                elements.append(wind_chart)
                elements.append(Spacer(1, 0.1*inch))

            rain_pop_chart = self.create_rain_pop_chart(
                weather_data)
            if rain_pop_chart:
                elements.append(rain_pop_chart)
                elements.append(Spacer(1, 0.1*inch))

            vis_chart = self.create_chart(
                weather_data, 'visibility', 'Visibility (m)', 'Visibility Trend')
            if vis_chart:
                elements.append(vis_chart)
                elements.append(Spacer(1, 0.05*inch))

            # NEW: Cloud Cover and Pressure charts (for both OWM and Open-Meteo)
            cloud_chart = self.create_chart(
                weather_data, 'cloud_cover', 'Cloud Cover (%)', 'Cloud Cover Trend')
            if cloud_chart:
                elements.append(cloud_chart)
                elements.append(Spacer(1, 0.05*inch))

            pressure_chart = self.create_chart(
                weather_data, 'pressure', 'Pressure (hPa)', 'Atmospheric Pressure Trend')
            if pressure_chart:
                elements.append(pressure_chart)
                elements.append(Spacer(1, 0.05*inch))
            # END NEW charts

            charts_added = sum(1 for chart in [
                               temp_hum_chart, wind_chart, rain_pop_chart, vis_chart,
                               cloud_chart, pressure_chart] if chart)  # Updated sum
            if charts_added == 0:
                elements.append(
                    Paragraph("No data available to generate weather charts.", normal_style))
            elements.append(Spacer(1, 0.1*inch))

        # --- NEW: Marine Forecast Section (for Open-Meteo only, specific locations) ---
        if api_source == "OpenMeteo" and marine_data:
            elements.append(
                Paragraph("Marine Forecast (Next 7 Days Hourly)", h2_style))

            marine_col_params = {
                'datetime': {'header': "Date/Time", 'format': lambda x: x, 'width': 1.8*inch, 'align': 'CENTER'},
                'wave_height': {'header': "Wave Height\n(m)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1.2*inch, 'align': 'RIGHT'},
                'wave_direction': {'header': "Wave Dir", 'format': lambda x: x, 'width': 1.2*inch, 'align': 'CENTER'},
                'wave_period': {'header': "Wave Period\n(s)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1.2*inch, 'align': 'RIGHT'}
            }
            marine_headers = [
                "Date/Time", "Wave Height\n(m)", "Wave Dir", "Wave Period\n(s)"]
            # Adjusted widths for fewer columns
            marine_col_widths = [1.8*inch, 1.2*inch, 1.2*inch, 1.2*inch]

            marine_table_data = [marine_headers]
            marine_numeric_data_for_highlight = {
                'wave_height': [], 'wave_period': []}
            marine_param_to_col_index = {'wave_height': 1, 'wave_period': 3}

            for row_idx, item in enumerate(marine_data):
                wave_height_formatted = marine_col_params['wave_height']['format'](
                    item.get('wave_height'))
                wave_period_formatted = marine_col_params['wave_period']['format'](
                    item.get('wave_period'))

                row = [
                    item['datetime'],
                    wave_height_formatted,
                    item['wave_direction'],
                    wave_period_formatted
                ]
                marine_table_data.append(row)

                table_row_index = row_idx + 1
                for param, value in [('wave_height', item.get('wave_height')),
                                     ('wave_period', item.get('wave_period'))]:
                    if isinstance(value, (int, float)) and not math.isnan(value):
                        marine_numeric_data_for_highlight[param].append(
                            (value, table_row_index))

            if len(marine_table_data) > 1:  # Only add table if there's actual data rows
                marine_table = Table(
                    marine_table_data, repeatRows=1, colWidths=marine_col_widths)
                marine_style_cmds = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10.5),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 6),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9.5),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),  # Wave Height
                    ('ALIGN', (3, 1), (3, -1), 'RIGHT'),  # Wave Period
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [colors.whitesmoke, colors.lightblue])
                ]
                for param, data_points in marine_numeric_data_for_highlight.items():
                    if data_points:
                        col_idx = marine_param_to_col_index[param]
                        min_val, min_row_idx = min(
                            data_points, key=lambda x: x[0])
                        max_val, max_row_idx = max(
                            data_points, key=lambda x: x[0])
                        marine_style_cmds.append(
                            ('BACKGROUND', (col_idx, min_row_idx), (col_idx, min_row_idx), colors.cyan))
                        marine_style_cmds.append(
                            ('BACKGROUND', (col_idx, max_row_idx), (col_idx, max_row_idx), colors.pink))
                marine_table.setStyle(TableStyle(marine_style_cmds))
                elements.append(marine_table)
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph(
                    "Note: Wave Dir = Direction waves are coming from.", small_note_style))
                elements.append(Spacer(1, 0.15*inch))

                elements.append(Paragraph("Marine Parameter Charts", h2_style))
                wave_height_chart = self.create_wave_chart(
                    marine_data, 'wave_height', 'Wave Height (m)', 'Wave Height Trend')
                if wave_height_chart:
                    elements.append(wave_height_chart)
                    elements.append(Spacer(1, 0.1*inch))

                wave_period_chart = self.create_wave_chart(
                    marine_data, 'wave_period', 'Wave Period (s)', 'Wave Period Trend')
                if wave_period_chart:
                    elements.append(wave_period_chart)
                    elements.append(Spacer(1, 0.05*inch))
            else:
                elements.append(Paragraph(
                    "Marine Forecast Data Not Available for this location or period.", normal_style))
            elements.append(Spacer(1, 0.1*inch))
        # --- END NEW Marine Forecast Section ---

        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("--- Report End ---", footer_style))
        if api_source == "OWM":
            elements.append(
                Paragraph("Weather data © OpenWeatherMap", footer_style))
        elif api_source == "OpenMeteo":
            elements.append(
                Paragraph("Weather data © Open-Meteo.com (Marine data also from Open-Meteo)", footer_style))  # Updated footer
        elements.append(
            Paragraph("Generated by Weather Reporter Tool | 2025 © TungTT", footer_style))

        try:
            doc.build(elements)
            print(f"PDF report generated: {file_name}")
        except Exception as build_err:
            print(f"Error building PDF: {build_err}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "PDF Error", f"Could not build PDF report:\n{build_err}")

    # --- MODIFIED generate_vietnamese_pdf_report (now accepts marine_data) ---
    def generate_vietnamese_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source, marine_data=None):

        page_width, page_height = landscape(letter)

        name_map = {'Đ': 'D', 'đ': 'd'}
        safe_name = ui_location_name
        for k, v in name_map.items():
            safe_name = safe_name.replace(k, v)
        file_name_location = re.sub(
            r'[\\/*?:"<>|()]+', "", safe_name).replace(' ', '_')
        file_name = f"BaoCao_ThoiTiet_{api_source}_{file_name_location}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

        doc = SimpleDocTemplate(
            file_name,
            pagesize=(page_width, page_height),
            topMargin=0.5*inch, bottomMargin=0.4*inch,
            leftMargin=0.5*inch, rightMargin=0.5*inch
        )

        elements = []
        styles = getSampleStyleSheet()

        title_style = styles['h1']
        h2_style = styles['h2']
        normal_style = styles['Normal']
        small_note_style = styles['Normal'].clone('SmallNote')
        footer_style = small_note_style.clone('Footer')

        title_style.fontName = VIETNAMESE_FONT_NAME_BOLD
        title_style.alignment = 1
        title_style.fontSize = 16

        h2_style.fontName = VIETNAMESE_FONT_NAME_BOLD
        h2_style.alignment = 0
        h2_style.fontSize = 14
        h2_style.spaceBefore = 15
        h2_style.spaceAfter = 4

        normal_style.fontName = VIETNAMESE_FONT_NAME
        normal_style.leading = 15
        normal_style.fontSize = 11

        small_note_style.fontName = VIETNAMESE_FONT_NAME
        small_note_style.fontSize = 9
        small_note_style.leading = 10
        small_note_style.textColor = colors.dimgray

        footer_style.fontName = VIETNAMESE_FONT_NAME
        footer_style.alignment = 1
        footer_style.fontSize = 8

        elements.append(Paragraph("Báo Cáo Dự Báo Thời Tiết",
                        title_style))
        elements.append(Spacer(1, 0.1*inch))

        api_name = location_info.get('name', '')
        country_code = location_info.get('country', 'N/A')

        api_details_parts = []
        if api_name and api_name != ui_location_name and not api_name.startswith("Coords ("):
            api_details_parts.append(api_name)
        if country_code and country_code != 'N/A':
            api_details_parts.append(country_code)

        location_string = f"<b>Vị trí:</b> {ui_location_name}"
        if api_details_parts:
            api_details = ", ".join(api_details_parts)
            location_string += f" ({api_details})"

        elements.append(Paragraph(location_string, normal_style))
        elements.append(Paragraph(
            f"<b>Tọa độ:</b> Vĩ độ: {lat:.4f}, Kinh độ: {lon:.4f}", normal_style))
        elements.append(Paragraph(
            f"<b>Múi giờ:</b> {location_info.get('timezone', DEFAULT_TIMEZONE)}", normal_style))
        elements.append(Paragraph(
            f"<b>Mặt trời mọc:</b> {location_info.get('sunrise', 'N/A')}, <b>Mặt trời lặn:</b> {location_info.get('sunset', 'N/A')}", normal_style))
        elements.append(Paragraph(
            f"<b>Báo cáo tạo lúc:</b> {datetime.now(pytz.timezone(location_info.get('timezone', DEFAULT_TIMEZONE))).strftime('%Y-%m-%d %H:%M:%S %Z')}", normal_style))
        elements.append(
            Paragraph(f"<b>Nguồn dữ liệu:</b> {api_source}", normal_style))
        elements.append(Spacer(1, 0.2*inch))

        if weather_data:
            elements.append(
                Paragraph("Dự Báo Thời Tiết (5-7 Ngày Tới Theo Giờ)", h2_style))
            weather_headers = ["Ngày/Giờ", "Mô Tả", "Nhiệt Độ\n(°C)", "Độ Ẩm\n(%)", "Tốc độ gió\n(knots)",
                               "Gió giật\n(knots)", "Hướng\ngió", "Lượng mưa\n(mm/h)", "XS mưa\n(%)", "Tầm nhìn\n(m)"]
            weather_table_data = [weather_headers]

            numeric_data_for_highlight = {'temperature': [], 'wind_speed': [
            ], 'wind_gust': [], 'rain': [], 'visibility': [], 'humidity': [], 'pop': []}
            param_to_col_index = {'temperature': 2, 'humidity': 3, 'wind_speed': 4,
                                  'wind_gust': 5, 'rain': 7, 'pop': 8, 'visibility': 9}

            max_entries_for_table = 7 * 24

            for row_idx, item in enumerate(weather_data[:max_entries_for_table]):
                eng_desc = item.get('description', 'N/A')
                eng_wind_dir = item.get('wind_direction', 'N/A')
                viet_desc = WEATHER_DESC_VIET.get(eng_desc, None)
                if viet_desc is None:
                    for code, desc_en in WMO_WEATHER_CODES_EN.items():
                        if desc_en == eng_desc:
                            viet_desc = WMO_WEATHER_CODES_VIET.get(
                                code, eng_desc)
                            break
                    if viet_desc is None:
                        viet_desc = eng_desc

                viet_wind_dir = WIND_DIR_VIET.get(eng_wind_dir, eng_wind_dir)

                vis = item.get('visibility', 'N/A')
                vis_formatted = f"{int(vis):,}" if isinstance(
                    vis, (int, float)) else 'N/A'
                temp_val = item.get('temperature', 'N/A')
                temp_formatted = f"{temp_val:.1f}" if isinstance(
                    temp_val, (int, float)) else 'N/A'
                hum_val = item.get('humidity', 'N/A')
                hum_formatted = f"{hum_val:.0f}" if isinstance(
                    hum_val, (int, float)) else 'N/A'
                wind_val = item.get('wind_speed', 'N/A')
                wind_formatted = f"{wind_val:.1f}" if isinstance(
                    wind_val, (int, float)) else 'N/A'
                gust_val = item.get('wind_gust', 'N/A')
                gust_formatted = f"{gust_val:.1f}" if isinstance(
                    gust_val, (int, float)) else 'N/A'
                rain_val = item.get('rain', 'N/A')
                rain_formatted = f"{rain_val:.1f}" if isinstance(
                    rain_val, (int, float)) else 'N/A'
                pop_val = item.get('pop', 'N/A')
                pop_formatted = f"{pop_val:.0f}" if isinstance(
                    pop_val, (int, float)) else 'N/A'
                row = [
                    item['datetime'],
                    viet_desc,
                    temp_formatted,
                    hum_formatted,
                    wind_formatted,
                    gust_formatted,
                    viet_wind_dir,
                    rain_formatted,
                    pop_formatted,
                    vis_formatted
                ]
                weather_table_data.append(row)

                table_row_index = row_idx + 1
                for param, value in [('temperature', temp_val), ('humidity', hum_val), ('wind_speed', wind_val), ('wind_gust', gust_val), ('rain', rain_val), ('pop', pop_val), ('visibility', vis)]:
                    if isinstance(value, (int, float)) and not math.isnan(value):
                        numeric_data_for_highlight[param].append(
                            (value, table_row_index))

            weather_col_widths = [1.45*inch, 1.65*inch, 0.75*inch, 0.8*inch,
                                  0.95*inch, 0.95*inch, 0.72*inch, 0.93*inch, 0.72*inch, 0.85*inch]
            weather_table = Table(weather_table_data,
                                  repeatRows=1, colWidths=weather_col_widths)
            weather_style_cmds = [('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                  ('FONTNAME', (0, 0), (-1, -1),
                                   VIETNAMESE_FONT_NAME),
                                  ('FONTNAME', (0, 0), (-1, 0),
                                   VIETNAMESE_FONT_NAME_BOLD),
                                  ('FONTSIZE', (0, 0), (-1, 0), 10.5), ('BOTTOMPADDING',
                                                                        (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 6),
                                  ('FONTSIZE', (0, 1), (-1, -1), 10), ('TOPPADDING', (0, 1),
                                                                       (-1, -1), 5), ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                                  ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ALIGN', (2, 1), (3, -1), 'RIGHT'), ('ALIGN', (4, 1), (5, -1), 'RIGHT'), ('ALIGN', (7, 1), (9, -1), 'RIGHT'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightblue])]
            for param, data_points in numeric_data_for_highlight.items():
                if data_points:
                    col_idx = param_to_col_index[param]
                    min_val, min_row_idx = min(data_points, key=lambda x: x[0])
                    max_val, max_row_idx = max(data_points, key=lambda x: x[0])
                    weather_style_cmds.append(
                        ('BACKGROUND', (col_idx, min_row_idx), (col_idx, min_row_idx), colors.cyan))
                    weather_style_cmds.append(
                        ('BACKGROUND', (col_idx, max_row_idx), (col_idx, max_row_idx), colors.pink))
            weather_table.setStyle(TableStyle(weather_style_cmds))
            elements.append(weather_table)
            elements.append(Spacer(1, 0.1*inch))
            note_text_viet = "Ghi chú: 1 knot = 1.85 km/h; Hướng gió = Hướng gió thổi tới; XS mưa = Xác suất có mưa (được ước tính theo giờ dựa trên sự hiện diện của mưa/tuyết đối với Open-Meteo). Giá trị lượng mưa là mỗi giờ đối với Open-Meteo, mỗi 3 giờ đối với OpenWeatherMap."
            elements.append(Paragraph(note_text_viet, small_note_style))
            elements.append(Spacer(1, 0.15*inch))
        else:
            elements.append(
                Paragraph("Không có dữ liệu dự báo thời tiết", h2_style))
            elements.append(Spacer(1, 0.15*inch))

        if weather_data:
            elements.append(
                Paragraph("Biểu Đồ Thông Số Thời Tiết", h2_style))

            temp_hum_chart = self.create_temp_humidity_chart(
                weather_data,
                xlabel_text='Ngày/Giờ',
                temp_ylabel='Nhiệt Độ (°C)',
                hum_ylabel='Độ Ẩm (%)',
                title_text='Xu Hướng Nhiệt Độ và Độ Ẩm',
                temp_label='Nhiệt Độ',
                hum_label='Độ Ẩm'
            )
            if temp_hum_chart:
                elements.append(temp_hum_chart)
                elements.append(Spacer(1, 0.1*inch))

            wind_chart = self.create_wind_chart(
                weather_data,
                xlabel_text='Ngày/Giờ',
                ylabel_text='Tốc độ (knots)',
                title_text='Xu Hướng Tốc Độ Gió và Gió Giật',
                speed_label='Tốc độ gió',
                gust_label='Gió giật'
            )
            if wind_chart:
                elements.append(wind_chart)
                elements.append(Spacer(1, 0.1*inch))

            rain_pop_chart = self.create_rain_pop_chart(
                weather_data,
                xlabel_text='Ngày/Giờ',
                rain_ylabel='Lượng mưa (mm/h)',
                pop_ylabel='Xác Suất Mưa (%)',
                title_text='Xu Hướng Lượng Mưa và Xác Suất Mưa',
                rain_label='Lượng mưa',
                pop_label='XS Mưa'
            )
            if rain_pop_chart:
                elements.append(rain_pop_chart)
                elements.append(Spacer(1, 0.1*inch))

            vis_chart = self.create_chart(
                weather_data,
                'visibility',
                'Tầm nhìn (m)',
                'Tầm Nhìn Xa',
                xlabel_text='Ngày/Giờ'
            )
            if vis_chart:
                elements.append(vis_chart)
                elements.append(Spacer(1, 0.05*inch))

            # NEW: Cloud Cover and Pressure charts (for both OWM and Open-Meteo) in Vietnamese
            cloud_chart = self.create_chart(
                weather_data, 'cloud_cover', 'Che phủ mây (%)', 'Xu Hướng Che Phủ Mây',
                xlabel_text='Ngày/Giờ')
            if cloud_chart:
                elements.append(cloud_chart)
                elements.append(Spacer(1, 0.05*inch))

            pressure_chart = self.create_chart(
                weather_data, 'pressure', 'Áp suất (hPa)', 'Xu Hướng Áp Suất Khí Quyển',
                xlabel_text='Ngày/Giờ')
            if pressure_chart:
                elements.append(pressure_chart)
                elements.append(Spacer(1, 0.05*inch))
            # END NEW charts

            charts_added = sum(1 for chart in [
                               temp_hum_chart, wind_chart, rain_pop_chart, vis_chart,
                               cloud_chart, pressure_chart] if chart)
            if charts_added == 0:
                elements.append(
                    Paragraph("Không có dữ liệu để tạo biểu đồ.", normal_style))
            elements.append(Spacer(1, 0.1*inch))

        # --- NEW: Marine Forecast Section (for Open-Meteo only, specific locations) in Vietnamese ---
        if api_source == "OpenMeteo" and marine_data:
            elements.append(
                Paragraph("Dự Báo Biển (7 Ngày Tới Theo Giờ)", h2_style))

            marine_headers_viet = [
                "Ngày/Giờ", "Chiều Cao Sóng\n(m)", "Hướng Sóng", "Chu Kỳ Sóng\n(giây)"]
            marine_col_widths_viet = [1.8*inch, 1.2*inch, 1.2*inch, 1.2*inch]

            marine_table_data_viet = [marine_headers_viet]
            marine_numeric_data_for_highlight_viet = {
                'wave_height': [], 'wave_period': []}
            marine_param_to_col_index_viet = {
                'wave_height': 1, 'wave_period': 3}

            for row_idx, item in enumerate(marine_data):
                wave_height_formatted = f"{item.get('wave_height'):.1f}" if isinstance(
                    item.get('wave_height'), (int, float)) else 'N/A'
                wave_period_formatted = f"{item.get('wave_period'):.1f}" if isinstance(
                    item.get('wave_period'), (int, float)) else 'N/A'

                row = [
                    item['datetime'],
                    wave_height_formatted,
                    # Translate direction
                    WIND_DIR_VIET.get(
                        item['wave_direction'], item['wave_direction']),
                    wave_period_formatted
                ]
                marine_table_data_viet.append(row)

                table_row_index = row_idx + 1
                for param, value in [('wave_height', item.get('wave_height')),
                                     ('wave_period', item.get('wave_period'))]:
                    if isinstance(value, (int, float)) and not math.isnan(value):
                        marine_numeric_data_for_highlight_viet[param].append(
                            (value, table_row_index))

            if len(marine_table_data_viet) > 1:
                marine_table_viet = Table(
                    marine_table_data_viet, repeatRows=1, colWidths=marine_col_widths_viet)
                marine_style_cmds_viet = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    # Apply Vietnamese font to whole table
                    ('FONTNAME', (0, 0), (-1, -1), VIETNAMESE_FONT_NAME),
                    ('FONTNAME', (0, 0), (-1, 0),
                     VIETNAMESE_FONT_NAME_BOLD),  # Bold header
                    ('FONTSIZE', (0, 0), (-1, 0), 10.5),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 6),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                    ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [colors.whitesmoke, colors.lightblue])
                ]
                for param, data_points in marine_numeric_data_for_highlight_viet.items():
                    if data_points:
                        col_idx = marine_param_to_col_index_viet[param]
                        min_val, min_row_idx = min(
                            data_points, key=lambda x: x[0])
                        max_val, max_row_idx = max(
                            data_points, key=lambda x: x[0])
                        marine_style_cmds_viet.append(
                            ('BACKGROUND', (col_idx, min_row_idx), (col_idx, min_row_idx), colors.cyan))
                        marine_style_cmds_viet.append(
                            ('BACKGROUND', (col_idx, max_row_idx), (col_idx, max_row_idx), colors.pink))
                marine_table_viet.setStyle(TableStyle(marine_style_cmds_viet))
                elements.append(marine_table_viet)
                elements.append(Spacer(1, 0.1*inch))
                elements.append(
                    Paragraph("Ghi chú: Hướng sóng = Hướng sóng tới.", small_note_style))
                elements.append(Spacer(1, 0.15*inch))

                elements.append(Paragraph("Biểu Đồ Thông Số Biển", h2_style))
                wave_height_chart_viet = self.create_wave_chart(
                    marine_data, 'wave_height', 'Chiều Cao Sóng (m)', 'Xu Hướng Chiều Cao Sóng', xlabel_text='Ngày/Giờ')
                if wave_height_chart_viet:
                    elements.append(wave_height_chart_viet)
                    elements.append(Spacer(1, 0.1*inch))

                wave_period_chart_viet = self.create_wave_chart(
                    marine_data, 'wave_period', 'Chu Kỳ Sóng (giây)', 'Xu Hướng Chu Kỳ Sóng', xlabel_text='Ngày/Giờ')
                if wave_period_chart_viet:
                    elements.append(wave_period_chart_viet)
                    elements.append(Spacer(1, 0.05*inch))
            else:
                elements.append(Paragraph(
                    "Không có dữ liệu dự báo biển cho vị trí hoặc thời gian này.", normal_style))
            elements.append(Spacer(1, 0.1*inch))
        # --- END NEW Marine Forecast Section in Vietnamese ---

        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("--- Kết thúc báo cáo ---",
                        footer_style))
        if api_source == "OWM":
            elements.append(
                Paragraph("Dữ liệu thời tiết © OpenWeatherMap", footer_style))
        elif api_source == "OpenMeteo":
            elements.append(
                Paragraph("Dữ liệu thời tiết © Open-Meteo.com (Dữ liệu biển cũng từ Open-Meteo)", footer_style))  # Updated footer
        elements.append(Paragraph(
            "Tạo bởi Weather Reporter Tool | 2025 © TungTT", footer_style))

        try:
            doc.build(elements)
            print(f"PDF report generated (Vietnamese): {file_name}")
        except Exception as build_err:
            print(f"Error building Vietnamese PDF: {build_err}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Lỗi PDF", f"Không thể tạo báo cáo PDF (Tiếng Việt):\n{build_err}")

    # --- NEW: generate_historical_pdf_report ---
    def generate_historical_pdf_report(self, lat, lon, historical_data, location_info, ui_location_name, from_date, to_date):
        page_width, page_height = landscape(letter)

        file_name_location = re.sub(
            r'[\\/*?:"<>|()]+', "", ui_location_name).replace(' ', '_')
        file_name = f"Historical_Weather_Report_OpenMeteo_{file_name_location}_{from_date.strftime('%Y%m%d')}_to_{to_date.strftime('%Y%m%d')}.pdf"

        doc = SimpleDocTemplate(
            file_name,
            pagesize=(page_width, page_height),
            topMargin=0.5*inch, bottomMargin=0.4*inch,
            leftMargin=0.5*inch, rightMargin=0.5*inch
        )

        elements = []
        styles = getSampleStyleSheet()

        title_style = styles['h1']
        title_style.alignment = 1
        title_style.fontSize = 16
        h2_style = styles['h2']
        h2_style.alignment = 0
        h2_style.fontSize = 14
        h2_style.spaceBefore = 15
        h2_style.spaceAfter = 4
        normal_style = styles['Normal']
        normal_style.leading = 15
        normal_style.fontSize = 11
        small_note_style = styles['Normal'].clone('SmallNote')
        small_note_style.fontSize = 9
        small_note_style.leading = 10
        small_note_style.textColor = colors.dimgray
        footer_style = small_note_style.clone('Footer')
        footer_style.alignment = 1
        footer_style.fontSize = 8

        elements.append(
            Paragraph("Historical Weather Data Report", title_style))
        elements.append(Spacer(1, 0.1*inch))

        api_name = location_info.get('name', '')
        country_code = location_info.get('country', 'N/A')

        api_details_parts = []
        if api_name and api_name != ui_location_name and not api_name.startswith("Coords ("):
            api_details_parts.append(api_name)
        if country_code and country_code != 'N/A':
            api_details_parts.append(country_code)

        location_string = f"<b>Location:</b> {ui_location_name}"
        if api_details_parts:
            api_details = ", ".join(api_details_parts)
            location_string += f" ({api_details})"

        elements.append(Paragraph(location_string, normal_style))
        elements.append(
            Paragraph(f"<b>Coordinates:</b> Lat: {lat:.4f}, Lon: {lon:.4f}", normal_style))
        elements.append(Paragraph(
            f"<b>Timezone:</b> {location_info.get('timezone', DEFAULT_TIMEZONE)}", normal_style))
        elements.append(Paragraph(
            f"<b>Data Period:</b> {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}", normal_style))
        elements.append(Paragraph(
            f"<b>Report Generated:</b> {datetime.now(pytz.timezone(location_info.get('timezone', DEFAULT_TIMEZONE))).strftime('%Y-%m-%d %H:%M:%S %Z')}", normal_style))
        elements.append(
            Paragraph("<b>Data Source:</b> Open-Meteo Historical Archive", normal_style))
        elements.append(Spacer(1, 0.2*inch))

        if historical_data:
            elements.append(
                Paragraph("Historical Weather Data (Hourly)", h2_style))

            col_params = {
                'datetime': {'header': "Date/Time", 'format': lambda x: x, 'width': 1.28*inch, 'align': 'CENTER'},
                'description': {'header': "Description", 'format': lambda x: x, 'width': 1.88*inch, 'align': 'CENTER'},
                'temperature': {'header': "Temp\n(°C)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
                'humidity': {'header': "Humidity\n(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.8*inch, 'align': 'RIGHT'},
                'wind_speed': {'header': "Wind Speed\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'wind_gust': {'header': "Wind Gust\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'wind_direction': {'header': "Wind\nDir", 'format': lambda x: x, 'width': 0.72*inch, 'align': 'CENTER'},
                'rain': {'header': "Rain\n(mm/h)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.75*inch, 'align': 'RIGHT'},
                'visibility': {'header': "Visibility\n(m)", 'format': lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.88*inch, 'align': 'RIGHT'},
                'cloud_cover': {'header': "Cloud\nCover(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.8*inch, 'align': 'RIGHT'},
                'pressure': {'header': "Pressure\n(hPa)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.8*inch, 'align': 'RIGHT'},
            }

            historical_headers = ["Date/Time", "Description", "Temp\n(°C)", "Humidity\n(%)",
                                  "Wind Speed\n(knots)", "Wind Gust\n(knots)", "Wind\nDir",
                                  "Rain\n(mm/h)", "Visibility\n(m)", "Cloud\nCover(%)", "Pressure\n(hPa)"]
            historical_col_widths = [1.28*inch, 1.88*inch, 0.72*inch, 0.8*inch,
                                     1*inch, 1*inch, 0.72*inch, 0.75*inch, 0.88*inch, 0.8*inch, 0.8*inch]

            param_to_col_index = {
                'temperature': 2, 'humidity': 3, 'wind_speed': 4, 'wind_gust': 5,
                'rain': 7, 'visibility': 8, 'cloud_cover': 9, 'pressure': 10
            }
            numeric_data_for_highlight = {p: []
                                          for p in param_to_col_index.keys()}

            historical_table_data = [historical_headers]

            # All historical data will be in table
            for row_idx, item in enumerate(historical_data):
                vis_formatted = col_params['visibility']['format'](
                    item.get('visibility'))
                temp_formatted = col_params['temperature']['format'](
                    item.get('temperature'))
                hum_formatted = col_params['humidity']['format'](
                    item.get('humidity'))
                wind_formatted = col_params['wind_speed']['format'](
                    item.get('wind_speed'))
                gust_formatted = col_params['wind_gust']['format'](
                    item.get('wind_gust'))
                rain_formatted = col_params['rain']['format'](item.get('rain'))
                cloud_formatted = col_params['cloud_cover']['format'](
                    item.get('cloud_cover'))
                pressure_formatted = col_params['pressure']['format'](
                    item.get('pressure'))

                row = [
                    item['datetime'],
                    item['description'],
                    temp_formatted,
                    hum_formatted,
                    wind_formatted,
                    gust_formatted,
                    item['wind_direction'],
                    rain_formatted,
                    vis_formatted,
                    cloud_formatted,
                    pressure_formatted
                ]
                historical_table_data.append(row)

                table_row_index = row_idx + 1
                for param, value in [('temperature', item.get('temperature')),
                                     ('humidity', item.get('humidity')),
                                     ('wind_speed', item.get('wind_speed')),
                                     ('wind_gust', item.get('wind_gust')),
                                     ('rain', item.get('rain')),
                                     ('visibility', item.get('visibility')),
                                     ('cloud_cover', item.get('cloud_cover')),
                                     ('pressure', item.get('pressure'))]:
                    if param in numeric_data_for_highlight and isinstance(value, (int, float)) and not math.isnan(value):
                        numeric_data_for_highlight[param].append(
                            (value, table_row_index))

            historical_table = Table(historical_table_data,
                                     repeatRows=1, colWidths=historical_col_widths)
            historical_style_cmds = [('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 10.5), ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 6), ('FONTNAME',
                                                                                                                                                                                                                                                                                                                                                                                           (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 9.5), ('TOPPADDING', (0, 1), (-1, -1), 5), ('BOTTOMPADDING', (0, 1), (-1, -1), 5), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ALIGN', (2, 1), (3, -1), 'RIGHT'), ('ALIGN', (4, 1), (5, -1), 'RIGHT'), ('ALIGN', (7, 1), (10, -1), 'RIGHT'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightblue])]
            for param, data_points in numeric_data_for_highlight.items():
                if data_points:
                    col_idx = param_to_col_index[param]
                    min_val, min_row_idx = min(data_points, key=lambda x: x[0])
                    max_val, max_row_idx = max(data_points, key=lambda x: x[0])
                    historical_style_cmds.append(
                        ('BACKGROUND', (col_idx, min_row_idx), (col_idx, min_row_idx), colors.cyan))
                    historical_style_cmds.append(
                        ('BACKGROUND', (col_idx, max_row_idx), (col_idx, max_row_idx), colors.pink))
            historical_table.setStyle(TableStyle(historical_style_cmds))
            elements.append(historical_table)
            elements.append(Spacer(1, 0.1*inch))
            note_text = "Note: 1 knot = 1.85 km/h; Wind Dir = Wind Direction. Rainfall values are per hour. PoP (Probability of Precipitation) is not available for historical data from Open-Meteo."
            elements.append(Paragraph(note_text, small_note_style))
            elements.append(Spacer(1, 0.15*inch))
        else:
            elements.append(
                Paragraph("Historical Weather Data Not Available for the selected period.", h2_style))
            elements.append(Spacer(1, 0.15*inch))

        if historical_data:
            elements.append(
                Paragraph("Historical Weather Parameter Charts", h2_style))

            temp_hum_chart = self.create_temp_humidity_chart(
                historical_data)
            if temp_hum_chart:
                elements.append(temp_hum_chart)
                elements.append(Spacer(1, 0.1*inch))

            wind_chart = self.create_wind_chart(historical_data)
            if wind_chart:
                elements.append(wind_chart)
                elements.append(Spacer(1, 0.1*inch))

            rain_chart = self.create_chart(
                historical_data, 'rain', 'Rainfall (mm/h)', 'Historical Rainfall Trend')
            if rain_chart:
                elements.append(rain_chart)
                elements.append(Spacer(1, 0.1*inch))

            vis_chart = self.create_chart(
                historical_data, 'visibility', 'Visibility (m)', 'Historical Visibility Trend')
            if vis_chart:
                elements.append(vis_chart)
                elements.append(Spacer(1, 0.05*inch))

            cloud_chart = self.create_chart(
                historical_data, 'cloud_cover', 'Cloud Cover (%)', 'Historical Cloud Cover Trend')
            if cloud_chart:
                elements.append(cloud_chart)
                elements.append(Spacer(1, 0.05*inch))

            pressure_chart = self.create_chart(
                historical_data, 'pressure', 'Pressure (hPa)', 'Historical Atmospheric Pressure Trend')
            if pressure_chart:
                elements.append(pressure_chart)
                elements.append(Spacer(1, 0.05*inch))

            charts_added = sum(1 for chart in [
                               temp_hum_chart, wind_chart, rain_chart, vis_chart,
                               cloud_chart, pressure_chart] if chart)
            if charts_added == 0:
                elements.append(
                    Paragraph("No data available to generate historical charts.", normal_style))
            elements.append(Spacer(1, 0.1*inch))

        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("--- Report End ---", footer_style))
        elements.append(
            Paragraph("Weather data © Open-Meteo.com (Historical Archive)", footer_style))
        elements.append(
            Paragraph("Generated by Weather Reporter Tool | 2025 © TungTT", footer_style))

        try:
            doc.build(elements)
            print(f"PDF historical report generated: {file_name}")
        except Exception as build_err:
            print(f"Error building historical PDF: {build_err}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "PDF Error", f"Could not build historical PDF report:\n{build_err}")

    # --- END NEW HISTORICAL PDF FUNCTION ---

    def closeEvent(self, event):
        if hasattr(self, 'session') and self.session:
            self.session.close()
            print("Requests session closed.")
        if hasattr(self, 'realtime_timer') and self.realtime_timer.isActive():
            self.realtime_timer.stop()
            print("Real-time update timer stopped.")
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    weather_app = WeatherCrawlerApp()
    weather_app.show()
    sys.exit(app.exec_())

# --- END OF FILE ---
