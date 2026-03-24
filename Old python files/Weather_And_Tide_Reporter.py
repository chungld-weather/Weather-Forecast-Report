# -*- coding: utf-8 -*-
# Add this line at the top for better Unicode handling

import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QRadioButton,
                             QMessageBox, QDateEdit, QProgressBar)  # Added QDateEdit
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QDate  # Import QDate
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import ImageReader
import requests
import json
# Added date, time, make sure 'date' is imported from datetime
from datetime import datetime, timedelta, timezone, date, time
import pytz
from requests.adapters import HTTPAdapter
# Corrected import for newer urllib3 versions
from urllib3.util.retry import Retry
import matplotlib.pyplot as plt
from io import BytesIO
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
# Removed tempfile, PyPDF2 - replaced by pdfplumber and io
import io  # For handling PDF download in memory
import traceback  # For better error printing

# --- Add pdfplumber import ---
try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber library not found.")
    print("Please install it using: pip install pdfplumber")
    print("Tidal PDF scraping will be disabled.")
    pdfplumber = None  # Set to None if import fails
# --- End pdfplumber import ---

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

# --- Constants ---
TIDAL_INDEX_URL = "http://www.kttv-nb.org.vn/index.php/thong-tin-kttv/thuy-van"

# --- Tidal PDF Scraping Function (Modified for specific date) ---


def scrape_and_download_tidal_pdf_for_date(session, target_date, download_dir="."):
    """
    Scrapes the tidal forecast PDF URL for a SPECIFIC DATE from the kttv-nb.org.vn site
    (assuming all reports are on the main index page), downloads it, and returns the path and URL.
    Handles different title formats like "TIN..." and "BẢN TIN..." with dd-mm-yyyy dates.

    Args:
        session: A requests.Session object.
        target_date: A datetime.date object for the desired report date.
        download_dir: Directory to save the downloaded PDF.

    Returns:
        A tuple: (downloaded_file_path, pdf_source_url)
    """
    target_date_str_compare = target_date.strftime(
        '%d-%m-%Y')  # Format for comparison
    print(
        f"\n--- Starting Tidal PDF URL Scraping for Date: {target_date_str_compare} ---")
    article_url = None
    pdf_src_url_relative = None
    pdf_url = None
    downloaded_file_path = None
    base_url = "http://www.kttv-nb.org.vn"
    timeout = (180, 720)  # (connect, read)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': base_url
    }

    try:
        # --- Step 1: Fetch the SINGLE index page and find the ARTICLE link ---
        list_url = TIDAL_INDEX_URL
        print(f"Checking index page: {list_url}")
        found_article_link = None

        try:
            index_response = session.get(
                list_url, headers=headers, timeout=timeout)
            index_response.raise_for_status()
        except requests.exceptions.RequestException as req_err:
            print(f"  Error accessing index page: {req_err}. Cannot proceed.")
            return None, None

        index_soup = BeautifulSoup(index_response.content, 'lxml')

        # *** UPDATED Regex to match BOTH title formats ***
        # Matches "TIN..." or "BẢN TIN..."
        # Matches "TP.HCM" or "THÀNH PHỐ HỒ CHÍ MINH" or "TPHCM"
        # Matches space or " - " before NGÀY
        # Captures dd-mm-yyyy date

        bulletin_title_pattern = re.compile(
            # Match "TIN" OR "BẢN TIN" at the start
            r"(?:BẢN TIN)\s+DỰ BÁO THỦY VĂN"
            # Match space, then "TP.HCM" (optional dot) OR "THÀNH PHỐ HỒ CHÍ MINH"
            r"\s+(?:TP\.?HCM|THÀNH PHỐ HỒ CHÍ MINH)"
            # Match either " - " OR just space(s) before NGÀY
            r"(?:\s+-\s+|\s+)"
            # Match NGÀY
            r"NGÀY"
            # Match space, then capture the date dd-mm-yyyy (using only hyphens)
            r"\s+(\d{1,2}[/.-]\d{1,2}(?:[/.-]\d{2,4})?)",
            re.IGNORECASE  # Keep it case-insensitive
        )
        # --- End Regex Definition ---

        all_links = index_soup.find_all('a', href=True)
        print(f"Searching {len(all_links)} links on the page...")

        for link in all_links:
            title = link.get_text(strip=True)
            # *** DEBUG: Print the exact title being checked ***
            # print(f"  Checking Title: '{title}'")
            # *** END DEBUG ***

            match = bulletin_title_pattern.search(title)
            if match:
                date_str_from_title = match.group(1)
                try:
                    article_date = datetime.strptime(
                        date_str_from_title, '%d-%m-%Y').date()

                    if article_date == target_date:
                        found_article_link = link['href']
                        print(
                            f"  Found matching article: Date={article_date.strftime('%Y-%m-%d')}, Title='{title}', Href='{link['href']}'")
                        break

                except ValueError:
                    continue

        if found_article_link:
            article_url = urljoin(base_url, found_article_link)
            print(f"Article URL for {target_date_str_compare}: {article_url}")
        else:
            print(
                f"Error: Could not find an article link for the specific date: {target_date_str_compare} on the page.")
            return None, None

    except Exception as e:
        print(
            f"Unexpected error processing index page: {e}\n{traceback.format_exc()}")
        return None, None

    # --- Step 2 & 3 remain the same: Fetch article, find PDF, download ---
    # (No changes needed in the rest of the function)
    try:
        print(f"Fetching article page: {article_url}")
        article_response = session.get(
            article_url, headers=headers, timeout=timeout)
        article_response.raise_for_status()
        article_soup = BeautifulSoup(article_response.content, 'lxml')
        print("Article page fetched.")

        content_area = article_soup.find(
            'div', class_='item-page') or article_soup.body
        if not content_area:
            content_area = article_soup.body

        print("Searching for PDF source (embed/iframe/a) in article content...")
        pdf_source_found = False
        pdf_search_patterns = [
            ('embed', 'src'), ('iframe', 'src'), ('a', 'href')]

        for tag_name, attr_name in pdf_search_patterns:
            pdf_pattern = re.compile(r'\.pdf$', re.IGNORECASE)
            tags = content_area.find_all(tag_name, **{attr_name: pdf_pattern})
            if tags:
                best_match_url = None
                date_pdf_str_1 = target_date.strftime("%d-%m-%Y")  # DD-MM-YYYY
                date_pdf_str_2 = target_date.strftime("%d%m%y")  # DDMMYY
                date_pdf_str_3 = target_date.strftime("%Y%m%d")  # YYYYMMDD

                for tag in tags:
                    url = tag.get(attr_name)
                    if url and (date_pdf_str_1 in url or date_pdf_str_2 in url or date_pdf_str_3 in url):
                        best_match_url = url
                        break

                if best_match_url:
                    pdf_src_url_relative = best_match_url
                    print(
                        f"Found specific PDF source in <{tag_name}> (matches date): {pdf_src_url_relative}")
                else:
                    pdf_src_url_relative = tags[0].get(attr_name)
                    print(
                        f"Found generic PDF source in <{tag_name}> (using first match): {pdf_src_url_relative}")
                pdf_source_found = True
                break

        if pdf_source_found and pdf_src_url_relative:
            pdf_url = urljoin(article_url, pdf_src_url_relative)
            print(f"Constructed absolute PDF URL: {pdf_url}")
        else:
            print(
                f"Error: Could not find PDF source within article page: {article_url}")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching/parsing article page: {e}")
        return None, article_url
    except Exception as e:
        print(
            f"Unexpected error processing article page: {e}\n{traceback.format_exc()}")
        return None, article_url

    if not pdf_url:
        return None, None

    # --- Step 3: Download PDF and save locally ---
    try:
        print(f"Downloading PDF from: {pdf_url}")
        pdf_response = session.get(
            pdf_url, headers=headers, timeout=timeout, stream=True)
        pdf_response.raise_for_status()

        content_type = pdf_response.headers.get('Content-Type', '').lower()
        if 'application/pdf' not in content_type and not pdf_url.lower().endswith('.pdf'):
            print(
                f"Warning: URL content type ('{content_type}') may not be PDF. Proceeding anyway.")

        pdf_filename = f"Tidal_Report_{target_date.strftime('%Y%m%d')}.pdf"
        os.makedirs(download_dir, exist_ok=True)
        downloaded_file_path = os.path.join(download_dir, pdf_filename)

        with open(downloaded_file_path, 'wb') as f:
            for chunk in pdf_response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"PDF downloaded and saved to: {downloaded_file_path}")
        return downloaded_file_path, pdf_url

    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None, pdf_url
    except OSError as e:
        print(f"Error saving PDF file to {download_dir}: {e}")
        return None, pdf_url
    except Exception as e:
        print(
            f"Unexpected error during PDF download/saving: {e}\n{traceback.format_exc()}")
        return None, pdf_url

