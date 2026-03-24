# -*- coding: utf-8 -*-
# Add this line at the top for better Unicode handling

import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QRadioButton,
                             QMessageBox)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QDate  # Import QDate for default date handling
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import ImageReader
import requests
import json
from datetime import datetime, timedelta, timezone, date  # Import date
import pytz
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import matplotlib.pyplot as plt
from io import BytesIO
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import tempfile  # Needed for PDF download
import PyPDF2  # Needed for PDF processing


# --- Tidal Data Scraping Dependencies (from ScrapeWorker.py) ---
# No direct PyQt5 imports needed here as we run it synchronously

# --- End Tidal Data Dependencies ---


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


# --- Tidal Data Scraping Functions (Adapted from ScrapeWorker) ---

def _extract_tidal_data_from_pdf(pdf_path):
    """Extract Phu An peak water level data from PDF (returns level in cm or error string)."""
    print(f"Extracting data from PDF: {pdf_path}")
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                try:
                    text += page.extract_text() or ""  # Ensure text is not None
                except Exception as extract_err:
                    print(
                        f"Warning: Error extracting text from page {page_num}: {extract_err}")
                    continue  # Try next page

        if not text:
            print("Warning: No text could be extracted from the PDF.")
            return "Extraction Error"

        print(
            f"Searching for Phú An data in PDF text (first 500 chars): {text[:500]}")

        # Pattern 1: Look for "Phú An" followed by a number and "cm" (more robust)
        # Match "Phú An", optional space/colon/tab, optional text like "(cao nhất)", optional space/tab,
        # a number (potentially with comma/dot decimal), optional space, "cm".
        # Capture the number part. Allows for variations like "Phú An: 155 cm", "Phú An (cao nhất) 1.55m" (though we expect cm)
        phu_an_pattern = r"Ph[úu]\s*An(?:\s*:)?(?:\s*\(.*?\))?\s*.*?([\d.,]+)\s*cm"
        match = re.search(phu_an_pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            peak_level_str = match.group(1).replace(
                ',', '.')  # Normalize decimal separator
            try:
                peak_level_cm = float(peak_level_str)
                # If the value seems like meters (e.g., 1.55), convert to cm
                if peak_level_cm < 10:
                    peak_level_cm *= 100
                print(
                    f"Found peak water level (Pattern 1): {peak_level_cm} cm")
                # Return as integer string
                return str(int(round(peak_level_cm)))
            except ValueError:
                print(
                    f"Could not convert found value '{match.group(1)}' to number.")

        # Pattern 2: Try a table format where Phu An might be in a row/column
        # Looking for "Phú An" followed by spaces/tabs then a number.
        table_pattern = r"Ph[úu]\s*An\s+([\d.,]+)"
        match = re.search(table_pattern, text, re.IGNORECASE)
        if match:
            peak_level_str = match.group(1).replace(',', '.')
            try:
                peak_level_cm = float(peak_level_str)
                if peak_level_cm < 10:
                    peak_level_cm *= 100
                print(
                    f"Found peak water level (Pattern 2 - Table): {peak_level_cm} cm")
                return str(int(round(peak_level_cm)))
            except ValueError:
                print(
                    f"Could not convert found value '{match.group(1)}' to number.")

        # Pattern 3: Broader search if specific structure fails
        # Look for "Phú An", then up to 150 chars later, a number, optionally followed by "cm"
        broader_pattern = r"Ph[úu]\s*An.{0,150}?([\d.,]+)(?:\s*cm)?"
        match = re.search(broader_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            peak_level_str = match.group(1).replace(',', '.')
            try:
                peak_level_cm = float(peak_level_str)
                if peak_level_cm < 10:
                    peak_level_cm *= 100
                print(
                    f"Found peak water level (Pattern 3 - Broader): {peak_level_cm} cm")
                return str(int(round(peak_level_cm)))
            except ValueError:
                print(
                    f"Could not convert found value '{match.group(1)}' to number.")

        print("Could not find Phú An peak water level data in the PDF")
        return "Not Found"

    except FileNotFoundError:
        print(f"Error: PDF file not found at {pdf_path}")
        return "File Error"
    except Exception as e:
        print(f"Error extracting PDF data: {str(e)}")
        return "Extraction Error"


def fetch_tidal_data_for_date(target_date, session):
    """Fetches the Phu An tidal data for a specific date."""
    print(
        f"\n--- Fetching tidal data for {target_date.strftime('%d-%m-%Y')} ---")
    # Format date for URL and searching
    date_str = target_date.strftime("%d-%m-%Y")
    day_str = target_date.strftime("%d")
    month_str = target_date.strftime("%m")
    year_str = target_date.strftime("%yyyy")

    # Set up headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'http://www.kttv-nb.org.vn/',
        'Connection': 'keep-alive'
    }
    timeout = (15, 30)  # connection, read timeout

    # Step 1: Find the article URL for the date
    print(f"Searching for article with date: {date_str}")
    date_patterns = [
        f"{day_str}-{month_str}-{year_str}",
        f"{day_str}/{month_str}/{year_str}",
        f"ngày {day_str}/{month_str}/{year_str}",
    ]
    base_url = "http://www.kttv-nb.org.vn"
    main_url = f"{base_url}/index.php/thong-tin-kttv/thuy-van"
    article_url = None
    max_pages = 3  # Check fewer pages to speed up

    for page_num in range(max_pages):
        page_url = f"{main_url}?start={page_num * 10}" if page_num > 0 else main_url
        print(f"Checking page {page_num+1}: {page_url}")
        try:
            response = session.get(page_url, headers=headers, timeout=timeout)
            if response.status_code != 200:
                print(
                    f"Failed page {page_num+1} access. Status: {response.status_code}")
                continue

            # Use response.content for encoding
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)  # Ensure href exists
            for link in links:
                title = link.get_text(strip=True)
                href = link['href']
                # Prioritize links containing the exact date string
                if any(pattern in title for pattern in date_patterns):
                    article_url = href
                    print(f"Found potential article: {title} - {href}")
                    break
            if article_url:
                break
        except requests.exceptions.RequestException as e:
            print(f"Error accessing page {page_num+1}: {str(e)}")
        except Exception as e:
            print(f"Error parsing page {page_num+1}: {str(e)}")

    if article_url:
        article_url = urljoin(base_url, article_url)  # Make URL absolute
        print(f"Found article URL: {article_url}")
    else:
        # Try a fallback using common patterns if search fails
        # Example: /index.php/thong-tin-kttv/thuy-van/100-thong-tin-kttv/thuy-van/23105-tin-da-ba-o-tha-y-v-n-tp-hcm-nga-y-07-04-2025
        # This part is tricky as the ID (23105) changes. We might need a broader search or direct PDF guess.
        # Let's try guessing the PDF URL directly as a primary fallback.
        print("Could not find article link via title search. Trying direct PDF guess.")
        # Fallback to known PDF URL pattern is more reliable if article search fails
        formatted_date_pdf = target_date.strftime("%Y%m%d")
        # Placeholder ID
        pdf_link = f"{base_url}/attachments/article/placeholder/HCMC_TVHN_{formatted_date_pdf}.pdf"
        # We need to find the article ID somehow, or hope the direct link structure is stable.
        # Let's skip article search for now and go straight to PDF guessing if direct link fails
        # This requires knowing the PDF naming convention.

    # Step 2: Access article or guess PDF link
    pdf_link_found = None
    if article_url:
        print(f"Accessing article page to find PDF link: {article_url}")
        try:
            article_response = session.get(
                article_url, headers=headers, timeout=timeout)
            if article_response.status_code == 200:
                article_soup = BeautifulSoup(
                    article_response.content, 'html.parser')
                content_div = article_soup.find(
                    'div', class_='item-page')  # Common Joomla content area
                pdf_links = []
                if content_div:
                    pdf_links = content_div.find_all(
                        'a', href=lambda href: href and href.lower().endswith('.pdf'))
                if not pdf_links:  # Search whole page if not in content div
                    pdf_links = article_soup.find_all(
                        'a', href=lambda href: href and href.lower().endswith('.pdf'))

                if pdf_links:
                    # Try to find link containing the date string for better accuracy
                    best_pdf_link = None
                    date_pdf_str = target_date.strftime("%Y%m%d")
                    for pdf_a in pdf_links:
                        if date_pdf_str in pdf_a['href']:
                            best_pdf_link = pdf_a['href']
                            break
                    if best_pdf_link:
                        pdf_link_found = urljoin(base_url, best_pdf_link)
                        print(
                            f"Found specific PDF link in article: {pdf_link_found}")
                    else:
                        # Fallback to first PDF
                        pdf_link_found = urljoin(
                            base_url, pdf_links[0]['href'])
                        print(
                            f"Found generic PDF link in article: {pdf_link_found}")
                else:
                    print("No direct PDF link found in article content.")
            else:
                print(
                    f"Failed to access article page. Status: {article_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error accessing article page {article_url}: {str(e)}")
        except Exception as e:
            print(f"Error parsing article page {article_url}: {str(e)}")

    # If no PDF link found via article, try the direct guess pattern
    if not pdf_link_found:
        formatted_date_pdf = target_date.strftime("%Y%m%d")
        # We need to find the article ID - this is the hard part. Let's *assume* the ID changes predictably or search results give it.
        # Since we don't have the article ID reliably, this guess is weak.
        # A better guess might ignore the ID part:
        guessed_pdf_link = f"{base_url}/attachments/HCMC_TVHN_{formatted_date_pdf}.pdf"
        # A more specific (but potentially fragile) guess based on observed patterns:
        # We need the article ID, e.g., 23105. How to get this reliably without scraping list pages? Very difficult.
        # Let's try a request to the guessed link and see if it works.
        # Generic path attempt
        potential_link = f"{base_url}/attachments/article/unknown/HCMC_TVHN_{formatted_date_pdf}.pdf"
        print(
            f"Attempting direct PDF guess (pattern): HCMC_TVHN_{formatted_date_pdf}.pdf")
        # For now, let's assume the direct guess requires manual ID finding if the website structure is unstable.
        # We will rely on the scraping finding the link first. If not, return error.
        print("PDF link not found via scraping. Cannot proceed with direct guess reliably without article ID.")
        return "PDF Link Not Found", None

    # Step 3: Download the PDF
    print(f"Downloading PDF from: {pdf_link_found}")
    tmp_path = None
    try:
        # Stream=True for large files
        pdf_response = session.get(
            pdf_link_found, headers=headers, timeout=timeout, stream=True)
        if pdf_response.status_code == 200:
            content_type = pdf_response.headers.get('Content-Type', '').lower()
            if 'application/pdf' in content_type or pdf_link_found.lower().endswith('.pdf'):
                # Save PDF to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        tmp_file.write(chunk)
                    tmp_path = tmp_file.name
                print(f"PDF saved to temporary file: {tmp_path}")
                # Extract data
                peak_level_cm = _extract_tidal_data_from_pdf(tmp_path)
                # Return level (cm) and source URL
                return peak_level_cm, pdf_link_found
            else:
                print(
                    f"Downloaded content might not be a PDF. Content-Type: {content_type}")
                return "Download Error (Not PDF)", pdf_link_found
        else:
            print(
                f"Failed to download PDF. Status: {pdf_response.status_code}")
            # Try the other guessed link if the first failed (less reliable)
            # print(f"Trying fallback PDF pattern: {guessed_pdf_link}")
            # pdf_response = session.get(guessed_pdf_link, headers=headers, timeout=timeout)
            # ... (repeat download and check logic) ...
            return f"Download Error ({pdf_response.status_code})", pdf_link_found

    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {str(e)}")
        return "Download Error", pdf_link_found
    except Exception as e:
        print(
            f"An unexpected error occurred during PDF download/processing: {e}")
        return "Processing Error", pdf_link_found
    finally:
        # Clean up temp file if it exists
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                print(f"Temporary file deleted: {tmp_path}")
            except Exception as e:
                print(f"Error deleting temporary file {tmp_path}: {e}")

    # Should not reach here if successful, but as a fallback
    return "Unknown Error", pdf_link_found


