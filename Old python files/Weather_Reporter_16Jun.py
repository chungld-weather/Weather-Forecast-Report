import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QRadioButton,
                             QMessageBox, QDateEdit, QProgressBar, QSizePolicy,
                             QGroupBox)
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt, QDate, QTimer, QSize
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import ImageReader
import requests
import json
from datetime import datetime, timedelta, timezone
import pytz
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import re
import traceback
import math

# --- ReportLab Font Registration ---
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
        print("Registered NotoSans font.")
    else:
        # Fallback logic can be added here if needed
        print("Warning: NotoSans font not found. Using default Helvetica.")
except Exception as font_err:
    print(f"Warning: Could not register Vietnamese font. Error: {font_err}")

# --- Global Dictionaries and Constants ---
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


class WeatherCrawlerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather Reporter")
        self.setGeometry(100, 100, 1100, 700)

        icon_path = "weather_icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file '{icon_path}' not found.")

        self.realtime_locations = {
            'Lan Tay Platform - Block 06.1': (7.5783, 108.8694),
            'Rong Doi Platform - Block 11.2': (7.7925, 108.2021),
            'An Phu Office - An Khanh Commune': (10.8094, 106.7366),
            'Vung Tau Airport - Vung Tau': (10.3760, 107.0932)
        }
        self.realtime_labels_data = {}

        self.api_key = "e1a69775e0d7c149a4e2bdb69bb59a82"

        self.initUI()
        self.session = self.create_requests_session()

        self.realtime_timer = QTimer(self)
        self.realtime_timer.timeout.connect(self._update_realtime_display)
        self.realtime_timer.start(15 * 60 * 1000)
        self._update_realtime_display()

        self.showMaximized()

    def initUI(self):
        main_hbox = QHBoxLayout()
        left_vbox = QVBoxLayout()
        right_vbox = QVBoxLayout()
        bottom_layout = QVBoxLayout()

        # --- LEFT PANEL ---
        api_group = QGroupBox("Select Weather API Source:")
        api_group.setFont(QFont("Arial", 11, QFont.Bold))
        api_layout = QVBoxLayout()
        self.api_radio_openmeteo = QRadioButton(
            "Open-Meteo (07-day forecast, Marine & Historical)")
        self.api_radio_openmeteo.setFont(QFont("Arial", 10))
        self.api_radio_openmeteo.setChecked(True)
        self.api_radio_owm = QRadioButton(
            "OpenWeatherMap (05-day forecast, Weather Maps)")
        self.api_radio_owm.setFont(QFont("Arial", 10))
        api_layout.addWidget(self.api_radio_openmeteo)
        api_layout.addWidget(self.api_radio_owm)
        api_group.setLayout(api_layout)
        left_vbox.addWidget(api_group)

        locations_group = QGroupBox("Select Location:")
        locations_group.setFont(QFont("Arial", 11, QFont.Bold))
        input_layout = QVBoxLayout()
        self.locations = {'Lan Tay Platform - Block 06.1': (7.5783, 108.8694), 'Rong Doi Platform - Block 11.2': (7.7925, 108.2021), 'Home': (10.8317, 106.7327), 'Ha Noi home': (
            21.0042, 105.8145), 'An Phu Office - An Khanh Commune': (10.8094, 106.7366), 'Thao Dien Pitch': (10.807, 106.739), 'Vung Tau Airport - Vung Tau': (10.376, 107.0932)}
        self.location_radios = {}
        for name, coords in self.locations.items():
            location_hbox = QHBoxLayout()
            radio = QRadioButton(name)
            radio.setFont(QFont("Arial", 10))
            self.location_radios[name] = radio
            radio.toggled.connect(self.toggle_gps_input)
            coord_label = QLabel(f"({coords[0]:.4f}, {coords[1]:.4f})")
            coord_label.setFont(QFont("Arial", 10))
            coord_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            location_hbox.addWidget(radio)
            location_hbox.addWidget(coord_label)
            input_layout.addLayout(location_hbox)
        self.gps_radio = QRadioButton("Enter Custom GPS Coordinates:")
        self.gps_radio.setFont(QFont("Arial", 10))
        self.gps_radio.toggled.connect(self.toggle_gps_input)
        input_layout.addWidget(self.gps_radio)
        gps_name_layout = QHBoxLayout()
        self.gps_name_label = QLabel("Custom Name (Optional):")
        self.gps_name_input = QLineEdit()
        self.gps_name_input.setPlaceholderText("e.g., My Offshore Site")
        self.gps_name_label.setEnabled(False)
        self.gps_name_input.setEnabled(False)
        gps_name_layout.addWidget(self.gps_name_label)
        gps_name_layout.addWidget(self.gps_name_input)
        input_layout.addLayout(gps_name_layout)
        gps_coord_layout = QHBoxLayout()
        self.lat_label = QLabel("Latitude:")
        self.lon_label = QLabel("Longitude:")
        self.lat_input = QLineEdit()
        self.lon_input = QLineEdit()
        self.lat_label.setEnabled(False)
        self.lon_label.setEnabled(False)
        self.lat_input.setEnabled(False)
        self.lon_input.setEnabled(False)
        gps_coord_layout.addWidget(self.lat_label)
        gps_coord_layout.addWidget(self.lat_input)
        gps_coord_layout.addWidget(self.lon_label)
        gps_coord_layout.addWidget(self.lon_input)
        input_layout.addLayout(gps_coord_layout)
        default_location_key = 'An Phu Office - An Khanh Commune'
        if default_location_key in self.location_radios:
            self.location_radios[default_location_key].setChecked(True)
        locations_group.setLayout(input_layout)
        left_vbox.addWidget(locations_group)

        # --- Report Actions & Historical Weather Data Retrieval (moved here) ---
        report_actions_group = QGroupBox("Report Actions")
        report_actions_group.setFont(QFont("Arial", 11, QFont.Bold))
        report_actions_vbox = QVBoxLayout()

        forecast_group = QGroupBox("Generate Weather Forecast Report")
        forecast_vbox = QVBoxLayout()
        self.weather_button = QPushButton("Generate Report (English)")
        self.weather_button.setFont(QFont("Arial", 11))
        self.weather_button.setFixedHeight(30)  # Increased height
        self.weather_button.setStyleSheet(
            "background-color: #a7fcfd; color: black; font-weight: bold;")
        self.weather_button.clicked.connect(
            self.generate_weather_report_action)
        forecast_vbox.addWidget(self.weather_button)
        self.vietnamese_weather_button = QPushButton(
            "Tạo Báo Cáo Thời Tiết (Tiếng Việt)")
        self.vietnamese_weather_button.setFont(QFont("Arial", 11))
        self.vietnamese_weather_button.setFixedHeight(30)  # Increased height
        self.vietnamese_weather_button.setStyleSheet(
            "background-color: #a7fcfd; color: black; font-weight: bold;")
        self.vietnamese_weather_button.clicked.connect(
            self.generate_vietnamese_weather_report_action)
        forecast_vbox.addWidget(self.vietnamese_weather_button)
        forecast_group.setLayout(forecast_vbox)
        report_actions_vbox.addWidget(forecast_group)

        historical_group = QGroupBox(
            "Historical Weather Data Retrieval (Open-Meteo)")
        historical_layout = QVBoxLayout()
        date_range_layout = QHBoxLayout()

        # Set smaller font for labels and date edits
        date_label_font = QFont("Arial", 10)
        date_edit_font = QFont("Arial", 10)

        from_label = QLabel("From:")
        from_label.setFont(date_label_font)
        date_range_layout.addWidget(from_label)

        self.historical_from_date = QDateEdit(calendarPopup=True)
        self.historical_from_date.setFont(date_edit_font)
        self.historical_from_date.setDate(QDate.currentDate().addDays(-8))
        self.historical_from_date.setDisplayFormat("dd/MM/yyyy")
        self.historical_from_date.setFixedWidth(126)
        date_range_layout.addWidget(self.historical_from_date)
        to_label = QLabel("To:")
        to_label.setFont(date_label_font)
        date_range_layout.addWidget(to_label)

        self.historical_to_date = QDateEdit(calendarPopup=True)
        self.historical_to_date.setFont(date_edit_font)
        self.historical_to_date.setDate(QDate.currentDate().addDays(-1))
        self.historical_to_date.setDisplayFormat("dd/MM/yyyy")
        self.historical_to_date.setFixedWidth(126)
        date_range_layout.addWidget(self.historical_to_date)
        date_range_layout.addStretch()
        historical_layout.addLayout(date_range_layout)
        self.fetch_historical_button = QPushButton(
            "Generate Historical Report (PDF)")
        self.fetch_historical_button.setFont(QFont("Arial", 11))
        self.fetch_historical_button.setFixedHeight(30)  # Increased height
        self.fetch_historical_button.setStyleSheet(
            "background-color: #a7fcfd; color: black; font-weight: bold;")
        self.fetch_historical_button.clicked.connect(
            self._fetch_historical_and_generate_report_action)
        historical_layout.addWidget(self.fetch_historical_button)
        historical_group.setLayout(historical_layout)
        report_actions_vbox.addWidget(historical_group)
        report_actions_group.setLayout(report_actions_vbox)
        left_vbox.addWidget(report_actions_group)

        # --- Progress bar and status label (left panel only) ---
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setVisible(False)
        left_vbox.addWidget(self.progress_bar)
        left_vbox.addWidget(self.status_label)
        left_vbox.addStretch()

        # --- RIGHT PANEL ---
        realtime_group = QGroupBox("Real-time Dashboard")
        realtime_group.setFont(QFont("Arial", 11, QFont.Bold))
        realtime_layout = QVBoxLayout()
        icon_size = 27
        location_image_size = QSize(250, 125)
        for loc_name in self.realtime_locations.keys():
            loc_group = QGroupBox(loc_name)
            loc_group.setFont(QFont("Arial", 10, QFont.Bold))
            loc_main_hbox = QHBoxLayout()
            loc_details_vbox = QVBoxLayout()

            # Weather details with icons
            for param in ['desc', 'temp', 'wind', 'rain']:
                hbox = QHBoxLayout()
                icon_label = QLabel()
                icon_label.setPixmap(QPixmap(f"icons/{param}.png").scaled(
                    icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                data_label = QLabel(f"{param.capitalize()}: N/A")
                data_label.setFont(QFont("Arial", 10))
                hbox.addWidget(icon_label)
                hbox.addWidget(data_label)
                hbox.addStretch()
                loc_details_vbox.addLayout(hbox)
                self.realtime_labels_data.setdefault(
                    loc_name, {})[param] = data_label

            loc_main_hbox.addLayout(loc_details_vbox)

            # Location picture
            location_image_label = QLabel()
            # "Lan Tay Platform - Block 06.1" -> "Lan Tay Platform"
            safe_loc_name = re.sub(r'\s-\s.*', '', loc_name)
            image_path = os.path.join(
                "Pictures", safe_loc_name.replace(" ", "_") + ".png")
            if os.path.exists(image_path):
                location_image_label.setPixmap(QPixmap(image_path).scaled(
                    location_image_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                location_image_label.setText("Image not found")
            location_image_label.setFixedSize(location_image_size)
            loc_main_hbox.addWidget(
                location_image_label, alignment=Qt.AlignRight | Qt.AlignVCenter)

            loc_group.setLayout(loc_main_hbox)
            realtime_layout.addWidget(loc_group)

        alert_refresh_hbox = QHBoxLayout()
        self.rt_refresh_button = QPushButton("Refresh Now")
        self.rt_refresh_button.setFont(QFont("Arial", 11))
        self.rt_refresh_button.setFixedWidth(180)  # Increased width
        self.rt_refresh_button.setFixedHeight(30)  # Increased height
        self.rt_refresh_button.setStyleSheet(
            "background-color: #a7fcfd; color: black; font-weight: bold;")
        self.rt_refresh_button.clicked.connect(self._update_realtime_display)
        alert_refresh_hbox.addWidget(self.rt_refresh_button)
        alert_refresh_hbox.addStretch()
        self.rt_alert_label = QLabel("Wind Speed Alert: None")
        self.rt_alert_label.setFont(QFont("Arial", 11, QFont.Bold))

        realtime_layout.addLayout(alert_refresh_hbox)
        realtime_layout.addWidget(self.rt_alert_label)
        realtime_group.setLayout(realtime_layout)
        right_vbox.addWidget(realtime_group)
        right_vbox.addStretch()

        # --- FINAL ASSEMBLY ---
        main_hbox.addLayout(left_vbox, stretch=1)
        main_hbox.addLayout(right_vbox, stretch=1)

        final_layout = QVBoxLayout(self)
        final_layout.addLayout(main_hbox)
        # Progress bar and status label are now only in left panel, not in bottom_layout
        self.toggle_gps_input()

    def toggle_gps_input(self):
        is_gps_selected = self.gps_radio.isChecked()
        for widget in [self.lat_label, self.lon_label, self.lat_input, self.lon_input, self.gps_name_label, self.gps_name_input]:
            widget.setEnabled(is_gps_selected)

    def get_api_choice(self):
        return "OWM" if self.api_radio_owm.isChecked() else "OpenMeteo"

    def generate_weather_report_action(self):
        self._generate_report(lang='en')

    def generate_vietnamese_weather_report_action(self):
        self._generate_report(lang='vi')

    def _generate_report(self, lang):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return
        api_choice = self.get_api_choice()

        lang_map = {'en': ("Preparing", "Fetching", "Generating", "report"), 'vi': (
            "Đang chuẩn bị", "Đang lấy", "Đang tạo", "báo cáo")}
        self._start_progress(
            f"{lang_map[lang][0]} to fetch data from {api_choice}...")
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
                if location_name_selected in ['Lan Tay Platform - Block 06.1', 'Rong Doi Platform - Block 11.2']:
                    self._update_progress_status(
                        f"{lang_map[lang][1]} marine data...")
                    marine_data = self._fetch_marine_data_openmeteo(
                        lat, lon, location_info.get('timezone', DEFAULT_TIMEZONE))

            if not weather_data:
                QMessageBox.warning(
                    self, "Error", f"Failed to fetch weather data.")
                raise Exception("Weather data fetch failed")

            self._update_progress_status(
                f"{lang_map[lang][2]} PDF {lang_map[lang][3]}...")
            if lang == 'en':
                self.generate_pdf_report(lat, lon, weather_data, location_info,
                                         location_name_selected, api_choice, marine_data)
            else:
                self.generate_vietnamese_pdf_report(
                    lat, lon, weather_data, location_info, location_name_selected, api_choice, marine_data)

            self._end_progress(f"Report generated successfully!", success=True)
            QMessageBox.information(
                self, "Success", f"PDF report generated successfully!")

        except Exception as e:
            self._end_progress("Report generation failed.", success=False)
            print(
                f"An error occurred during report generation: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _fetch_historical_and_generate_report_action(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return
        from_date, to_date = self.historical_from_date.date(
        ).toPyDate(), self.historical_to_date.date().toPyDate()
        if from_date > to_date:
            QMessageBox.warning(self, "Date Error",
                                "From Date cannot be after To Date.")
            return
        if (to_date - from_date).days > 365 * 2:
            QMessageBox.warning(self, "Date Range Warning",
                                "Please select a date range of up to 2 years.")
            return

        self._start_progress(
            f"Fetching historical data for {location_name_selected}...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            _, location_info = self._fetch_weather_data_openmeteo(
                lat, lon)  # Get timezone info
            timezone_for_historical = location_info.get(
                'timezone', DEFAULT_TIMEZONE)

            historical_data = self._fetch_historical_data_openmeteo(lat, lon, from_date.strftime(
                '%Y-%m-%d'), to_date.strftime('%Y-%m-%d'), timezone_for_historical)
            if not historical_data:
                raise Exception("Failed to fetch historical weather data.")

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
                    return self.locations[name][0], self.locations[name][1], name
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
                    # Try to find a matching pytz timezone name
                    now_utc = datetime.now(timezone.utc)
                    for tz_name in pytz.common_timezones:
                        tz = pytz.timezone(tz_name)
                        if now_utc.astimezone(tz).utcoffset() == timedelta(seconds=offset_sec):
                            timezone_str = tz_name
                            break
                    else:  # If no match found, use fixed offset
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
        params = {"latitude": lat, "longitude": lon, "hourly": "temperature_2m,relative_humidity_2m,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m,visibility,cloud_cover,pressure_msl,uv_index",
                  "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,weather_code", "timezone": "auto", "forecast_days": 7, "temperature_unit": "celsius", "wind_speed_unit": "kn", "precipitation_unit": "mm"}
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
        """
        Fetch real-time weather data from Open-Meteo for a given location.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "precipitation,weather_code,apparent_temperature",
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
            apparent_temp_val = None
            if "hourly" in data:
                now = datetime.now(local_tz)
                times = data["hourly"].get("time", [])
                rain_vals = data["hourly"].get("precipitation", [])
                apparent_temps = data["hourly"].get("apparent_temperature", [])
                for t_idx, (t, v) in enumerate(zip(times, rain_vals)):
                    dt = datetime.fromisoformat(t).astimezone(local_tz)
                    if abs((dt - now).total_seconds()) < 3600:
                        rain_val = v
                        # Get apparent temperature for the same hour
                        if t_idx < len(apparent_temps):
                            apparent_temp_val = apparent_temps[t_idx]
                        break
            # Fallback to current temperature if apparent not available
            if apparent_temp_val is None:
                apparent_temp_val = current.get(
                    'apparent_temperature', current.get('temperature', None))
            weather_code = current.get('weathercode', None)
            return {
                'temperature': f"{apparent_temp_val:.1f}°C" if apparent_temp_val is not None else "N/A",
                'wind_speed': f"{current.get('windspeed', 'N/A'):.1f} knots" if current.get('windspeed') is not None else "N/A",
                'wind_speed_value': current.get('windspeed', 0) if current.get('windspeed') is not None else 0,
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
            rain_val = data.get('rain', {}).get('1h', 0.0)
            return {
                'temperature': f"{data.get('main', {}).get('temp', 'N/A'):.1f}°C" if data.get('main', {}).get('temp') is not None else "N/A",
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
        print("\n--- Updating Real-time Weather Dashboard (Open-Meteo preferred, fallback to OWM) ---")
        max_wind_speed_overall = 0.0
        for name, coords in self.realtime_locations.items():
            if name in self.realtime_labels_data:  # Check if this location is on the dashboard
                # Try Open-Meteo first
                data = self._fetch_realtime_data_openmeteo(
                    coords[0], coords[1], name)
                # Fallback to OWM if OM fails or returns incomplete data
                if not data or data['temperature'] == "N/A":
                    data = self._fetch_realtime_data_owm(
                        coords[0], coords[1], name)
                labels = self.realtime_labels_data[name]
                if data:
                    labels['temp'].setText(data['temperature'])
                    labels['rain'].setText(data['rain'])
                    labels['wind'].setText(
                        f"{data['wind_speed']} ({data['wind_direction']})")
                    labels['desc'].setText(
                        f"{data['weather_description']} (as of {data['time_as_of']})")
                    if isinstance(data.get('wind_speed_value'), (int, float)) and data['wind_speed_value'] > max_wind_speed_overall:
                        max_wind_speed_overall = data['wind_speed_value']
                else:
                    for label in labels.values():
                        label.setText("Failed to load")

        if max_wind_speed_overall > 30.0:
            self.rt_alert_label.setText(
                f"HIGH WIND ALERT! ({max_wind_speed_overall:.1f} knots)")
            self.rt_alert_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.rt_alert_label.setText(
                f"Wind Speed Alert: None (Max: {max_wind_speed_overall:.1f} knots)")
            self.rt_alert_label.setStyleSheet("color: green;")
        QApplication.processEvents()

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

            # Helper function to safely get data from list
            def get_val(key, index):
                lst = data.get(key, [])
                return lst[index] if index < len(lst) and lst[index] is not None else 'N/A'

            for i in range(len(data.get('time', []))):
                processed_data.append({
                    'datetime_obj': datetime.fromisoformat(data['time'][i]).astimezone(local_tz),
                    'datetime': datetime.fromisoformat(data['time'][i]).astimezone(local_tz).strftime('%Y-%m-%d %H:%M'),
                    'description': WMO_WEATHER_CODES_EN.get(get_val('weather_code', i), 'N/A'),
                    'temperature': get_val('temperature_2m', i),
                    'humidity': get_val('relative_humidity_2m', i),
                    'wind_speed': get_val('wind_speed_10m', i),
                    'wind_gust': get_val('wind_gusts_10m', i),
                    'wind_direction': self._degrees_to_direction(get_val('wind_direction_10m', i)),
                    'rain': get_val('precipitation', i),
                    'cloud_cover': get_val('cloud_cover', i),
                    'pressure': get_val('pressure_msl', i),
                    'visibility': get_val('visibility', i),
                    'pop': 'N/A'
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
            return Image(BytesIO(response.content), width=2.2*inch, height=2.2*inch)
        except Exception as e:
            print(f"Failed to fetch OWM map tile for layer {layer}: {e}")
            return None

    def _fetch_all_owm_map_tiles(self, lat, lon, zoom):
        x, y = self._convert_coord_to_tile(lat, lon, zoom)
        maps = {}
        layers = {'Clouds': 'clouds_new', 'Temperature': 'temp_new',
                  'Wind Speed': 'wind_new', 'Precipitation': 'precipitation_new'}
        for name, layer_code in layers.items():
            if tile := self._fetch_owm_map_tile(layer_code, zoom, x, y):
                maps[name] = tile
        return maps

    def _process_forecast_data_owm(self, data, local_tz):
        processed = []
        now_local = datetime.now(local_tz)
        for item in data.get('list', []):
            local_time = datetime.fromtimestamp(
                item['dt'], tz=timezone.utc).astimezone(local_tz)
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
                rain = (hourly_data.get('rain', [])[i] or 0) + (hourly_data.get('showers',
                                                                                [])[i] or 0) + (hourly_data.get('snowfall', [])[i] or 0)
                processed.append({
                    'datetime_obj': local_time, 'datetime': local_time.strftime('%Y-%m-%d %H:%M'),
                    'description': WMO_WEATHER_CODES_EN.get(hourly_data.get('weather_code', [])[i], 'N/A'),
                    'temperature': hourly_data.get('temperature_2m', [])[i], 'humidity': hourly_data.get('relative_humidity_2m', [])[i],
                    'pressure': hourly_data.get('pressure_msl', [])[i],
                    'wind_speed': hourly_data.get('wind_speed_10m', [])[i], 'wind_gust': hourly_data.get('wind_gusts_10m', [])[i],
                    'wind_direction': self._degrees_to_direction(hourly_data.get('wind_direction_10m', [])[i]),
                    'rain': rain, 'visibility': hourly_data.get('visibility', [])[i],
                    'pop': 100 if rain > 0 else 0, 'cloud_cover': hourly_data.get('cloud_cover', [])[i]
                })
        return processed

    def _degrees_to_direction(self, degrees):
        if degrees is None or degrees == 'N/A':
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
        return Image(buf, width=9.6*inch, height=3.0*inch)

    # Simplified chart functions would follow, they can be copied from the previous version.
    # The key change is ensuring they handle 'N/A' values gracefully.
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

    # def generate_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source, marine_data=None, owm_maps=None):
    #     # This is a placeholder. The full implementation is very long but follows the logic
    #     # of building a list of ReportLab elements and then calling doc.build(elements).
    #     # Key additions are sections for `owm_maps` and the expanded `marine_data`.
    #     print("Generating English PDF report...")
    #     # doc = SimpleDocTemplate(...)
    #     # elements = []
    #     # ... append headers, weather table, charts ...
    #     # if owm_maps: ... append map table ...
    #     # if marine_data: ... append expanded marine table and charts ...
    #     # ... append footer ...
    #     # doc.build(elements)
    #     pass

    # def generate_vietnamese_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source, marine_data=None, owm_maps=None):
    #     # Placeholder for the full Vietnamese PDF generation logic.
    #     print("Generating Vietnamese PDF report...")
    #     pass

    # def generate_historical_pdf_report(self, lat, lon, historical_data, location_info, ui_location_name, from_date, to_date):
    #     # Placeholder for the full Historical PDF generation logic.
    #     print("Generating Historical PDF report...")
    #     pass

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
        if hasattr(self, 'session'):
            self.session.close()
        if hasattr(self, 'realtime_timer'):
            self.realtime_timer.stop()
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

# --- END OF FILE ---