# --- End of scrape_and_download_tidal_pdf_for_date ---


class WeatherCrawlerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather & Tide Reporter")
        # Increased height slightly for date edit
        self.setGeometry(200, 200, 500, 400)

        icon_path = "weather_icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file {icon_path} not found")

        self.api_key = "e1a69775e0d7c149a4e2bdb69bb59a82"  # Replace with your actual key

        self.initUI()
        self.session = self.create_requests_session()

        if pdfplumber is None:
            QMessageBox.warning(self, "Dependency Warning",
                                "The 'pdfplumber' library is missing.\n"
                                "Tidal PDF scraping might be affected or disabled.\n\n"
                                "Please install it using:\npip install pdfplumber")

    # In Weather_And_Tide_Reporter.py
# Inside the WeatherCrawlerApp class

    def initUI(self):
        main_layout = QVBoxLayout()

        # --- 1. Location Input Section ---
        input_layout = QVBoxLayout()  # Create the layout for this section
        input_label = QLabel("Locations:")
        input_label.setFont(QFont("Arial", 12, QFont.Bold))
        input_layout.addWidget(input_label)

        self.lat_label = QLabel("Latitude:")
        self.lat_input = QLineEdit()
        self.lon_label = QLabel("Longitude:")
        self.lon_input = QLineEdit()
        self.lat_input.setEnabled(False)
        self.lon_input.setEnabled(False)

        self.locations = {
            'Lan Tay Platform': (7.5783, 108.8694),
            'Rong Doi Platform': (7.7925, 108.2021),
            # Keep HCMC marker
            'An Phu Office (HCMC)': (10.809427, 106.736553),
            'Vung Tau Airport': (10.376001, 107.093239)
        }

        self.location_radios = {}
        for name, coords in self.locations.items():
            radio = QRadioButton(
                f"{name}      ({coords[0]:.4f}, {coords[1]:.4f})")
            self.location_radios[name] = radio
            input_layout.addWidget(radio)  # Add radio to input_layout
            radio.toggled.connect(self.toggle_gps_input)

        self.gps_radio = QRadioButton("Enter Custom GPS Coordinates:")
        self.gps_radio.toggled.connect(self.toggle_gps_input)
        input_layout.addWidget(self.gps_radio)  # Add GPS radio to input_layout

        gps_input_layout = QHBoxLayout()
        gps_input_layout.addWidget(self.lat_label)
        gps_input_layout.addWidget(self.lat_input)
        gps_input_layout.addWidget(self.lon_label)
        gps_input_layout.addWidget(self.lon_input)
        # Add GPS fields layout to input_layout
        input_layout.addLayout(gps_input_layout)

        default_location = 'An Phu Office (HCMC)'
        if default_location in self.location_radios:
            self.location_radios[default_location].setChecked(True)
        else:
            self.location_radios['Lan Tay Platform'].setChecked(True)

        # *** ADDED: Add the input_layout to the main_layout ***
        main_layout.addLayout(input_layout)

        # --- Spacer ---
        main_layout.addSpacing(15)

        # --- 2. Generate Weather Report Title ---
        # *** CORRECTED: Create a separate layout for the centered title ***
        weather_title_layout = QHBoxLayout()
        weather_title_label = QLabel("Generate Weather Report")
        weather_title_label.setFont(QFont("Arial", 11, QFont.Bold))
        weather_title_label.setAlignment(Qt.AlignCenter)
        weather_title_layout.addStretch()
        weather_title_layout.addWidget(weather_title_label)
        weather_title_layout.addStretch()
        # *** ADDED: Add the weather_title_layout to the main_layout ***
        main_layout.addLayout(weather_title_layout)

        # --- 3. Generate Weather Report Button ---
        self.weather_button = QPushButton("Generate Weather PDF Report")
        self.weather_button.clicked.connect(
            self.generate_weather_report_action)
        main_layout.addWidget(self.weather_button)

        # --- Spacer ---
        main_layout.addSpacing(15)

        # --- 4. Download Tide Report Title ---
        # *** CORRECTED: Create a separate layout for the centered title ***
        tide_title_layout = QHBoxLayout()
        tide_title_label = QLabel("Download Tide Report (HCMC)")
        tide_title_label.setFont(QFont("Arial", 11, QFont.Bold))
        tide_title_label.setAlignment(Qt.AlignCenter)
        tide_title_layout.addStretch()
        tide_title_layout.addWidget(tide_title_label)
        tide_title_layout.addStretch()
        # *** ADDED: Add the tide_title_layout to the main_layout ***
        main_layout.addLayout(tide_title_layout)

        # --- 5. Tidal Report Date Selection ---
        date_layout = QHBoxLayout()
        date_label = QLabel("Select Date:")
        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()

        main_layout.addLayout(date_layout)  # Add date selection section

        # --- 6. Download Tide Report Button ---
        self.tidal_button = QPushButton(
            "Download Tide Report for Selected Date")
        self.tidal_button.clicked.connect(self.download_tidal_report_action)
        main_layout.addWidget(self.tidal_button)

        # --- Spacer ---
        main_layout.addSpacing(10)

        # --- 7. Progress Bar ---
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)  # Initially hidden
        main_layout.addWidget(self.progress_bar)

        # --- Final Layout Setup ---
        main_layout.addStretch()  # Add stretch at the end
        self.setLayout(main_layout)
        self.toggle_gps_input()  # Set initial GPS field state

        # Adjust window height slightly more if needed
        self.resize(self.width(), 450)  # Adjust height as needed

     # --- Action for Weather Report Button ---

    def toggle_gps_input(self):
        """Enables/disables the Latitude and Longitude input fields based on GPS radio selection."""
        # Directly check the state of the gps_radio button
        is_gps_selected = self.gps_radio.isChecked()

        self.lat_input.setEnabled(is_gps_selected)
        self.lon_input.setEnabled(is_gps_selected)

        # No need to manually uncheck other radios here,
        # the radio button group behavior handles mutual exclusivity.

    def generate_weather_report_action(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return

        # --- Progress Bar Start ---
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()  # Allow UI to update
        # -------------------------

        QApplication.setOverrideCursor(Qt.WaitCursor)
        weather_data = None
        location_info = None

        try:
            print("--- Starting Weather Data Fetch for Report ---")
            self.progress_bar.setValue(10)  # Update progress
            QApplication.processEvents()

            # 1. Fetch Weather Data
            weather_data, location_info = self.fetch_weather_data(lat, lon)

            self.progress_bar.setValue(50)  # Update progress
            QApplication.processEvents()

            if not weather_data:
                if not location_info:
                    location_info = {'name': location_name_selected, 'country': 'N/A',
                                     'sunrise': 'N/A', 'sunset': 'N/A', 'timezone': DEFAULT_TIMEZONE}
                QMessageBox.warning(
                    self, "Weather Error", "Failed to fetch weather data. Report generation stopped.")
                # --- Progress Bar End (Error) ---
                # self.progress_bar.setVisible(False)
                # QApplication.restoreOverrideCursor()
                # --------------------------------
                return

            display_location_name = location_info.get(
                'name', location_name_selected)
            if "Custom GPS" in location_name_selected and location_info.get('name') != 'Unknown Location':
                display_location_name = location_info.get(
                    'name', location_name_selected)

            # --- Generate PDF Report (Weather Only) ---
            print("\nGenerating Weather PDF report...")
            self.progress_bar.setValue(70)  # Update progress
            QApplication.processEvents()

            self.generate_pdf_report(
                lat, lon,
                weather_data,
                location_info,
                display_location_name
            )

            self.progress_bar.setValue(100)  # Update progress
            QApplication.processEvents()

            QMessageBox.information(
                self, "Success", "Weather PDF report generated successfully!")

        except Exception as e:
            print(f"An error occurred during weather report generation: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred generating the weather report:\n{e}")
        finally:
            # --- Progress Bar End ---
            self.progress_bar.setVisible(False)
            QApplication.restoreOverrideCursor()
            # -----------------------
            print("--- Weather Report Process Finished ---")

    # --- Action for Tidal Download Button ---
    def download_tidal_report_action(self):
        selected_date_qdate = self.date_edit.date()
        selected_date = selected_date_qdate.toPyDate()

        # --- Progress Bar Start ---
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()
        # -------------------------

        QApplication.setOverrideCursor(Qt.WaitCursor)
        tidal_pdf_path = None  # Initialize here for broader scope
        tidal_pdf_url = None  # Initialize here for broader scope
        try:
            print(
                f"\n--- Starting Tidal PDF Download for Date: {selected_date.strftime('%d/%m/%Y')} ---")
            self.progress_bar.setValue(20)  # Update progress
            QApplication.processEvents()

            # Call the scraping function
            tidal_pdf_path, tidal_pdf_url = scrape_and_download_tidal_pdf_for_date(
                self.session, selected_date, download_dir=".")

            self.progress_bar.setValue(90)  # Update progress
            QApplication.processEvents()

            if not tidal_pdf_url:
                QMessageBox.warning(
                    self, "Tidal PDF Not Found", f"Could not find the URL for the tidal PDF report for {selected_date.strftime('%d/%m/%Y')}.")
            elif not tidal_pdf_path:
                QMessageBox.warning(
                    self, "Download Failed", f"Found tidal PDF URL, but failed to download it.\nURL: {tidal_pdf_url}")
            else:
                abs_path = os.path.abspath(tidal_pdf_path)
                QMessageBox.information(
                    self, "Download Successful", f"Tidal PDF for {selected_date.strftime('%d/%m/%Y')} downloaded successfully to:\n{abs_path}")
                print(f"Tidal PDF downloaded: {abs_path}")

            self.progress_bar.setValue(100)  # Update progress
            QApplication.processEvents()

        except Exception as e:
            print(f"An error occurred during tidal PDF download: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Download Error", f"An unexpected error occurred during download:\n{e}")
        finally:
            # --- Progress Bar End ---
            self.progress_bar.setVisible(False)
            QApplication.restoreOverrideCursor()
            # -----------------------
            print("--- Tidal Download Process Finished ---")

    def get_coordinates(self):
        if self.gps_radio.isChecked():
            try:
                lat_str = self.lat_input.text().strip()
                lon_str = self.lon_input.text().strip()
                if not lat_str or not lon_str:
                    QMessageBox.warning(self, "Input Error", "Lat/Lon empty.")
                    return None, None, None
                lat = float(lat_str)
                lon = float(lon_str)
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Lat/Lon out of range.")
                return lat, lon, f"Custom GPS ({lat:.4f}, {lon:.4f})"
            except ValueError as e:
                QMessageBox.warning(self, "Input Error",
                                    f"Invalid Lat/Lon: {e}")
                return None, None, None
        else:
            for name, radio in self.location_radios.items():
                if radio.isChecked():
                    return self.locations[name][0], self.locations[name][1], name
        QMessageBox.warning(self, "Input Error", "Select location.")
        return None, None, None

    # --- Action for Weather Report Button ---
    def generate_weather_report_action(self):  # Renamed
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return

         # --- Progress Bar Start ---
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()  # Allow UI to update

        QApplication.setOverrideCursor(Qt.WaitCursor)
        weather_data = None
        location_info = None

        try:
            print("--- Starting Weather Data Fetch for Report ---")
            weather_data, location_info = self.fetch_weather_data(lat, lon)
            if not weather_data:
                if not location_info:
                    location_info = {'name': location_name_selected, 'country': 'N/A',
                                     'sunrise': 'N/A', 'sunset': 'N/A', 'timezone': DEFAULT_TIMEZONE}
                QMessageBox.warning(
                    self, "Weather Error", "Failed to fetch weather data. Report generation stopped.")
                QApplication.restoreOverrideCursor()
                return

            display_location_name = location_info.get(
                'name', location_name_selected)
            if "Custom GPS" in location_name_selected and location_info.get('name') != 'Unknown Location':
                display_location_name = location_info.get(
                    'name', location_name_selected)

            # --- Generate PDF Report (Weather Only) ---
            print("\nGenerating Weather PDF report...")
            # Call the modified generate_pdf_report (which no longer takes tidal args)
            self.generate_pdf_report(
                lat, lon,
                weather_data,
                location_info,
                display_location_name
            )
            QMessageBox.information(
                self, "Success", "Weather PDF report generated successfully!")

        except Exception as e:
            print(f"An error occurred during weather report generation: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred generating the weather report:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()
            print("--- Weather Report Process Finished ---")

    # --- Action for Tidal Download Button ---
    def download_tidal_report_action(self):
        """Handles downloading the tidal PDF for the selected date."""
        selected_date_qdate = self.date_edit.date()
        # Convert QDate to Python datetime.date
        selected_date = selected_date_qdate.toPyDate()

        # --- Progress Bar Start ---
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()  # Allow UI to update

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            print(
                f"\n--- Starting Tidal PDF Download for Date: {selected_date.strftime('%d/%m/%Y')} ---")
            # Call the modified scraping function with the selected date
            tidal_pdf_path, tidal_pdf_url = scrape_and_download_tidal_pdf_for_date(
                self.session, selected_date, download_dir=".")

            if not tidal_pdf_url:
                QMessageBox.warning(
                    self, "Tidal PDF Not Found", f"Could not find the URL for the tidal PDF report for {selected_date.strftime('%d/%m/%Y')}.")
            elif not tidal_pdf_path:
                QMessageBox.warning(
                    self, "Download Failed", f"Found tidal PDF URL, but failed to download it.\nURL: {tidal_pdf_url}")
            else:
                abs_path = os.path.abspath(tidal_pdf_path)
                QMessageBox.information(
                    self, "Download Successful", f"Tidal PDF for {selected_date.strftime('%d/%m/%Y')} downloaded successfully to:\n{abs_path}")
                print(f"Tidal PDF downloaded: {abs_path}")

        except Exception as e:
            print(f"An error occurred during tidal PDF download: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Download Error", f"An unexpected error occurred during download:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()
            print("--- Tidal Download Process Finished ---")

    def create_requests_session(self):
        # ... (Keep implementation) ...
        session = requests.Session()
        retries = Retry(
            total=5,  # Number of retries
            backoff_factor=1,  # Delay factor (e.g., 1s, 2s, 4s, 8s, 16s)
            # Status codes to retry on
            status_forcelist=[429, 500, 502, 503, 504],
            # Methods to retry (use allowed_methods)
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=10,  # Increase pool size slightly
            pool_maxsize=10,
            pool_block=False  # Don't block if pool is full, raise exception instead
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        # Add common headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',  # Add Vietnamese preference
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
        })
        return session

    def fetch_weather_data(self, lat, lon):
        # ... (Keep implementation - no changes needed here) ...
        base_url = "https://api.openweathermap.org/data/2.5/"
        units = "metric"
        # Use the shared session: self.session
        timeout = (15, 30)  # connection, read timeout
        current_data = None
        forecast_data = None
        location_info = {  # Pre-fill defaults
            'name': f"Coords ({lat:.4f}, {lon:.4f})",
            'country': 'N/A',
            'sunrise': 'N/A',
            'sunset': 'N/A',
            'timezone': DEFAULT_TIMEZONE  # Start with default
        }

        try:
            # Get current weather for location info and sun times
            current_url = f"{base_url}weather?lat={lat}&lon={lon}&appid={self.api_key}&units={units}"
            print(f"Fetching OWM current: {current_url}")
            current_response = self.session.get(current_url, timeout=timeout)
            # Raise HTTPError for bad responses (4xx or 5xx)
            current_response.raise_for_status()
            current_data = current_response.json()

            # Get 5-day/3-hour forecast data
            # cnt=40 for 5 days * 8 points/day
            forecast_url = f"{base_url}forecast?lat={lat}&lon={lon}&appid={self.api_key}&units={units}&cnt=40"
            print(f"Fetching OWM forecast: {forecast_url}")
            forecast_response = self.session.get(forecast_url, timeout=timeout)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # --- Determine Timezone ---
            timezone_str = DEFAULT_TIMEZONE  # Default
            country_code = current_data.get('sys', {}).get('country')

            if country_code and country_code in LOCATION_TIMEZONES:
                timezone_str = LOCATION_TIMEZONES[country_code]
                print(
                    f"Using timezone from mapped country code '{country_code}': {timezone_str}")
            elif 'timezone' in current_data:
                # Try to use the timezone offset provided by OWM if country not mapped
                # This is less ideal than a proper IANA timezone name
                try:
                    offset_sec = int(current_data['timezone'])
                    # Create a fixed offset timezone object
                    fixed_tz = timezone(timedelta(seconds=offset_sec))
                    # Use pytz for consistency if possible, find matching offset (can be ambiguous)
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
                        # Fallback to fixed offset string if no pytz match found
                        offset_hours = offset_sec / 3600
                        # e.g., UTC+07:00 (Offset)
                        timezone_str = f"UTC{offset_hours:+03.0f}:00 (Offset)"
                        print(
                            f"Warning: Could not find exact pytz match for offset {offset_sec}s. Using fixed offset: {timezone_str}")
                        local_tz = fixed_tz  # Use the fixed offset object directly

                except Exception as tz_offset_err:
                    print(
                        f"Warning: Could not process timezone offset {current_data.get('timezone')}. Using default {DEFAULT_TIMEZONE}. Error: {tz_offset_err}")
                    timezone_str = DEFAULT_TIMEZONE
            else:
                print(
                    f"Warning: No country code or timezone offset from OWM. Using default {DEFAULT_TIMEZONE}.")

            # Get the actual timezone object
            try:
                if isinstance(timezone_str, str) and not "(Offset)" in timezone_str:
                    local_tz = pytz.timezone(timezone_str)
                # If it was a fixed offset, local_tz is already set
                # Ensure local_tz is set if using default
                elif not isinstance(local_tz, timezone):
                    local_tz = pytz.timezone(DEFAULT_TIMEZONE)

            except pytz.exceptions.UnknownTimeZoneError:
                print(
                    f"Error: pytz does not recognize timezone '{timezone_str}'. Falling back to {DEFAULT_TIMEZONE}.")
                timezone_str = DEFAULT_TIMEZONE
                local_tz = pytz.timezone(DEFAULT_TIMEZONE)

            print(f"Final timezone for processing: {timezone_str}")
            # Store the determined timezone string
            location_info['timezone'] = timezone_str

            # --- Update Location Info (using local_tz) ---
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

            # --- Process Forecast Data ---
            processed_forecast = self.process_forecast_data(
                forecast_data, local_tz)
            return processed_forecast, location_info

        except requests.exceptions.Timeout:
            QMessageBox.critical(
                self, "Connection Error", "Weather API request timed out. Please check internet connection.")
            # Return None for data, but keep any location info we might have gotten
            return None, location_info
        except requests.exceptions.HTTPError as e:
            err_msg = f"Weather API HTTP Error: {e}"
            if e.response is not None:
                status_code = e.response.status_code
                err_msg += f"\nStatus Code: {status_code}"
                try:  # Try to get more details from response body
                    details = e.response.json()
                    err_msg += f"\nMessage: {details.get('message', e.response.text)}"
                except json.JSONDecodeError:
                    # Show partial raw response
                    err_msg += f"\nResponse: {e.response.text[:200]}..."

                if status_code == 401:  # Unauthorized
                    err_msg = "Invalid OpenWeatherMap API Key. Please check the key in the script."
                elif status_code == 404:  # Not Found
                    err_msg = f"Location (Lat: {lat}, Lon: {lon}) not found by Weather API."
                elif status_code == 429:  # Too Many Requests
                    err_msg = "Weather API rate limit exceeded. Please wait and try again later."

            QMessageBox.critical(self, "API Error", err_msg)
            return None, location_info
        except requests.exceptions.RequestException as e:
            # Catch other connection errors (DNS, refused connection etc.)
            QMessageBox.critical(self, "Connection Error",
                                 f"Could not connect to weather service: {e}")
            return None, location_info
        except Exception as e:
            # Catch unexpected errors during processing
            print(f"Unexpected error in fetch_weather_data: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Processing Error", f"An error occurred while processing weather data: {e}")
            return None, location_info

    def process_forecast_data(self, data, local_tz):
        # ... (Keep implementation - no changes needed here) ...
        def degrees_to_direction(degrees):
            # Handle potential None or non-numeric input
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

        processed_data = []
        if not data or 'list' not in data:
            print("Warning: Forecast data is missing or invalid.")
            return processed_data

        now_local = datetime.now(local_tz)

        for item in data.get('list', []):
            try:
                # Parse UTC time and convert to local
                dt_utc = datetime.fromtimestamp(item['dt'], tz=timezone.utc)
                local_time = dt_utc.astimezone(local_tz)

                # Filter for the next 5 days (approximately) - include current day's remaining slots
                # Check if the forecast slot ENDS within the next 5 days from now
                if local_time >= now_local - timedelta(hours=3) and local_time <= now_local + timedelta(days=5, hours=3):

                    weather_desc = item.get('weather', [{}])[0].get(
                        'description', 'N/A').capitalize()
                    main_data = item.get('main', {})
                    temp = main_data.get('temp')
                    humidity = main_data.get('humidity')

                    wind_data = item.get('wind', {})
                    wind_speed_mps = wind_data.get('speed')
                    wind_speed_knots = round(
                        wind_speed_mps * 1.94384, 1) if wind_speed_mps is not None else 'N/A'

                    wind_gust_mps = wind_data.get(
                        'gust')  # Gust might be missing
                    wind_gust_knots = round(
                        wind_gust_mps * 1.94384, 1) if wind_gust_mps is not None else 'N/A'

                    wind_deg = wind_data.get('deg')
                    wind_direction = degrees_to_direction(wind_deg)

                    rain_3h = item.get('rain', {}).get(
                        '3h', 0.0)  # Default to 0.0 if missing
                    # Visibility in meters
                    visibility = item.get('visibility', 'N/A')
                    # Probability of Precipitation (%)
                    # Default to 0.0, convert to %, round
                    pop = round(item.get('pop', 0.0) * 100)

                    processed_data.append({
                        'datetime_obj': local_time,  # Store datetime object for charting
                        # Formatted string for table
                        'datetime': local_time.strftime('%Y-%m-%d %H:%M'),
                        'description': weather_desc,
                        'temperature': float(temp) if temp is not None else 'N/A',
                        'humidity': float(humidity) if humidity is not None else 'N/A',
                        'wind_speed': wind_speed_knots,
                        'wind_gust': wind_gust_knots,
                        'wind_direction': wind_direction,
                        'rain': float(rain_3h),
                        'visibility': int(visibility) if isinstance(visibility, (int, float)) else 'N/A',
                        'pop': pop
                    })
            except Exception as e:
                print(f"Error processing forecast item: {item}. Error: {e}")
                continue  # Skip this item and proceed with the next

        return processed_data

    def create_chart(self, data, param_name, ylabel, title, date_key='datetime_obj'):
        # ... (Keep implementation - no changes needed here) ...
        if not data:  # Handle empty data list
            print(f"Warning: No data provided for chart: {title}")
            return None

        plt.figure(figsize=(9.0, 2.8))  # Width, Height in inches
        dates = []
        values = []

        # Extract valid data points
        for item in data:
            item_val = item.get(param_name)
            item_date = item.get(date_key)  # Use the datetime object

            # Check if value is valid (not None, not 'N/A') and date is valid
            if item_val not in [None, 'N/A'] and isinstance(item_date, datetime):
                try:
                    # Append the datetime object directly
                    dates.append(item_date)
                    values.append(float(item_val))
                except (ValueError, TypeError) as e:
                    # print(f"Skipping chart point: Param: {param_name}, Val: {item_val}, Error: {e}")
                    continue  # Skip if value conversion fails

        if not dates or not values:
            print(
                f"Warning: No valid numeric data points found for chart: {title}")
            plt.close()  # Close the empty figure
            return None

        # Plotting
        try:
            plt.plot(dates, values, marker='.', linestyle='-',
                     markersize=4, linewidth=1)  # Smaller markers, thinner line
            plt.title(title, fontsize=10)
            plt.xlabel('Date/Time', fontsize=9)
            plt.ylabel(ylabel, fontsize=9)
            # Rotate labels, align right
            plt.xticks(rotation=30, ha='right', fontsize=9)
            plt.yticks(fontsize=9)

            # Improve date formatting on X-axis
            # Auto-format based on date range
            plt.gca().xaxis.set_major_locator(
                plt.matplotlib.dates.AutoDateLocator(minticks=4, maxticks=10))
            plt.gca().xaxis.set_major_formatter(
                plt.matplotlib.dates.ConciseDateFormatter(plt.gca().xaxis.get_major_locator()))

            plt.grid(True, linestyle='--', linewidth=0.5,
                     alpha=0.6)  # Thinner grid lines
            plt.tight_layout(pad=0.5)  # Adjust padding slightly

            # Save to BytesIO
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150,
                        bbox_inches='tight')  # Use bbox_inches='tight'
            plt.close()  # Close the figure to free memory
            img_buffer.seek(0)  # Rewind buffer

            # Create ReportLab Image
            img = Image(img_buffer, width=8.5*inch, height=2.5 *
                        inch)  # Adjust size as needed
            img.hAlign = 'CENTER'
            return img

        except Exception as chart_err:
            print(f"Error during chart plotting for '{title}': {chart_err}")
            plt.close()  # Ensure figure is closed on error
            return None

    # --- Modify generate_pdf_report (Remove tidal parameters and link section) ---

    # REMOVED tidal args
    def generate_pdf_report(self, lat, lon, weather_data, location_info, display_location_name):

        page_width, page_height = landscape(letter)
        file_name_location = re.sub(
            r'[\\/*?:"<>|()]+', "", display_location_name).replace(' ', '_')
        # Updated filename
        file_name = f"Weather_Report_{file_name_location}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

        doc = SimpleDocTemplate(
            file_name,
            pagesize=(page_width, page_height),
            topMargin=0.5*inch, bottomMargin=0.4*inch,
            leftMargin=0.5*inch, rightMargin=0.5*inch
        )

        elements = []
        styles = getSampleStyleSheet()

        # --- Define Styles ---
        title_style = styles['h1']
        title_style.alignment = 1
        title_style.fontSize = 16
        h2_style = styles['h2']
        h2_style.alignment = 0
        h2_style.fontSize = 12
        h2_style.spaceBefore = 10
        h2_style.spaceAfter = 4
        normal_style = styles['Normal']
        normal_style.leading = 14
        normal_style.fontSize = 11  # Adjusted font size
        small_note_style = styles['Normal'].clone('SmallNote')
        small_note_style.fontSize = 9
        small_note_style.leading = 9
        small_note_style.textColor = colors.dimgray
        footer_style = small_note_style.clone('Footer')
        footer_style.alignment = 1
        footer_style.fontSize = 8
        # link_style removed

        # --- Report Header ---
        elements.append(Paragraph("Weather Forecast Report", title_style))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(
            f"<b>Location:</b> {display_location_name} ({location_info.get('country', 'N/A')})", normal_style))
        elements.append(
            Paragraph(f"<b>Coordinates:</b> Lat: {lat:.4f}, Lon: {lon:.4f}", normal_style))
        elements.append(Paragraph(
            f"<b>Timezone:</b> {location_info.get('timezone', DEFAULT_TIMEZONE)}", normal_style))
        elements.append(Paragraph(
            f"<b>Sunrise:</b> {location_info.get('sunrise', 'N/A')}, <b>Sunset:</b> {location_info.get('sunset', 'N/A')}", normal_style))
        elements.append(Paragraph(
            f"<b>Report Generated:</b> {datetime.now(pytz.timezone(location_info.get('timezone', DEFAULT_TIMEZONE))).strftime('%Y-%m-%d %H:%M:%S %Z')}", normal_style))
        elements.append(Spacer(1, 0.2*inch))

        # --- Weather Forecast Table ---
        if weather_data:
            elements.append(
                Paragraph("Weather Forecast (Next 5 Days)", h2_style))
            # ... (Keep weather table generation logic: headers, data loop, widths, style) ...
            weather_headers = ["Date/Time", "Description", "Temp\n(°C)", "Humidity\n(%)", "Wind Speed\n(knots)",
                               "Wind Gust\n(knots)", "Wind\nDir", "Rain\n(mm)", "PoP\n(%)", "Visibility\n(m)"]
            weather_table_data = [weather_headers]
            for item in weather_data:
                vis = item['visibility']
                vis_formatted = f"{int(vis):,}" if vis != 'N/A' else 'N/A'
                temp_val = item['temperature']
                temp_formatted = f"{temp_val:.1f}" if isinstance(
                    temp_val, (int, float)) else 'N/A'
                hum_val = item['humidity']
                hum_formatted = f"{hum_val:.0f}" if isinstance(
                    hum_val, (int, float)) else 'N/A'
                wind_val = item['wind_speed']
                wind_formatted = f"{wind_val:.1f}" if isinstance(
                    wind_val, (int, float)) else 'N/A'
                gust_val = item['wind_gust']
                gust_formatted = str(gust_val)
                rain_val = item['rain']
                rain_formatted = f"{rain_val:.1f}" if isinstance(
                    rain_val, (int, float)) else 'N/A'
                pop_val = item['pop']
                pop_formatted = f"{pop_val:.0f}" if isinstance(
                    pop_val, (int, float)) else 'N/A'
                row = [item['datetime'], item['description'], temp_formatted, hum_formatted, wind_formatted,
                       gust_formatted, item['wind_direction'], rain_formatted, pop_formatted, vis_formatted]
                weather_table_data.append(row)
            weather_col_widths = [1.3*inch, 1.6*inch, 0.6*inch, 0.7*inch,
                                  0.8*inch, 0.8*inch, 0.5*inch, 0.6*inch, 0.5*inch, 0.8*inch]
            weather_table = Table(weather_table_data,
                                  repeatRows=1, colWidths=weather_col_widths)
            weather_style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 8), ('BOTTOMPADDING', (0, 0), (-1, 0), 6), ('TOPPADDING', (0, 0), (-1, 0), 4), ('FONTNAME',
                                       (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 7.5), ('TOPPADDING', (0, 1), (-1, -1), 3), ('BOTTOMPADDING', (0, 1), (-1, -1), 3), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ALIGN', (2, 1), (3, -1), 'RIGHT'), ('ALIGN', (4, 1), (5, -1), 'RIGHT'), ('ALIGN', (7, 1), (9, -1), 'RIGHT'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightblue])])
            weather_table.setStyle(weather_style)
            elements.append(weather_table)
            elements.append(
                Paragraph("PoP = Probability of Precipitation.", small_note_style))
            elements.append(Spacer(1, 0.15*inch))
        else:
            elements.append(
                Paragraph("Weather Forecast Data Not Available", h2_style))
            elements.append(Spacer(1, 0.15*inch))

        # --- REMOVED Tidal PDF Link Section ---

        # --- Weather Charts ---
        if weather_data:
            elements.append(Paragraph("Weather Parameter Charts", h2_style))
            # ... (Keep chart generation logic) ...
            chart_params = [('temperature', 'Temperature (°C)', 'Temperature Trend'), ('humidity', 'Humidity (%)', 'Humidity Trend'), (
                'wind_speed', 'Wind Speed (knots)', 'Wind Speed Trend'), ('pop', 'Probability (%)', 'Precipitation Probability Trend'),]
            charts_added = 0
            for param, unit, title in chart_params:
                has_data = any(item.get(param) not in [None, 'N/A'] and isinstance(
                    item.get('datetime_obj'), datetime) for item in weather_data)
                if has_data:
                    chart = self.create_chart(weather_data, param, unit, title)
                    if chart:
                        elements.append(chart)
                        elements.append(Spacer(1, 0.05*inch))
                        charts_added += 1
            if charts_added == 0:
                elements.append(
                    Paragraph("No data available to generate weather charts.", normal_style))
            elements.append(Spacer(1, 0.1*inch))

        # --- Footer ---
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("--- Report End ---", footer_style))
        # Updated footer text
        # Removed tidal source
        elements.append(
            Paragraph("Weather data © OpenWeatherMap", footer_style))
        elements.append(
            Paragraph("Generated by Weather Reporter Tool | 2025 © TungTT", footer_style))

        # Build the PDF
        try:
            doc.build(elements)
            print(f"PDF report generated: {file_name}")
        except Exception as build_err:
            print(f"Error building PDF: {build_err}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "PDF Error", f"Could not build PDF report:\n{build_err}")

    def closeEvent(self, event):
        # ... (Keep implementation) ...
        if hasattr(self, 'session') and self.session:
            self.session.close()
            print("Requests session closed.")
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    weather_app = WeatherCrawlerApp()
    weather_app.show()
    sys.exit(app.exec_())
