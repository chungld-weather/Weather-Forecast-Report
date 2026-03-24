import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QRadioButton,
                             QMessageBox, QDateEdit, QProgressBar, QSizePolicy,
                             QGroupBox)  # Added QGroupBox for API selection
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
import matplotlib.dates as mdates  # Add this line
from io import BytesIO
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import io  # For handling PDF download in memory
import traceback  # For better error printing
import math  # For isnan check
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# -*- coding: utf-8 -*-
# Add this line at the top for better Unicode handling


# Added date, time, make sure 'date' is imported from datetime
# Corrected import for newer urllib3 versions
# Removed tempfile, PyPDF2 - replaced by pdfplumber and io

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
TIDAL_INDEX_URL = "http://www.kttv-nb.org.vn/index.php/thong-tin-kttv/thuy-van"
OPENMETEO_API_URL = "https://api.open-meteo.com/v1/forecast"


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

        # Regex tailored for the specific HCMC hydrological report titles on the target page
        # Handles "TIN..."/"BẢN TIN...", location variations, separator variations, and captures dd-mm-yyyy date
        bulletin_title_pattern = re.compile(
            # Match "TIN" OR "BẢN TIN" at the start
            r"(?:TIN|BẢN TIN)\s+DỰ BÁO THỦY VĂN"
            # Match space, then "TP.HCM" (optional dot) OR "THÀNH PHỐ HỒ CHÍ MINH"
            r"\s+(?:TP\.?HCM|THÀNH PHỐ HỒ CHÍ MINH)"
            r"(?:\s+-\s+|\s+)"  # Match either " - " OR just space(s) before NGÀY
            r"NGÀY"  # Match NGÀY
            # Match space, then capture the date dd-mm-yyyy (using only hyphens) # Allow / . - as separators, capture dd/mm/yyyy or dd/mm
            r"\s+(\d{1,2}[/.-]\d{1,2}(?:[/.-]\d{2,4})?)",
            re.IGNORECASE  # Keep it case-insensitive
        )
        # --- End Regex Definition ---

        all_links = index_soup.find_all('a', href=True)
        print(f"Searching {len(all_links)} links on the page...")

        for link in all_links:
            title = link.get_text(strip=True)
            # print(f"  Checking Title: '{title}'") # DEBUG
            match = bulletin_title_pattern.search(title)
            if match:
                date_str_from_title = match.group(1).replace(
                    '/', '-').replace('.', '-')  # Normalize separators to '-' for parsing
                try:
                    # Try parsing with year first
                    try:
                        article_date = datetime.strptime(
                            date_str_from_title, '%d-%m-%Y').date()
                    except ValueError:
                        # If year missing, assume target year
                        article_date = datetime.strptime(
                            f"{date_str_from_title}-{target_date.year}", '%d-%m-%Y').date()
                        # Handle year boundary (e.g., Dec report viewed in Jan)
                        if abs((article_date - target_date).days) > 180:
                            article_date = datetime.strptime(
                                f"{date_str_from_title}-{target_date.year-1}", '%d-%m-%Y').date()

                    if article_date == target_date:
                        found_article_link = link['href']
                        print(
                            f"  Found matching article: Date={article_date.strftime('%Y-%m-%d')}, Title='{title}', Href='{link['href']}'")
                        break

                except ValueError:
                    # print(f"  Warning: Could not parse date '{date_str_from_title}' from title '{title}'")
                    continue  # Ignore links with unparseable dates

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
        self.setWindowTitle("Weather Reporter")
        # Increased height slightly for date edit
        # Increased height for new API selection
        self.setGeometry(200, 100, 450, 750)

        icon_path = "weather_icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file {icon_path} not found")

        self.api_key = "e1a69775e0d7c149a4e2bdb69bb59a82"  # OpenWeatherMap API Key
        # Open-Meteo does not require an API key for its free tier.

        self.initUI()
        self.session = self.create_requests_session()

        if pdfplumber is None:
            QMessageBox.warning(self, "Dependency Warning",
                                "The 'pdfplumber' library is missing.\n"
                                "Tidal PDF scraping might be affected or disabled.\n\n"
                                "Please install it using:\npip install pdfplumber")

    # --- MODIFIED initUI ---
    def initUI(self):
        main_layout = QVBoxLayout()

        # --- 0. API Selection Section (NEW) ---
        api_group = QGroupBox("Select Weather API Source:")
        api_group.setFont(QFont("Arial", 10))  # Set font for group box title
        api_layout = QVBoxLayout()

        self.api_radio_owm = QRadioButton("OpenWeatherMap (5-day forecast)")
        # Set font for first radio button
        self.api_radio_owm.setFont(QFont("Arial", 10))

        self.api_radio_openmeteo = QRadioButton(
            "Open-Meteo (Up to 16-day forecast)")
        # Set font for second radio button
        self.api_radio_openmeteo.setFont(QFont("Arial", 10))

        # Change default selection to Open-Meteo
        # Default selection changed to Open-Meteo
        self.api_radio_openmeteo.setChecked(True)
        self.api_radio_owm.setChecked(False)  # Ensure OWM is unchecked

        api_layout.addWidget(self.api_radio_owm)
        api_layout.addWidget(self.api_radio_openmeteo)
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
        self.lat_input = QLineEdit()
        self.lon_label = QLabel("Longitude:")
        self.lon_label.setFont(QFont("Arial", 10))
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
        location_font = QFont("Arial", 10)  # Font for location text

        # --- Loop for Location Radio Buttons ---
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
        # --- End Loop ---

        # --- Custom GPS Section ---
        self.gps_radio = QRadioButton("Enter Custom GPS Coordinates:")
        self.gps_radio.setFont(location_font)
        self.gps_radio.toggled.connect(self.toggle_gps_input)
        input_layout.addWidget(self.gps_radio)

        # --- NEW: Custom GPS Name Input ---
        gps_name_layout = QHBoxLayout()
        self.gps_name_label = QLabel("Custom Name (Optional):")
        self.gps_name_label.setFont(QFont("Arial", 10))
        self.gps_name_input = QLineEdit()
        self.gps_name_input.setPlaceholderText("e.g., My Offshore Site")
        self.gps_name_input.setEnabled(False)  # Initially disabled
        gps_name_layout.addWidget(self.gps_name_label)
        gps_name_layout.addWidget(self.gps_name_input)
        input_layout.addLayout(gps_name_layout)  # Add name input layout
        # --- END NEW ---

        gps_coord_layout = QHBoxLayout()  # Renamed for clarity
        gps_coord_layout.addWidget(self.lat_label)
        gps_coord_layout.addWidget(self.lat_input)
        gps_coord_layout.addWidget(self.lon_label)
        gps_coord_layout.addWidget(self.lon_input)
        gps_coord_layout.addStretch()
        input_layout.addLayout(gps_coord_layout)  # Add coordinate input layout
        # --- End Custom GPS Section ---

        # --- Default Location Selection ---
        default_location_key = 'An Phu Office'
        if default_location_key not in self.location_radios:
            default_location_key = next(iter(self.locations))
        if default_location_key in self.location_radios:
            self.location_radios[default_location_key].setChecked(True)
        # --- End Default Location Selection ---

        main_layout.addLayout(input_layout)

        # --- Spacer ---
        main_layout.addSpacing(20)  # Reduced spacing

        # --- 2. Generate Weather Report Title ---
        weather_title_layout = QHBoxLayout()
        weather_title_label = QLabel("Generate Weather Report")
        weather_title_label.setFont(QFont("Arial", 11, QFont.Bold))
        weather_title_label.setAlignment(Qt.AlignCenter)
        weather_title_layout.addStretch()
        weather_title_layout.addWidget(weather_title_label)
        weather_title_layout.addStretch()
        main_layout.addLayout(weather_title_layout)

        # --- Spacer ---
        main_layout.addSpacing(5)  # Reduced spacing

        # --- 3. Generate Weather Report Button ---
        self.weather_button = QPushButton("Generate Report")
        self.weather_button.setFont(QFont("Arial", 10))
        self.weather_button.clicked.connect(
            self.generate_weather_report_action)
        main_layout.addWidget(self.weather_button)

        # --- Generate Vietnamese Weather Report Button ---
        self.vietnamese_weather_button = QPushButton(
            "Tạo Báo Cáo Thời Tiết (Tiếng Việt)")
        self.vietnamese_weather_button.setFont(QFont("Arial", 10))
        self.vietnamese_weather_button.clicked.connect(
            self.generate_vietnamese_weather_report_action)
        main_layout.addWidget(self.vietnamese_weather_button)

        # --- Spacer ---
        main_layout.addSpacing(20)  # Reduced spacing

        # --- 4. Download Tide Report Title ---
        tide_title_layout = QHBoxLayout()
        tide_title_label = QLabel("Download Tide Report (HCMC)")
        tide_title_label.setFont(QFont("Arial", 11, QFont.Bold))
        tide_title_label.setAlignment(Qt.AlignCenter)
        tide_title_layout.addStretch()
        tide_title_layout.addWidget(tide_title_label)
        tide_title_layout.addStretch()
        main_layout.addLayout(tide_title_layout)

        # --- Spacer ---
        main_layout.addSpacing(5)  # Reduced spacing

        # --- 5. Tidal Report Date Selection ---
        date_layout = QHBoxLayout()
        date_label = QLabel("Select Date:")
        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setMinimumWidth(90)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        main_layout.addLayout(date_layout)

        # --- Spacer ---
        main_layout.addSpacing(5)  # Reduced spacing

        # --- 6. Download Tide Report Button ---
        self.tidal_button = QPushButton(
            "Download Tide Report for the selected date")
        self.tidal_button.setFont(QFont("Arial", 10))
        self.tidal_button.clicked.connect(self.download_tidal_report_action)
        main_layout.addWidget(self.tidal_button)

        # --- Spacer ---
        main_layout.addSpacing(15)  # Reduced spacing

        # --- 7. Progress Bar ---
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFormat("")
        self.progress_bar.setVisible(False)
        self.progress_bar.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.progress_bar)

        # --- 8. Status Label ---
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setVisible(False)
        main_layout.addWidget(self.status_label)

        # --- Final Layout Setup ---
        main_layout.addStretch()
        self.setLayout(main_layout)
        self.toggle_gps_input()  # Call once to set initial state

        self.resize(self.width(), 650)  # Adjusted height for API selection
    # --- END MODIFIED initUI ---

    # --- MODIFIED toggle_gps_input ---
    def toggle_gps_input(self):
        """Enables/disables the Latitude, Longitude, and Custom Name input fields based on GPS radio selection."""
        is_gps_selected = self.gps_radio.isChecked()
        self.lat_input.setEnabled(is_gps_selected)
        self.lon_input.setEnabled(is_gps_selected)
        self.gps_name_input.setEnabled(
            is_gps_selected)  # Enable/disable name input
        self.gps_name_label.setEnabled(
            is_gps_selected)  # Also enable/disable label
    # --- END MODIFIED toggle_gps_input ---

    # --- NEW: get_api_choice ---
    def get_api_choice(self):
        """Returns the currently selected weather API source."""
        if self.api_radio_owm.isChecked():
            return "OWM"
        elif self.api_radio_openmeteo.isChecked():
            return "OpenMeteo"
        return None  # Should not happen
    # --- END NEW: get_api_choice ---

    # --- MODIFIED generate_weather_report_action ---
    def generate_weather_report_action(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return

        api_choice = self.get_api_choice()
        if not api_choice:
            QMessageBox.warning(
                self, "API Selection Error", "Please select a weather API source.")
            return

        # Start progress bar and status label
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(True)
        self.status_label.setText(
            f"Preparing to fetch weather data from {api_choice}...")
        self.status_label.setVisible(True)
        QApplication.processEvents()  # Force UI update

        QApplication.setOverrideCursor(Qt.WaitCursor)
        weather_data = None
        location_info = None
        success = False

        try:
            print(
                f"--- Starting Weather Data Fetch for Report ({api_choice}) ---")

            self.status_label.setText(
                f"Fetching weather data from {api_choice}... Please wait")
            QApplication.processEvents()

            if api_choice == "OWM":
                weather_data, location_info = self._fetch_weather_data_owm(
                    lat, lon)
            elif api_choice == "OpenMeteo":
                weather_data, location_info = self._fetch_weather_data_openmeteo(
                    lat, lon)

            if not weather_data:
                if not location_info:  # Fallback if location_info is also None
                    location_info = {'name': location_name_selected, 'country': 'N/A',
                                     'sunrise': 'N/A', 'sunset': 'N/A', 'timezone': DEFAULT_TIMEZONE}
                QMessageBox.warning(
                    self, "Weather Error", "Failed to fetch weather data. Report generation stopped.")
                return

            self.status_label.setText("Generating PDF report...")
            QApplication.processEvents()

            self.generate_pdf_report(
                lat, lon, weather_data, location_info, location_name_selected, api_choice)

            success = True
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.status_label.setText("Report generated successfully!")
            QApplication.processEvents()

            QMessageBox.information(
                self, "Success", "Weather PDF report generated successfully!")

        except Exception as e:
            success = False
            print(f"An error occurred during weather report generation: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred generating the weather report:\n{e}")
        finally:
            if success:
                QTimer.singleShot(1000, lambda: [self.status_label.setVisible(
                    False), self.progress_bar.setVisible(False)])
            else:
                self.status_label.setVisible(False)
                self.progress_bar.setVisible(False)
            QApplication.restoreOverrideCursor()

    # --- MODIFIED generate_vietnamese_weather_report_action ---
    def generate_vietnamese_weather_report_action(self):
        lat, lon, location_name_selected = self.get_coordinates()
        if lat is None:
            return

        api_choice = self.get_api_choice()
        if not api_choice:
            QMessageBox.warning(
                self, "API Selection Error", "Vui lòng chọn nguồn API thời tiết.")
            return

        # Start progress bar and status label
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(True)
        self.status_label.setText(
            f"Đang chuẩn bị lấy dữ liệu thời tiết từ {api_choice}...")  # Vietnamese
        self.status_label.setVisible(True)
        QApplication.processEvents()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        weather_data = None
        location_info = None
        success = False

        try:
            print(
                f"--- Starting Weather Data Fetch for Vietnamese Report ({api_choice}) ---")

            self.status_label.setText(
                f"Đang lấy dữ liệu thời tiết từ {api_choice}... Vui lòng chờ")  # Vietnamese
            QApplication.processEvents()

            if api_choice == "OWM":
                weather_data, location_info = self._fetch_weather_data_owm(
                    lat, lon)
            elif api_choice == "OpenMeteo":
                weather_data, location_info = self._fetch_weather_data_openmeteo(
                    lat, lon)

            if not weather_data:
                if not location_info:
                    location_info = {'name': location_name_selected, 'country': 'N/A',
                                     'sunrise': 'N/A', 'sunset': 'N/A', 'timezone': DEFAULT_TIMEZONE}
                QMessageBox.warning(
                    self, "Lỗi Dữ Liệu Thời Tiết", "Không thể lấy dữ liệu thời tiết. Đã dừng tạo báo cáo.")  # Vietnamese
                return

            self.status_label.setText(
                "Đang tạo báo cáo PDF (Tiếng Việt)...")  # Vietnamese
            QApplication.processEvents()

            self.generate_vietnamese_pdf_report(
                lat, lon, weather_data, location_info, location_name_selected, api_choice)

            success = True
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.status_label.setText(
                "Đã tạo báo cáo thành công!")  # Vietnamese
            QApplication.processEvents()

            QMessageBox.information(
                self, "Thành Công", "Đã tạo báo cáo thời tiết PDF (Tiếng Việt) thành công!")  # Vietnamese

        except Exception as e:
            success = False
            print(
                f"An error occurred during Vietnamese weather report generation: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Lỗi", f"Đã xảy ra lỗi không mong muốn khi tạo báo cáo:\n{e}")  # Vietnamese
        finally:
            if success:
                QTimer.singleShot(1000, lambda: [self.status_label.setVisible(
                    False), self.progress_bar.setVisible(False)])
            else:
                self.status_label.setVisible(False)
                self.progress_bar.setVisible(False)
            QApplication.restoreOverrideCursor()

    # ... (Keep download_tidal_report_action) ...
    def download_tidal_report_action(self):
        selected_date_qdate = self.date_edit.date()
        selected_date = selected_date_qdate.toPyDate()

        # --- Start Progress Bar EARLIER ---
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)
        self.status_label.setText(
            "Preparing to fetch tide data...")  # Update status label
        self.status_label.setVisible(True)
        QApplication.processEvents()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        tidal_pdf_path = None
        tidal_pdf_url = None
        success = False

        try:
            print(
                f"\n--- Starting Tidal PDF Download for Date: {selected_date.strftime('%d/%m/%Y')} ---")

            # Update progress message before scraping
            self.status_label.setText(
                "Searching for tide report...")  # Update status label
            QApplication.processEvents()

            tidal_pdf_path, tidal_pdf_url = scrape_and_download_tidal_pdf_for_date(
                self.session, selected_date, download_dir=".")

            if not tidal_pdf_url:
                success = False
                QMessageBox.warning(
                    self, "Tidal PDF Not Found",
                    f"Could not find the URL for the tidal PDF report for {selected_date.strftime('%d/%m/%Y')}.")
            elif not tidal_pdf_path:
                success = False
                QMessageBox.warning(
                    self, "Download Failed",
                    f"Found tidal PDF URL, but failed to download it.\nURL: {tidal_pdf_url}")
            else:
                success = True
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(100)
                self.status_label.setText(
                    "Download completed successfully!")  # Update status label
                QApplication.processEvents()

                abs_path = os.path.abspath(tidal_pdf_path)
                QMessageBox.information(
                    self, "Download Successful",
                    f"Tidal PDF for {selected_date.strftime('%d/%m/%Y')} downloaded successfully to:\n{abs_path}")
                print(f"Tidal PDF downloaded: {abs_path}")

        except Exception as e:
            success = False
            print(f"An error occurred during tidal PDF download: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Download Error", f"An unexpected error occurred during download:\n{e}")
        finally:
            # Hide progress bar and label after a short delay on success, immediately on failure
            if success:
                QTimer.singleShot(1000, lambda: [self.status_label.setVisible(
                    False), self.progress_bar.setVisible(False)])
            else:
                self.status_label.setVisible(False)
                self.progress_bar.setVisible(False)
            QApplication.restoreOverrideCursor()

    # --- MODIFIED get_coordinates ---
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

                # --- Get custom name ---
                custom_name = self.gps_name_input.text().strip()
                if custom_name:
                    # Use the provided custom name
                    location_name = custom_name
                else:
                    # Use the default format if no name is given
                    location_name = f"Custom GPS ({lat:.4f}, {lon:.4f})"
                # --- End custom name logic ---

                return lat, lon, location_name  # Return custom or default name
            except ValueError as e:
                QMessageBox.warning(self, "Input Error",
                                    f"Invalid Latitude or Longitude: {e}")
                return None, None, None
        else:
            for name, radio in self.location_radios.items():
                if radio.isChecked():
                    # Return lat, lon, and the predefined name
                    return self.locations[name][0], self.locations[name][1], name
        QMessageBox.warning(self, "Input Error",
                            "Please select a location option.")
        return None, None, None  # Return three values consistently
    # --- END MODIFIED get_coordinates ---

    # ... (Keep create_requests_session) ...
    def create_requests_session(self):
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

    # --- RENAMED: _fetch_weather_data_owm (original fetch_weather_data) ---
    def _fetch_weather_data_owm(self, lat, lon):
        base_url = "https://api.openweathermap.org/data/2.5/"
        units = "metric"
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
            current_response.raise_for_status()
            current_data = current_response.json()

            # Get 5-day/3-hour forecast data (cnt=40 for 5 days * 8 points/day)
            forecast_url = f"{base_url}forecast?lat={lat}&lon={lon}&appid={self.api_key}&units={units}&cnt=40"
            print(f"Fetching OWM forecast: {forecast_url}")
            forecast_response = self.session.get(forecast_url, timeout=timeout)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # --- Determine Timezone ---
            timezone_str = DEFAULT_TIMEZONE  # Default
            country_code = current_data.get('sys', {}).get('country')
            local_tz = None  # Initialize local_tz

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

    # --- NEW: _fetch_weather_data_openmeteo ---
    def _fetch_weather_data_openmeteo(self, lat, lon):
        timeout = (15, 30)
        location_info = {
            'name': f"Coords ({lat:.4f}, {lon:.4f})",
            'country': 'N/A',  # Open-Meteo doesn't directly provide country code
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
            "timezone": "auto",  # Let Open-Meteo determine best IANA timezone
            "forecast_days": 16,  # Fetch up to 16 days of daily, 7 days of hourly
            "temperature_unit": "celsius",
            "wind_speed_unit": "kn",  # Request directly in knots
            "precipitation_unit": "mm"
        }

        try:
            print(
                f"Fetching Open-Meteo: {OPENMETEO_API_URL} with params: {params}")
            response = self.session.get(
                OPENMETEO_API_URL, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            # --- Extract location info ---
            location_info['timezone'] = data.get(
                'timezone', DEFAULT_TIMEZONE)

            # Use data.get('timezone') as the source of truth for timezone
            try:
                local_tz = pytz.timezone(location_info['timezone'])
            except pytz.exceptions.UnknownTimeZoneError:
                print(
                    f"Error: pytz does not recognize timezone '{location_info['timezone']}'. Falling back to {DEFAULT_TIMEZONE}.")
                location_info['timezone'] = DEFAULT_TIMEZONE
                local_tz = pytz.timezone(DEFAULT_TIMEZONE)

            # Open-Meteo typically doesn't provide a human-readable location name beyond coordinates
            # or country code directly in the forecast API, so we stick to the UI name.
            # But it does provide `name` in geocoding API, not in forecast.
            # For `location_info['name']`, we'll keep the `ui_location_name` passed from the UI
            # or the default `Coords (lat,lon)` if not provided.

            daily_data = data.get('daily', {})
            # Sunrise/Sunset are arrays, take the first entry for today
            if daily_data.get('sunrise') and len(daily_data['sunrise']) > 0:
                # Convert ISO string to datetime, then to local timezone
                sunrise_utc = datetime.fromisoformat(
                    daily_data['sunrise'][0].replace('Z', '+00:00'))
                location_info['sunrise'] = sunrise_utc.astimezone(
                    local_tz).strftime('%H:%M')
            if daily_data.get('sunset') and len(daily_data['sunset']) > 0:
                sunset_utc = datetime.fromisoformat(
                    daily_data['sunset'][0].replace('Z', '+00:00'))
                location_info['sunset'] = sunset_utc.astimezone(
                    local_tz).strftime('%H:%M')

            # --- Process hourly data ---
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

            # Get current time in local timezone for filtering
            now_local = datetime.now(local_tz)

            # Limit to next 7 days of hourly data (168 hours)
            # The API also returns up to 168 hours by default for hourly data.
            # We will use this directly.
            for i in range(len(times)):
                try:
                    # Time is ISO 8601 string, convert to local datetime object
                    dt_local_str = times[i]
                    dt_obj = datetime.fromisoformat(
                        dt_local_str).astimezone(local_tz)

                    # Filter for the next 7 days (approximately, including current hour's remaining)
                    if dt_obj >= now_local - timedelta(hours=1) and dt_obj <= now_local + timedelta(days=7, hours=1):

                        wmo_code = weather_codes[i] if i < len(
                            weather_codes) else None
                        weather_desc_en = WMO_WEATHER_CODES_EN.get(
                            wmo_code, f"Unknown code {wmo_code}" if wmo_code is not None else 'N/A')

                        temp = temperatures[i] if i < len(
                            temperatures) else None
                        humidity = humidities[i] if i < len(
                            humidities) else None

                        wind_speed = wind_speeds[i] if i < len(
                            wind_speeds) else None
                        wind_gust = wind_gusts[i] if i < len(
                            wind_gusts) else None
                        wind_deg = wind_directions[i] if i < len(
                            wind_directions) else None
                        wind_direction = self._degrees_to_direction(wind_deg)

                        # Sum up all precipitation types for total rain
                        total_rain_hourly = (rain_amounts[i] if i < len(rain_amounts) and rain_amounts[i] is not None else 0.0) + \
                            (showers_amounts[i] if i < len(showers_amounts) and showers_amounts[i] is not None else 0.0) + \
                            (snowfall_amounts[i] if i < len(
                                snowfall_amounts) and snowfall_amounts[i] is not None else 0.0)

                        # Open-Meteo doesn't have hourly PoP.
                        # Simple derivation: if any rain is forecast, PoP is 100%, otherwise 0%.
                        pop = 100 if total_rain_hourly > 0.0 else 0

                        visibility = visibilities[i] if i < len(
                            visibilities) else None
                        cloud_cover = cloud_covers[i] if i < len(
                            cloud_covers) else None
                        pressure = pressures[i] if i < len(pressures) else None
                        uv_index = uv_indices[i] if i < len(
                            uv_indices) else None

                        processed_data.append({
                            'datetime_obj': dt_obj,
                            'datetime': dt_obj.strftime('%Y-%m-%d %H:%M'),
                            'description': weather_desc_en,
                            'temperature': float(temp) if temp is not None else 'N/A',
                            'humidity': float(humidity) if humidity is not None else 'N/A',
                            # Already in knots
                            'wind_speed': float(wind_speed) if wind_speed is not None else 'N/A',
                            # Already in knots
                            'wind_gust': float(wind_gust) if wind_gust is not None else 'N/A',
                            'wind_direction': wind_direction,
                            # Total precipitation for the hour
                            'rain': float(total_rain_hourly),
                            'visibility': int(visibility) if isinstance(visibility, (int, float)) else 'N/A',
                            'pop': pop,  # Derived PoP
                            # Additional data points (not in OWM, but useful)
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

    # --- RENAMED: _process_forecast_data_owm (original process_forecast_data) ---
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
                        'pop': pop
                    })
            except Exception as e:
                print(
                    f"Error processing OWM forecast item: {item}. Error: {e}")
                continue

        return processed_data

    # Helper method for degrees to direction (also used by Open-Meteo processing)
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

    # ... (Keep create_chart, create_wind_chart, create_temp_humidity_chart, create_rain_pop_chart) ...

    def create_chart(self, data, param_name, ylabel, title, date_key='datetime_obj',
                     xlabel_text='Date/Time'):  # Added xlabel_text argument
        if not data:
            print(f"Warning: No data provided for chart: {title}")
            return None

        plt.figure(figsize=(9.0, 2.8))
        dates = []
        values = []
        for item in data:
            item_val = item.get(param_name)
            # Ensure the date object is timezone-aware if it comes from processing
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

        # Plotting
        try:
            plt.plot(dates, values, marker='.',
                     linestyle='-', markersize=4, linewidth=1)
            plt.title(title, fontsize=10)  # Uses argument
            plt.xlabel(xlabel_text, fontsize=9)  # <--- USE ARGUMENT
            plt.ylabel(ylabel, fontsize=9)  # Uses argument
            plt.xticks(rotation=30, ha='right', fontsize=9)
            plt.yticks(fontsize=9)

            # --- X-axis Tick Formatting ---
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(
                byhour=[1, 7, 13, 19], tz=dates[0].tzinfo if dates else None))
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(
                '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))

            plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
            plt.tight_layout(pad=0.5)

            # Save to BytesIO
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)

            # Create ReportLab Image
            img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
            img.hAlign = 'CENTER'
            return img

        except Exception as chart_err:
            print(f"Error during chart plotting for '{title}': {chart_err}")
            print(traceback.format_exc())  # Add traceback for debugging
            plt.close()
            return None

    # ... (Keep create_wind_chart) ...
    def create_wind_chart(self, data, date_key='datetime_obj',
                          xlabel_text='Date/Time', ylabel_text='Speed (knots)',
                          title_text='Wind Speed and Gust Trend',
                          speed_label='Wind Speed', gust_label='Wind Gust'):  # Added labels
        """Generates a chart with both wind speed and gust."""
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
                # Only append if date is valid
                dates.append(item_date)
                # Append speed, converting 'N/A' or errors to NaN for plotting gaps
                try:
                    speeds.append(float(speed_val) if speed_val not in [
                                  None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    speeds.append(math.nan)
                # Append gust, converting 'N/A' or errors to NaN
                try:
                    gusts.append(float(gust_val) if gust_val not in [
                                 None, 'N/A'] else math.nan)
                except (ValueError, TypeError):
                    gusts.append(math.nan)

        if not dates or (all(math.isnan(s) for s in speeds) and all(math.isnan(g) for g in gusts)):
            print("Warning: No valid numeric data points found for wind chart.")
            plt.close()
            return None

        # Plotting
        try:
            # Plot Wind Speed (default color)
            line1, = plt.plot(dates, speeds, marker='.', linestyle='-',
                              markersize=4, linewidth=1, label=speed_label)  # <--- USE ARGUMENT
            # Plot Wind Gust (orange color)
            line2, = plt.plot(dates, gusts, marker='.', linestyle='-', markersize=4,
                              linewidth=1, color='orange', label=gust_label)  # <--- USE ARGUMENT

            plt.title(title_text, fontsize=10)  # <--- USE ARGUMENT
            plt.xlabel(xlabel_text, fontsize=9)  # <--- USE ARGUMENT
            plt.ylabel(ylabel_text, fontsize=9)  # <--- USE ARGUMENT
            plt.xticks(rotation=30, ha='right', fontsize=9)
            plt.yticks(fontsize=9)
            plt.legend(fontsize=8)  # Legend uses labels from plot() calls

            # --- X-axis Tick Formatting (same as other charts) ---
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(
                byhour=[1, 7, 13, 19], tz=dates[0].tzinfo if dates else None))
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(
                '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))
            # --- End X-axis Tick Formatting ---

            plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
            plt.tight_layout(pad=0.5)

            # Save to BytesIO
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)

            # Create ReportLab Image
            img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
            img.hAlign = 'CENTER'
            return img

        except Exception as chart_err:
            print(f"Error during wind chart plotting: {chart_err}")
            print(traceback.format_exc())
            plt.close()
            return None

    # ... (Keep create_temp_humidity_chart) ...
    def create_temp_humidity_chart(self, data, date_key='datetime_obj',
                                   xlabel_text='Date/Time', temp_ylabel='Temperature (°C)',
                                   hum_ylabel='Humidity (%)', title_text='Temperature and Humidity Trend',
                                   temp_label='Temperature', hum_label='Humidity'):  # Added labels
        """Generates a chart with Temperature and Humidity using dual axes."""
        if not data:
            print("Warning: No data provided for Temp/Humidity chart.")
            return None

        # Create figure and primary axis
        fig, ax1 = plt.subplots(figsize=(9.0, 2.8))  # Use fig, ax1

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

        if not dates or (all(math.isnan(t) for t in temps) and all(math.isnan(h) for h in humidity)):
            print("Warning: No valid numeric data points found for Temp/Humidity chart.")
            plt.close(fig)
            return None

        # Plotting
        try:
            # --- Configure ax1 BEFORE creating ax2 ---
            color_temp = 'tab:blue'
            ax1.set_xlabel('Date/Time', fontsize=9)
            ax1.set_xlabel(xlabel_text, fontsize=9)  # <--- USE ARGUMENT
            ax1.set_ylabel(temp_ylabel, color=color_temp,
                           fontsize=9)  # <--- USE ARGUMENT
            # Apply rotation here, remove ha
            ax1.tick_params(axis='x', rotation=30, labelsize=9)

            # --- X-axis Tick Formatting (Apply BEFORE ax2 creation) ---
            ax1.xaxis.set_major_locator(mdates.HourLocator(
                byhour=[1, 7, 13, 19], tz=dates[0].tzinfo if dates else None))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter(
                '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))
            # --- End X-axis Tick Formatting ---

            # --- Plot on ax1 ---
            line1, = ax1.plot(dates, temps, marker='.', linestyle='-',
                              markersize=4, linewidth=1, color=color_temp, label=temp_label)  # <--- USE ARGUMENT

            # --- Create and plot on ax2 ---
            ax2 = ax1.twinx()
            color_hum = 'orange'
            ax2.set_ylabel(hum_ylabel, color=color_hum,
                           fontsize=9)  # <--- USE ARGUMENT
            line2, = ax2.plot(dates, humidity, marker='.', linestyle='-',
                              markersize=4, linewidth=1, color=color_hum, label=hum_label)  # <--- USE ARGUMENT
            ax2.tick_params(axis='y', labelcolor=color_hum, labelsize=9)
            # --- End ax2 plotting ---

            # Add Legend
            lines = [line1, line2]
            ax1.legend(lines, [l.get_label()
                       for l in lines], loc='upper left', fontsize=8)

            plt.title(title_text, fontsize=10)  # <--- USE ARGUMENT
            ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)

            # --- Adjust Layout and Label Alignment BEFORE Saving ---
            fig.tight_layout(pad=0.5)  # Apply tight layout first

            # --- NEW: Adjust X-tick label alignment AFTER layout ---
            # Iterate through labels and set alignment to 'right'
            for label in ax1.get_xticklabels():
                label.set_horizontalalignment('right')
                # Keep rotation_mode='anchor' if needed, but 'right' might be sufficient
                # label.set_rotation_mode("anchor")
            # --- END NEW ---

            # Optional: Force redraw if needed
            # fig.canvas.draw()

            # Save to BytesIO
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            img_buffer.seek(0)

            # Create ReportLab Image
            img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
            img.hAlign = 'CENTER'
            return img

        except Exception as chart_err:
            print(f"Error during Temp/Humidity chart plotting: {chart_err}")
            print(traceback.format_exc())
            plt.close(fig)
            return None

    # ... (Keep create_rain_pop_chart) ...
    def create_rain_pop_chart(self, data, date_key='datetime_obj',
                              # Changed mm/3h to mm/h
                              xlabel_text='Date/Time', rain_ylabel='Rainfall (mm/h)',
                              pop_ylabel='Probability of Precipitation (%)',
                              title_text='Rainfall and Precipitation Probability Trend',
                              rain_label='Rainfall', pop_label='PoP'):  # Added labels
        """Generates a chart with Rainfall and PoP using dual axes."""
        if not data:
            print("Warning: No data provided for Rain/PoP chart.")
            return None

        # Create figure and primary axis
        fig, ax1 = plt.subplots(figsize=(9.0, 2.8))  # Use fig, ax1

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

        # Plotting
        try:
            # --- Configure ax1 BEFORE creating ax2 ---
            color_rain = 'tab:blue'
            ax1.set_xlabel(xlabel_text, fontsize=9)  # <--- USE ARGUMENT
            ax1.set_ylabel(rain_ylabel, color=color_rain,
                           fontsize=9)  # <--- USE ARGUMENT
            ax1.tick_params(axis='y', labelcolor=color_rain, labelsize=9)
            ax1.tick_params(axis='x', rotation=30, labelsize=9)

            # --- X-axis Tick Formatting (Apply BEFORE ax2 creation) ---
            ax1.xaxis.set_major_locator(mdates.HourLocator(
                byhour=[1, 7, 13, 19], tz=dates[0].tzinfo if dates else None))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter(
                '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))
            # --- End X-axis Tick Formatting ---

            # --- Plot on ax1 ---
            line1, = ax1.plot(dates, rains, marker='.', linestyle='-',
                              markersize=4, linewidth=1, color=color_rain, label=rain_label)  # <--- USE ARGUMENT

            # --- Create and plot on ax2 ---
            ax2 = ax1.twinx()
            color_pop = 'orange'
            ax2.set_ylabel(pop_ylabel, color=color_pop,
                           fontsize=9)  # <--- USE ARGUMENT
            line2, = ax2.plot(dates, pops, marker='.', linestyle='-',
                              markersize=4, linewidth=1, color=color_pop, label=pop_label)  # <--- USE ARGUMENT
            ax2.tick_params(axis='y', labelcolor=color_pop, labelsize=9)
            ax2.set_ylim(0, 105)
            # --- End ax2 plotting ---

            # Add Legend
            lines = [line1, line2]
            ax1.legend(lines, [l.get_label()
                       for l in lines], loc='upper left', fontsize=8)

            plt.title(title_text, fontsize=10)  # <--- USE ARGUMENT
            ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)

            # --- Adjust Layout and Label Alignment BEFORE Saving ---
            fig.tight_layout(pad=0.5)  # Apply tight layout first

            # --- NEW: Adjust X-tick label alignment AFTER layout ---
            # Iterate through labels and set alignment to 'right'
            for label in ax1.get_xticklabels():
                label.set_horizontalalignment('right')
                # Keep rotation_mode='anchor' if needed
                # label.set_rotation_mode("anchor")
            # --- END NEW ---

            # Optional: Force redraw if needed
            # fig.canvas.draw()

            # Save to BytesIO
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            img_buffer.seek(0)

            # Create ReportLab Image
            img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
            img.hAlign = 'CENTER'
            return img

        except Exception as chart_err:
            print(f"Error during Rain/PoP chart plotting: {chart_err}")
            print(traceback.format_exc())
            plt.close(fig)
            return None

    # --- MODIFIED generate_pdf_report ---
    def generate_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source):

        page_width, page_height = landscape(letter)

        # --- Filename Logic (Keep as is) ---
        # Use ui_location_name for filename safety
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

        # --- Define Styles (Keep as is) ---
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

        # --- Report Header (Revised Logic) ---
        elements.append(Paragraph("Weather Forecast Report", title_style))
        elements.append(Spacer(1, 0.1*inch))

        api_name = location_info.get('name', '')
        country_code = location_info.get('country', 'N/A')

        # Determine if API name/country provides extra info beyond the UI name
        api_details_parts = []
        # Add API name if it's different from UI name and not just coordinates
        if api_name and api_name != ui_location_name and not api_name.startswith("Coords ("):
            api_details_parts.append(api_name)
        # Add country code if valid
        if country_code and country_code != 'N/A':
            api_details_parts.append(country_code)

        # Display the UI name (predefined, custom, or default GPS string)
        location_string = f"<b>Location:</b> {ui_location_name}"
        # Append API details in parentheses if they provide useful extra info
        if api_details_parts:
            api_details = ", ".join(api_details_parts)
            location_string += f" ({api_details})"

        elements.append(Paragraph(location_string, normal_style))
        # Coordinates, Timezone, Sunrise/Sunset, Generated time remain the same
        elements.append(
            Paragraph(f"<b>Coordinates:</b> Lat: {lat:.4f}, Lon: {lon:.4f}", normal_style))
        elements.append(Paragraph(
            f"<b>Timezone:</b> {location_info.get('timezone', DEFAULT_TIMEZONE)}", normal_style))
        elements.append(Paragraph(
            f"<b>Sunrise:</b> {location_info.get('sunrise', 'N/A')}, <b>Sunset:</b> {location_info.get('sunset', 'N/A')}", normal_style))
        elements.append(Paragraph(
            f"<b>Report Generated:</b> {datetime.now(pytz.timezone(location_info.get('timezone', DEFAULT_TIMEZONE))).strftime('%Y-%m-%d %H:%M:%S %Z')}", normal_style))
        # Add API source to report header
        elements.append(
            Paragraph(f"<b>Data Source:</b> {api_source}", normal_style))
        elements.append(Spacer(1, 0.2*inch))
        # --- End Report Header ---

        # --- Weather Forecast Table (Keep as is, adjusted to use all available columns) ---
        if weather_data:
            elements.append(
                Paragraph("Weather Forecast (Next 5-7 Days Hourly)", h2_style))  # Adjusted length for Open-Meteo

            # Define specific parameters for columns and their formatting
            col_params = {
                'datetime': {'header': "Date/Time", 'format': lambda x: x, 'width': 1.28*inch, 'align': 'CENTER'},
                'description': {'header': "Description", 'format': lambda x: x, 'width': 1.88*inch, 'align': 'CENTER'},
                'temperature': {'header': "Temp\n(°C)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
                'humidity': {'header': "Humidity\n(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.8*inch, 'align': 'RIGHT'},
                'wind_speed': {'header': "Wind Speed\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'wind_gust': {'header': "Wind Gust\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                'wind_direction': {'header': "Wind\nDir", 'format': lambda x: x, 'width': 0.72*inch, 'align': 'CENTER'},
                # Changed to mm/h for Open-Meteo hourly
                'rain': {'header': "Rain\n(mm/h)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.75*inch, 'align': 'RIGHT'},
                'pop': {'header': "PoP\n(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
                'visibility': {'header': "Visibility\n(m)", 'format': lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.88*inch, 'align': 'RIGHT'},
            }

            # These will be the fixed headers and column widths for the table
            weather_headers = ["Date/Time", "Description", "Temp\n(°C)", "Humidity\n(%)",
                               "Wind Speed\n(knots)", "Wind Gust\n(knots)", "Wind\nDir",
                               "Rain\n(mm/h)", "PoP\n(%)", "Visibility\n(m)"]
            weather_col_widths = [1.28*inch, 1.88*inch, 0.72*inch, 0.8*inch,
                                  1*inch, 1*inch, 0.72*inch, 0.75*inch, 0.72*inch, 0.88*inch]

            # Redefine param_to_col_index for highlighting based on the new fixed headers
            param_to_col_index = {
                'temperature': 2, 'humidity': 3, 'wind_speed': 4, 'wind_gust': 5,
                'rain': 7, 'pop': 8, 'visibility': 9
            }
            numeric_data_for_highlight = {p: []
                                          for p in param_to_col_index.keys()}

            weather_table_data = [weather_headers]

            # Max 7 days for the table to avoid excessively long PDF
            max_entries_for_table = 7 * 24  # Full 7 days hourly data from Open-Meteo

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

                table_row_index = row_idx + 1  # +1 for header row
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
            # Note needs to mention hourly data from Open-Meteo.
            note_text = "Note: 1 knot = 1.85 km/h; Wind Dir = Wind Direction; PoP = Probability of Precipitation (hourly derived based on presence of rain/snow for Open-Meteo). Rainfall values are per hour for Open-Meteo, per 3 hours for OpenWeatherMap."
            elements.append(Paragraph(note_text, small_note_style))
            elements.append(Spacer(1, 0.15*inch))
        else:
            elements.append(
                Paragraph("Weather Forecast Data Not Available", h2_style))
            elements.append(Spacer(1, 0.15*inch))

        # --- Weather Charts (Keep as is) ---
        if weather_data:
            elements.append(Paragraph("Weather Parameter Charts", h2_style))

            # --- Call charts with default English labels ---
            temp_hum_chart = self.create_temp_humidity_chart(
                weather_data)  # Default labels
            if temp_hum_chart:
                elements.append(temp_hum_chart)
                elements.append(Spacer(1, 0.1*inch))

            wind_chart = self.create_wind_chart(weather_data)  # Default labels
            if wind_chart:
                elements.append(wind_chart)
                elements.append(Spacer(1, 0.1*inch))

            rain_pop_chart = self.create_rain_pop_chart(
                weather_data)  # Default labels
            if rain_pop_chart:
                elements.append(rain_pop_chart)
                elements.append(Spacer(1, 0.1*inch))

            # Visibility chart (individual)
            vis_chart = self.create_chart(
                weather_data, 'visibility', 'Visibility (m)', 'Visibility Trend')  # Default labels
            if vis_chart:
                elements.append(vis_chart)
                elements.append(Spacer(1, 0.05*inch))
            # --- End chart calls ---

            charts_added = sum(1 for chart in [
                               temp_hum_chart, wind_chart, rain_pop_chart, vis_chart] if chart)
            if charts_added == 0:
                elements.append(
                    Paragraph("No data available to generate weather charts.", normal_style))
            elements.append(Spacer(1, 0.1*inch))

        # --- Footer (Keep as is) ---
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("--- Report End ---", footer_style))
        # Update footer for data source
        if api_source == "OWM":
            elements.append(
                Paragraph("Weather data © OpenWeatherMap", footer_style))
        elif api_source == "OpenMeteo":
            elements.append(
                Paragraph("Weather data © Open-Meteo.com", footer_style))
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
    # --- END MODIFIED generate_pdf_report ---

    # --- MODIFIED generate_vietnamese_pdf_report ---
    def generate_vietnamese_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source):

        page_width, page_height = landscape(letter)

        # --- Filename Logic (Vietnamese) ---
        # Use ui_location_name for filename safety
        name_map = {'Đ': 'D', 'đ': 'd'}
        safe_name = ui_location_name
        for k, v in name_map.items():
            safe_name = safe_name.replace(k, v)
        file_name_location = re.sub(
            r'[\\/*?:"<>|()]+', "", safe_name).replace(' ', '_')
        # Vietnamese filename
        file_name = f"BaoCao_ThoiTiet_{api_source}_{file_name_location}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

        doc = SimpleDocTemplate(
            file_name,
            pagesize=(page_width, page_height),
            topMargin=0.5*inch, bottomMargin=0.4*inch,
            leftMargin=0.5*inch, rightMargin=0.5*inch
        )

        elements = []
        styles = getSampleStyleSheet()
        # --- Define Styles (Get base styles first) ---
        title_style = styles['h1']
        h2_style = styles['h2']
        normal_style = styles['Normal']
        small_note_style = styles['Normal'].clone('SmallNote')
        footer_style = small_note_style.clone('Footer')

        # --- >>> ADD FONT ASSIGNMENTS HERE <<< ---
        title_style.fontName = VIETNAMESE_FONT_NAME_BOLD  # Use registered bold font
        title_style.alignment = 1
        title_style.fontSize = 16

        h2_style.fontName = VIETNAMESE_FONT_NAME_BOLD  # Use registered bold font
        h2_style.alignment = 0
        h2_style.fontSize = 14
        h2_style.spaceBefore = 15
        h2_style.spaceAfter = 4

        normal_style.fontName = VIETNAMESE_FONT_NAME  # Use registered regular font
        normal_style.leading = 15
        normal_style.fontSize = 11

        small_note_style.fontName = VIETNAMESE_FONT_NAME  # Use registered regular font
        small_note_style.fontSize = 9
        small_note_style.leading = 10
        small_note_style.textColor = colors.dimgray

        footer_style.fontName = VIETNAMESE_FONT_NAME  # Use registered regular font
        footer_style.alignment = 1
        footer_style.fontSize = 8
        # --- >>> END FONT ASSIGNMENTS <<< ---

        # --- Report Header (Translated & Revised Logic) ---
        elements.append(Paragraph("Báo Cáo Dự Báo Thời Tiết",
                        title_style))  # Vietnamese
        elements.append(Spacer(1, 0.1*inch))

        api_name = location_info.get('name', '')
        country_code = location_info.get('country', 'N/A')

        # Determine if API name/country provides extra info beyond the UI name
        api_details_parts = []
        # Add API name if it's different from UI name and not just coordinates
        if api_name and api_name != ui_location_name and not api_name.startswith("Coords ("):
            api_details_parts.append(api_name)
        # Add country code if valid
        if country_code and country_code != 'N/A':
            api_details_parts.append(country_code)

        # Display the UI name (predefined, custom, or default GPS string)
        location_string = f"<b>Vị trí:</b> {ui_location_name}"  # Vietnamese
        # Append API details in parentheses if they provide useful extra info
        if api_details_parts:
            api_details = ", ".join(api_details_parts)
            location_string += f" ({api_details})"

        elements.append(Paragraph(location_string, normal_style))
        # Coordinates, Timezone, Sunrise/Sunset, Generated time remain the same (but translated labels)
        elements.append(Paragraph(
            f"<b>Tọa độ:</b> Vĩ độ: {lat:.4f}, Kinh độ: {lon:.4f}", normal_style))  # Vietnamese
        elements.append(Paragraph(
            f"<b>Múi giờ:</b> {location_info.get('timezone', DEFAULT_TIMEZONE)}", normal_style))  # Vietnamese
        elements.append(Paragraph(
            f"<b>Mặt trời mọc:</b> {location_info.get('sunrise', 'N/A')}, <b>Mặt trời lặn:</b> {location_info.get('sunset', 'N/A')}", normal_style))  # Vietnamese
        elements.append(Paragraph(
            f"<b>Báo cáo tạo lúc:</b> {datetime.now(pytz.timezone(location_info.get('timezone', DEFAULT_TIMEZONE))).strftime('%Y-%m-%d %H:%M:%S %Z')}", normal_style))  # Vietnamese
        elements.append(
            Paragraph(f"<b>Nguồn dữ liệu:</b> {api_source}", normal_style))  # Vietnamese
        elements.append(Spacer(1, 0.2*inch))
        # --- End Report Header ---

        # --- Weather Forecast Table (Translated Headers) ---
        if weather_data:
            elements.append(
                Paragraph("Dự Báo Thời Tiết (5-7 Ngày Tới Theo Giờ)", h2_style))  # Vietnamese, adjusted length
            # Translated Headers
            weather_headers = ["Ngày/Giờ", "Mô Tả", "Nhiệt Độ\n(°C)", "Độ Ẩm\n(%)", "Tốc độ gió\n(knots)",
                               "Gió giật\n(knots)", "Hướng\ngió", "Lượng mưa\n(mm/h)", "XS mưa\n(%)", "Tầm nhìn\n(m)"]  # Changed mm/3h to mm/h
            weather_table_data = [weather_headers]

            # Data processing and highlighting logic remains the same
            numeric_data_for_highlight = {'temperature': [], 'wind_speed': [
            ], 'wind_gust': [], 'rain': [], 'visibility': [], 'humidity': [], 'pop': []}
            param_to_col_index = {'temperature': 2, 'humidity': 3, 'wind_speed': 4,
                                  'wind_gust': 5, 'rain': 7, 'pop': 8, 'visibility': 9}

            max_entries_for_table = 7 * 24  # Full 7 days hourly data from Open-Meteo

            for row_idx, item in enumerate(weather_data[:max_entries_for_table]):
                # --- Get English values -
                eng_desc = item.get('description', 'N/A')
                eng_wind_dir = item.get('wind_direction', 'N/A')
                # --- Translate ---
                # Check OpenWeatherMap translations first
                viet_desc = WEATHER_DESC_VIET.get(eng_desc, None)
                # If not found in OWM translations, check WMO codes (for Open-Meteo)
                if viet_desc is None:
                    # Attempt to find WMO code from description to get Vietnamese translation
                    # This is a bit of a hack, ideally WMO code would be passed directly.
                    # For a robust solution, you'd pass `wmo_code` from _fetch_weather_data_openmeteo
                    # and use WMO_WEATHER_CODES_VIET[wmo_code]
                    for code, desc_en in WMO_WEATHER_CODES_EN.items():
                        if desc_en == eng_desc:
                            viet_desc = WMO_WEATHER_CODES_VIET.get(
                                code, eng_desc)
                            break
                    if viet_desc is None:  # Fallback if no specific WMO translation found
                        viet_desc = eng_desc

                # Fallback to English if not found
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
               # --- Create row with translated values ---
                row = [
                    item['datetime'],
                    viet_desc,  # Use translated description
                    temp_formatted,
                    hum_formatted,
                    wind_formatted,
                    gust_formatted,
                    viet_wind_dir,  # Use translated wind direction
                    rain_formatted,
                    pop_formatted,
                    vis_formatted
                ]
                weather_table_data.append(row)

                # --- Highlighting logic ---
                table_row_index = row_idx + 1
                for param, value in [('temperature', temp_val), ('humidity', hum_val), ('wind_speed', wind_val), ('wind_gust', gust_val), ('rain', rain_val), ('pop', pop_val), ('visibility', vis)]:
                    if isinstance(value, (int, float)) and not math.isnan(value):
                        numeric_data_for_highlight[param].append(
                            (value, table_row_index))

            # Use same column widths and styles, but ensure font is set
            weather_col_widths = [1.45*inch, 1.65*inch, 0.75*inch, 0.8*inch,
                                  0.95*inch, 0.95*inch, 0.72*inch, 0.93*inch, 0.72*inch, 0.85*inch]
            weather_table = Table(weather_table_data,
                                  repeatRows=1, colWidths=weather_col_widths)
            weather_style_cmds = [('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                  # Apply Vietnamese font to whole table
                                  ('FONTNAME', (0, 0), (-1, -1),
                                   VIETNAMESE_FONT_NAME),
                                  # Bold header using registered bold name
                                  ('FONTNAME', (0, 0), (-1, 0),
                                   VIETNAMESE_FONT_NAME_BOLD),
                                  ('FONTSIZE', (0, 0), (-1, 0), 10.5), ('BOTTOMPADDING',
                                                                        (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 6),
                                  ('FONTSIZE', (0, 1), (-1, -1), 10), ('TOPPADDING', (0, 1),
                                                                       (-1, -1), 5), ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                                  ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ALIGN', (2, 1), (3, -1), 'RIGHT'), ('ALIGN', (4, 1), (5, -1), 'RIGHT'), ('ALIGN', (7, 1), (9, -1), 'RIGHT'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightblue])]
            # Highlighting logic remains the same
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
            # Translated Note
            # Translated note updated for Open-Meteo differences
            note_text_viet = "Ghi chú: 1 knot = 1.85 km/h; Hướng gió = Hướng gió thổi tới; XS mưa = Xác suất có mưa (được ước tính theo giờ dựa trên sự hiện diện của mưa/tuyết đối với Open-Meteo). Giá trị lượng mưa là mỗi giờ đối với Open-Meteo, mỗi 3 giờ đối với OpenWeatherMap."
            elements.append(Paragraph(note_text_viet, small_note_style))
            elements.append(Spacer(1, 0.15*inch))
        else:
            elements.append(
                Paragraph("Không có dữ liệu dự báo thời tiết", h2_style))  # Vietnamese
            elements.append(Spacer(1, 0.15*inch))

        # --- Weather Charts (Translated Titles/Labels) ---
        if weather_data:
            elements.append(
                Paragraph("Biểu Đồ Thông Số Thời Tiết", h2_style))  # Vietnamese

            # --- Call charts with Vietnamese labels ---
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
                rain_ylabel='Lượng mưa (mm/h)',  # Changed to mm/h
                pop_ylabel='Xác Suất Mưa (%)',
                title_text='Xu Hướng Lượng Mưa và Xác Suất Mưa',
                rain_label='Lượng mưa',
                pop_label='XS Mưa'
            )
            if rain_pop_chart:
                elements.append(rain_pop_chart)
                elements.append(Spacer(1, 0.1*inch))

            # Visibility chart (individual) - REMOVED xlabel_text
            vis_chart = self.create_chart(
                weather_data,
                'visibility',
                'Tầm nhìn (m)',       # ylabel
                'Tầm Nhìn Xa',  # title
                xlabel_text='Ngày/Giờ'
            )
            if vis_chart:
                elements.append(vis_chart)
                elements.append(Spacer(1, 0.05*inch))
            # --- End chart calls ---

            charts_added = sum(1 for chart in [
                               temp_hum_chart, wind_chart, rain_pop_chart, vis_chart] if chart)
            if charts_added == 0:
                elements.append(
                    Paragraph("Không có dữ liệu để tạo biểu đồ.", normal_style))  # Vietnamese
            elements.append(Spacer(1, 0.1*inch))

        # --- Footer (Translated) ---
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("--- Kết thúc báo cáo ---",
                        footer_style))  # Vietnamese
        # Update footer for data source
        if api_source == "OWM":
            elements.append(
                Paragraph("Dữ liệu thời tiết © OpenWeatherMap", footer_style))  # Vietnamese
        elif api_source == "OpenMeteo":
            elements.append(
                Paragraph("Dữ liệu thời tiết © Open-Meteo.com", footer_style))  # Vietnamese
        elements.append(Paragraph(
            "Tạo bởi Weather Reporter Tool | 2025 © TungTT", footer_style))  # Vietnamese

        # Build the PDF
        try:
            doc.build(elements)
            print(f"PDF report generated (Vietnamese): {file_name}")
        except Exception as build_err:
            print(f"Error building Vietnamese PDF: {build_err}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self, "Lỗi PDF", f"Không thể tạo báo cáo PDF (Tiếng Việt):\n{build_err}")  # Vietnamese
    # --- END NEW VIETNAMESE PDF FUNCTION ---

    # ... (Keep closeEvent) ...
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

# --- END OF FILE ---