def fetch_tidal_forecast(start_date, num_days, session):
    """Fetches tidal data for a range of dates."""
    tidal_data = {}
    source_url = None  # Store the URL of the latest successful PDF
    for i in range(num_days):
        current_date = start_date + timedelta(days=i)
        level, url = fetch_tidal_data_for_date(current_date, session)
        tidal_data[current_date.strftime('%Y-%m-%d')] = level
        # Store last good URL
        if not isinstance(level, str) or "Error" not in level and "Not Found" not in level:
            source_url = url
            # We assume the *latest* report contains forecasts for subsequent days.
            # So, once we find a valid PDF, we might only need to parse that one.
            # Let's fetch just the *first* day for now, assuming it contains the forecast.
            print(
                "Found valid tidal data PDF. Assuming it contains the forecast for subsequent days.")
            break  # Exit loop after first successful fetch

    # Placeholder: Currently, we only extract *one* value per PDF.
    # To get the forecast for multiple days *from one PDF*, the PDF parsing logic
    # in _extract_tidal_data_from_pdf needs significant enhancement to find
    # data associated with specific future dates within the PDF text.
    # For now, we will just report the single value found for the *start_date*.
    # We'll add placeholder entries for future dates.

    first_day_level = tidal_data.get(start_date.strftime('%Y-%m-%d'), "Error")

    # Create placeholder results for the forecast period
    forecast_results = {}
    for i in range(num_days):
        current_date_str = (start_date + timedelta(days=i)
                            ).strftime('%Y-%m-%d')
        if i == 0:
            forecast_results[current_date_str] = {
                'level_cm': first_day_level, 'source': source_url}
        else:
            # Mark subsequent days as needing enhanced parsing
            forecast_results[current_date_str] = {
                'level_cm': "Parse PDF", 'source': source_url}

    # --- !!! IMPORTANT DEVELOPMENT NOTE !!! ---
    # The current PDF parsing only gets *one* value. To get the full 5-day forecast,
    # `_extract_tidal_data_from_pdf` needs to be rewritten to find a table or list
    # containing dates and corresponding peak levels within the PDF text.
    # This requires analyzing the PDF structure and using more complex regex or table extraction logic.
    # The current implementation provides the structure but needs the parsing enhancement.
    # For demonstration, we'll show the fetched value for day 1 and placeholders.
    # --- !!! END NOTE !!! ---

    print(
        f"Tidal forecast results (requires enhanced PDF parsing): {forecast_results}")
    return forecast_results


