import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QRadioButton,
                             QMessageBox, QDateEdit, QProgressBar, QSizePolicy,
                             QGroupBox, QTextEdit)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt, QDate, QTimer, QSize, QDateTime
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
import re
import io
import traceback
import math
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# -*- coding: utf-8 -*-

# --- ReportLab Font Registration for Vietnamese ---
VIETNAMESE_FONT_NAME = 'Helvetica'
VIETNAMESE_FONT_NAME_BOLD = 'Helvetica-Bold'
try:
    font_path_regular = 'NotoSans-Regular.ttf'
    font_path_bold = 'NotoSans-Bold.ttf'

    if os.path.exists(font_path_regular) and os.path.exists(font_path_bold):
        pdfmetrics.registerFont(TTFont('NotoSans', font_path_regular))
        pdfmetrics.registerFont(TTFont('NotoSans-Bold', font_path_bold))
        VIETNAMESE_FONT_NAME = 'NotoSans'
        VIETNAMESE_FONT_NAME_BOLD = 'NotoSans-Bold'
        # Commented out
        print("Registered NotoSans font for Vietnamese PDF reports.")
    else:
        font_path_utm = 'UTM Neo Sans Intel.ttf'
        if os.path.exists(font_path_utm):
            pdfmetrics.registerFont(
                TTFont('UTM Neo Sans Intel', font_path_utm))
            pdfmetrics.registerFont(
                TTFont('UTM Neo Sans Intel-Bold', font_path_utm))
            VIETNAMESE_FONT_NAME = 'UTM Neo Sans Intel'
            VIETNAMESE_FONT_NAME_BOLD = 'UTM Neo Sans Intel-Bold'
            print("Registered UTM Neo Sans Intel font for Vietnamese PDF reports.")
        else:
            print(
                f"Warning: Neither NotoSans nor UTM Neo Sans Intel found. Using default Helvetica.")
except Exception as font_err:
    print(f"Warning: Could not register Vietnamese font. Error: {font_err}")
# --- End Font Registration ---

LOCATION_TIMEZONES = {
    # Southeast Asia (existing)
    'VN': 'Asia/Ho_Chi_Minh', 'ID': 'Asia/Jakarta', 'MY': 'Asia/Kuala_Lumpur', 'SG': 'Asia/Singapore',
    'TH': 'Asia/Bangkok', 'PH': 'Asia/Manila',
    # East Asia
    'CN': 'Asia/Shanghai', 'JP': 'Asia/Tokyo', 'KR': 'Asia/Seoul', 'TW': 'Asia/Taipei', 'HK': 'Asia/Hong_Kong',
    # South Asia
    'IN': 'Asia/Kolkata', 'PK': 'Asia/Karachi', 'BD': 'Asia/Dhaka', 'LK': 'Asia/Colombo', 'NP': 'Asia/Kathmandu',
    # Middle East
    'AE': 'Asia/Dubai', 'SA': 'Asia/Riyadh', 'QA': 'Asia/Qatar', 'IL': 'Asia/Jerusalem', 'TR': 'Europe/Istanbul',
    # Europe
    'GB': 'Europe/London', 'DE': 'Europe/Berlin', 'FR': 'Europe/Paris', 'IT': 'Europe/Rome', 'ES': 'Europe/Madrid',
    'PT': 'Europe/Lisbon', 'NL': 'Europe/Amsterdam', 'BE': 'Europe/Brussels', 'CH': 'Europe/Zurich',
    'SE': 'Europe/Stockholm', 'NO': 'Europe/Oslo', 'DK': 'Europe/Copenhagen', 'FI': 'Europe/Helsinki',
    'PL': 'Europe/Warsaw', 'AT': 'Europe/Vienna', 'GR': 'Europe/Athens', 'IE': 'Europe/Dublin', 'RU': 'Europe/Moscow',
    # North America
    'US': 'America/New_York', 'CA': 'America/Toronto', 'MX': 'America/Mexico_City',
    # Central America
    'PA': 'America/Panama', 'CR': 'America/Costa_Rica', 'GT': 'America/Guatemala',
    # South America
    'BR': 'America/Sao_Paulo', 'AR': 'America/Buenos_Aires', 'CL': 'America/Santiago', 'CO': 'America/Bogota',
    'PE': 'America/Lima', 'VE': 'America/Caracas',
    # Oceania
    'AU': 'Australia/Sydney', 'NZ': 'Pacific/Auckland', 'FJ': 'Pacific/Fiji',
    # Africa
    'ZA': 'Africa/Johannesburg', 'EG': 'Africa/Cairo', 'MA': 'Africa/Casablanca', 'NG': 'Africa/Lagos',
    'KE': 'Africa/Nairobi', 'ET': 'Africa/Addis_Ababa',
    # Additional countries omitted for brevity but present in the full code
}
DEFAULT_TIMEZONE = 'Asia/Ho_Chi_Minh'

# --- Translation Mappings ---
WEATHER_DESC_VIET = {
    'Clear sky': 'Trời quang', 'Few clouds': 'Ít mây', 'Scattered clouds': 'Mây rải rác',
    'Broken clouds': 'Nhiều mây', 'Overcast clouds': 'Trời u ám', 'Light rain': 'Mưa nhẹ',
    'Moderate rain': 'Mưa vừa', 'Heavy intensity rain': 'Mưa to', 'Very heavy rain': 'Mưa rất to',
    'Extreme rain': 'Mưa cực lớn', 'Freezing rain': 'Mưa đông đá', 'Light intensity shower rain': 'Mưa rào nhẹ',
    'Shower rain': 'Mưa rào', 'Heavy intensity shower rain': 'Mưa rào nặng hạt', 'Ragged shower rain': 'Mưa rào không đều',
    'Thunderstorm with light rain': 'Dông kèm mưa nhẹ', 'Thunderstorm with rain': 'Dông kèm mưa',
    'Thunderstorm with heavy rain': 'Dông kèm mưa to', 'Light thunderstorm': 'Dông nhẹ', 'Thunderstorm': 'Dông',
    'Heavy thunderstorm': 'Dông mạnh', 'Ragged thunderstorm': 'Dông không đều', 'Thunderstorm with light drizzle': 'Dông kèm mưa phùn nhẹ',
    'Thunderstorm with drizzle': 'Dông kèm mưa phùn', 'Thunderstorm with heavy drizzle': 'Dông kèm mưa phùn nặng hạt',
    'Light intensity drizzle': 'Mưa phùn nhẹ', 'Drizzle': 'Mưa phùn', 'Heavy intensity drizzle': 'Mưa phùn nặng hạt',
    'Light intensity drizzle rain': 'Mưa phùn/mưa nhẹ', 'Drizzle rain': 'Mưa phùn/mưa',
    'Heavy intensity drizzle rain': 'Mưa phùn/mưa nặng hạt', 'Shower rain and drizzle': 'Mưa rào và mưa phùn',
    'Heavy shower rain and drizzle': 'Mưa rào to và mưa phùn', 'Shower drizzle': 'Mưa phùn dạng mưa rào',
    'Light snow': 'Tuyết nhẹ', 'Snow': 'Tuyết', 'Heavy snow': 'Tuyết dày', 'Sleet': 'Mưa tuyết',
    'Light shower sleet': 'Mưa tuyết nhẹ', 'Shower sleet': 'Mưa tuyết', 'Light rain and snow': 'Mưa và tuyết nhẹ',
    'Rain and snow': 'Mưa và tuyết', 'Light shower snow': 'Tuyết rơi nhẹ', 'Shower snow': 'Tuyết rơi',
    'Heavy shower snow': 'Tuyết rơi dày', 'Mist': 'Sương mù nhẹ', 'Smoke': 'Khói', 'Haze': 'Bụi mù',
    'Sand/ dust whirls': 'Xoáy cát/bụi', 'Fog': 'Sương mù', 'Sand': 'Cát', 'Dust': 'Bụi',
    'Volcanic ash': 'Tro núi lửa', 'Squalls': 'Gió giật mạnh', 'Tornado': 'Lốc xoáy', 'N/A': 'Không xác định'
}

