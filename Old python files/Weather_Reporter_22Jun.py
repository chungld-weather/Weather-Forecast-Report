import sys
import os
import json
import re
import traceback
import math
from io import BytesIO
from datetime import datetime, timedelta, timezone

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import xlsxwriter
import pytz
import requests
from PyQt5.QtCore import (QPropertyAnimation, QEasingCurve, QTimer, Qt, QDate, pyqtProperty,
                          QSize)
from PyQt5.QtGui import QFont, QIcon, QColor, QPixmap
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QRadioButton,
                             QMessageBox, QDateEdit, QProgressBar, QCheckBox,
                             QGroupBox)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                Spacer)
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                Spacer, Image as RLImage)


# --- Validation: Prevent running after 30 Jun 2026 ---
VALIDATION_DEADLINE = datetime(2026, 6, 30, 23, 59, 59)
if datetime.now() > VALIDATION_DEADLINE:
    # Ensure QApplication instance exists for QMessageBox
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication(sys.argv)
    QMessageBox.critical(
        None,
        "Validation Expired",
        "This version of Weather Reporter is no longer valid after 30 Jun 2026.\nPlease contact the developer - Tung TT (0906921885) for an updated version."
    )
    sys.exit(1)

# --- Configuration Loading ---


def load_config():
    """Loads configuration from config.json."""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config.json: {e}")
        default_config = {
            "api_key_openweathermap": "YOUR_API_KEY_HERE",
            "dashboard_locations": ["Lan Tay Platform"],
            "locations": {
                "Lan Tay Platform": {"pdf_name": "Lan Tay Platform - Block 06.1", "coords": [7.5783, 108.8694]}
            }
        }
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        QMessageBox.warning(
            None, "Config Created", "config.json was not found. A default file has been created. Please edit it with your API key.")
        return default_config


CONFIG = load_config()

# --- Font and Constant Definitions ---
VIETNAMESE_FONT_NAME = 'Helvetica'
VIETNAMESE_FONT_NAME_BOLD = 'Helvetica-Bold'
try:
    font_path_regular, font_path_bold = 'NotoSans-Regular.ttf', 'NotoSans-Bold.ttf'
    if os.path.exists(font_path_regular) and os.path.exists(font_path_bold):
        pdfmetrics.registerFont(TTFont('NotoSans', font_path_regular))
        pdfmetrics.registerFont(TTFont('NotoSans-Bold', font_path_bold))
        VIETNAMESE_FONT_NAME, VIETNAMESE_FONT_NAME_BOLD = 'NotoSans', 'NotoSans-Bold'
        print("Registered NotoSans font.")
    else:
        print("Warning: NotoSans font not found. Using default Helvetica.")
except Exception as font_err:
    print(f"Warning: Could not register Vietnamese font. Error: {font_err}")

# ... (Translation dictionaries remain the same for brevity) ...
LOCATION_TIMEZONES = {'VN': 'Asia/Ho_Chi_Minh', 'ID': 'Asia/Jakarta', 'MY': 'Asia/Kuala_Lumpur', 'SG': 'Asia/Singapore', 'TH': 'Asia/Bangkok', 'PH': 'Asia/Manila', 'CN': 'Asia/Shanghai', 'JP': 'Asia/Tokyo', 'KR': 'Asia/Seoul', 'TW': 'Asia/Taipei', 'HK': 'Asia/Hong_Kong', 'IN': 'Asia/Kolkata', 'PK': 'Asia/Karachi', 'BD': 'Asia/Dhaka', 'LK': 'Asia/Colombo', 'NP': 'Asia/Kathmandu', 'AE': 'Asia/Dubai', 'SA': 'Asia/Riyadh', 'QA': 'Asia/Qatar', 'IL': 'Asia/Jerusalem', 'TR': 'Europe/Istanbul', 'GB': 'Europe/London', 'DE': 'Europe/Berlin', 'FR': 'Europe/Paris', 'IT': 'Europe/Rome', 'ES': 'Europe/Madrid', 'PT': 'Europe/Lisbon', 'NL': 'Europe/Amsterdam', 'BE': 'Europe/Brussels', 'CH': 'Europe/Zurich', 'SE': 'Europe/Stockholm',
                      'NO': 'Europe/Oslo', 'DK': 'Europe/Copenhagen', 'FI': 'Europe/Helsinki', 'PL': 'Europe/Warsaw', 'AT': 'Europe/Vienna', 'GR': 'Europe/Athens', 'IE': 'Europe/Dublin', 'RU': 'Europe/Moscow', 'US': 'America/New_York', 'CA': 'America/Toronto', 'MX': 'America/Mexico_City', 'PA': 'America/Panama', 'CR': 'America/Costa_Rica', 'GT': 'America/Guatemala', 'BR': 'America/Sao_Paulo', 'AR': 'America/Buenos_Aires', 'CL': 'America/Santiago', 'CO': 'America/Bogota', 'PE': 'America/Lima', 'VE': 'America/Caracas', 'AU': 'Australia/Sydney', 'NZ': 'Pacific/Auckland', 'FJ': 'Pacific/Fiji', 'ZA': 'Africa/Johannesburg', 'EG': 'Africa/Cairo', 'MA': 'Africa/Casablanca', 'NG': 'Africa/Lagos', 'KE': 'Africa/Nairobi', 'ET': 'Africa/Addis_Ababa'}
DEFAULT_TIMEZONE = 'Asia/Ho_Chi_Minh'
WEATHER_DESC_VIET = {'Clear sky': 'Trời quang', 'Few clouds': 'Ít mây', 'Scattered clouds': 'Mây rải rác', 'Broken clouds': 'Nhiều mây', 'Overcast clouds': 'Trời u ám', 'Light rain': 'Mưa nhẹ', 'Moderate rain': 'Mưa vừa', 'Heavy intensity rain': 'Mưa to', 'Very heavy rain': 'Mưa rất to', 'Extreme rain': 'Mưa cực lớn', 'Freezing rain': 'Mưa đông đá', 'Light intensity shower rain': 'Mưa rào nhẹ', 'Shower rain': 'Mưa rào', 'Heavy intensity shower rain': 'Mưa rào nặng hạt', 'Ragged shower rain': 'Mưa rào không đều', 'Thunderstorm with light rain': 'Dông kèm mưa nhẹ', 'Thunderstorm with rain': 'Dông kèm mưa', 'Thunderstorm with heavy rain': 'Dông kèm mưa to', 'Light thunderstorm': 'Dông nhẹ', 'Thunderstorm': 'Dông', 'Heavy thunderstorm': 'Dông mạnh', 'Ragged thunderstorm': 'Dông không đều', 'Thunderstorm with light drizzle': 'Dông kèm mưa phùn nhẹ', 'Thunderstorm with drizzle': 'Dông kèm mưa phùn', 'Thunderstorm with heavy drizzle': 'Dông kèm mưa phùn nặng hạt',
                     'Light intensity drizzle': 'Mưa phùn nhẹ', 'Drizzle': 'Mưa phùn', 'Heavy intensity drizzle': 'Mưa phùn nặng hạt', 'Light intensity drizzle rain': 'Mưa phùn/mưa nhẹ', 'Drizzle rain': 'Mưa phùn/mưa', 'Heavy intensity drizzle rain': 'Mưa phùn/mưa nặng hạt', 'Shower rain and drizzle': 'Mưa rào và mưa phùn', 'Heavy shower rain and drizzle': 'Mưa rào to và mưa phùn', 'Shower drizzle': 'Mưa phùn dạng mưa rào', 'Light snow': 'Tuyết nhẹ', 'Snow': 'Tuyết', 'Heavy snow': 'Tuyết dày', 'Sleet': 'Mưa tuyết', 'Light shower sleet': 'Mưa tuyết nhẹ', 'Shower sleet': 'Mưa tuyết', 'Light rain and snow': 'Mưa và tuyết nhẹ', 'Rain and snow': 'Mưa và tuyết', 'Light shower snow': 'Tuyết rơi nhẹ', 'Shower snow': 'Tuyết rơi', 'Heavy shower snow': 'Tuyết rơi dày', 'Mist': 'Sương mù nhẹ', 'Smoke': 'Khói', 'Haze': 'Bụi mù', 'Sand/ dust whirls': 'Xoáy cát/bụi', 'Fog': 'Sương mù', 'Sand': 'Cát', 'Dust': 'Bụi', 'Volcanic ash': 'Tro núi lửa', 'Squalls': 'Gió giật mạnh', 'Tornado': 'Lốc xoáy', 'N/A': 'Không xác định'}
WIND_DIR_VIET = {'N': 'B', 'NNE': 'BĐB', 'NE': 'ĐB', 'ENE': 'ĐĐB', 'E': 'Đ', 'ESE': 'ĐĐN', 'SE': 'ĐN', 'SSE': 'NĐN',
                 'S': 'N', 'SSW': 'NTN', 'SW': 'TN', 'WSW': 'TTN', 'W': 'T', 'WNW': 'TTB', 'NW': 'TB', 'NNW': 'BTB', 'N/A': 'N/A'}
WMO_WEATHER_CODES_EN = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle", 56: "Light freezing drizzle", 57: "Dense freezing drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 66: "Light freezing rain",
                        67: "Heavy freezing rain", 71: "Light snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall", 77: "Snow grains", 80: "Slight showers", 81: "Moderate showers", 82: "Violent showers", 85: "Slight snow showers", 86: "Heavy snow showers", 95: "Thunderstorm (slight/moderate)", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"}
WMO_WEATHER_CODES_VIET = {0: "Trời quang", 1: "Chủ yếu quang mây", 2: "Mây rải rác", 3: "Trời nhiều mây", 45: "Sương mù", 48: "Sương mù có sương giá", 51: "Mưa phùn nhẹ", 53: "Mưa phùn vừa", 55: "Mưa phùn nặng hạt", 56: "Mưa phùn nhẹ kèm đông đá", 57: "Mưa phùn nặng hạt kèm đông đá", 61: "Mưa nhẹ", 63: "Mưa vừa",
                          65: "Mưa to", 66: "Mưa nhẹ kèm đông đá", 67: "Mưa to kèm đông đá", 71: "Tuyết rơi nhẹ", 73: "Tuyết rơi vừa", 75: "Tuyết rơi dày", 77: "Hạt tuyết", 80: "Mưa rào nhẹ", 81: "Mưa rào vừa", 82: "Mưa rào dữ dội", 85: "Mưa tuyết nhẹ", 86: "Mưa tuyết dày", 95: "Dông (nhẹ/vừa)", 96: "Dông kèm mưa đá nhỏ", 99: "Dông kèm mưa đá lớn"}

OPENMETEO_API_URL = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
OPENMETEO_ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"

APP_STYLESHEET = """
    QWidget {
        font-family: Arial, sans-serif;
    }
    QGroupBox {
        font-size: 11pt;
        font-weight: bold;
        border: 1px solid #CCC;
        border-radius: 5px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
    }
    QPushButton {
        font-size: 10pt;
        font-weight: bold;
        padding: 8px;
        background-color: #a7fcfd;
        color: black;
        border: 1px solid #888;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #90e0e1;
    }
    QPushButton:pressed {
        background-color: #79c6c7;
    }
"""

# --- NEW: Color scale for precipitation map legend, as per fetch_weather_map.py ---
# All colors are standardized to RGBA to prevent blending errors.
COLOR_SCALES = {
    'precipitation': {
        'min': 0,
        'max': 20,
        'colors': [
            (214, 236, 255, 255), (173, 216, 230, 255), (0, 191, 255, 255),
            (0, 255, 255, 255),   (0, 255, 0, 255),     (255, 255, 0, 255),
            (255, 215, 0, 255),   (255, 165, 0, 255),   (255, 69, 0, 255),
            (255, 0, 0, 255),     (211, 0, 148, 255),   (255, 0, 255, 255),
            (148, 0, 211, 255),
        ]
    }
}


class ColorFadeWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bg_color = QColor("transparent")
        self.animation = QPropertyAnimation(self, b"backgroundColor")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

    def setBackgroundColor(self, color):
        if isinstance(color, QColor):
            self._bg_color = color
        else:
            self._bg_color = QColor(color)
        self.setStyleSheet(
            f"QGroupBox {{ background-color: {self._bg_color.name()}; border-radius: 5px; }}")

    def getBackgroundColor(self):
        return self._bg_color

    def flash(self):
        self.animation.stop()
        self.animation.setStartValue(QColor("#3BF2FF"))  # Flash color
        self.animation.setEndValue(QColor("#FFFEE4"))
        self.animation.start()

    backgroundColor = pyqtProperty(
        QColor, fget=getBackgroundColor, fset=setBackgroundColor)


class WeatherCrawlerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather Reporter")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(APP_STYLESHEET)

        icon_path = "weather_icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.api_key = CONFIG.get("api_key_openweathermap")
        self.locations = CONFIG.get("locations", {})
        self.dashboard_locations_names = CONFIG.get("dashboard_locations", [])

        self.realtime_widgets = {}
        self.session = self.create_requests_session()
        self.initUI()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self._flash_alert)
        self._alert_flash_state = False

        self.realtime_update_timer = QTimer(self)
        self.realtime_update_timer.timeout.connect(
            self._update_realtime_display)
        self.realtime_update_timer.start(15 * 60 * 1000)
        self._update_realtime_display()

        self.showMaximized()

    def initUI(self):
        main_hbox = QHBoxLayout()
        left_vbox = QVBoxLayout()
        right_vbox = QVBoxLayout()

        # --- LEFT PANEL ---
        # Use a larger font for left panel contents (not headers)
        left_content_font = QFont("Arial", 10)

        # API Source group
        api_group = self._create_api_source_group()
        # Only set font for children, not the header
        for child in api_group.findChildren((QRadioButton, QLabel, QLineEdit, QDateEdit, QPushButton)):
            child.setFont(left_content_font)
        left_vbox.addWidget(api_group)

        # Locations group
        locations_group = self._create_locations_group()
        for child in locations_group.findChildren((QRadioButton, QLabel, QLineEdit, QDateEdit, QPushButton)):
            child.setFont(left_content_font)
        left_vbox.addWidget(locations_group)

        # Report Actions group
        actions_group = self._create_actions_group()
        for child in actions_group.findChildren((QRadioButton, QLabel, QLineEdit, QDateEdit, QPushButton)):
            child.setFont(left_content_font)
        left_vbox.addWidget(actions_group)

        # Progress bar and status label (now under Report Actions)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setVisible(False)
        self.status_label.setFont(left_content_font)
        self.progress_bar.setFont(left_content_font)

        left_vbox.addWidget(self.progress_bar)
        left_vbox.addWidget(self.status_label)

        left_vbox.addStretch()

        # --- RIGHT PANEL ---
        right_vbox.addWidget(self._create_dashboard_group())
        right_vbox.addStretch()

        # --- FINAL ASSEMBLY ---
        main_hbox.addLayout(left_vbox, stretch=1)
        main_hbox.addLayout(right_vbox, stretch=1)

        final_layout = QVBoxLayout(self)
        final_layout.addLayout(main_hbox)

    def _create_api_source_group(self):
        group = QGroupBox("Select Weather API Source")
        layout = QVBoxLayout()
        self.api_radio_openmeteo = QRadioButton(
            "Open-Meteo (07-day forecast, Marine, Historical)")
        self.api_radio_openmeteo.setChecked(True)
        self.api_radio_owm = QRadioButton(
            "OpenWeatherMap (05-day forecast, Weather Maps)")
        layout.addWidget(self.api_radio_openmeteo)
        layout.addWidget(self.api_radio_owm)
        group.setLayout(layout)
        return group

    def _create_locations_group(self):
        group = QGroupBox("Select Location")
        layout = QVBoxLayout()
        self.location_radios = {}
        for name, data in self.locations.items():
            hbox = QHBoxLayout()
            radio = QRadioButton(name)
            self.location_radios[name] = radio
            radio.toggled.connect(self.toggle_gps_input)
            coord_label = QLabel(
                f"({data['coords'][0]:.4f}, {data['coords'][1]:.4f})")
            coord_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            hbox.addWidget(radio)
            hbox.addWidget(coord_label)
            layout.addLayout(hbox)

        self.gps_radio = QRadioButton("Enter Custom GPS Coordinates:")
        self.gps_radio.toggled.connect(self.toggle_gps_input)
        layout.addWidget(self.gps_radio)

        # --- Add Marine Forecast checkbox for custom GPS ---
        self.gps_marine_checkbox = QCheckBox("With Marine Forecast")
        self.gps_marine_checkbox.setEnabled(False)
        layout.addWidget(self.gps_marine_checkbox)

        gps_name_layout = QHBoxLayout()
        self.gps_name_label = QLabel("Custom Name:")
        self.gps_name_input = QLineEdit()
        gps_name_layout.addWidget(self.gps_name_label)
        gps_name_layout.addWidget(self.gps_name_input)
        layout.addLayout(gps_name_layout)

        gps_coord_layout = QHBoxLayout()
        self.lat_label = QLabel("Lat:")
        self.lon_label = QLabel("Lon:")
        self.lat_input = QLineEdit()
        self.lon_input = QLineEdit()
        gps_coord_layout.addWidget(self.lat_label)
        gps_coord_layout.addWidget(self.lat_input)
        gps_coord_layout.addWidget(self.lon_label)
        gps_coord_layout.addWidget(self.lon_input)
        layout.addLayout(gps_coord_layout)

        if "An Phu Office - An Khanh Ward" in self.location_radios:
            self.location_radios["An Phu Office - An Khanh Ward"].setChecked(
                True)

        self.toggle_gps_input()  # Set initial state
        group.setLayout(layout)
        return group

    def _create_actions_group(self):
        group = QGroupBox("Report Actions")
        layout = QVBoxLayout()

        forecast_group = QGroupBox("Weather Forecast")
        forecast_vbox = QVBoxLayout()
        self.weather_button = QPushButton("Generate Report (English)")
        self.weather_button.clicked.connect(
            self.generate_weather_report_action)
        forecast_vbox.addWidget(self.weather_button)
        self.vietnamese_weather_button = QPushButton(
            "Tạo Báo Cáo Thời Tiết (Tiếng Việt)")
        self.vietnamese_weather_button.clicked.connect(
            self.generate_vietnamese_weather_report_action)
        forecast_vbox.addWidget(self.vietnamese_weather_button)
        forecast_group.setLayout(forecast_vbox)
        layout.addWidget(forecast_group)

        historical_group = QGroupBox("Historical Data")
        historical_layout = QVBoxLayout()
        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(QLabel("From:"))
        self.historical_from_date = QDateEdit(
            calendarPopup=True, date=QDate.currentDate().addDays(-8))
        self.historical_from_date.setDisplayFormat("dd/MM/yyyy")
        date_range_layout.addWidget(self.historical_from_date)
        self.historical_from_date.setFixedWidth(125)
        date_range_layout.addWidget(QLabel("To:"))
        self.historical_to_date = QDateEdit(
            calendarPopup=True, date=QDate.currentDate().addDays(-1))
        self.historical_to_date.setDisplayFormat("dd/MM/yyyy")
        date_range_layout.addWidget(self.historical_to_date)
        self.historical_to_date.setFixedWidth(125)
        date_range_layout.addStretch()
        historical_layout.addLayout(date_range_layout)
        self.fetch_historical_button = QPushButton(
            "Generate Historical Report (PDF)")
        self.fetch_historical_button.clicked.connect(
            self._fetch_historical_and_generate_report_action)
        historical_layout.addWidget(self.fetch_historical_button)
        # --- Add Excel export button below PDF button ---
        self.fetch_historical_excel_button = QPushButton(
            "Generate Historical Report (Excel)")
        self.fetch_historical_excel_button.clicked.connect(
            self._fetch_historical_and_generate_excel_action)
        historical_layout.addWidget(self.fetch_historical_excel_button)
        historical_group.setLayout(historical_layout)
        layout.addWidget(historical_group)

        group.setLayout(layout)
        return group

    def _create_dashboard_group(self):
        group = QGroupBox("Real-time Dashboard")
        main_layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        self.clock_label = QLabel("00:00:00")
        self.clock_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.clock_label.setStyleSheet("color: #337ab7;")
        header_layout.addStretch()
        header_layout.addWidget(self.clock_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        for loc_name in self.dashboard_locations_names:
            loc_group = ColorFadeWidget(loc_name)
            loc_main_hbox = QHBoxLayout()
            loc_details_vbox = QVBoxLayout()

            self.realtime_widgets[loc_name] = {'group': loc_group}

            for param, icon_name in [('desc', 'desc'), ('temp', 'temp'), ('wind', 'wind'), ('rain', 'rain')]:
                hbox = QHBoxLayout()
                icon_label = QLabel()
                icon_label.setPixmap(QPixmap(
                    f"icons/{icon_name}.png").scaled(27, 27, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                data_label = QLabel(f"{param.capitalize()}: N/A")
                data_label.setFont(QFont("Arial", 10))
                hbox.addWidget(icon_label)
                hbox.addWidget(data_label)
                hbox.addStretch()
                loc_details_vbox.addLayout(hbox)
                self.realtime_widgets[loc_name][param] = data_label

            loc_main_hbox.addLayout(loc_details_vbox)

            image_path = os.path.join(
                "Pictures", loc_name.replace(" ", "_") + ".png")
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path).scaled(
                    QSize(250, 125), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                location_image_label = QLabel()
                location_image_label.setPixmap(pixmap)
                loc_main_hbox.addWidget(
                    location_image_label, alignment=Qt.AlignRight | Qt.AlignVCenter)

            loc_group.setLayout(loc_main_hbox)
            main_layout.addWidget(loc_group)

        alert_refresh_hbox = QHBoxLayout()
        self.rt_refresh_button = QPushButton("Refresh Now")
        self.rt_refresh_button.clicked.connect(self._update_realtime_display)
        alert_refresh_hbox.addWidget(self.rt_refresh_button)
        alert_refresh_hbox.addStretch()
        self.rt_alert_label = QLabel("Wind Speed Alert: None")
        self.rt_alert_label.setFont(QFont("Arial", 11, QFont.Bold))
        main_layout.addLayout(alert_refresh_hbox)
        main_layout.addWidget(self.rt_alert_label)
        group.setLayout(main_layout)
        return group

    def toggle_gps_input(self):
        is_gps_selected = self.gps_radio.isChecked()
        for widget in [self.lat_label, self.lon_label, self.lat_input, self.lon_input, self.gps_name_label, self.gps_name_input]:
            widget.setEnabled(is_gps_selected)
        if hasattr(self, "gps_marine_checkbox"):
            self.gps_marine_checkbox.setEnabled(is_gps_selected)

    def get_api_choice(self):
        return "OWM" if self.api_radio_owm.isChecked() else "OpenMeteo"

    # --- OWM MAP TILE HELPERS (UPDATED) ---

    def _get_font(self, size):
        """Helper to load a font, with a default fallback."""
        try:
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            return ImageFont.load_default()

    def _deg2num(self, lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return xtile, ytile

    def _get_tile_url(self, layer, x, y, z):
        layer_map = {'precipitation': 'precipitation_new'}
        return f"https://tile.openweathermap.org/map/{layer_map.get(layer, layer)}/{z}/{x}/{y}.png?appid={self.api_key}"

    def _fetch_base_tile(self, x, y, z):
        url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        headers = {"User-Agent": "WeatherMapGenerator/1.0"}
        resp = self.session.get(url, headers=headers)
        resp.raise_for_status()
        return RLImage.open(BytesIO(resp.content)).convert("RGB")

    def _fetch_tile_grid(self, layer, x_center, y_center, z, radius=1):
        tile_size, grid_dim = 256, 2 * radius + 1
        stitched_image = RLImage.new(
            "RGB", (tile_size * grid_dim, tile_size * grid_dim))
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                xtile, ytile = x_center + dx, y_center + dy
                try:
                    base_tile = self._fetch_base_tile(xtile, ytile, z)
                except Exception as e:
                    print(
                        f"Warning: Failed to fetch base tile ({xtile},{ytile}): {e}")
                    base_tile = RLImage.new(
                        "RGB", (tile_size, tile_size), color=(220, 220, 220))

                try:
                    overlay_resp = self.session.get(
                        self._get_tile_url(layer, xtile, ytile, z))
                    overlay_resp.raise_for_status()
                    overlay = RLImage.open(
                        BytesIO(overlay_resp.content)).convert("RGBA")
                    base_tile.paste(overlay, (0, 0), overlay)
                except requests.RequestException as e:
                    print(
                        f"Warning: Failed to fetch overlay for {layer} at ({xtile},{ytile}): {e}")

                stitched_image.paste(
                    base_tile, ((dx + radius) * tile_size, (dy + radius) * tile_size))
        return stitched_image

    def _mark_location(self, image, lat, lon, zoom, x_center, y_center, radius):
        tile_size, n = 256, 2.0 ** zoom
        x_rel = (lon + 180.0) / 360.0 * n
        y_rel = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
        px = int((x_rel - x_center + radius) * tile_size)
        py = int((y_rel - y_center + radius) * tile_size)
        draw = ImageDraw.Draw(image)
        marker_rad = 6
        draw.ellipse((px - marker_rad, py - marker_rad, px + marker_rad,
                     py + marker_rad), fill='red', outline='white', width=2)
        return image

    def _annotate_image(self, img, layer_name, value, unit):
        draw = ImageDraw.Draw(img, 'RGBA')
        font = self._get_font(24)
        text = f"{layer_name.title()}: {value:.1f} {unit}"
        text_bbox = draw.textbbox((10, 10), text, font=font)
        rect_coords = (
            5, 5, 5 + text_bbox[2] - text_bbox[0] + 10, 5 + text_bbox[3] - text_bbox[1] + 10)
        draw.rectangle(rect_coords, fill=(255, 255, 255, 200))
        draw.text((10, 10), text, fill="black", font=font)
        return img

    def _draw_color_legend(self, layer, width, height=30):
        scale = COLOR_SCALES[layer]
        min_val, max_val, colors = scale['min'], scale['max'], scale['colors']
        legend_img = RLImage.new(
            "RGBA", (width, height + 20), (255, 255, 255, 0))
        draw = ImageDraw.Draw(legend_img)
        for x in range(width):
            t = x / (width - 1)
            index_float = t * (len(colors) - 1)
            index_floor, t_local = int(
                index_float), index_float - int(index_float)
            c1, c2 = colors[index_floor], colors[min(
                index_floor + 1, len(colors) - 1)]
            blended = tuple(int(c1[i] + (c2[i] - c1[i]) * t_local)
                            for i in range(4))
            draw.line([(x, 0), (x, height)], fill=blended)
        font = self._get_font(12)
        num_ticks = 6
        for i in range(num_ticks):
            val = min_val + i * (max_val - min_val) / (num_ticks - 1)
            label = f"{val:.0f}"
            x_pos = int(i * (width - 1) / (num_ticks - 1))
            label_bbox = draw.textbbox((0, 0), label, font=font)
            draw.text((x_pos - (label_bbox[2]-label_bbox[0]) / 2,
                      height + 2), label, font=font, fill="black")
        return legend_img

    def _fetch_current_weather_for_map(self, lat, lon):
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={self.api_key}"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def _create_precipitation_map_image(self, lat, lon, zoom, precipitation_value):
        """Creates a single composite image for the precipitation map."""
        try:
            x_center, y_center = self._deg2num(lat, lon, zoom)
            stitched_map = self._fetch_tile_grid(
                "precipitation", x_center, y_center, zoom, radius=1)
            marked_map = self._mark_location(
                stitched_map, lat, lon, zoom, x_center, y_center, radius=1)
            annotated_map = self._annotate_image(
                marked_map, "precipitation", precipitation_value, CONFIG['UNITS']['precipitation'])
            legend = self._draw_color_legend(
                "precipitation", width=annotated_map.width)

            final_image = RLImage.new(
                "RGB", (annotated_map.width, annotated_map.height + legend.height), "white")
            final_image.paste(annotated_map, (0, 0))
            final_image.paste(legend, (0, annotated_map.height), legend)

            # Convert to ReportLab Image object for the PDF
            with BytesIO() as buffer:
                final_image.save(buffer, "PNG")
                buffer.seek(0)
                # Adjust size for PDF layout
                return RLImage(buffer, width=7.5*inch, height=7.5 * (final_image.height / final_image.width) * inch)
        except Exception as e:
            print(f"Error creating precipitation map image: {e}")
            traceback.print_exc()
            return None

    def _fetch_all_owm_map_tiles(self, lat, lon, zoom):
        """
        Fetches current weather and creates a composite precipitation map image.
        Returns a dictionary containing the final image.
        """
        # try:
        #     weather_data = self._fetch_current_weather_for_map(lat, lon)
        #     precipitation_value = weather_data.get('rain', {}).get('1h', 0)

        #     map_image = self._create_precipitation_map_image(
        #         lat, lon, zoom, precipitation_value)

        #     if map_image:
        #         return {'Precipitation': map_image}
        # except Exception as e:
        #     print(f"Could not fetch data for OWM map: {e}")

        # return None
        x, y = self._convert_coord_to_tile(lat, lon, zoom)
        owm_maps = {}
        layer_code = 'precipitation_new'
        img_buffer = self._fetch_owm_map_tile(layer_code, zoom, x, y)
        if img_buffer:
            img_buffer.seek(0)
            owm_maps['Precipitation'] = img_buffer
        return owm_maps  # Always return a dict, even if empty

    # ... (All other class methods like _generate_report, generate_pdf_report, etc. remain here)
    def generate_weather_report_action(self):
        self._generate_report(lang='en')

    def generate_vietnamese_weather_report_action(self):
        self._generate_report(lang='vi')

    def _generate_report(self, lang):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return
        api_choice = self.get_api_choice()
        pdf_name = self.locations.get(location_name_selected, {}).get(
            'pdf_name', location_name_selected)

        lang_map = {'en': ("Preparing", "Fetching", "Generating", "report"), 'vi': (
            "Đang chuẩn bị", "Đang lấy", "Đang tạo", "báo cáo")}
        self._start_progress(f"{lang_map[lang][0]} data from {api_choice}...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        weather_data, location_info, marine_data, owm_maps = None, None, None, None
        try:
            self._update_progress_status(
                f"{lang_map[lang][1]} weather data...")
            if api_choice == "OWM":
                weather_data, location_info = self._fetch_weather_data_owm(
                    lat, lon)
                self._update_progress_status(
                    f"{lang_map[lang][1]} weather maps...")
                owm_maps = self._fetch_all_owm_map_tiles(lat, lon, zoom=6)
            else:  # OpenMeteo
                weather_data, location_info = self._fetch_weather_data_openmeteo(
                    lat, lon)
                # --- Marine forecast for Lan Tay, Rong Doi, or custom GPS with marine checked ---
                include_marine = (
                    ("Lan Tay Platform" in location_name_selected)
                    or ("Rong Doi Platform" in location_name_selected)
                    or (getattr(self, "gps_radio", None) and self.gps_radio.isChecked() and getattr(self, "gps_marine_checkbox", None) and self.gps_marine_checkbox.isChecked())
                )
                if include_marine:
                    self._update_progress_status(
                        f"{lang_map[lang][1]} marine data...")
                    marine_data = self._fetch_marine_data_openmeteo(
                        lat, lon, location_info.get('timezone', DEFAULT_TIMEZONE))

            if not weather_data:
                raise Exception("Weather data fetch failed")

            self._update_progress_status(
                f"{lang_map[lang][2]} PDF {lang_map[lang][3]}...")
            if lang == 'en':
                self.generate_pdf_report(
                    lat, lon, weather_data, location_info, pdf_name, api_choice, marine_data)
            else:
                self.generate_vietnamese_pdf_report(
                    lat, lon, weather_data, location_info, pdf_name, api_choice, marine_data)

            self._end_progress("Report generated successfully!", success=True)
            QMessageBox.information(
                self, "Success", "PDF report generated successfully!")

        except Exception as e:
            self._end_progress("Report generation failed.", success=False)
            print(
                f"An error occurred during report generation: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _fetch_historical_and_generate_report_action(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return
        pdf_name = self.locations.get(location_name_selected, {}).get(
            'pdf_name', location_name_selected)

        from_date = self.historical_from_date.date().toPyDate()
        to_date = self.historical_to_date.date().toPyDate()
        if from_date > to_date:
            QMessageBox.warning(self, "Date Error",
                                "From Date cannot be after To Date.")
            return
        if (to_date - from_date).days > 365 * 2:
            QMessageBox.warning(self, "Date Range Warning",
                                "Please select a date range up to 2 years.")
            return

        self._start_progress(
            f"Fetching historical data for {location_name_selected}...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            _, location_info = self._fetch_weather_data_openmeteo(lat, lon)
            timezone_for_historical = location_info.get(
                'timezone', DEFAULT_TIMEZONE)

            historical_data = self._fetch_historical_data_openmeteo(lat, lon, from_date.strftime(
                '%Y-%m-%d'), to_date.strftime('%Y-%m-%d'), timezone_for_historical)
            if not historical_data:
                raise Exception("Failed to fetch historical weather data.")

            self._update_progress_status("Generating historical PDF report...")
            self.generate_historical_pdf_report(
                lat, lon, historical_data, location_info, pdf_name, from_date, to_date)
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

    def _fetch_historical_and_generate_excel_action(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return
        pdf_name = self.locations.get(location_name_selected, {}).get(
            'pdf_name', location_name_selected)

        from_date = self.historical_from_date.date().toPyDate()
        to_date = self.historical_to_date.date().toPyDate()
        if from_date > to_date:
            QMessageBox.warning(self, "Date Error",
                                "From Date cannot be after To Date.")
            return
        if (to_date - from_date).days > 365 * 50:
            QMessageBox.warning(self, "Date Range Warning",
                                "Please select a date range up to 50 years.")
            return

        self._start_progress(
            f"Fetching historical data for {location_name_selected}...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            _, location_info = self._fetch_weather_data_openmeteo(lat, lon)
            timezone_for_historical = location_info.get(
                'timezone', DEFAULT_TIMEZONE)

            historical_data = self._fetch_historical_data_openmeteo(lat, lon, from_date.strftime(
                '%Y-%m-%d'), to_date.strftime('%Y-%m-%d'), timezone_for_historical)
            if not historical_data:
                raise Exception("Failed to fetch historical weather data.")

            self._update_progress_status(
                "Generating historical Excel report...")
            self.generate_historical_excel_report(
                lat, lon, historical_data, location_info, pdf_name, from_date, to_date)
            self._end_progress(
                "Historical Excel report generated successfully!", success=True)
            QMessageBox.information(
                self, "Success", "Historical Excel report generated successfully!")
        except Exception as e:
            self._end_progress(
                "Historical Excel report generation failed.", success=False)
            print(
                f"An error occurred during historical Excel report generation: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    def generate_historical_excel_report(self, lat, lon, historical_data, location_info, ui_location_name, from_date, to_date):
        # Prepare file name
        file_name_location = re.sub(
            r'[\\/*?:"<>|()]+', "", ui_location_name).replace(' ', '_')
        file_name = f"Historical_Weather_Report_OpenMeteo_{file_name_location}_{from_date.strftime('%Y%m%d')}_to_{to_date.strftime('%Y%m%d')}.xlsx"

        # Create workbook and worksheet
        workbook = xlsxwriter.Workbook(file_name)
        worksheet = workbook.add_worksheet("Weather Data")

        # Styles
        header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#003366', 'font_color': 'white', 'align': 'center'})
        normal_format = workbook.add_format({'align': 'center'})
        number_format = workbook.add_format(
            {'num_format': '0.0', 'align': 'center'})
        percent_format = workbook.add_format(
            {'num_format': '0%', 'align': 'center'})
        date_format = workbook.add_format(
            {'num_format': 'yyyy-mm-dd hh:mm', 'align': 'center'})
        min_format = workbook.add_format({'bg_color': '#00FFFF'})
        max_format = workbook.add_format({'bg_color': '#FFC0CB'})

        # Write metadata
        worksheet.write("A1", "Location:", header_format)
        worksheet.write("B1", ui_location_name, normal_format)
        worksheet.write("A2", "Coordinates:", header_format)
        worksheet.write("B2", f"Lat: {lat:.4f}, Lon: {lon:.4f}", normal_format)
        worksheet.write("A3", "Timezone:", header_format)
        worksheet.write("B3", location_info.get(
            'timezone', DEFAULT_TIMEZONE), normal_format)
        worksheet.write("A4", "Data Period:", header_format)
        worksheet.write(
            "B4", f"{from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}", normal_format)
        worksheet.write("A5", "Report Generated:", header_format)
        worksheet.write("B5", datetime.now(pytz.timezone(location_info.get(
            'timezone', DEFAULT_TIMEZONE))).strftime('%Y-%m-%d %H:%M:%S %Z'), normal_format)
        worksheet.write("A6", "Data Source:", header_format)
        worksheet.write("B6", "Open-Meteo Historical Archive", normal_format)

        # Table headers
        headers = ["Date/Time", "Description", "Temp (°C)", "Humidity (%)",
                   "Wind Speed (knots)", "Wind Gust (knots)", "Wind Dir",
                   "Rain (mm/h)", "Cloud Cover (%)", "Pressure (hPa)"]
        worksheet.write_row("A8", headers, header_format)

        # Write data rows
        row_offset = 8
        for row_idx, item in enumerate(historical_data):
            dt = item['datetime_obj']
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            worksheet.write_datetime(row_offset + row_idx, 0, dt, date_format)
            worksheet.write(row_offset + row_idx, 1,
                            item.get('description', 'N/A'), normal_format)
            # Helper for safe number writing

            def safe_write_number(ws, row, col, val, fmt):
                if isinstance(val, (int, float)):
                    ws.write_number(row, col, val, fmt)
                else:
                    ws.write(row, col, "", fmt)
            safe_write_number(worksheet, row_offset + row_idx,
                              2, item.get('temperature'), number_format)
            safe_write_number(worksheet, row_offset + row_idx,
                              3, item.get('humidity'), number_format)
            safe_write_number(worksheet, row_offset + row_idx,
                              4, item.get('wind_speed'), number_format)
            safe_write_number(worksheet, row_offset + row_idx,
                              5, item.get('wind_gust'), number_format)
            worksheet.write(row_offset + row_idx, 6,
                            item.get('wind_direction', 'N/A'), normal_format)
            safe_write_number(worksheet, row_offset + row_idx,
                              7, item.get('rain'), number_format)
            safe_write_number(worksheet, row_offset + row_idx,
                              8, item.get('cloud_cover'), number_format)
            safe_write_number(worksheet, row_offset + row_idx,
                              9, item.get('pressure'), number_format)

        # Set column widths
        worksheet.set_column("A:A", 18)
        worksheet.set_column("B:B", 27)
        worksheet.set_column("C:J", 16)

        # Highlight min/max for numeric columns
        col_indices = {'temperature': 2, 'humidity': 3, 'wind_speed': 4,
                       'wind_gust': 5, 'rain': 7, 'cloud_cover': 8, 'pressure': 9}
        for param, col in col_indices.items():
            values = [item.get(param) for item in historical_data if isinstance(
                item.get(param), (int, float))]
            if values:
                min_val = min(values)
                max_val = max(values)
                for row_idx, item in enumerate(historical_data):
                    val = item.get(param)
                    if isinstance(val, (int, float)):
                        cell = xlsxwriter.utility.xl_rowcol_to_cell(
                            row_offset + row_idx, col)
                        if val == min_val:
                            worksheet.write(row_offset + row_idx,
                                            col, val, min_format)
                        elif val == max_val:
                            worksheet.write(row_offset + row_idx,
                                            col, val, max_format)

        # --- Add charts ---
        chart_types = [
            ('Temperature & Humidity', ['temperature', 'humidity'], [
             'Temp (°C)', 'Humidity (%)']),
            ('Wind Speed & Gust', ['wind_speed', 'wind_gust'], [
             'Wind Speed (knots)', 'Wind Gust (knots)']),
            ('Rainfall', ['rain'], ['Rain (mm/h)']),
            ('Cloud Cover', ['cloud_cover'], ['Cloud Cover (%)']),
            ('Pressure', ['pressure'], ['Pressure (hPa)']),
        ]
        chart_row = row_offset + len(historical_data) + 3
        for chart_title, params, y_labels in chart_types:
            chart = workbook.add_chart({'type': 'line'})
            for i, param in enumerate(params):
                col = col_indices[param]
                chart.add_series({
                    'name':       y_labels[i],
                    'categories': ['Weather Data', row_offset, 0, row_offset + len(historical_data) - 1, 0],
                    'values':     ['Weather Data', row_offset, col, row_offset + len(historical_data) - 1, col],
                })
            chart.set_title({'name': chart_title})
            chart.set_x_axis(
                {'name': 'Date/Time', 'date_axis': True, 'num_font': {'rotation': -45}})
            chart.set_y_axis({'name': ', '.join(y_labels)})
            chart.set_legend({'position': 'bottom'})
            worksheet.insert_chart(chart_row, 0, chart, {
                                   'x_scale': 2.7, 'y_scale': 2.2})
            chart_row += 32

        workbook.close()
        print(f"Excel report generated: {file_name}")

    def get_coordinates(self):
        if self.gps_radio.isChecked():
            try:
                lat, lon = float(self.lat_input.text()), float(
                    self.lon_input.text())
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Range error")
                name = self.gps_name_input.text().strip(
                ) or f"Custom GPS ({lat:.4f}, {lon:.4f})"
                return lat, lon, name
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Input Error",
                                    "Invalid GPS coordinates.")
                return None, None, None
        else:
            for name, radio in self.location_radios.items():
                if radio.isChecked():
                    return self.locations[name]['coords'][0], self.locations[name]['coords'][1], name
        return None, None, None

    def create_requests_session(self):
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1,
                        status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update({'User-Agent': 'WeatherReporterApp/1.0'})
        return session

    def _start_progress(self, message):
        self.status_label.setText(message)
        self.progress_bar.setRange(0, 0)
        self.status_label.setVisible(True)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()

    def _update_progress_status(self, message):
        self.status_label.setText(message)
        QApplication.processEvents()

    def _end_progress(self, message, success=True):
        self.status_label.setText(message)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        QTimer.singleShot(2000, lambda: [self.status_label.setVisible(
            False), self.progress_bar.setVisible(False)])

    def _fetch_weather_data_owm(self, lat, lon):
        base_url = "https://api.openweathermap.org/data/2.5/"
        params = {'lat': lat, 'lon': lon,
                  'appid': self.api_key, 'units': 'metric'}
        try:
            current_response = self.session.get(
                f"{base_url}weather", params=params, timeout=20)
            current_response.raise_for_status()
            current_data = current_response.json()

            forecast_response = self.session.get(f"{base_url}forecast", params={
                                                 **params, 'cnt': 40}, timeout=20)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # Robust timezone handling
            timezone_str = DEFAULT_TIMEZONE
            local_tz = None
            country_code = current_data.get('sys', {}).get('country')
            if country_code and country_code in LOCATION_TIMEZONES:
                timezone_str = LOCATION_TIMEZONES[country_code]
            elif 'timezone' in current_data:
                try:
                    offset_sec = int(current_data['timezone'])
                    now_utc = datetime.now(timezone.utc)
                    for tz_name in pytz.common_timezones:
                        tz = pytz.timezone(tz_name)
                        if now_utc.astimezone(tz).utcoffset() == timedelta(seconds=offset_sec):
                            timezone_str = tz_name
                            break
                    else:
                        local_tz = timezone(timedelta(seconds=offset_sec))
                        timezone_str = f"UTC{offset_sec/3600:+03.0f}:00"
                except Exception as tz_err:
                    print(f"Could not process OWM timezone offset: {tz_err}")

            if local_tz is None:
                try:
                    local_tz = pytz.timezone(timezone_str)
                except pytz.exceptions.UnknownTimeZoneError:
                    print(
                        f"pytz unknown timezone '{timezone_str}', falling back to default.")
                    timezone_str = DEFAULT_TIMEZONE
                    local_tz = pytz.timezone(timezone_str)

            location_info = {
                'name': current_data.get('name', f"Coords ({lat:.4f}, {lon:.4f})"),
                'country': current_data.get('sys', {}).get('country', 'N/A'),
                'timezone': timezone_str,
                'sunrise': datetime.fromtimestamp(current_data['sys']['sunrise'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M'),
                'sunset': datetime.fromtimestamp(current_data['sys']['sunset'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M')
            }

            processed_forecast = self._process_forecast_data_owm(
                forecast_data, local_tz)
            return processed_forecast, location_info
        except Exception as e:
            print(f"Error in _fetch_weather_data_owm: {e}")
            return None, None

    def _fetch_weather_data_openmeteo(self, lat, lon):
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "apparent_temperature,temperature_2m,relative_humidity_2m,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m,cloud_cover,pressure_msl,uv_index",
            "daily": "apparent_temperature_max,apparent_temperature_min,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,weather_code",
            "timezone": "auto",
            "forecast_days": 7,
            "temperature_unit": "celsius",
            "wind_speed_unit": "kn",
            "precipitation_unit": "mm"
        }
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
                location_info['sunrise'] = datetime.fromisoformat(
                    daily_data['sunrise'][0]).astimezone(local_tz).strftime('%H:%M')
            if daily_data.get('sunset') and daily_data['sunset']:
                location_info['sunset'] = datetime.fromisoformat(
                    daily_data['sunset'][0]).astimezone(local_tz).strftime('%H:%M')
            processed_data = self._process_forecast_data_openmeteo(
                data.get('hourly', {}), local_tz)
            return processed_data, location_info
        except Exception as e:
            print(f"Error in _fetch_weather_data_openmeteo: {e}")
            return None, {}

    def _fetch_realtime_data_openmeteo(self, lat, lon, location_name):
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "apparent_temperature,precipitation",
            "timezone": "auto",
            "wind_speed_unit": "kn"
        }
        try:
            response = self.session.get(
                OPENMETEO_API_URL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            current = data.get("current_weather", {})
            local_tz = pytz.timezone(data.get("timezone", DEFAULT_TIMEZONE))
            now = datetime.now(local_tz)
            rain_val = 0.0
            apparent_temp_val = None

            # Try to get apparent temperature and precipitation for the current hour
            if "hourly" in data:
                times = data["hourly"].get("time", [])
                apparent_temps = data["hourly"].get("apparent_temperature", [])
                rains = data["hourly"].get("precipitation", [])
                for t_idx, t in enumerate(times):
                    dt = datetime.fromisoformat(t).astimezone(local_tz)
                    if abs((dt - now).total_seconds()) < 3600:
                        if t_idx < len(apparent_temps):
                            apparent_temp_val = apparent_temps[t_idx]
                        if t_idx < len(rains):
                            rain_val = rains[t_idx]
                        break

            # Fallback to current temperature if apparent not available
            if apparent_temp_val is None:
                apparent_temp_val = current.get(
                    'apparent_temperature', current.get('temperature'))

            wind_val = current.get('windspeed')
            return {
                'temperature': f"{apparent_temp_val:.1f}°C" if apparent_temp_val is not None else "N/A",
                'wind_speed': f"{wind_val:.1f} knots" if wind_val is not None else "N/A",
                'wind_speed_value': wind_val or 0,
                'weather_description': WMO_WEATHER_CODES_EN.get(current.get('weathercode'), "N/A"),
                'wind_direction': self._degrees_to_direction(current.get('winddirection')),
                'time_as_of': now.strftime('%H:%M'),
                'rain': f"{rain_val:.1f} mm/over the last hour for the entire area"
            }
        except Exception as e:
            print(f"Error fetching real-time OM data for {location_name}: {e}")
            return None

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
                    'datetime_obj': dt_obj,
                    'datetime': dt_obj.strftime('%Y-%m-%d %H:%M'),
                    'wave_height': data['wave_height'][i],
                    'wave_direction': self._degrees_to_direction(data['wave_direction'][i]),
                    'wave_period': data['wave_period'][i],
                    'sea_level': data.get('sea_level', [None]*len(data.get('time', [])))[i],
                    'wind_wave_height': data['wind_wave_height'][i],
                    'wind_wave_direction': self._degrees_to_direction(data['wind_wave_direction'][i]),
                    'wind_wave_period': data['wind_wave_period'][i],
                    'swell_wave_height': data['swell_wave_height'][i],
                    'swell_wave_direction': self._degrees_to_direction(data['swell_wave_direction'][i]),
                    'swell_wave_period': data['swell_wave_period'][i],
                })
            return processed_data
        except Exception as e:
            print(f"Error in _fetch_marine_data_openmeteo: {e}")
            return None

    def update_clock(self):
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))

    def _update_realtime_display(self):
        # Store widgets that need to flash: {label: ("color1", "color2", font_size1, font_size2)}
        self._realtime_flash_widgets = []

        max_wind_speed = 0.0
        high_wind_locations = []
        for name in self.dashboard_locations_names:
            coords = self.locations[name]['coords']
            data = self._fetch_realtime_data_openmeteo(
                coords[0], coords[1], name)
            widgets = self.realtime_widgets.get(name)
            if data and widgets:
                widgets['group'].flash()

                # --- Temperature Highlight & Flash ---
                temp_val = data['temperature']
                try:
                    temp_num = float(temp_val.replace("°C", "").strip())
                except Exception:
                    temp_num = None
                temp_flash = False
                if temp_num is not None:
                    if 37 <= temp_num <= 40:
                        widgets['temp'].setStyleSheet(
                            "color: orange; font-weight: bold; font-size: 10pt;")
                        temp_flash = True
                        self._realtime_flash_widgets.append(
                            (widgets['temp'], "color: black; font-weight: bold; font-size: 10pt;",
                             "color: orange; font-weight: bold; font-size: 10pt;")
                        )
                    elif temp_num > 40:
                        widgets['temp'].setStyleSheet(
                            "color: red; font-weight: bold; font-size: 11pt;")
                        temp_flash = True
                        self._realtime_flash_widgets.append(
                            (widgets['temp'], "color: red; font-weight: bold; font-size: 10pt;",
                             "color: darkred; font-weight: bold; font-size: 10pt;")
                        )
                    else:
                        widgets['temp'].setStyleSheet("")
                widgets['temp'].setText(temp_val)

                # --- Rain Highlight & Flash ---
                rain_val = data['rain']
                try:
                    rain_num = float(rain_val.split()[0])
                except Exception:
                    rain_num = None
                rain_flash = False
                if rain_num is not None:
                    if 3.0 <= rain_num <= 8.0:
                        widgets['rain'].setStyleSheet(
                            "color: orange; font-weight: bold; font-size: 10pt;")
                        rain_flash = True
                        self._realtime_flash_widgets.append(
                            (widgets['rain'], "color: black; font-weight: bold; font-size: 10pt;",
                             "color: orange; font-weight: bold; font-size: 10pt;")
                        )
                    elif rain_num > 8.0:
                        widgets['rain'].setStyleSheet(
                            "color: red; font-weight: bold; font-size: 11pt;")
                        rain_flash = True
                        self._realtime_flash_widgets.append(
                            (widgets['rain'], "color: red; font-weight: bold; font-size: 10pt;",
                             "color: darkred; font-weight: bold; font-size: 10pt;")
                        )
                    else:
                        widgets['rain'].setStyleSheet("")
                widgets['rain'].setText(rain_val)

                # --- Wind Highlight & Flash ---
                wind_speed_val = data['wind_speed']
                wind_dir_val = data['wind_direction']
                try:
                    wind_num = float(
                        wind_speed_val.replace("knots", "").strip())
                except Exception:
                    wind_num = None
                wind_display = f"{wind_speed_val} ({wind_dir_val})"
                wind_flash = False
                if wind_num is not None:
                    if 25 <= wind_num <= 34:
                        widgets['wind'].setStyleSheet(
                            "color: orange; font-weight: bold; font-size: 10pt;")
                        wind_flash = True
                        high_wind_locations.append(name)
                        self._realtime_flash_widgets.append(
                            (widgets['wind'], "color: black; font-weight: bold; font-size: 10pt;",
                             "color: orange; font-weight: bold; font-size: 10pt;")
                        )
                    elif wind_num > 34:
                        widgets['wind'].setStyleSheet(
                            "color: red; font-weight: bold; font-size: 10pt;")
                        wind_flash = True
                        high_wind_locations.append(name)
                        self._realtime_flash_widgets.append(
                            (widgets['wind'], "color: red; font-weight: bold; font-size: 10pt;",
                             "color: darkred; font-weight: bold; font-size: 10pt;")
                        )
                    else:
                        widgets['wind'].setStyleSheet("")
                widgets['wind'].setText(wind_display)

                # --- Description ---
                widgets['desc'].setText(
                    f"{data['weather_description']} (as of {data['time_as_of']})"
                )

                # Track max wind speed for alert
                if isinstance(data.get('wind_speed_value'), (int, float)) and data['wind_speed_value'] > max_wind_speed:
                    max_wind_speed = data['wind_speed_value']

        # --- Wind Speed Alert ---
        if high_wind_locations:
            alert_names = ", ".join(high_wind_locations)
            if max_wind_speed > 30:
                self.rt_alert_label.setText(
                    f"HIGH-HIGH WIND ALERT at: {alert_names}"
                )
                self.rt_alert_label.setStyleSheet(
                    "color: red; font-weight: bold;")
                if not self.alert_timer.isActive():
                    self.alert_timer.start(3000)
            else:
                self.rt_alert_label.setText(
                    f"HIGH WIND ALERT at: {alert_names}"
                )
                self.rt_alert_label.setStyleSheet(
                    "color: orange; font-weight: bold;")
                if self.alert_timer.isActive():
                    self.alert_timer.stop()
        else:
            self.rt_alert_label.setText(
                f"Wind Speed Alert: None (Max: {max_wind_speed:.1f} knots)"
            )
            self.rt_alert_label.setStyleSheet(
                "color: green; font-weight: normal;")
            if self.alert_timer.isActive():
                self.alert_timer.stop()

        # --- Start/stop flashing for high/high-high values ---
        if self._realtime_flash_widgets:
            if not hasattr(self, "_realtime_flash_timer"):
                self._realtime_flash_timer = QTimer(self)
                self._realtime_flash_timer.timeout.connect(
                    self._flash_realtime_high)
            self._flash_state = False
            self._realtime_flash_timer.start(3000)
        else:
            if hasattr(self, "_realtime_flash_timer"):
                self._realtime_flash_timer.stop()
                # Reset all styles to normal
                for widgets in self.realtime_widgets.values():
                    for key in ['temp', 'wind', 'rain']:
                        widgets[key].setStyleSheet("")

    def _flash_realtime_high(self):
        self._flash_state = not getattr(self, "_flash_state", False)
        for label, style1, style2 in getattr(self, "_realtime_flash_widgets", []):
            label.setStyleSheet(style1 if self._flash_state else style2)

    def _flash_alert(self):
        self._alert_flash_state = not self._alert_flash_state
        color = "red" if self._alert_flash_state else "black"
        self.rt_alert_label.setStyleSheet(
            f"color: {color}; font-weight: bold;")

    def _fetch_historical_data_openmeteo(self, lat, lon, start, end, tz):
        params = {"latitude": lat, "longitude": lon, "start_date": start, "end_date": end, "hourly": "apparent_temperature,temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m,cloud_cover,pressure_msl,uv_index",
                  "timezone": tz, "temperature_unit": "celsius", "wind_speed_unit": "kn", "precipitation_unit": "mm"}
        try:
            response = self.session.get(
                OPENMETEO_ARCHIVE_API_URL, params=params, timeout=30)
            response.raise_for_status()
            data, processed = response.json().get('hourly', {}), []
            def get(k, i): return data.get(k, [])[i] if i < len(
                data.get(k, [])) and data.get(k, [])[i] is not None else 'N/A'
            times = data.get('time', [])
            for i, time_str in enumerate(times):
                # Use apparent_temperature if available, else fallback to temperature_2m
                apparent_temp = get('apparent_temperature', i)
                if apparent_temp == 'N/A':
                    apparent_temp = get('temperature_2m', i)
                processed.append({'datetime_obj': datetime.fromisoformat(time_str).astimezone(pytz.timezone(tz)), 'datetime': datetime.fromisoformat(time_str).astimezone(pytz.timezone(tz)).strftime('%Y-%m-%d %H:%M'), 'description': WMO_WEATHER_CODES_EN.get(get('weather_code', i)), 'temperature': apparent_temp, 'humidity': get(
                    'relative_humidity_2m', i), 'wind_speed': get('wind_speed_10m', i), 'wind_gust': get('wind_gusts_10m', i), 'wind_direction': self._degrees_to_direction(get('wind_direction_10m', i)), 'rain': get('precipitation', i), 'cloud_cover': get('cloud_cover', i), 'pressure': get('pressure_msl', i), 'uv_index': get('uv_index', i), 'pop': 'N/A'})
            return processed
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
        if layer != 'precipitation_new':
            return None
        url = f"https://tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png?appid={self.api_key}"
        try:
            response = self.session.get(url, timeout=10, stream=True)
            response.raise_for_status()
            img = PILImage.open(BytesIO(response.content)).convert("RGB")
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            # --- Debug: Save to disk to verify ---
            with open("debug_precipitation.png", "wb") as f:
                f.write(img_buffer.getvalue())
            print("Saved debug_precipitation.png")
            # -------------------------------------
            print(f"Fetched OWM map tile for layer {layer} at {z}/{x}/{y}")
            return img_buffer
        except Exception as e:
            print(f"Failed to fetch OWM map tile for layer {layer}: {e}")
            return None

    def _fetch_all_owm_map_tiles(self, lat, lon, zoom):
        x, y = self._convert_coord_to_tile(lat, lon, zoom)
        owm_maps = {}
        layer_code = 'precipitation_new'
        img_buffer = self._fetch_owm_map_tile(layer_code, zoom, x, y)
        if img_buffer:
            img_buffer.seek(0)
            owm_maps['Precipitation'] = img_buffer
        return owm_maps

    def _process_forecast_data_owm(self, data, local_tz):
        processed = []
        now_local = datetime.now(local_tz)
        for item in data.get('list', []):
            local_time = datetime.fromtimestamp(
                item['dt'], tz=timezone.utc).astimezone(local_tz)
            if now_local - timedelta(hours=3) <= local_time <= now_local + timedelta(days=5, hours=3):
                # Use 'feels_like' as apparent temperature if available, else fallback to 'temp'
                main_data = item.get('main', {})
                apparent_temp = main_data.get(
                    'feels_like', main_data.get('temp'))
                processed.append({
                    'datetime_obj': local_time, 'datetime': local_time.strftime('%Y-%m-%d %H:%M'),
                    'description': item.get('weather', [{}])[0].get('description', 'N/A').capitalize(),
                    'temperature': apparent_temp,  # Apparent temperature
                    'humidity': main_data.get('humidity'),
                    'pressure': main_data.get('pressure'),
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
                # Use apparent_temperature if available, else fallback to temperature_2m
                apparent_temp = hourly_data.get(
                    'apparent_temperature', [None]*len(times))[i]
                if apparent_temp is None:
                    apparent_temp = hourly_data.get(
                        'temperature_2m', [None]*len(times))[i]
                rain = (hourly_data.get('rain', [])[i] or 0) + (hourly_data.get('showers',
                                                                                [])[i] or 0) + (hourly_data.get('snowfall', [])[i] or 0)
                processed.append({
                    'datetime_obj': local_time, 'datetime': local_time.strftime('%Y-%m-%d %H:%M'),
                    'description': WMO_WEATHER_CODES_EN.get(hourly_data.get('weather_code', [])[i], 'N/A'),
                    'temperature': apparent_temp,  # Apparent temperature
                    'humidity': hourly_data.get('relative_humidity_2m', [])[i],
                    'pressure': hourly_data.get('pressure_msl', [])[i],
                    'wind_speed': hourly_data.get('wind_speed_10m', [])[i], 'wind_gust': hourly_data.get('wind_gusts_10m', [])[i],
                    'wind_direction': self._degrees_to_direction(hourly_data.get('wind_direction_10m', [])[i]),
                    'rain': rain, 'uv_index': hourly_data.get('uv_index', [])[i],
                    'pop': 100 if rain > 0 else 0, 'cloud_cover': hourly_data.get('cloud_cover', [])[i]
                })
        return processed

    # Chart creation and other helper methods go here...
    def _degrees_to_direction(self, degrees):
        if degrees is None or degrees == 'N/A':
            return 'N/A'
        try:
            directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE',
                          'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
            return directions[round(float(degrees) / (360 / len(directions))) % len(directions)]
        except (ValueError, TypeError):
            return 'N/A'

    def create_chart(self, data, param_name, ylabel, title, date_key='datetime_obj', xlabel_text='Date/Time', color='tab:blue'):
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
        plt.plot(dates, values, marker='.', linestyle='-',
                 markersize=4, linewidth=1, color=color)
        plt.title(title, fontsize=10)
        plt.xlabel(xlabel_text, fontsize=9)
        plt.ylabel(ylabel, fontsize=9)
        plt.xticks(rotation=30, ha='right', fontsize=9)
        plt.yticks(fontsize=9)
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
        plt.gca().xaxis.set_major_formatter(
            mdates.DateFormatter('%m-%d %Hh', tz=dates[0].tzinfo))
        plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
        plt.tight_layout(pad=0.5)
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        plt.close()
        buf.seek(0)
        return RLImage(buf, width=9.6*inch, height=3.0*inch)

    def create_wind_chart(self, data, date_key='datetime_obj',
                          xlabel_text='Date/Time', ylabel_text='Speed (knots)',
                          title_text='Wind Speed and Gust Trend',
                          speed_label='Wind Speed', gust_label='Wind Gust', limit_xticks=False):
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

            # --- Limit x-ticks if requested ---
            if limit_xticks and len(dates) > 7 * 24:
                plt.gca().xaxis.set_major_locator(mticker.MaxNLocator(nbins=21))
            else:
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

            img = RLImage(img_buffer, width=9.6*inch, height=3.6*inch)
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
                                   temp_label='Temperature', hum_label='Humidity', limit_xticks=False):
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

            # --- Limit x-ticks if requested ---
            if limit_xticks and len(dates) > 7 * 24:
                ax1.xaxis.set_major_locator(mticker.MaxNLocator(nbins=21))
            else:
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

            img = RLImage(img_buffer, width=9.6*inch, height=3.6*inch)
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

            img = RLImage(img_buffer, width=9.6*inch, height=3.6*inch)
            img.hAlign = 'CENTER'
            return img

        except Exception as chart_err:
            print(f"Error during Rain/PoP chart plotting: {chart_err}")
            print(traceback.format_exc())
            plt.close(fig)
            return None

    # --- NEW: create_combined_wave_chart ---
    def create_combined_wave_chart(self, data, date_key='datetime_obj',
                                   xlabel_text='Date/Time',
                                   height_ylabel='Height (m)',
                                   period_ylabel='Period (s)',
                                   height_title='Wave & Swell Height Trend',
                                   period_title='Wave & Swell Period Trend',
                                   wave_height_label='Wave Height',
                                   swell_height_label='Swell Height',
                                   wave_period_label='Wave Period',
                                   swell_period_label='Swell Period'):
        if not data:
            print("Warning: No data provided for combined wave chart.")
            return None, None

        # Prepare data
        dates = []
        wave_heights = []
        swell_heights = []
        wave_periods = []
        swell_periods = []

        for item in data:
            item_date = item.get(date_key)
            if isinstance(item_date, datetime):
                dates.append(item_date)
                try:
                    wave_heights.append(float(item.get('wave_height')) if item.get(
                        'wave_height') not in [None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    wave_heights.append(math.nan)
                try:
                    swell_heights.append(float(item.get('swell_wave_height')) if item.get(
                        'swell_wave_height') not in [None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    swell_heights.append(math.nan)
                try:
                    wave_periods.append(float(item.get('wave_period')) if item.get(
                        'wave_period') not in [None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    wave_periods.append(math.nan)
                try:
                    swell_periods.append(float(item.get('swell_wave_period')) if item.get(
                        'swell_wave_period') not in [None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    swell_periods.append(math.nan)

        # --- Height Chart ---
        height_img = None
        if dates and (any(not math.isnan(h) for h in wave_heights) or any(not math.isnan(h) for h in swell_heights)):
            plt.figure(figsize=(9.0, 2.8))
            plt.plot(dates, wave_heights, marker='.', linestyle='-', markersize=4,
                     linewidth=1.8, color='#0077be', label=wave_height_label)
            plt.plot(dates, swell_heights, marker='.', linestyle='-', markersize=4,
                     linewidth=1.8, color='orange', label=swell_height_label)
            plt.title(height_title, fontsize=10)
            plt.xlabel(xlabel_text, fontsize=9)
            plt.ylabel(height_ylabel, fontsize=9)
            plt.xticks(rotation=30, ha='right', fontsize=9)
            plt.yticks(fontsize=9)
            plt.legend(fontsize=8)
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(
                byhour=[1, 7, 13, 19], tz=dates[0].tzinfo if dates else None))
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(
                '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))
            plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
            plt.tight_layout(pad=0.5)
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            buf.seek(0)
            height_img = RLImage(buf, width=9.6*inch, height=3.0*inch)
            height_img.hAlign = 'CENTER'

        # --- Period Chart ---
        period_img = None
        if dates and (any(not math.isnan(p) for p in wave_periods) or any(not math.isnan(p) for p in swell_periods)):
            plt.figure(figsize=(9.0, 2.8))
            plt.plot(dates, wave_periods, marker='.', linestyle='-', markersize=4,
                     linewidth=1.8, color='#0077be', label=wave_period_label)
            plt.plot(dates, swell_periods, marker='.', linestyle='-', markersize=4,
                     linewidth=1.8, color='orange', label=swell_period_label)
            plt.title(period_title, fontsize=10)
            plt.xlabel(xlabel_text, fontsize=9)
            plt.ylabel(period_ylabel, fontsize=9)
            plt.xticks(rotation=30, ha='right', fontsize=9)
            plt.yticks(fontsize=9)
            plt.legend(fontsize=8)
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(
                byhour=[1, 7, 13, 19], tz=dates[0].tzinfo if dates else None))
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(
                '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))
            plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
            plt.tight_layout(pad=0.5)
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            buf.seek(0)
            period_img = RLImage(buf, width=9.6*inch, height=3.0*inch)
            period_img.hAlign = 'CENTER'

        return height_img, period_img

    def generate_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source, marine_data=None, owm_maps=None):

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
        title_style.fontSize = 18
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
        elements.append(Spacer(1, 0.2*inch))

        # Add location image if available (for dashboard locations)
        image_path = os.path.join(
            "Pictures", ui_location_name.replace(" ", "_") + ".png")
        if os.path.exists(image_path):
            try:
                img = RLImage(image_path, width=5.6*inch, height=2.8*inch)
                img.hAlign = 'CENTER'
                elements.append(img)
                elements.append(Spacer(1, 0.08*inch))
            except Exception as img_err:
                print(f"Could not add image for {ui_location_name}: {img_err}")

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
            # Set forecast section header based on data source
            if api_source == "OpenMeteo":
                forecast_header = "Weather Forecast (Next 7 Days Hourly)"
            else:
                forecast_header = "Weather Forecast (Next 5 Days 03-Hourly)"
            elements.append(
                Paragraph(forecast_header, h2_style))

            # --- BEGIN: Add summary section ---
            temp_vals = [item.get('temperature') for item in weather_data if isinstance(
                item.get('temperature'), (int, float))]
            wind_vals = [item.get('wind_speed') for item in weather_data if isinstance(
                item.get('wind_speed'), (int, float))]
            rain_vals = [item.get('rain') for item in weather_data if isinstance(
                item.get('rain'), (int, float))]
            uv_vals = [item.get('uv_index') for item in weather_data if isinstance(
                item.get('uv_index'), (int, float))]

            temp_min = f"{min(temp_vals):.1f}°C" if temp_vals else "N/A"
            temp_max = f"{max(temp_vals):.1f}°C" if temp_vals else "N/A"
            wind_min = f"{min(wind_vals):.1f} knots" if wind_vals else "N/A"
            wind_max = f"{max(wind_vals):.1f} knots" if wind_vals else "N/A"
            rain_max = f"{max(rain_vals):.1f} mm/h" if rain_vals else "N/A"
            uv_max = f"{max(uv_vals):.1f}" if uv_vals else "N/A"

            summary_text = (
                f"<b>Summary:</b><br/>"
                f"<b>Temperature</b>: {temp_min} - {temp_max}<br/>"
                f"<b>Wind Speed</b>: {wind_min} - {wind_max}<br/>"
                f"<b>Rain</b>: Max {rain_max}<br/>"
                f"<b>UV Index</b>: Max {uv_max}"
            )
            elements.append(Paragraph(summary_text, normal_style))
            elements.append(Spacer(1, 0.08*inch))
            # --- END: Add summary section ---

            col_params = {
                'datetime': {'header': "Date/Time", 'format': lambda x: x, 'width': 1.28*inch, 'align': 'CENTER'},
                'description': {'header': "Description", 'format': lambda x: x, 'width': 2.1*inch, 'align': 'CENTER'},
                'temperature': {'header': "Temp\n(°C)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
                'humidity': {'header': "Humidity\n(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.8*inch, 'align': 'RIGHT'},
                'wind_speed': {'header': "Wind Speed\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'wind_gust': {'header': "Wind Gust\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.96*inch, 'align': 'RIGHT'},
                'wind_direction': {'header': "Wind\nDir", 'format': lambda x: x, 'width': 0.72*inch, 'align': 'CENTER'},
                'rain': {'header': "Rain\n(mm/h)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.75*inch, 'align': 'RIGHT'},
                'pop': {'header': "PoP\n(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
                'uv_index': {'header': "UV\nIndex", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
            }

            weather_headers = ["Date/Time", "Description", "Temp\n(°C)", "Humidity\n(%)",
                               "Wind Speed\n(knots)", "Wind Gust\n(knots)", "Wind\nDir",
                               "Rain\n(mm/h)", "PoP\n(%)", "UV\nIndex"]
            weather_col_widths = [1.28*inch, 2.1*inch, 0.72*inch, 0.8*inch,
                                  1*inch, 0.96*inch, 0.72*inch, 0.75*inch, 0.72*inch, 0.72*inch]

            param_to_col_index = {
                'temperature': 2, 'humidity': 3, 'wind_speed': 4, 'wind_gust': 5,
                'rain': 7, 'pop': 8, 'uv_index': 9
            }
            numeric_data_for_highlight = {p: []
                                          for p in param_to_col_index.keys()}

            weather_table_data = [weather_headers]

            max_entries_for_table = 7 * 24

            for row_idx, item in enumerate(weather_data[:max_entries_for_table]):
                uv_index_formatted = col_params['uv_index']['format'](
                    item.get('uv_index'))
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
                    uv_index_formatted
                ]
                weather_table_data.append(row)

                table_row_index = row_idx + 1
                for param, value in [('temperature', item.get('temperature')),
                                     ('humidity', item.get('humidity')),
                                     ('wind_speed', item.get('wind_speed')),
                                     ('wind_gust', item.get('wind_gust')),
                                     ('rain', item.get('rain')),
                                     ('pop', item.get('pop')),
                                     ('uv_index', item.get('uv_index'))]:
                    if param in numeric_data_for_highlight and isinstance(value, (int, float)) and not math.isnan(value):
                        numeric_data_for_highlight[param].append(
                            (value, table_row_index))

            weather_table = Table(weather_table_data,
                                  repeatRows=1, colWidths=weather_col_widths)
            weather_style_cmds = [('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 11), ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 6), ('FONTNAME',
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
            note_text = "Note: 1 knot = 1.85 km/h; Wind Dir = Wind Direction; PoP = Probability of Precipitation (hourly)."
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

            cloud_chart = self.create_chart(
                weather_data, 'cloud_cover', 'Cloud Cover (%)', 'Cloud Cover Trend')
            if cloud_chart:
                elements.append(cloud_chart)
                elements.append(Spacer(1, 0.1*inch))

            uv_chart = self.create_chart(
                weather_data, 'uv_index', 'UV Index', 'UV Index Trend')
            if uv_chart:
                elements.append(uv_chart)
                elements.append(Spacer(1, 0.1*inch))

            charts_added = sum(1 for chart in [
                               temp_hum_chart, wind_chart, rain_pop_chart,
                               cloud_chart, uv_chart] if chart)  # Updated sum
            if charts_added == 0:
                elements.append(
                    Paragraph("No data available to generate weather charts.", normal_style))
            elements.append(Spacer(1, 0.1*inch))

        # --- NEW: Marine Forecast Section (for Open-Meteo only, specific locations) ---
        if api_source == "OpenMeteo" and marine_data:
            elements.append(
                Paragraph("Marine Forecast (Next 7 Days Hourly)", h2_style))

            # --- BEGIN: Marine summary section (English) ---
            wave_heights = [item.get('wave_height') for item in marine_data if isinstance(
                item.get('wave_height'), (int, float))]
            wave_periods = [item.get('wave_period') for item in marine_data if isinstance(
                item.get('wave_period'), (int, float))]
            swell_heights = [item.get('swell_wave_height') for item in marine_data if isinstance(
                item.get('swell_wave_height'), (int, float))]
            swell_periods = [item.get('swell_wave_period') for item in marine_data if isinstance(
                item.get('swell_wave_period'), (int, float))]
            wave_min = f"{min(wave_heights):.2f} m" if wave_heights else "N/A"
            wave_max = f"{max(wave_heights):.2f} m" if wave_heights else "N/A"
            wave_period_min = f"{min(wave_periods):.2f} s" if wave_periods else "N/A"
            wave_period_max = f"{max(wave_periods):.2f} s" if wave_periods else "N/A"
            swell_min = f"{min(swell_heights):.2f} m" if swell_heights else "N/A"
            swell_max = f"{max(swell_heights):.2f} m" if swell_heights else "N/A"
            swell_period_min = f"{min(swell_periods):.2f} s" if swell_periods else "N/A"
            swell_period_max = f"{max(swell_periods):.2f} s" if swell_periods else "N/A"
            marine_summary = (
                f"<b>Summary:</b><br/> "
                f"<b>Wave height</b>: {wave_min} - {wave_max}<br/>"
                f"<b>Swell wave height</b>: {swell_min} - {swell_max}<br/>"
                f"<b>Wave period</b>: {wave_period_min} - {wave_period_max}<br/>"
                f"<b>Swell wave period</b>: {swell_period_min} - {swell_period_max}"
            )
            elements.append(Paragraph(marine_summary, normal_style))
            elements.append(Spacer(1, 0.08*inch))

            # Remove sea level, wind wave height, wind wave direction, wind wave period
            marine_col_params = {
                'datetime': {'header': "Date/Time", 'format': lambda x: x, 'width': 1.5*inch, 'align': 'CENTER'},
                'wave_height': {'header': "Wave Height\n(m)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'wave_direction': {'header': "Wave Dir", 'format': lambda x: x, 'width': 0.9*inch, 'align': 'CENTER'},
                'wave_period': {'header': "Wave Period\n(s)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'swell_wave_height': {'header': "Swell Wave Height\n(m)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'swell_wave_direction': {'header': "Swell Wave Dir", 'format': lambda x: x, 'width': 0.9*inch, 'align': 'CENTER'},
                'swell_wave_period': {'header': "Swell Wave Period\n(s)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
            }
            marine_headers = [
                "Date/Time", "Wave Height\n(m)", "Wave\nDir", "Wave Period\n(s)",
                "Swell Wave Height\n(m)", "Swell Wave\nDir", "Swell Wave Period\n(s)"
            ]
            marine_col_widths = [1.5*inch, 1.1*inch, 0.9 *
                                 inch, 1.1*inch, 1.5*inch, 1.1*inch, 1.5*inch]

            marine_table_data = [marine_headers]
            marine_numeric_data_for_highlight = {
                'wave_height': [], 'wave_period': [],
                'swell_wave_height': [], 'swell_wave_period': []
            }
            marine_param_to_col_index = {
                'wave_height': 1, 'wave_period': 3,
                'swell_wave_height': 4, 'swell_wave_period': 6
            }

            for row_idx, item in enumerate(marine_data):
                row = [
                    item['datetime'],
                    marine_col_params['wave_height']['format'](
                        item.get('wave_height')),
                    marine_col_params['wave_direction']['format'](
                        item.get('wave_direction')),
                    marine_col_params['wave_period']['format'](
                        item.get('wave_period')),
                    marine_col_params['swell_wave_height']['format'](
                        item.get('swell_wave_height')),
                    marine_col_params['swell_wave_direction']['format'](
                        item.get('swell_wave_direction')),
                    marine_col_params['swell_wave_period']['format'](
                        item.get('swell_wave_period')),
                ]
                marine_table_data.append(row)

                table_row_index = row_idx + 1
                for param in marine_numeric_data_for_highlight.keys():
                    value = item.get(param)
                    if isinstance(value, (int, float)) and not math.isnan(value):
                        marine_numeric_data_for_highlight[param].append(
                            (value, table_row_index))

            if len(marine_table_data) > 1:
                marine_table = Table(
                    marine_table_data, repeatRows=1, colWidths=marine_col_widths)
                marine_style_cmds = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 6),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9.5),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
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

                # Combined Wave & Swell Height Chart
                height_img, period_img = self.create_combined_wave_chart(
                    marine_data,
                    xlabel_text='Date/Time',
                    height_ylabel='Height (m)',
                    period_ylabel='Period (s)',
                    height_title='Wave & Swell Height Trend',
                    period_title='Wave & Swell Period Trend',
                    wave_height_label='Wave Height',
                    swell_height_label='Swell Height',
                    wave_period_label='Wave Period',
                    swell_period_label='Swell Period'
                )
                if height_img:
                    elements.append(height_img)
                    elements.append(Spacer(1, 0.1*inch))
                if period_img:
                    elements.append(period_img)
                    elements.append(Spacer(1, 0.1*inch))
            else:
                elements.append(Paragraph(
                    "Marine Forecast Data Not Available for this location or period.", normal_style))
            elements.append(Spacer(1, 0.1*inch))
        # --- END Marine Forecast Section ---

        elements.append(Spacer(1, 0.2*inch))

        if api_source == "OWM" and owm_maps and owm_maps.get('Precipitation') is not None:
            try:
                owm_maps['Precipitation'].seek(0)
                pdf_image = RLImage(
                    owm_maps['Precipitation'], width=4*inch, height=4*inch)
                elements.append(Paragraph("Precipitation Map", h2_style))
                elements.append(pdf_image)
                elements.append(Spacer(1, 0.1*inch))
                print("Precipitation map added to PDF.")
            except Exception as e:
                print(f"Error adding precipitation map: {e}")
                elements.append(Paragraph(
                    "Could not generate precipitation map.", getSampleStyleSheet()['Normal']))
        else:
            print("No precipitation map available to add to PDF.")

        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("--- End of Report ---", footer_style))
        if api_source == "OWM":
            elements.append(
                Paragraph("Weather data © OpenWeatherMap", footer_style))
        elif api_source == "OpenMeteo":
            elements.append(
                Paragraph("Weather data, Marine data © Open-Meteo.com", footer_style))  # Updated footer
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
    def generate_vietnamese_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source, marine_data=None, owm_maps=None):

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
        title_style.fontSize = 18

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
        elements.append(Spacer(1, 0.2*inch))

        image_path = os.path.join(
            "Pictures", ui_location_name.replace(" ", "_") + ".png")
        if os.path.exists(image_path):
            try:
                img = RLImage(image_path, width=5.6*inch, height=2.8*inch)
                img.hAlign = 'CENTER'
                elements.append(img)
                elements.append(Spacer(1, 0.08*inch))
            except Exception as img_err:
                print(f"Could not add image for {ui_location_name}: {img_err}")

        elements.append(Spacer(1, 0.1*inch))
        api_name = location_info.get('name', '')
        country_code = location_info.get('country', 'N/A')

        api_details_parts = []
        if api_name and api_name != ui_location_name and not api_name.startswith("Coords ("):
            api_details_parts.append(api_name)
        if country_code and country_code != 'N/A':
            api_details_parts.append(country_code)

        location_string = f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Vị trí:</font> {ui_location_name}'
        if api_details_parts:
            api_details = ", ".join(api_details_parts)
            location_string += f" ({api_details})"

        elements.append(Paragraph(location_string, normal_style))

        elements.append(Paragraph(
            f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Tọa độ:</font> Vĩ độ: {lat:.4f}, Kinh độ: {lon:.4f}', normal_style))
        elements.append(Paragraph(
            f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Múi giờ:</font> {location_info.get("timezone", DEFAULT_TIMEZONE)}', normal_style))
        elements.append(Paragraph(
            f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Mặt trời mọc:</font> {location_info.get("sunrise", "N/A")}, <font name="{VIETNAMESE_FONT_NAME_BOLD}">Mặt trời lặn:</font> {location_info.get("sunset", "N/A")}', normal_style))
        elements.append(Paragraph(
            f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Báo cáo tạo lúc:</font> {datetime.now(pytz.timezone(location_info.get("timezone", DEFAULT_TIMEZONE))).strftime("%Y-%m-%d %H:%M:%S %Z")}', normal_style))
        elements.append(Paragraph(
            f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Nguồn dữ liệu:</font> {api_source}', normal_style))
        elements.append(Spacer(1, 0.2*inch))

        if weather_data:
            # Set forecast section header based on data source
            if api_source == "OpenMeteo":
                forecast_header_vn = "Dự Báo Thời Tiết (7 Ngày Tới Theo Giờ)"
            else:
                forecast_header_vn = "Dự Báo Thời Tiết (5 Ngày Tới, Mỗi 3 Giờ)"
            elements.append(
                Paragraph(forecast_header_vn, h2_style))

            # --- BEGIN: Add summary section (Vietnamese) ---
            temp_vals = [item.get('temperature') for item in weather_data if isinstance(
                item.get('temperature'), (int, float))]
            wind_vals = [item.get('wind_speed') for item in weather_data if isinstance(
                item.get('wind_speed'), (int, float))]
            rain_vals = [item.get('rain') for item in weather_data if isinstance(
                item.get('rain'), (int, float))]
            uv_vals = [item.get('uv_index') for item in weather_data if isinstance(
                item.get('uv_index'), (int, float))]

            temp_min = f"{min(temp_vals):.1f}°C" if temp_vals else "N/A"
            temp_max = f"{max(temp_vals):.1f}°C" if temp_vals else "N/A"
            wind_min = f"{min(wind_vals):.1f} knots" if wind_vals else "N/A"
            wind_max = f"{max(wind_vals):.1f} knots" if wind_vals else "N/A"
            rain_max = f"{max(rain_vals):.1f} mm/h" if rain_vals else "N/A"
            uv_max = f"{max(uv_vals):.1f}" if uv_vals else "N/A"

            summary_text_vn = (
                f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Tóm tắt:</font><br/> '
                f'Nhiệt độ: {temp_min} - {temp_max}<br/>'
                f'Tốc độ gió: {wind_min} - {wind_max}<br/>'
                f'Lượng mưa: lớn nhất {rain_max}<br/>'
                f'Chỉ số UV: lớn nhất {uv_max}'
            )
            elements.append(Paragraph(summary_text_vn, normal_style))
            elements.append(Spacer(1, 0.08*inch))
            # --- END: Add summary section (Vietnamese) ---

            weather_headers = ["Ngày/Giờ", "Mô Tả", "Nhiệt Độ\n(°C)", "Độ Ẩm\n(%)", "Tốc độ gió\n(knots)",
                               "Gió giật\n(knots)", "Hướng\ngió", "Lượng mưa\n(mm/h)", "XS mưa\n(%)", "Chỉ số\nUV"]
            weather_table_data = [weather_headers]

            numeric_data_for_highlight = {'temperature': [], 'wind_speed': [
            ], 'wind_gust': [], 'rain': [], 'uv_index': [], 'humidity': [], 'pop': []}
            param_to_col_index = {'temperature': 2, 'humidity': 3, 'wind_speed': 4,
                                  'wind_gust': 5, 'rain': 7, 'pop': 8, 'uv_index': 9}

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

                uvi = item.get('uv_index', 'N/A')
                uv_index_formatted = f"{item.get('uv_index'):.1f}" if isinstance(
                    item.get('uv_index'), (int, float)) else 'N/A'
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
                    uv_index_formatted
                ]
                weather_table_data.append(row)

                table_row_index = row_idx + 1
                for param, value in [('temperature', temp_val), ('humidity', hum_val), ('wind_speed', wind_val), ('wind_gust', gust_val), ('rain', rain_val), ('pop', pop_val), ('uv_index', uvi)]:
                    if isinstance(value, (int, float)) and not math.isnan(value):
                        numeric_data_for_highlight[param].append(
                            (value, table_row_index))

            weather_col_widths = [1.45*inch, 1.75*inch, 0.75*inch, 0.8*inch,
                                  0.95*inch, 0.95*inch, 0.72*inch, 0.93*inch, 0.72*inch, 0.75*inch]
            weather_table = Table(weather_table_data,
                                  repeatRows=1, colWidths=weather_col_widths)
            weather_style_cmds = [('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                  ('FONTNAME', (0, 0), (-1, -1),
                                   VIETNAMESE_FONT_NAME),
                                  ('FONTNAME', (0, 0), (-1, 0),
                                   VIETNAMESE_FONT_NAME_BOLD),
                                  ('FONTSIZE', (0, 0), (-1, 0), 11), ('BOTTOMPADDING',
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
            note_text_viet = "Ghi chú: 1 knot = 1.85 km/h; Hướng gió = Hướng gió thổi tới; XS mưa = Xác suất có mưa (được ước tính theo giờ dựa trên sự hiện diện của mưa/tuyết)."
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

            cloud_chart = self.create_chart(
                weather_data, 'cloud_cover', 'Mây che phủ (%)', 'Xu Hướng Mây Che Phủ',
                xlabel_text='Ngày/Giờ')
            if cloud_chart:
                elements.append(cloud_chart)
                elements.append(Spacer(1, 0.1*inch))

            uv_chart = self.create_chart(
                weather_data,
                'uv_index',
                'Chỉ số UV',
                'Xu Hướng Chỉ Số UV',
                xlabel_text='Ngày/Giờ'
            )
            if uv_chart:
                elements.append(uv_chart)
                elements.append(Spacer(1, 0.1*inch))

            charts_added = sum(1 for chart in [
                               temp_hum_chart, wind_chart, rain_pop_chart,
                               cloud_chart, uv_chart] if chart)
            if charts_added == 0:
                elements.append(
                    Paragraph("Không có dữ liệu để tạo biểu đồ.", normal_style))
            elements.append(Spacer(1, 0.1*inch))

        # --- NEW: Marine Forecast Section (for Open-Meteo only, specific locations) in Vietnamese ---
        if api_source == "OpenMeteo" and marine_data:
            elements.append(
                Paragraph("Dự Báo Biển (7 Ngày Tới Theo Giờ)", h2_style))

            # --- BEGIN: Marine summary section (Vietnamese) ---
            wave_heights = [item.get('wave_height') for item in marine_data if isinstance(
                item.get('wave_height'), (int, float))]
            wave_periods = [item.get('wave_period') for item in marine_data if isinstance(
                item.get('wave_period'), (int, float))]
            swell_heights = [item.get('swell_wave_height') for item in marine_data if isinstance(
                item.get('swell_wave_height'), (int, float))]
            swell_periods = [item.get('swell_wave_period') for item in marine_data if isinstance(
                item.get('swell_wave_period'), (int, float))]
            wave_min = f"{min(wave_heights):.2f} m" if wave_heights else "N/A"
            wave_max = f"{max(wave_heights):.2f} m" if wave_heights else "N/A"
            wave_period_min = f"{min(wave_periods):.2f} s" if wave_periods else "N/A"
            wave_period_max = f"{max(wave_periods):.2f} s" if wave_periods else "N/A"
            swell_min = f"{min(swell_heights):.2f} m" if swell_heights else "N/A"
            swell_max = f"{max(swell_heights):.2f} m" if swell_heights else "N/A"
            swell_period_min = f"{min(swell_periods):.2f} s" if swell_periods else "N/A"
            swell_period_max = f"{max(swell_periods):.2f} s" if swell_periods else "N/A"
            marine_summary_vn = (
                f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Tóm tắt:</font><br/> '
                f'Chiều cao sóng: {wave_min} - {wave_max}<br/>'
                f'Chiều cao sóng trường: {swell_min} - {swell_max}<br/>'
                f'Chu kỳ sóng: {wave_period_min} - {wave_period_max}<br/>'
                f'Chu kỳ sóng trường: {swell_period_min} - {swell_period_max}'
            )
            elements.append(Paragraph(marine_summary_vn, normal_style))
            elements.append(Spacer(1, 0.08*inch))
            # --- END: Marine summary section (Vietnamese) ---

            marine_headers_viet = [
                "Ngày/Giờ", "Chiều Cao Sóng\n(m)", "Hướng\nSóng", "Chu Kỳ Sóng\n(giây)",
                "Chiều Cao\nSóng Trường (m)", "Hướng\nSóng Trường", "Chu Kỳ\nSóng Trường (giây)"
            ]
            marine_col_widths_viet = [1.5*inch, 1.28*inch,
                                      1.1*inch, 1.1*inch, 1.4*inch, 1.2*inch, 1.6*inch]

            marine_table_data_viet = [marine_headers_viet]
            marine_numeric_data_for_highlight_viet = {
                'wave_height': [], 'wave_period': [],
                'swell_wave_height': [], 'swell_wave_period': []
            }
            marine_param_to_col_index_viet = {
                'wave_height': 1, 'wave_period': 3,
                'swell_wave_height': 4, 'swell_wave_period': 6
            }

            for row_idx, item in enumerate(marine_data):
                row = [
                    item['datetime'],
                    f"{item.get('wave_height'):.1f}" if isinstance(
                        item.get('wave_height'), (int, float)) else 'N/A',
                    WIND_DIR_VIET.get(item.get('wave_direction'),
                                      item.get('wave_direction')),
                    f"{item.get('wave_period'):.1f}" if isinstance(
                        item.get('wave_period'), (int, float)) else 'N/A',
                    f"{item.get('swell_wave_height'):.1f}" if isinstance(
                        item.get('swell_wave_height'), (int, float)) else 'N/A',
                    WIND_DIR_VIET.get(item.get('swell_wave_direction'), item.get(
                        'swell_wave_direction')),
                    f"{item.get('swell_wave_period'):.1f}" if isinstance(
                        item.get('swell_wave_period'), (int, float)) else 'N/A'
                ]
                marine_table_data_viet.append(row)

                table_row_index = row_idx + 1
                for param in marine_numeric_data_for_highlight_viet.keys():
                    value = item.get(param)
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
                    ('FONTNAME', (0, 0), (-1, -1), VIETNAMESE_FONT_NAME),
                    ('FONTNAME', (0, 0), (-1, 0), VIETNAMESE_FONT_NAME_BOLD),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 6),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                    ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                    ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
                    ('ALIGN', (6, 1), (6, -1), 'RIGHT'),
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
                height_img, period_img = self.create_combined_wave_chart(
                    marine_data,
                    xlabel_text='Ngày/Giờ',
                    height_ylabel='Chiều Cao (m)',
                    period_ylabel='Chu Kỳ (giây)',
                    height_title='Xu Hướng Chiều Cao Sóng & Sóng Trường',
                    period_title='Xu Hướng Chu Kỳ Sóng & Sóng Trường',
                    wave_height_label='Chiều Cao Sóng',
                    swell_height_label='Chiều Cao Sóng Trường',
                    wave_period_label='Chu Kỳ Sóng',
                    swell_period_label='Chu Kỳ Sóng Trường'
                )
                if height_img:
                    elements.append(height_img)
                    elements.append(Spacer(1, 0.1*inch))
                if period_img:
                    elements.append(period_img)
                    elements.append(Spacer(1, 0.1*inch))
            else:
                elements.append(Paragraph(
                    "Không có dữ liệu dự báo biển cho vị trí hoặc thời gian này.", normal_style))
            elements.append(Spacer(1, 0.1*inch))
        # --- END Marine Forecast Section in Vietnamese ---

        elements.append(Spacer(1, 0.2*inch))

        if api_source == "OWM" and owm_maps and 'Precipitation' in owm_maps:
            try:
                owm_maps['Precipitation'].seek(0)
                pdf_image = RLImage(
                    owm_maps['Precipitation'], width=4*inch, height=4*inch)
                elements.append(Paragraph("Precipitation Map", h2_style))
                elements.append(pdf_image)
                elements.append(Spacer(1, 0.1*inch))
                print("Precipitation map added to PDF.")
            except Exception as e:
                print(f"Error adding precipitation map: {e}")
                elements.append(Paragraph(
                    "Could not generate precipitation map.", getSampleStyleSheet()['Normal']))
        else:
            print("No precipitation map available to add to PDF.")

        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("--- Kết thúc báo cáo ---",
                        footer_style))
        if api_source == "OWM":
            elements.append(
                Paragraph("Dữ liệu thời tiết © OpenWeatherMap", footer_style))
        elif api_source == "OpenMeteo":
            elements.append(
                Paragraph("Dữ liệu thời tiết, Dữ liệu biển © Open-Meteo.com", footer_style))  # Updated footer
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
        title_style.fontSize = 18
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
        elements.append(Spacer(1, 0.2*inch))

        image_path = os.path.join(
            "Pictures", ui_location_name.replace(" ", "_") + ".png")
        if os.path.exists(image_path):
            try:
                img = RLImage(image_path, width=5.6*inch, height=2.8*inch)
                img.hAlign = 'CENTER'
                elements.append(img)
                elements.append(Spacer(1, 0.08*inch))
            except Exception as img_err:
                print(f"Could not add image for {ui_location_name}: {img_err}")

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

        # --- BEGIN: Add summary section for historical report ---
        if historical_data:
            elements.append(
                Paragraph("Historical Weather Data (Hourly)", h2_style))
            temp_vals = [item.get('temperature') for item in historical_data if isinstance(
                item.get('temperature'), (int, float))]
            hum_vals = [item.get('humidity') for item in historical_data if isinstance(
                item.get('humidity'), (int, float))]
            wind_vals = [item.get('wind_speed') for item in historical_data if isinstance(
                item.get('wind_speed'), (int, float))]
            rain_vals = [item.get('rain') for item in historical_data if isinstance(
                item.get('rain'), (int, float))]

            temp_min = f"{min(temp_vals):.1f}°C" if temp_vals else "N/A"
            temp_max = f"{max(temp_vals):.1f}°C" if temp_vals else "N/A"
            hum_min = f"{min(hum_vals):.0f}%" if hum_vals else "N/A"
            hum_max = f"{max(hum_vals):.0f}%" if hum_vals else "N/A"
            wind_min = f"{min(wind_vals):.1f} knots" if wind_vals else "N/A"
            wind_max = f"{max(wind_vals):.1f} knots" if wind_vals else "N/A"
            rain_max = f"{max(rain_vals):.1f} mm/h" if rain_vals else "N/A"

            summary_text = (
                f"<b>Summary:</b><br/>"
                f"<b>Temperature</b>: {temp_min} - {temp_max}<br/>"
                f"<b>Humidity</b>: {hum_min} - {hum_max}<br/>"
                f"<b>Wind Speed</b>: {wind_min} - {wind_max}<br/>"
                f"<b>Rain</b>: Max {rain_max}"
            )
            elements.append(Paragraph(summary_text, normal_style))
            elements.append(Spacer(1, 0.08*inch))

            col_params = {
                'datetime': {'header': "Date/Time", 'format': lambda x: x, 'width': 1.28*inch, 'align': 'CENTER'},
                'description': {'header': "Description", 'format': lambda x: x, 'width': 1.88*inch, 'align': 'CENTER'},
                'temperature': {'header': "Temp\n(°C)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
                'humidity': {'header': "Humidity\n(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.8*inch, 'align': 'RIGHT'},
                'wind_speed': {'header': "Wind Speed\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'wind_gust': {'header': "Wind Gust\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'wind_direction': {'header': "Wind\nDir", 'format': lambda x: x, 'width': 0.72*inch, 'align': 'CENTER'},
                'rain': {'header': "Rain\n(mm/h)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.75*inch, 'align': 'RIGHT'},
                'cloud_cover': {'header': "Cloud\nCover(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.8*inch, 'align': 'RIGHT'},
                'pressure': {'header': "Pressure\n(hPa)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.8*inch, 'align': 'RIGHT'},
            }

            historical_headers = ["Date/Time", "Description", "Temp\n(°C)", "Humidity\n(%)",
                                  "Wind Speed\n(knots)", "Wind Gust\n(knots)", "Wind\nDir",
                                  "Rain\n(mm/h)", "Cloud\nCover(%)", "Pressure\n(hPa)"]
            historical_col_widths = [1.28*inch, 1.88*inch, 0.72*inch, 0.8*inch,
                                     1*inch, 1*inch, 0.72*inch, 0.75*inch, 0.8*inch, 0.8*inch]

            param_to_col_index = {
                'temperature': 2, 'humidity': 3, 'wind_speed': 4, 'wind_gust': 5,
                'rain': 7, 'cloud_cover': 8, 'pressure': 9
            }
            numeric_data_for_highlight = {p: []
                                          for p in param_to_col_index.keys()}

            historical_table_data = [historical_headers]

            # All historical data will be in table
            for row_idx, item in enumerate(historical_data):
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
                                     ('cloud_cover', item.get('cloud_cover')),
                                     ('pressure', item.get('pressure'))]:
                    if param in numeric_data_for_highlight and isinstance(value, (int, float)) and not math.isnan(value):
                        numeric_data_for_highlight[param].append(
                            (value, table_row_index))

            historical_table = Table(historical_table_data,
                                     repeatRows=1, colWidths=historical_col_widths)
            historical_style_cmds = [('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 11), ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 6), ('FONTNAME',
                                                                                                                                                                                                                                                                                                                                                                                         (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 9.5), ('TOPPADDING', (0, 1), (-1, -1), 5), ('BOTTOMPADDING', (0, 1), (-1, -1), 5), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ALIGN', (2, 1), (3, -1), 'RIGHT'), ('ALIGN', (4, 1), (5, -1), 'RIGHT'), ('ALIGN', (7, 1), (9, -1), 'RIGHT'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightblue])]
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
            note_text = "Note: 1 knot = 1.85 km/h; Wind Dir = Wind Direction. Rainfall values are per hour."
            elements.append(Paragraph(note_text, small_note_style))
            elements.append(Spacer(1, 0.15*inch))

        if historical_data:
            elements.append(
                Paragraph("Historical Weather Parameter Charts", h2_style))

            # Pass limit_xticks=True for historical charts with many dates
            limit_xticks = len(historical_data) > 7 * 24

            temp_hum_chart = self.create_temp_humidity_chart(
                historical_data, limit_xticks=limit_xticks)
            if temp_hum_chart:
                elements.append(temp_hum_chart)
                elements.append(Spacer(1, 0.1*inch))

            wind_chart = self.create_wind_chart(
                historical_data, limit_xticks=limit_xticks)
            if wind_chart:
                elements.append(wind_chart)
                elements.append(Spacer(1, 0.1*inch))

            rain_chart = self.create_chart(
                historical_data, 'rain', 'Rainfall (mm/h)', 'Historical Rainfall Trend')
            if rain_chart:
                elements.append(rain_chart)
                elements.append(Spacer(1, 0.1*inch))

            vis_chart = self.create_chart(
                historical_data, 'uv_index', 'UV Index', 'Historical UV Index Trend')
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
        self.session.close()
        self.realtime_update_timer.stop()
        self.clock_timer.stop()
        if self.alert_timer.isActive():
            self.alert_timer.stop()
        print("Session closed and timers stopped.")
        event.accept()


if __name__ == '__main__':
    for folder in ['icons', 'Pictures']:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Warning: Folder '{folder}' not found. Created folder.")

    app = QApplication(sys.argv)
    weather_app = WeatherCrawlerApp()
    weather_app.show()
    sys.exit(app.exec_())