# --- End Tidal Data Scraping Functions ---


class WeatherCrawlerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather Reporter")
        # Adjusted size for better layout
        self.setGeometry(200, 200, 600, 300)

        # Add window icon
        icon_path = "weather_icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file {icon_path} not found")

        self.default_lat = 7.5783
        self.default_lon = 108.8694

        # Replace with your API key - DONE
        self.api_key = "e1a69775e0d7c149a4e2bdb69bb59a82"  # Replace with your actual key

        self.initUI()
        self.session = self.create_requests_session()  # Create session once

    # def initUI(self):
    #     main_layout = QVBoxLayout()

    #     # Input Options Section
    #     input_layout = QVBoxLayout()
    #     input_label = QLabel("Locations:")
    #     input_label.setFont(QFont("Arial", 12, QFont.Bold))
    #     input_layout.addWidget(input_label)

    #     # --- Location Selection ---
    #     self.lat_label = QLabel("Latitude:")
    #     self.lat_input = QLineEdit()
    #     self.lon_label = QLabel("Longitude:")
    #     self.lon_input = QLineEdit()
    #     self.lat_input.setEnabled(False)
    #     self.lon_input.setEnabled(False)

    #     # Define locations first
    #     self.locations = {
    #         'Lan Tay Platform': (7.5783, 108.8694),
    #         'Rong Doi Platform': (7.7925, 108.2021),
    #         'An Phu Office': (10.809427, 106.736553),
    #         'Vung Tau Airport': (10.376001, 107.093239)
    #     }

    #     # Add predefined locations radio buttons
    #     self.location_radios = {}
    #     for name, coords in self.locations.items():
    #         radio = QRadioButton(f"{name}      ({coords[0]}, {coords[1]})")
    #         self.location_radios[name] = radio
    #         input_layout.addWidget(radio)
    #         radio.toggled.connect(self.toggle_gps_input)

    #     # Set default selection
    #     self.location_radios['Lan Tay Platform'].setChecked(True)

    #     # GPS Radio button group
    #     self.gps_radio = QRadioButton("Enter GPS Coordinates:")
    #     self.gps_radio.toggled.connect(self.toggle_gps_input)
    #     input_layout.addWidget(self.gps_radio)

    #     gps_input_layout = QHBoxLayout()
    #     gps_input_layout.addWidget(self.lat_label)
    #     gps_input_layout.addWidget(self.lat_input)
    #     gps_input_layout.addWidget(self.lon_label)
    #     gps_input_layout.addWidget(self.lon_input)
    #     input_layout.addLayout(gps_input_layout)

    #     # Result Options Section
    #     result_label_layout = QHBoxLayout()
    #     result_label = QLabel("Create Report")
    #     result_label.setFont(QFont("Arial", 12, QFont.Bold))
    #     result_label.setAlignment(Qt.AlignCenter)
    #     result_label_layout.addStretch()
    #     result_label_layout.addWidget(result_label)
    #     result_label_layout.addStretch()

    #     # Crawl Button
    #     crawl_button = QPushButton("Crawl Weather & Tidal Data - Generate PDF")
    #     crawl_button.clicked.connect(
    #         self.crawl_and_generate_report)  # Updated connect

    #     main_layout.addLayout(input_layout)
    #     # Add the centered label layout
    #     main_layout.addLayout(result_label_layout)
    #     main_layout.addWidget(crawl_button)

    #     self.setLayout(main_layout)

    def initUI(self):
        main_layout = QVBoxLayout()

        # Input Options Section
        input_layout = QVBoxLayout()
        input_label = QLabel("Locations:")
        input_label.setFont(QFont("Arial", 12, QFont.Bold))
        input_layout.addWidget(input_label)

        # --- Location Selection ---
        self.lat_label = QLabel("Latitude:")
        self.lat_input = QLineEdit()
        self.lon_label = QLabel("Longitude:")
        self.lon_input = QLineEdit()
        self.lat_input.setEnabled(False)
        self.lon_input.setEnabled(False)

        # Define locations first
        self.locations = {
            'Lan Tay Platform': (7.5783, 108.8694),
            'Rong Doi Platform': (7.7925, 108.2021),
            'An Phu Office': (10.809427, 106.736553),
            'Vung Tau Airport': (10.376001, 107.093239)
        }

        # Add predefined locations radio buttons
        self.location_radios = {}
        for name, coords in self.locations.items():
            radio = QRadioButton(f"{name}      ({coords[0]}, {coords[1]})")
            self.location_radios[name] = radio
            input_layout.addWidget(radio)
            # radio.toggled.connect(self.toggle_gps_input) # <--- MOVE THIS CONNECTION

        # GPS Radio button group
        self.gps_radio = QRadioButton("Enter GPS Coordinates:")
        # self.gps_radio.toggled.connect(self.toggle_gps_input) # <--- MOVE THIS CONNECTION
        input_layout.addWidget(self.gps_radio)

        gps_input_layout = QHBoxLayout()
        gps_input_layout.addWidget(self.lat_label)
        gps_input_layout.addWidget(self.lat_input)
        gps_input_layout.addWidget(self.lon_label)
        gps_input_layout.addWidget(self.lon_input)
        input_layout.addLayout(gps_input_layout)

        # Set default selection (AFTER all radio buttons are created)
        self.location_radios['Lan Tay Platform'].setChecked(True)

        # --- Connect Signals AFTER all radio buttons exist ---
        self.gps_radio.toggled.connect(self.toggle_gps_input)
        for radio in self.location_radios.values():
            radio.toggled.connect(self.toggle_gps_input)
        # ----------------------------------------------------

        # Result Options Section
        result_label_layout = QHBoxLayout()
        result_label = QLabel("Create Report")
        result_label.setFont(QFont("Arial", 12, QFont.Bold))
        result_label.setAlignment(Qt.AlignCenter)
        result_label_layout.addStretch()
        result_label_layout.addWidget(result_label)
        result_label_layout.addStretch()

        # Crawl Button
        crawl_button = QPushButton("Crawl Weather & Tidal Data - Generate PDF")
        crawl_button.clicked.connect(
            self.crawl_and_generate_report)  # Updated connect

        main_layout.addLayout(input_layout)
        # Add the centered label layout
        main_layout.addLayout(result_label_layout)
        main_layout.addWidget(crawl_button)

        self.setLayout(main_layout)

    def toggle_gps_input(self):
        is_gps_checked = self.gps_radio.isChecked()
        self.lat_input.setEnabled(is_gps_checked)
        self.lon_input.setEnabled(is_gps_checked)
        # Uncheck GPS if a location is selected
        if not is_gps_checked:
            for radio in self.location_radios.values():
                if radio.isChecked():  # Find the selected location radio
                    # self.gps_radio.setChecked(False) # This creates infinite loop if connected both ways
                    break
        # Ensure only one option is checked conceptually
        # The QRadioButton group behavior handles this visually

    def get_coordinates(self):
        if self.gps_radio.isChecked():
            try:
                lat_str = self.lat_input.text().strip()
                lon_str = self.lon_input.text().strip()
                if not lat_str or not lon_str:
                    QMessageBox.warning(
                        self, "Input Error", "Latitude and Longitude cannot be empty.")
                    return None, None, "Custom GPS"
                lat = float(lat_str)
                lon = float(lon_str)
                return lat, lon, "Custom GPS Coordinates"
            except ValueError:
                QMessageBox.warning(
                    self, "Input Error", "Invalid Latitude or Longitude. Please enter numbers.")
                return None, None, None
        else:
            for name, radio in self.location_radios.items():
                if radio.isChecked():
                    # Return lat, lon, name
                    return self.locations[name][0], self.locations[name][1], name
        # Fallback if somehow nothing is selected (shouldn't happen with default)
        QMessageBox.warning(self, "Input Error",
                            "Please select a location option.")
        return None, None, None

    def crawl_and_generate_report(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return

        # Show busy cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            print("--- Starting Data Fetch ---")
            # 1. Fetch Weather Data
            print("Fetching weather data...")
            weather_data, location_info = self.fetch_weather_data(lat, lon)
            if not weather_data:
                QMessageBox.warning(
                    self, "Error", "Failed to fetch weather data.")
                return  # Stop if weather fails

            # If GPS coords were entered, use the name from weather API if available
            if location_name_selected == "Custom GPS Coordinates":
                display_location_name = location_info.get('name', 'Custom GPS')
            else:
                display_location_name = location_name_selected

            # 2. Fetch Tidal Data (for today + 4 days = 5 days total)
            print("\nFetching tidal data...")
            today = date.today()
            # Use the shared session
            tidal_forecast = fetch_tidal_forecast(today, 5, self.session)

            # 3. Generate PDF Report
            print("\nGenerating PDF report...")
            self.generate_pdf_report(
                lat, lon, weather_data, location_info, display_location_name, tidal_forecast
            )
            QMessageBox.information(
                self, "Success", f"Weather & Tidal data processed.\nPDF report generated successfully!")

        except Exception as e:
            print(f"An error occurred: {e}")  # Print detailed error to console
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred:\n{e}")
        finally:
            # Restore cursor
            QApplication.restoreOverrideCursor()
            print("--- Process Finished ---")

    def create_requests_session(self):
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504, 408, 429],
            # Changed to allowed_methods from method_whitelist
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=5,  # Increased pool size
            pool_maxsize=10,
            pool_block=True
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        # Add common headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        return session

    def fetch_weather_data(self, lat, lon):
        base_url = "https://api.openweathermap.org/data/2.5/"
        units = "metric"
        # Use the shared session
        # session = self.create_requests_session() # Now created in __init__
        timeout = (15, 30)

        try:
            # Get current weather for location info and sun times
            current_url = f"{base_url}weather?lat={lat}&lon={lon}&appid={self.api_key}&units={units}"
            current_response = self.session.get(current_url, timeout=timeout)
            current_response.raise_for_status()
            current_data = current_response.json()

            # Get forecast data
            # cnt=40 for 5 days * 8 points/day
            forecast_url = f"{base_url}forecast?lat={lat}&lon={lon}&appid={self.api_key}&units={units}&cnt=40"
            forecast_response = self.session.get(forecast_url, timeout=timeout)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # Determine timezone
            country_code = current_data.get('sys', {}).get('country')
            timezone_str = DEFAULT_TIMEZONE  # Default
            if country_code and country_code in LOCATION_TIMEZONES:
                timezone_str = LOCATION_TIMEZONES[country_code]
            elif 'timezone' in current_data:  # Use timezone offset if country not mapped
                try:
                    # Convert offset seconds to timezone string if possible (complex)
                    # For simplicity, stick to mapped or default for now
                    offset_sec = int(current_data['timezone'])
                    # Find matching pytz timezone (can be slow)
                    # Alternatives: Use timezonefinder library (needs install) or stick to default
                    # tz_name = tf.timezone_at(lng=lon, lat=lat)
                    # if tz_name: timezone_str = tz_name
                    print(
                        f"Warning: Country code '{country_code}' not in map and timezone offset used. Time formatting might use default {DEFAULT_TIMEZONE}.")
                except Exception:
                    print(
                        f"Warning: Could not process timezone offset {current_data.get('timezone')}. Using default {DEFAULT_TIMEZONE}.")

            local_tz = pytz.timezone(timezone_str)
            print(f"Using Timezone: {timezone_str}")

            location_info = {
                'name': current_data.get('name', 'Unknown Location'),
                'country': current_data.get('sys', {}).get('country', 'N/A'),
                'sunrise': datetime.fromtimestamp(current_data['sys']['sunrise'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M') if 'sunrise' in current_data.get('sys', {}) else 'N/A',
                'sunset': datetime.fromtimestamp(current_data['sys']['sunset'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M') if 'sunset' in current_data.get('sys', {}) else 'N/A',
                'timezone': timezone_str  # Store the determined timezone
            }

            processed_forecast = self.process_forecast_data(
                forecast_data, local_tz)
            return processed_forecast, location_info

        except requests.exceptions.Timeout:
            QMessageBox.critical(
                self, "Connection Error", "Weather API request timed out. Please check internet connection.")
            return None, None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                QMessageBox.critical(
                    self, "API Error", "Invalid OpenWeatherMap API Key. Please check the key in the script.")
            elif e.response.status_code == 404:
                QMessageBox.critical(
                    self, "API Error", f"Location (Lat: {lat}, Lon: {lon}) not found by Weather API.")
            else:
                QMessageBox.critical(
                    self, "API Error", f"Weather API HTTP Error: {e}")
            return None, None
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error",
                                 f"Could not connect to weather service: {e}")
            return None, None
        # Removed session.close() as we reuse the session

    def process_forecast_data(self, data, local_tz):
        def degrees_to_direction(degrees):
            directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE',
                          'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
            index = round(degrees / (360 / len(directions))) % len(directions)
            return directions[index]

        processed_data = []
        now_local = datetime.now(local_tz)

        for item in data.get('list', []):
            try:
                # Parse UTC time and convert to local
                dt_utc = datetime.fromtimestamp(item['dt'], tz=timezone.utc)
                local_time = dt_utc.astimezone(local_tz)

                # Filter for the next 5 days (approximately)
                # Include slightly more than 5 days
                if local_time >= now_local and local_time <= now_local + timedelta(days=5, hours=3):
                    weather_desc = item['weather'][0]['description'].capitalize(
                    )
                    temp = float(item['main']['temp'])
                    humidity = float(item['main']['humidity'])
                    wind_speed_mps = float(item['wind']['speed'])
                    wind_speed_knots = wind_speed_mps * 1.94384  # knots

                    wind_gust_knots = 'N/A'
                    if 'gust' in item['wind']:
                        try:
                            wind_gust_knots = round(
                                float(item['wind']['gust']) * 1.94384, 1)
                        except (ValueError, TypeError):
                            pass  # Keep N/A if conversion fails

                    wind_deg = item['wind']['deg']
                    wind_direction = degrees_to_direction(wind_deg)
                    rain_3h = float(item.get('rain', {}).get('3h', 0))
                    # Keep as is, might not be number
                    visibility = item.get('visibility', 'N/A')
                    # Probability of Precipitation (%)
                    pop = float(item.get('pop', 0)) * 100

                    processed_data.append({
                        'datetime_obj': local_time,  # Store datetime object
                        # Formatted string
                        'datetime': local_time.strftime('%Y-%m-%d %H:%M'),
                        'description': weather_desc,
                        'temperature': temp,
                        'humidity': humidity,
                        'wind_speed': round(wind_speed_knots, 1),
                        'wind_gust': wind_gust_knots,
                        'wind_direction': wind_direction,
                        'rain': rain_3h,
                        'visibility': visibility,
                        'pop': pop
                    })
            except Exception as e:
                print(f"Error processing forecast item: {item}. Error: {e}")
                continue

        return processed_data

    def create_chart(self, data, param_name, ylabel, title, date_key='datetime_obj'):  # Use datetime_obj
        """Generates a chart and returns a ReportLab Image object."""
        plt.figure(figsize=(8.5, 2.8))
        dates = []
        values = []

        for item in data:
            item_val = item.get(param_name)
            item_date = item.get(date_key)  # Use the datetime object
            if item_val != 'N/A' and item_date is not None:
                try:
                    # Append the datetime object directly
                    dates.append(item_date)
                    values.append(float(item_val))
                except (ValueError, TypeError) as e:
                    print(
                        f"Skipping chart point: Param: {param_name}, Val: {item_val}, Error: {e}")
                    continue

        if not dates or not values:
            print(f"Warning: No valid data for chart: {title}")
            plt.close()
            return None

        plt.plot(dates, values, marker='.', linestyle='-',
                 markersize=4)  # Smaller markers
        plt.title(title, fontsize=10)
        plt.xlabel('Date/Time', fontsize=8)
        plt.ylabel(ylabel, fontsize=8)
        plt.xticks(rotation=30, ha='right', fontsize=7)
        plt.yticks(fontsize=7)
        plt.gca().xaxis.set_major_formatter(
            plt.matplotlib.dates.DateFormatter('%m-%d %H:%M'))  # Format dates on axis
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout(pad=0.5)  # Adjust padding

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        img_buffer.seek(0)

        img = Image(img_buffer, width=7.5*inch, height=2.5*inch)
        img.hAlign = 'CENTER'
        return img

    def generate_pdf_report(self, lat, lon, weather_data, location_info, display_location_name, tidal_forecast):

        page_width, page_height = landscape(letter)  # Use standard landscape
        file_name_location = re.sub(
            r'[\\/*?:"<>|]', "", display_location_name).replace(' ', '_')  # Sanitize name
        file_name = f"Weather_Tidal_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name_location}.pdf"

        doc = SimpleDocTemplate(
            file_name,
            pagesize=(page_width, page_height),
            topMargin=0.5*inch,
            bottomMargin=0.3*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )

        elements = []
        styles = getSampleStyleSheet()
        title_style = styles['h1']
        title_style.alignment = 1  # Center

        normal_style = styles['Normal']
        normal_style.leading = 14  # Line spacing

        small_note_style = styles['Normal'].clone('SmallNote')
        small_note_style.fontSize = 8
        small_note_style.leading = 10

        # --- Report Header ---
        elements.append(
            Paragraph("Weather & Tidal Forecast Report", title_style))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(
            f"Location: {display_location_name} ({location_info.get('country', 'N/A')})", normal_style))
        elements.append(
            Paragraph(f"Coordinates: Lat: {lat:.4f}, Lon: {lon:.4f}", normal_style))
        elements.append(Paragraph(
            f"Timezone: {location_info.get('timezone', DEFAULT_TIMEZONE)}", normal_style))
        elements.append(Paragraph(
            f"Sunrise: {location_info.get('sunrise', 'N/A')}, Sunset: {location_info.get('sunset', 'N/A')}", normal_style))
        elements.append(Paragraph(
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        elements.append(Spacer(1, 0.2*inch))

        # --- Weather Forecast Table ---
        elements.append(
            Paragraph("<b>Weather Forecast (Next 5 Days)</b>", styles['h2']))
        elements.append(Spacer(1, 0.1*inch))

        weather_headers = ["Date/Time", "Description", "Temp (°C)", "Humidity (%)",
                           "Wind (knots)", "Gust (knots)", "Wind Dir",
                           "Rain (mm/3h)", "PoP (%)", "Visibility (m)"]
        weather_table_data = [weather_headers]

        for item in weather_data:
            vis = item['visibility']
            # Try converting visibility to int/float for consistent formatting, handle 'N/A'
            try:
                vis_formatted = f"{int(vis):,}" if vis != 'N/A' else 'N/A'
            except:
                vis_formatted = str(vis)  # Fallback if not number

            row = [
                item['datetime'],  # Use formatted string
                item['description'],
                f"{item['temperature']:.1f}",
                f"{item['humidity']:.0f}",
                f"{item['wind_speed']:.1f}",
                str(item['wind_gust']),
                item['wind_direction'],
                f"{item['rain']:.1f}",
                f"{item['pop']:.0f}",
                vis_formatted
            ]
            weather_table_data.append(row)

        # Adjusted widths for weather table
        weather_col_widths = [95, 120, 50, 60, 65, 65, 50, 65, 50, 70]
        weather_table = Table(weather_table_data,
                              repeatRows=1, colWidths=weather_col_widths)

        weather_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical align
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Smaller header font
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 4),  # Padding for data rows
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Smaller data font
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            # Right align numeric columns (adjust indices if table changes)
            ('ALIGN', (2, 1), (3, -1), 'RIGHT'),  # Temp, Humidity
            ('ALIGN', (4, 1), (5, -1), 'RIGHT'),  # Wind, Gust
            ('ALIGN', (7, 1), (9, -1), 'RIGHT'),  # Rain, PoP, Visibility
        ])
        weather_table.setStyle(weather_style)
        elements.append(weather_table)
        elements.append(
            Paragraph("<br/>Note: PoP = Probability of Precipitation.", small_note_style))
        elements.append(Spacer(1, 0.2*inch))

        # --- Tidal Forecast Table ---
        elements.append(
            Paragraph("<b>Phú An Tidal Forecast (Highest Level)</b>", styles['h2']))
        elements.append(Spacer(1, 0.1*inch))

        tidal_headers = ["Forecast Date",
                         "Highest Water Level (m)", "Alarm Level"]
        tidal_table_data = [tidal_headers]
        tidal_style_cmds = [  # Base style for tidal table
            ('BACKGROUND', (0, 0), (-1, 0), colors.teal),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.darkgrey),
        ]

        alarm1_m = 1.4
        alarm2_m = 1.5
        tidal_source_url = "N/A"  # Default source URL

        # Sort dates for the table
        sorted_dates = sorted(tidal_forecast.keys())

        # Start row index from 1 for styling
        for row_idx, date_str in enumerate(sorted_dates, start=1):
            data = tidal_forecast[date_str]
            level_cm_str = data['level_cm']
            source_url = data['source']
            if source_url:
                tidal_source_url = source_url  # Capture the source URL

            level_m_str = "N/A"
            alarm_str = "-"

            if isinstance(level_cm_str, str) and ("Error" in level_cm_str or "Not Found" in level_cm_str or "Parse PDF" in level_cm_str):
                level_m_str = level_cm_str  # Show the error/placeholder
            else:
                try:
                    level_cm = float(level_cm_str)
                    level_m = level_cm / 100.0
                    level_m_str = f"{level_m:.2f}"

                    # Determine alarm level and apply highlighting
                    if level_m >= alarm2_m:
                        alarm_str = "Alarm 2"
                        # Highlight cell red
                        tidal_style_cmds.append(
                            ('BACKGROUND', (1, row_idx), (1, row_idx), colors.red))
                        tidal_style_cmds.append(
                            ('TEXTCOLOR', (1, row_idx), (1, row_idx), colors.white))
                    elif level_m >= alarm1_m:
                        alarm_str = "Alarm 1"
                        # Highlight cell yellow
                        tidal_style_cmds.append(
                            ('BACKGROUND', (1, row_idx), (1, row_idx), colors.yellow))
                        # Ensure text readable on yellow
                        tidal_style_cmds.append(
                            ('TEXTCOLOR', (1, row_idx), (1, row_idx), colors.black))

                except (ValueError, TypeError) as e:
                    level_m_str = "Invalid Data"
                    print(
                        f"Error converting tidal level '{level_cm_str}' to number: {e}")

            row = [date_str, level_m_str, alarm_str]
            tidal_table_data.append(row)

        tidal_col_widths = [120, 150, 100]
        tidal_table = Table(tidal_table_data, colWidths=tidal_col_widths)
        tidal_table.setStyle(TableStyle(tidal_style_cmds))

        elements.append(tidal_table)
        elements.append(Paragraph(
            f"<br/>Tidal Data Source: {tidal_source_url or 'Not Found'}", small_note_style))
        elements.append(Paragraph(
            "Note: Alarm Level 1 ≥ 1.40m (Yellow), Alarm Level 2 ≥ 1.50m (Red). 'Parse PDF' requires enhanced PDF extraction.", small_note_style))
        elements.append(Spacer(1, 0.2*inch))

        # --- Weather Charts ---
        if weather_data:  # Only add charts if weather data exists
            elements.append(
                Paragraph("<b>Weather Parameter Charts</b>", styles['h2']))
            elements.append(Spacer(1, 0.1*inch))

            chart_params = [
                ('temperature', 'Temperature (°C)', 'Temperature Trend'),
                ('humidity', 'Humidity (%)', 'Humidity Trend'),
                ('wind_speed', 'Wind Speed (knots)', 'Wind Speed Trend'),
                ('pop', 'Probability (%)', 'Precipitation Probability Trend'),
                # ('visibility', 'Visibility (m)', 'Visibility Trend'), # Visibility can be less chart-friendly
                # ('rain', 'Rainfall (mm/3h)', 'Rainfall Accumulation (3h)'), # Rainfall is often sparse
            ]

            for param, unit, title in chart_params:
                # Check if there's any valid numeric data for this parameter
                if any(isinstance(item.get(param), (int, float)) and item.get(param) != 'N/A' for item in weather_data):
                    chart = self.create_chart(weather_data, param, unit, title)
                    if chart:
                        elements.append(chart)
                        elements.append(Spacer(1, 0.1*inch))
                else:
                    print(
                        f"Skipping chart for '{title}' due to lack of numeric data.")

        # --- Footer ---
        elements.append(Spacer(1, 0.2*inch))
        footer_style = small_note_style.clone('Footer')
        footer_style.alignment = 1  # Center align footer
        elements.append(Paragraph("--- Report End ---", footer_style))
        elements.append(Paragraph(
            "Weather data © OpenWeatherMap | Tidal data source: kttv-nb.org.vn", footer_style))
        elements.append(
            Paragraph("Generated by Weather Reporter Tool | 2025 © TungTT", footer_style))

        # Build the PDF
        try:
            doc.build(elements)
            print(f"PDF report generated: {file_name}")
        except Exception as build_err:
            print(f"Error building PDF: {build_err}")
            QMessageBox.critical(
                self, "PDF Error", f"Could not build PDF report:\n{build_err}")

    def closeEvent(self, event):
        # Clean up the session when the application closes
        if self.session:
            self.session.close()
            print("Requests session closed.")
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Optional: Set a specific font globally if needed
    # font = QFont("Segoe UI", 9)
    # app.setFont(font)
    weather_app = WeatherCrawlerApp()
    weather_app.show()
    sys.exit(app.exec_())