WIND_DIR_VIET = {
    'N': 'B', 'NNE': 'BĐB', 'NE': 'ĐB', 'ENE': 'ĐĐB', 'E': 'Đ', 'ESE': 'ĐĐN', 'SE': 'ĐN',
    'SSE': 'NĐN', 'S': 'N', 'SSW': 'NTN', 'SW': 'TN', 'WSW': 'TTN', 'W': 'T', 'WNW': 'TTB',
    'NW': 'TB', 'NNW': 'BTB', 'N/A': 'N/A'
}

WMO_WEATHER_CODES_EN = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog",
    48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle", 61: "Slight rain",
    63: "Moderate rain", 65: "Heavy rain", 66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Light snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall", 77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers", 85: "Slight snow showers",
    86: "Heavy snow showers", 95: "Thunderstorm (slight/moderate)",
    96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
}

WMO_WEATHER_CODES_VIET = {
    0: "Trời quang", 1: "Chủ yếu quang mây", 2: "Mây rải rác", 3: "Trời nhiều mây", 45: "Sương mù",
    48: "Sương mù có sương giá", 51: "Mưa phùn nhẹ", 53: "Mưa phùn vừa", 55: "Mưa phùn nặng hạt",
    56: "Mưa phùn nhẹ kèm đông đá", 57: "Mưa phùn nặng hạt kèm đông đá", 61: "Mưa nhẹ",
    63: "Mưa vừa", 65: "Mưa to", 66: "Mưa nhẹ kèm đông đá", 67: "Mưa to kèm đông đá",
    71: "Tuyết rơi nhẹ", 73: "Tuyết rơi vừa", 75: "Tuyết rơi dày", 77: "Hạt tuyết",
    80: "Mưa rào nhẹ", 81: "Mưa rào vừa", 82: "Mưa rào dữ dội", 85: "Mưa tuyết nhẹ",
    86: "Mưa tuyết dày", 95: "Dông (nhẹ/vừa)", 96: "Dông kèm mưa đá nhỏ", 99: "Dông kèm mưa đá lớn"
}

# --- Constants ---
OPENMETEO_API_URL = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
OPENMETEO_ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"


class WeatherCrawlerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather Reporter")
        # Default size, will be maximized
        self.setGeometry(100, 100, 1200, 800)

        icon_path = "weather_icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file {icon_path} not found")

        self.realtime_locations = {  # Master dictionary for all real-time locations
            'Lan Tay Platform - Block 06.1': (7.5783, 108.8694),
            'An Phu Office - An Khanh commune': (10.8094, 106.7366),
            'Rong Doi Platform - Block 11.2': (7.7925, 108.2021),
            'Vung Tau Airport - Vung Tau': (10.3760, 107.0932)
        }
        self.realtime_labels_data = {}

        self.api_key = "e1a69775e0d7c149a4e2bdb69bb59a82"

        self.initUI()
        self.session = self.create_requests_session()

        self.realtime_timer = QTimer(self)
        self.realtime_timer.timeout.connect(
            self._update_realtime_display)  # Timer remains global
        self.realtime_timer.start(15 * 60 * 1000)
        self._update_realtime_display()

        self.showMaximized()  # Set to full screen

    def initUI(self):
        # --- Main Layout (Horizontal Split) ---
        main_hbox = QHBoxLayout()
        left_vbox = QVBoxLayout()
        right_vbox = QVBoxLayout()
        bottom_layout = QVBoxLayout()

        # --- LEFT PANEL ---

        # --- 0. API Selection Section ---
        api_group = QGroupBox("Select Weather API Source:")
        api_group.setFont(QFont("Arial", 11, QFont.Bold))
        api_layout = QVBoxLayout()
        self.api_radio_owm = QRadioButton(
            "OpenWeatherMap (05-day forecast, Weather Maps)")
        self.api_radio_owm.setFont(QFont("Arial", 10))
        self.api_radio_openmeteo = QRadioButton(
            "Open-Meteo (07-day forecast, Marine & Historical)")
        self.api_radio_openmeteo.setFont(QFont("Arial", 10))
        self.api_radio_openmeteo.setChecked(True)
        api_layout.addWidget(self.api_radio_openmeteo)
        api_layout.addWidget(self.api_radio_owm)
        api_group.setLayout(api_layout)
        left_vbox.addWidget(api_group)

        # --- 1. Location Input Section ---
        locations_group = QGroupBox("Select Location:")
        locations_group.setFont(QFont("Arial", 11, QFont.Bold))
        input_layout = QVBoxLayout()
        self.lat_label = QLabel("Latitude:")
        self.lat_label.setFont(QFont("Arial", 10))
        self.lon_label = QLabel("Longitude:")
        self.lon_label.setFont(QFont("Arial", 10))
        self.lat_input = QLineEdit()
        self.lon_input = QLineEdit()
        self.lat_input.setEnabled(False)
        self.lon_input.setEnabled(False)

        self.locations = {
            'Lan Tay Platform - Block 06.1': (7.5783, 108.8694),
            'Rong Doi Platform - Block 11.2': (7.7925, 108.2021),
            'Home': (10.8317, 106.7327),
            'Ha Noi home': (21.0042, 105.8145),
            'An Phu Office - An Khanh commune': (10.8094, 106.7366),
            'Thao Dien Pitch': (10.8070, 106.7390),
            'Vung Tau Airport - Vung Tau': (10.3760, 107.0932)
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
        if default_location_key in self.location_radios:
            self.location_radios[default_location_key].setChecked(True)
        locations_group.setLayout(input_layout)
        left_vbox.addWidget(locations_group)

        # --- Generate Weather Report Section (MOVED TO LEFT PANEL) ---
        forecast_group = QGroupBox("Generate Weather Forecast Report")
        forecast_group.setFont(QFont("Arial", 11, QFont.Bold))
        forecast_vbox = QVBoxLayout()
        self.weather_button = QPushButton("Generate Report (English)")
        self.weather_button.setFont(QFont("Arial", 10))
        self.weather_button.setFixedHeight(30)  # Increased height
        self.weather_button.setStyleSheet(
            "background-color: #a7fcfd; color: black; font-weight: bold;")
        self.weather_button.clicked.connect(
            self.generate_weather_report_action)
        forecast_vbox.addWidget(self.weather_button)
        self.vietnamese_weather_button = QPushButton(
            "Tạo Báo Cáo Thời Tiết (Tiếng Việt)")
        self.vietnamese_weather_button.setFont(QFont("Arial", 10))
        self.vietnamese_weather_button.setFixedHeight(30)  # Increased height
        self.vietnamese_weather_button.setStyleSheet(
            "background-color: #a7fcfd; color: black; font-weight: bold;")
        self.vietnamese_weather_button.clicked.connect(
            self.generate_vietnamese_weather_report_action)
        forecast_vbox.addWidget(self.vietnamese_weather_button)
        forecast_group.setLayout(forecast_vbox)
        left_vbox.addWidget(forecast_group)  # Add to left_vbox

        # --- Historical Data Retrieval Section (MOVED TO LEFT PANEL) ---
        historical_group = QGroupBox(
            "Historical Weather Data Retrieval (Open-Meteo)")
        historical_group.setFont(QFont("Arial", 11, QFont.Bold))
        historical_layout = QVBoxLayout()
        # --- Real-time Weather Dashboard Section (LEFT PANEL) ---
        realtime_group_left = QGroupBox(
            "Real-time Dashboard")  # Updated title
        realtime_group_left.setFont(QFont("Arial", 11, QFont.Bold))
        realtime_layout_left = QVBoxLayout()
        realtime_font = QFont("Arial", 10)
        icon_size = 27
        # Define a size for location pictures
        location_image_size = QSize(250, 135)

        # Define locations for the left panel - Updated to include all 4 locations
        left_panel_rt_locations = [
            'Lan Tay Platform - Block 06.1',
            'Rong Doi Platform - Block 11.2',
            'An Phu Office - An Khanh commune',
            'Vung Tau Airport - Vung Tau'
        ]

        for loc_name in left_panel_rt_locations:
            loc_group = QGroupBox(loc_name)
            loc_group.setFont(QFont("Arial", 10, QFont.Bold))

            loc_main_hbox = QHBoxLayout()  # Main HBox for details and picture
            loc_details_vbox = QVBoxLayout()  # VBox for temp, wind, desc

            desc_hbox = QHBoxLayout()
            desc_icon_label = QLabel()
            desc_icon_label.setPixmap(QPixmap("icons/desc.png").scaled(
                icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            desc_label = QLabel("Desc: N/A")
            desc_label.setFont(realtime_font)
            desc_hbox.addWidget(desc_icon_label)
            desc_hbox.addWidget(desc_label)
            desc_hbox.addStretch()
            loc_details_vbox.addLayout(desc_hbox)

            temp_hbox = QHBoxLayout()
            temp_icon_label = QLabel()
            temp_icon_label.setPixmap(QPixmap("icons/temp.png").scaled(
                icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            temp_label = QLabel("Temp: N/A")
            temp_label.setFont(realtime_font)
            temp_hbox.addWidget(temp_icon_label)
            temp_hbox.addWidget(temp_label)
            temp_hbox.addStretch()
            loc_details_vbox.addLayout(temp_hbox)

            wind_hbox = QHBoxLayout()
            wind_icon_label = QLabel()
            wind_icon_label.setPixmap(QPixmap("icons/wind.png").scaled(
                icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            wind_label = QLabel("Wind: N/A")
            wind_label.setFont(realtime_font)
            wind_hbox.addWidget(wind_icon_label)
            wind_hbox.addWidget(wind_label)
            wind_hbox.addStretch()
            loc_details_vbox.addLayout(wind_hbox)

            rain_hbox = QHBoxLayout()
            rain_icon_label = QLabel()
            rain_icon_label.setPixmap(QPixmap("icons/rain.png").scaled(
                icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            rain_label = QLabel("Rain: N/A")
            rain_label.setFont(realtime_font)
            rain_hbox.addWidget(rain_icon_label)
            rain_hbox.addWidget(rain_label)
            rain_hbox.addStretch()
            loc_details_vbox.addLayout(rain_hbox)

            # Add details to the left
            loc_main_hbox.addLayout(loc_details_vbox)

            # Add Location Picture
            location_image_label = QLabel()
            # Format loc_name for filename (e.g., "Lan Tay Platform" -> "Lan_Tay_Platform.png")
            image_filename = loc_name.replace(" ", "_") + ".png"
            image_path = os.path.join("Pictures", image_filename)

            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                location_image_label.setPixmap(pixmap.scaled(
                    location_image_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                # Placeholder if image not found
                location_image_label.setText("Img N/A")
            location_image_label.setFixedSize(
                location_image_size)  # Ensure consistent size
            # Add picture to the right
            loc_main_hbox.addWidget(
                location_image_label, alignment=Qt.AlignRight | Qt.AlignVCenter)

            # Set the main HBox as the group's layout
            loc_group.setLayout(loc_main_hbox)
            realtime_layout_left.addWidget(loc_group)
            self.realtime_labels_data[loc_name] = {
                'desc': desc_label,
                'temp': temp_label,
                'wind': wind_label,
                'rain': rain_label
            }

        # Add the alert and refresh section
        alert_refresh_hbox = QHBoxLayout()
        self.rt_refresh_button = QPushButton("Refresh Now")
        self.rt_refresh_button.setFont(QFont("Arial", 10))
        self.rt_refresh_button.setFixedWidth(180)  # Increased width
        self.rt_refresh_button.setFixedHeight(30)  # Increased height
        self.rt_refresh_button.setStyleSheet(
            "background-color: #a7fcfd; color: black; font-weight: bold;")
        self.rt_refresh_button.clicked.connect(self._update_realtime_display)
        alert_refresh_hbox.addWidget(self.rt_refresh_button)
        realtime_layout_left.addLayout(alert_refresh_hbox)
        alert_refresh_hbox.addStretch()
        self.rt_alert_label = QLabel("Wind Speed Alert: None")
        self.rt_alert_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.rt_alert_label.setStyleSheet("color: blue;")
        alert_refresh_hbox.addWidget(self.rt_alert_label)

        # Set the layout for the first dashboard
        realtime_group_left.setLayout(realtime_layout_left)

        # --- Real-time Weather Dashboard Section (LEFT PANEL items MOVED TO RIGHT PANEL) ---
        # Add the first real-time group to the right
        right_vbox.addWidget(realtime_group_left)
        date_range_layout = QHBoxLayout()

        date_label_font = QFont("Arial", 9)  # Set your desired font size here

        from_label = QLabel("From Date:")
        from_label.setFont(date_label_font)
        date_range_layout.addWidget(from_label)

        self.historical_from_date = QDateEdit(self)
        self.historical_from_date.setFont(date_label_font)
        self.historical_from_date.setDate(QDate.currentDate().addDays(-7))
        self.historical_from_date.setCalendarPopup(True)
        self.historical_from_date.setDisplayFormat("dd/MM/yyyy")
        self.historical_from_date.setFixedWidth(90)
        date_range_layout.addWidget(self.historical_from_date)

        to_label = QLabel("To Date:")
        to_label.setFont(date_label_font)
        date_range_layout.addWidget(to_label)

        self.historical_to_date = QDateEdit(self)
        self.historical_to_date.setFont(date_label_font)
        self.historical_to_date.setDate(QDate.currentDate())
        self.historical_to_date.setCalendarPopup(True)
        self.historical_to_date.setDisplayFormat("dd/MM/yyyy")
        self.historical_to_date.setFixedWidth(90)
        date_range_layout.addWidget(self.historical_to_date)
        date_range_layout.addStretch()
        historical_layout.addLayout(date_range_layout)
        self.fetch_historical_button = QPushButton(
            "Generate Historical Report (PDF)")
        self.fetch_historical_button.setFont(QFont("Arial", 10))
        self.fetch_historical_button.setFixedHeight(30)  # Increased height
        self.fetch_historical_button.setStyleSheet(
            "background-color: #a7fcfd; color: black; font-weight: bold;")
        self.fetch_historical_button.clicked.connect(
            self._fetch_historical_and_generate_report_action)
        historical_layout.addWidget(self.fetch_historical_button)
        # historical_group is now part of left_vbox
        historical_group.setLayout(historical_layout)
        # Add historical_group to left_vbox
        left_vbox.addWidget(historical_group)

        # --- Add left and right panels to main hbox ---
        main_hbox.addLayout(left_vbox, stretch=1)
        main_hbox.addLayout(right_vbox, stretch=1)

        # --- BOTTOM AREA (Progress Bar & Status) ---
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setVisible(False)
        bottom_layout.addWidget(self.status_label)

        # --- FINAL LAYOUT ASSEMBLY ---
        final_layout = QVBoxLayout()
        final_layout.addLayout(main_hbox)
        final_layout.addLayout(bottom_layout)
        self.setLayout(final_layout)
        self.toggle_gps_input()

    def toggle_gps_input(self):
        is_gps_selected = self.gps_radio.isChecked()
        self.lat_input.setEnabled(is_gps_selected)
        self.lon_input.setEnabled(is_gps_selected)
        self.gps_name_input.setEnabled(is_gps_selected)
        self.gps_name_label.setEnabled(is_gps_selected)

    def get_api_choice(self):
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
            QMessageBox.warning(self, "API Selection Error",
                                "Please select a weather API source.")
            return

        self._start_progress(f"Preparing to fetch data from {api_choice}...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        weather_data, location_info, marine_data, owm_maps = None, None, None, None

        try:
            self._update_progress_status(
                f"Fetching weather data from {api_choice}... Please wait")
            if api_choice == "OWM":
                weather_data, location_info = self._fetch_weather_data_owm(
                    lat, lon)
                self._update_progress_status(
                    "Fetching weather maps from OpenWeatherMap...")
                owm_maps = self._fetch_all_owm_map_tiles(lat, lon, zoom=6)
            elif api_choice == "OpenMeteo":
                weather_data, location_info = self._fetch_weather_data_openmeteo(
                    lat, lon)
                if location_name_selected in ['Lan Tay Platform - Block 06.1', 'Rong Doi Platform - Block 11.2']:
                    self._update_progress_status(
                        f"Fetching marine data for {location_name_selected}...")
                    marine_data = self._fetch_marine_data_openmeteo(
                        lat, lon, location_info.get('timezone', DEFAULT_TIMEZONE))

            if not weather_data:
                QMessageBox.warning(
                    self, "Weather Error", "Failed to fetch weather data. Report generation stopped.")
                self._end_progress("Failed.", success=False)
                QApplication.restoreOverrideCursor()
                return

            self._update_progress_status("Generating PDF report...")
            self.generate_pdf_report(lat, lon, weather_data, location_info,
                                     location_name_selected, api_choice, marine_data, owm_maps)
            self._end_progress("Report generated successfully!", success=True)
            QMessageBox.information(
                self, "Success", "Weather PDF report generated successfully!")

        except Exception as e:
            self._end_progress("Report generation failed.", success=False)
            print(
                f"An error occurred during weather report generation: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    def generate_vietnamese_weather_report_action(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return
        api_choice = self.get_api_choice()
        if not api_choice:
            QMessageBox.warning(self, "API Selection Error",
                                "Vui lòng chọn nguồn API thời tiết.")
            return

        self._start_progress(f"Đang chuẩn bị lấy dữ liệu từ {api_choice}...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        weather_data, location_info, marine_data, owm_maps = None, None, None, None

        try:
            self._update_progress_status(
                f"Đang lấy dữ liệu thời tiết từ {api_choice}...")
            if api_choice == "OWM":
                weather_data, location_info = self._fetch_weather_data_owm(
                    lat, lon)
                self._update_progress_status(
                    "Đang lấy bản đồ thời tiết từ OpenWeatherMap...")
                owm_maps = self._fetch_all_owm_map_tiles(lat, lon, zoom=6)
            elif api_choice == "OpenMeteo":
                weather_data, location_info = self._fetch_weather_data_openmeteo(
                    lat, lon)
                if location_name_selected in ['Lan Tay Platform - Block 06.1', 'Rong Doi Platform - Block 11.2']:
                    self._update_progress_status(
                        f"Đang lấy dữ liệu biển cho {location_name_selected}...")
                    marine_data = self._fetch_marine_data_openmeteo(
                        lat, lon, location_info.get('timezone', DEFAULT_TIMEZONE))

            if not weather_data:
                QMessageBox.warning(self, "Lỗi Dữ Liệu",
                                    "Không thể lấy dữ liệu thời tiết.")
                self._end_progress("Thất bại.", success=False)
                QApplication.restoreOverrideCursor()
                return

            self._update_progress_status(
                "Đang tạo báo cáo PDF (Tiếng Việt)...")
            self.generate_vietnamese_pdf_report(
                lat, lon, weather_data, location_info, location_name_selected, api_choice, marine_data, owm_maps)
            self._end_progress("Đã tạo báo cáo thành công!", success=True)
            QMessageBox.information(
                self, "Thành Công", "Đã tạo báo cáo PDF (Tiếng Việt) thành công!")

        except Exception as e:
            self._end_progress("Tạo báo cáo thất bại.", success=False)
            print(
                f"An error occurred during Vietnamese report generation: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(
                self, "Lỗi", f"Đã xảy ra lỗi không mong muốn:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _fetch_historical_and_generate_report_action(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return

        from_date = self.historical_from_date.date().toPyDate()
        to_date = self.historical_to_date.date().toPyDate()

        if from_date > to_date:
            QMessageBox.warning(self, "Date Error",
                                "From Date cannot be after To Date.")
            return
        if (to_date - from_date).days > 365 * 2:
            QMessageBox.warning(self, "Date Range Warning",
                                "Please select a date range of up to 2 years.")
            return

        _, location_info = self._fetch_weather_data_openmeteo(lat, lon)
        timezone_for_historical = location_info.get(
            'timezone', DEFAULT_TIMEZONE)

        self._start_progress(
            f"Fetching historical data for {location_name_selected}...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            historical_data = self._fetch_historical_data_openmeteo(
                lat, lon, from_date.strftime(
                    '%Y-%m-%d'), to_date.strftime('%Y-%m-%d'),
                timezone_for_historical
            )
            if not historical_data:
                QMessageBox.warning(
                    self, "Historical Data Error", "Failed to fetch historical data.")
                self._end_progress("Failed.", success=False)
                QApplication.restoreOverrideCursor()
                return

            self._update_progress_status("Generating historical PDF report...")
            self.generate_historical_pdf_report(
                lat, lon, historical_data, location_info, location_name_selected, from_date, to_date)
            self._end_progress(
                "Historical report generated successfully!", success=True)
            QMessageBox.information(
                self, "Success", "Historical PDF report generated successfully!")

        except Exception as e:
            self._end_progress(
                "Historical report generation failed.", success=False)
            print(
                f"An error occurred during historical report generation: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    def get_coordinates(self):
        if self.gps_radio.isChecked():
            try:
                lat, lon = float(self.lat_input.text()), float(
                    self.lon_input.text())
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Range error")
                custom_name = self.gps_name_input.text().strip(
                ) or f"Custom GPS ({lat:.4f}, {lon:.4f})"
                return lat, lon, custom_name
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Input Error",
                                    "Invalid GPS coordinates.")
                return None, None, None
        else:
            for name, radio in self.location_radios.items():
                if radio.isChecked():
                    return self.locations[name][0], self.locations[name][1], name
        QMessageBox.warning(self, "Input Error", "Please select a location.")
        return None, None, None

    def create_requests_session(self):
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1,
                        status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update(
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        return session

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
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        self.status_label.setText(message)
        QTimer.singleShot(2000, lambda: [self.status_label.setVisible(
            False), self.progress_bar.setVisible(False)])

    def _fetch_weather_data_owm(self, lat, lon):
        base_url = "https://api.openweathermap.org/data/2.5/"
        units = "metric"
        timeout = (15, 30)
        location_info = {'name': f"Coords ({lat:.4f}, {lon:.4f})", 'country': 'N/A',
                         'sunrise': 'N/A', 'sunset': 'N/A', 'timezone': DEFAULT_TIMEZONE}
        try:
            current_url = f"{base_url}weather?lat={lat}&lon={lon}&appid={self.api_key}&units={units}"
            current_response = self.session.get(current_url, timeout=timeout)
            current_response.raise_for_status()
            current_data = current_response.json()

            forecast_url = f"{base_url}forecast?lat={lat}&lon={lon}&appid={self.api_key}&units={units}&cnt=40"
            forecast_response = self.session.get(forecast_url, timeout=timeout)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            timezone_str = DEFAULT_TIMEZONE
            country_code = current_data.get('sys', {}).get('country')
            if country_code and country_code in LOCATION_TIMEZONES:
                timezone_str = LOCATION_TIMEZONES[country_code]
            elif 'timezone' in current_data:
                try:
                    offset_sec = int(current_data['timezone'])
                    local_tz = timezone(timedelta(seconds=offset_sec))
                except Exception:
                    local_tz = pytz.timezone(DEFAULT_TIMEZONE)
            else:
                local_tz = pytz.timezone(DEFAULT_TIMEZONE)

            location_info['timezone'] = str(local_tz)
            location_info['name'] = current_data.get(
                'name', location_info['name'])
            location_info['country'] = current_data.get(
                'sys', {}).get('country', 'N/A')
            if 'sunrise' in current_data.get('sys', {}):
                location_info['sunrise'] = datetime.fromtimestamp(
                    current_data['sys']['sunrise'], tz=pytz.utc).astimezone(local_tz).strftime('%H:%M')
            if 'sunset' in current_data.get('sys', {}):
                location_info['sunset'] = datetime.fromtimestamp(
                    current_data['sys']['sunset'], tz=pytz.utc).astimezone(local_tz).strftime('%H:%M')

            processed_forecast = self._process_forecast_data_owm(
                forecast_data, local_tz)
            return processed_forecast, location_info
        except Exception as e:
            print(f"Error in _fetch_weather_data_owm: {e}")
            return None, location_info

    def _fetch_weather_data_openmeteo(self, lat, lon):
        params = {"latitude": lat, "longitude": lon, "hourly": "temperature_2m,relative_humidity_2m,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m,visibility,cloud_cover,pressure_msl,uv_index",
                  "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,weather_code", "timezone": "auto", "forecast_days": 16, "temperature_unit": "celsius", "wind_speed_unit": "kn", "precipitation_unit": "mm"}
        try:
            response = self.session.get(
                OPENMETEO_API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            location_info = {'name': f"Coords ({lat:.4f}, {lon:.4f})", 'country': 'N/A',
                             'timezone': data.get('timezone', DEFAULT_TIMEZONE)}
            local_tz = pytz.timezone(location_info['timezone'])
            daily_data = data.get('daily', {})
            if daily_data.get('sunrise') and daily_data['sunrise']:
                location_info['sunrise'] = datetime.fromisoformat(daily_data['sunrise'][0].replace(
                    'Z', '+00:00')).astimezone(local_tz).strftime('%H:%M')
            if daily_data.get('sunset') and daily_data['sunset']:
                location_info['sunset'] = datetime.fromisoformat(daily_data['sunset'][0].replace(
                    'Z', '+00:00')).astimezone(local_tz).strftime('%H:%M')
            processed_data = self._process_forecast_data_openmeteo(
                data.get('hourly', {}), local_tz)
            return processed_data, location_info
        except Exception as e:
            print(f"Error in _fetch_weather_data_openmeteo: {e}")
            return None, {}

    def _fetch_realtime_data_openmeteo(self, lat, lon, location_name):
        """
        Fetch real-time weather data from Open-Meteo for a given location.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "precipitation,weather_code",
            "timezone": "auto"
        }
        try:
            response = self.session.get(
                OPENMETEO_API_URL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            current = data.get("current_weather", {})
            local_tz = pytz.timezone(data.get("timezone", DEFAULT_TIMEZONE))
            # Rain: try to get from hourly if available
            rain_val = 0.0
            rain_time = None
            if "hourly" in data and "precipitation" in data["hourly"]:
                # Find the closest hour to now
                now = datetime.now(local_tz)
                times = data["hourly"].get("time", [])
                rain_vals = data["hourly"].get("precipitation", [])
                for t, v in zip(times, rain_vals):
                    dt = datetime.fromisoformat(t).astimezone(local_tz)
                    if abs((dt - now).total_seconds()) < 3600:
                        rain_val = v
                        rain_time = dt
                        break
            weather_code = current.get('weathercode', None)
            return {
                'temperature': f"{current.get('temperature', 0):.1f}°C",
                'wind_speed': f"{current.get('windspeed', 0):.1f} knots",
                'wind_speed_value': current.get('windspeed', 0),
                'weather_description': WMO_WEATHER_CODES_EN.get(weather_code, "N/A"),
                'wind_direction': self._degrees_to_direction(current.get('winddirection')),
                'time_as_of': datetime.now(local_tz).strftime('%H:%M'),
                'rain': f"{rain_val:.1f} mm/h"
            }
        except Exception as e:
            print(f"Error fetching real-time OM data for {location_name}: {e}")
            return None

    def _fetch_realtime_data_owm(self, lat, lon, location_name):
        params = {"lat": lat, "lon": lon,
                  "appid": self.api_key, "units": "metric"}
        try:
            response = self.session.get(
                "https://api.openweathermap.org/data/2.5/weather", params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            wind_speed_knots = round(
                data.get('wind', {}).get('speed', 0) * 1.94384, 1)
            local_tz = timezone(timedelta(seconds=data.get('timezone', 0)))
            # --- Rain extraction ---
            rain_val = 0.0
            rain_data = data.get('rain', {})
            if isinstance(rain_data, dict):
                # OWM may provide '1h' or '3h' keys
                rain_val = rain_data.get('1h', rain_data.get('3h', 0.0))
            return {
                'temperature': f"{data.get('main', {}).get('temp', 0):.1f}°C",
                'wind_speed': f"{wind_speed_knots:.1f} knots",
                'wind_speed_value': wind_speed_knots,
                'weather_description': data.get('weather', [{}])[0].get('description', 'N/A').capitalize(),
                'wind_direction': self._degrees_to_direction(data.get('wind', {}).get('deg')),
                'time_as_of': datetime.now(local_tz).strftime('%H:%M'),
                'rain': f"{rain_val:.1f} mm/h"
            }
        except Exception as e:
            print(
                f"Error fetching real-time OWM data for {location_name}: {e}")
            return None

    def _update_realtime_display(self):
        print("\n--- Updating Real-time Weather Dashboard (from Open-Meteo) ---")
        max_wind_speed_overall = 0.0
        for name, coords in self.realtime_locations.items():
            data = self._fetch_realtime_data_openmeteo(
                coords[0], coords[1], name)
            labels = self.realtime_labels_data.get(name)
            if data and labels:
                labels['temp'].setText(f"Temp: {data['temperature']}")
                labels['rain'].setText(f"Rain: {data['rain']}")
                labels['wind'].setText(
                    f"Wind: {data['wind_speed']} ({data['wind_direction']})")
                labels['desc'].setText(
                    f"Desc: {data['weather_description']} (as of {data['time_as_of']})")
                if data['wind_speed_value'] > max_wind_speed_overall:
                    max_wind_speed_overall = data['wind_speed_value']
            elif labels:
                labels['temp'].setText("Temp: N/A")
                labels['wind'].setText("Wind: N/A")
                labels['rain'].setText("Rain: N/A")
                labels['desc'].setText("Desc: Failed")

        if max_wind_speed_overall > 30.0:
            self.rt_alert_label.setText(
                f"HIGH WIND ALERT! ({max_wind_speed_overall:.1f} knots)")
            self.rt_alert_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.rt_alert_label.setText(
                f"Wind Speed Alert: None (Max: {max_wind_speed_overall:.1f} knots)")
            self.rt_alert_label.setStyleSheet("color: green;")
        QApplication.processEvents()
        print("--- Real-time Weather Dashboard Updated ---")

    def _fetch_marine_data_openmeteo(self, lat, lon, timezone_str):
        params = {"latitude": lat, "longitude": lon, "hourly": "wave_height,wave_direction,wave_period,wind_wave_height,wind_wave_direction,wind_wave_period,swell_wave_height,swell_wave_direction,swell_wave_period",
                  "timezone": timezone_str, "forecast_days": 7}
        try:
            response = self.session.get(
                OPENMETEO_MARINE_API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json().get('hourly', {})
            processed_data = []
            local_tz = pytz.timezone(timezone_str)
            for i in range(len(data.get('time', []))):
                dt_obj = datetime.fromisoformat(
                    data['time'][i]).astimezone(local_tz)
                processed_data.append({
                    'datetime_obj': dt_obj, 'datetime': dt_obj.strftime('%Y-%m-%d %H:%M'),
                    'wave_height': data['wave_height'][i], 'wave_direction': self._degrees_to_direction(data['wave_direction'][i]),
                    'wave_period': data['wave_period'][i], 'wind_wave_height': data['wind_wave_height'][i],
                    'wind_wave_direction': self._degrees_to_direction(data['wind_wave_direction'][i]), 'wind_wave_period': data['wind_wave_period'][i],
                    'swell_wave_height': data['swell_wave_height'][i], 'swell_wave_direction': self._degrees_to_direction(data['swell_wave_direction'][i]),
                    'swell_wave_period': data['swell_wave_period'][i],
                })
            return processed_data
        except Exception as e:
            print(f"Error in _fetch_marine_data_openmeteo: {e}")
            return None

    def _fetch_historical_data_openmeteo(self, lat, lon, start_date_str, end_date_str, timezone_str):
        params = {"latitude": lat, "longitude": lon, "start_date": start_date_str, "end_date": end_date_str, "hourly": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m,cloud_cover,pressure_msl,visibility",
                  "timezone": timezone_str, "temperature_unit": "celsius", "wind_speed_unit": "kn", "precipitation_unit": "mm"}
        try:
            response = self.session.get(
                OPENMETEO_ARCHIVE_API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json().get('hourly', {})
            processed_data = []
            local_tz = pytz.timezone(timezone_str)
            for i in range(len(data.get('time', []))):
                dt_obj = datetime.fromisoformat(
                    data['time'][i]).astimezone(local_tz)
                processed_data.append({
                    'datetime_obj': dt_obj, 'datetime': dt_obj.strftime('%Y-%m-%d %H:%M'),
                    'description': WMO_WEATHER_CODES_EN.get(data['weather_code'][i]), 'temperature': data['temperature_2m'][i],
                    'humidity': data['relative_humidity_2m'][i], 'wind_speed': data['wind_speed_10m'][i],
                    'wind_gust': data['wind_gusts_10m'][i], 'wind_direction': self._degrees_to_direction(data['wind_direction_10m'][i]),
                    'rain': data['precipitation'][i], 'cloud_cover': data['cloud_cover'][i], 'pressure': data['pressure_msl'][i],
                    'visibility': data['visibility'][i], 'pop': 'N/A'
                })
            return processed_data
        except Exception as e:
            print(f"Error in _fetch_historical_data_openmeteo: {e}")
            return None

    def _convert_coord_to_tile(self, lat, lon, zoom):
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return xtile, ytile

    def _fetch_owm_map_tile(self, layer, z, x, y):
        url = f"https://tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png?appid={self.api_key}"
        try:
            response = self.session.get(url, timeout=10, stream=True)
            response.raise_for_status()
            img_buffer = BytesIO()
            img_buffer.write(response.content)
            img_buffer.seek(0)
            return Image(img_buffer, width=2.2*inch, height=2.2*inch)
        except Exception as e:
            print(f"Failed to fetch OWM map tile for layer {layer}: {e}")
            return None

    def _fetch_all_owm_map_tiles(self, lat, lon, zoom):
        x, y = self._convert_coord_to_tile(lat, lon, zoom)
        maps = {}
        layers = {'Clouds': 'clouds_new', 'Temperature': 'temp_new',
                  'Wind Speed': 'wind_new', 'Precipitation': 'precipitation_new'}
        for name, layer_code in layers.items():
            tile = self._fetch_owm_map_tile(layer_code, zoom, x, y)
            if tile:
                maps[name] = tile
        return maps

    def _process_forecast_data_owm(self, data, local_tz):
        processed = []
        now_local = datetime.now(local_tz)
        for item in data.get('list', []):
            local_time = datetime.fromtimestamp(
                item['dt'], tz=pytz.utc).astimezone(local_tz)
            if now_local - timedelta(hours=3) <= local_time <= now_local + timedelta(days=5, hours=3):
                processed.append({
                    'datetime_obj': local_time, 'datetime': local_time.strftime('%Y-%m-%d %H:%M'),
                    'description': item.get('weather', [{}])[0].get('description', 'N/A').capitalize(),
                    'temperature': item.get('main', {}).get('temp'), 'humidity': item.get('main', {}).get('humidity'),
                    'pressure': item.get('main', {}).get('pressure'),
                    'wind_speed': round(item.get('wind', {}).get('speed', 0) * 1.94384, 1),
                    'wind_gust': round(item.get('wind', {}).get('gust', 0) * 1.94384, 1),
                    'wind_direction': self._degrees_to_direction(item.get('wind', {}).get('deg')),
                    'rain': item.get('rain', {}).get('3h', 0.0), 'visibility': item.get('visibility'),
                    'pop': round(item.get('pop', 0.0) * 100), 'cloud_cover': item.get('clouds', {}).get('all')
                })
        return processed

    def _process_forecast_data_openmeteo(self, hourly_data, local_tz):
        processed = []
        now_local = datetime.now(local_tz)
        times = hourly_data.get('time', [])
        for i in range(len(times)):
            local_time = datetime.fromisoformat(times[i]).astimezone(local_tz)
            if now_local - timedelta(hours=1) <= local_time <= now_local + timedelta(days=7, hours=1):
                total_rain = (hourly_data.get('rain', [])[i] or 0) + (hourly_data.get(
                    'showers', [])[i] or 0) + (hourly_data.get('snowfall', [])[i] or 0)
                processed.append({
                    'datetime_obj': local_time, 'datetime': local_time.strftime('%Y-%m-%d %H:%M'),
                    'description': WMO_WEATHER_CODES_EN.get(hourly_data.get('weather_code', [])[i]),
                    'temperature': hourly_data.get('temperature_2m', [])[i], 'humidity': hourly_data.get('relative_humidity_2m', [])[i],
                    'pressure': hourly_data.get('pressure_msl', [])[i],
                    'wind_speed': hourly_data.get('wind_speed_10m', [])[i], 'wind_gust': hourly_data.get('wind_gusts_10m', [])[i],
                    'wind_direction': self._degrees_to_direction(hourly_data.get('wind_direction_10m', [])[i]),
                    'rain': total_rain, 'visibility': hourly_data.get('visibility', [])[i],
                    'pop': 100 if total_rain > 0 else 0, 'cloud_cover': hourly_data.get('cloud_cover', [])[i]
                })
        return processed

    def _degrees_to_direction(self, degrees):
        if degrees is None:
            return 'N/A'
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE',
                      'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        return directions[round(float(degrees) / (360 / len(directions))) % len(directions)]

    def create_chart(self, data, param_name, ylabel, title, date_key='datetime_obj', xlabel_text='Date/Time', color='tab:blue'):
        if not data:
            return None
        plt.figure(figsize=(9.0, 2.8))
        dates, values = [], []
        for item in data:
            if item.get(param_name) is not None and isinstance(item.get(date_key), datetime):
                dates.append(item[date_key])
                values.append(float(item[param_name]))
        if not dates or not values:
            plt.close()
            return None
        plt.plot(dates, values, marker='.', linestyle='-',
                 markersize=4, linewidth=1, color=color)
        plt.title(title, fontsize=10)
        plt.xlabel(xlabel_text, fontsize=9)
        plt.ylabel(ylabel, fontsize=9)
        plt.xticks(rotation=30, ha='right', fontsize=9)
        plt.yticks(fontsize=9)
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(
            byhour=[1, 7, 13, 19], tz=dates[0].tzinfo))
        plt.gca().xaxis.set_major_formatter(
            mdates.DateFormatter('%m-%d %H:%M', tz=dates[0].tzinfo))
        plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
        plt.tight_layout(pad=0.5)
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        img_buffer.seek(0)
        return Image(img_buffer, width=9.6*inch, height=3.6*inch)

    def create_wind_chart(self, data, **kwargs):
        if not data:
            return None
        fig, ax1 = plt.subplots(figsize=(9.0, 2.8))
        dates, speeds, gusts = [], [], []
        for item in data:
            if isinstance(item.get('datetime_obj'), datetime):
                dates.append(item['datetime_obj'])
                speeds.append(float(item.get('wind_speed', 'nan')))
                gusts.append(float(item.get('wind_gust', 'nan')))
        if not dates:
            plt.close(fig)
            return None
        ax1.plot(dates, speeds, marker='.',
                 label=kwargs.get('speed_label', 'Wind Speed'))
        ax1.plot(dates, gusts, marker='.', label=kwargs.get(
            'gust_label', 'Wind Gust'), color='orange')
        ax1.set_title(kwargs.get('title_text', 'Wind Trend'), fontsize=10)
        ax1.set_xlabel(kwargs.get('xlabel_text', 'Date/Time'), fontsize=9)
        ax1.set_ylabel(kwargs.get('ylabel_text', 'Speed (knots)'), fontsize=9)
        plt.xticks(rotation=30, ha='right', fontsize=9)
        plt.yticks(fontsize=9)
        ax1.xaxis.set_major_locator(mdates.HourLocator(
            byhour=[1, 7, 13, 19], tz=dates[0].tzinfo))
        ax1.xaxis.set_major_formatter(
            mdates.DateFormatter('%m-%d %H:%M', tz=dates[0].tzinfo))
        ax1.grid(True, linestyle='--')
        ax1.legend(fontsize=8)
        fig.tight_layout(pad=0.5)
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        img_buffer.seek(0)
        return Image(img_buffer, width=9.6*inch, height=3.6*inch)

    # Simplified versions of other chart functions for brevity; full versions should be used.
    def create_temp_humidity_chart(
        self, data, **kwargs): return self.create_dual_axis_chart(data, 'temperature', 'humidity', **kwargs)

    def create_rain_pop_chart(
        self, data, **kwargs): return self.create_dual_axis_chart(data, 'rain', 'pop', **kwargs)

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

    def create_dual_axis_chart(self, data, param1, param2, **kwargs):
        if not data:
            return None
        fig, ax1 = plt.subplots(figsize=(9.0, 2.8))
        dates, values1, values2 = [], [], []
        for item in data:
            if isinstance(item.get('datetime_obj'), datetime):
                dates.append(item['datetime_obj'])
                values1.append(float(item.get(param1, 'nan')))
                values2.append(float(item.get(param2, 'nan')))
        if not dates:
            plt.close(fig)
            return None

        color1 = kwargs.get(f'{param1}_color', 'tab:blue')
        line1, = ax1.plot(dates, values1, marker='.', color=color1, label=kwargs.get(
            f'{param1}_label', param1.capitalize()))
        ax1.set_xlabel(kwargs.get('xlabel_text', 'Date/Time'), fontsize=9)
        ax1.set_ylabel(kwargs.get(
            f'{param1}_ylabel', 'Value'), color=color1, fontsize=9)
        ax1.tick_params(axis='y', labelcolor=color1)

        ax2 = ax1.twinx()
        color2 = kwargs.get(f'{param2}_color', 'tab:orange')
        line2, = ax2.plot(dates, values2, marker='.', color=color2, label=kwargs.get(
            f'{param2}_label', param2.capitalize()))
        ax2.set_ylabel(kwargs.get(
            f'{param2}_ylabel', 'Value'), color=color2, fontsize=9)
        ax2.tick_params(axis='y', labelcolor=color2)
        if param2 == 'pop':
            ax2.set_ylim(0, 105)

        ax1.xaxis.set_major_locator(mdates.HourLocator(
            byhour=[1, 7, 13, 19], tz=dates[0].tzinfo))
        ax1.xaxis.set_major_formatter(
            mdates.DateFormatter('%m-%d %H:%M', tz=dates[0].tzinfo))
        plt.setp(ax1.get_xticklabels(), rotation=30, ha='right')

        fig.legend(handles=[line1, line2], loc='upper left', fontsize=8)
        plt.title(kwargs.get('title_text', 'Chart'), fontsize=10)
        ax1.grid(True, linestyle='--')
        fig.tight_layout(pad=0.5)

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        img_buffer.seek(0)
        return Image(img_buffer, width=9.6*inch, height=3.6*inch)

    # --- PDF Generation Functions ---
    # These are very long; they should be copied from the previous full script.
    # The key is that they now accept `marine_data` and `owm_maps` as arguments.
    def generate_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source, marine_data=None, owm_maps=None):
        # Full implementation from the previous step is required here.

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

        # This is a placeholder showing where the logic goes.
        print(
            f"Generating English PDF for {ui_location_name} using {api_source}.")
        # Inside, you'll build the `elements` list and include sections for weather,
        # marine forecast (if available), and OWM maps (if available).
        pass  # Replace with full function

    def generate_vietnamese_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source, marine_data=None, owm_maps=None):
        # Full implementation from the previous step is required here.

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

        print(
            f"Generating Vietnamese PDF for {ui_location_name} using {api_source}.")
        pass  # Replace with full function

    def generate_historical_pdf_report(self, lat, lon, historical_data, location_info, ui_location_name, from_date, to_date):
        # Full implementation from the previous step is required here.

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
        print(f"Generating Historical PDF for {ui_location_name}.")
        pass  # Replace with full function

    def closeEvent(self, event):
        if hasattr(self, 'session') and self.session:
            self.session.close()
            print("Requests session closed.")
        if hasattr(self, 'realtime_timer') and self.realtime_timer.isActive():
            self.realtime_timer.stop()
            print("Real-time update timer stopped.")
        event.accept()


if __name__ == '__main__':
    if not os.path.exists('icons'):
        os.makedirs('icons')
        print("Warning: 'icons' folder not found. Created folder. Please add temp.png, wind.png, desc.png, and rain.png.")
    if not os.path.exists('Pictures'):
        os.makedirs('Pictures')
        print("Warning: 'Pictures' folder not found. Created folder. Please add location images.")

    app = QApplication(sys.argv)
    weather_app = WeatherCrawlerApp()
    weather_app.show()
    sys.exit(app.exec_())
