# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QRadioButton,
                             QMessageBox)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, letter
import requests
import json
from datetime import datetime, timedelta, timezone
import pytz
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry  # Correct import
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.platypus import Image
import traceback  # For error printing
from bs4 import BeautifulSoup  # Needed again for finding PDF link
import re  # Needed for parsing PDF text
from urllib.parse import urljoin  # Needed for PDF link
import io  # For handling PDF download in memory

# --- Add pdfplumber import ---
try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber library not found.")
    print("Please install it using: pip install pdfplumber")
    pdfplumber = None  # Set to None if import fails


# --- LOCATION_TIMEZONES dictionary (ensure it's complete) ---
LOCATION_TIMEZONES = {'VN': 'Asia/Ho_Chi_Minh', 'US': 'America/New_York', }
DEFAULT_TIMEZONE = 'Asia/Ho_Chi_Minh'

# --- Constants & Helper Function for Tidal ---
TIDAL_ALARM_1 = 1.4
TIDAL_ALARM_2 = 1.5
TIDAL_INDEX_URL = "http://www.kttv-nb.org.vn/index.php/thong-tin-kttv/thuy-van"


def get_tidal_highlight_color(level):
    # ... (keep implementation) ...
    if level is None:
        return None
    try:
        level_float = float(level)
        if level_float >= TIDAL_ALARM_2:
            return colors.red
        elif level_float >= TIDAL_ALARM_1:
            return colors.yellow
    except (ValueError, TypeError):
        return None
    return None


# --- REVISED PDF Scraping Function (Looks for Embed/Iframe/A link) ---
def scrape_tidal_data_from_pdf(index_url):
    if not pdfplumber:
        print("PDF scraping disabled: pdfplumber library not available.")
        return None, None  # Cannot proceed without pdfplumber

    print(f"Starting PDF tidal data scraping from index: {index_url}")
    session = requests.Session()  # Use a session
    article_url = None
    pdf_src_url_relative = None  # Store relative src/href found
    pdf_url = None  # Store final absolute URL
    tidal_forecast = []
    tidal_historical = []  # Will store latest observed peak

    try:
        # --- Step 1: Find the ARTICLE link on the index page ---
        print("Fetching index page to find ARTICLE link...")
        index_response = session.get(index_url, timeout=25)
        index_response.raise_for_status()
        index_response.encoding = 'utf-8'
        index_soup = BeautifulSoup(index_response.text, 'lxml')
        print("Index page fetched.")
        bulletin_title_pattern = re.compile(
            r"TIN DỰ BÁO THỦY VĂN TP\.?HCM NGÀY\s+\d{1,2}/\d{1,2}(?:/\d{4})?", re.IGNORECASE)
        all_links = index_soup.find_all('a', href=True)
        article_link_tag = None
        print(f"Searching {len(all_links)} links for bulletin title...")
        for link in all_links:
            if bulletin_title_pattern.search(link.get_text(strip=True)):
                article_link_tag = link
                print(f"Found article link: Href='{link['href']}'")
                break
        if article_link_tag:
            article_url = urljoin(index_url, article_link_tag['href'])
        else:
            print("Error: Could not find article link matching bulletin title.")
            return None, None
        print(f"Article URL: {article_url}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching/parsing index page: {e}")
        return None, None
    except Exception as e:
        print(f"Error processing index page: {e}\n{traceback.format_exc()}")
        return None, None

    if not article_url:
        return None, None

    try:
        # --- Step 2: Fetch ARTICLE page, find EMBEDDED PDF source (embed/iframe/a) ---
        print(f"Fetching article page: {article_url}")
        article_response = session.get(article_url, timeout=25)
        article_response.raise_for_status()
        article_response.encoding = 'utf-8'
        article_soup = BeautifulSoup(article_response.text, 'lxml')
        print("Article page fetched.")
        content_area = article_soup.find(
            'div', class_='item-page') or article_soup.body
        if not content_area:
            print("Error: Cannot find content area of article page.")
            return None, None

        print("Searching for PDF source (embed/iframe/a) in article content...")
        pdf_source_found = False
        # Prioritize <embed> or <iframe> pointing to a PDF
        embed_tag = content_area.find(
            'embed', src=re.compile(r'\.pdf$', re.IGNORECASE))
        if embed_tag and embed_tag.get('src'):
            pdf_src_url_relative = embed_tag['src']
            print(f"Found PDF source in <embed>: {pdf_src_url_relative}")
            pdf_source_found = True
        else:
            iframe_tag = content_area.find(
                'iframe', src=re.compile(r'\.pdf$', re.IGNORECASE))
            if iframe_tag and iframe_tag.get('src'):
                pdf_src_url_relative = iframe_tag['src']
                print(f"Found PDF source in <iframe>: {pdf_src_url_relative}")
                pdf_source_found = True
            else:
                # Fallback: Look for a direct download link <a>
                link_tag = content_area.find(
                    'a', href=re.compile(r'\.pdf$', re.IGNORECASE))
                if link_tag and link_tag.get('href'):
                    pdf_src_url_relative = link_tag['href']
                    print(
                        f"Found PDF source in <a> link: {pdf_src_url_relative}")
                    pdf_source_found = True

        if pdf_source_found and pdf_src_url_relative:
            # Construct absolute URL using the ARTICLE's URL as the base
            pdf_url = urljoin(article_url, pdf_src_url_relative)
            print(f"Constructed absolute PDF URL: {pdf_url}")
        else:
            print(
                f"Error: Could not find PDF source (embed/iframe/a) within article page: {article_url}")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching/parsing article page: {e}")
        return None, None
    except Exception as e:
        print(f"Error processing article page: {e}\n{traceback.format_exc()}")
        return None, None

    if not pdf_url:
        return None, None

    # --- Step 3: Download PDF ---
    try:
        print(f"Downloading PDF from: {pdf_url}")
        pdf_response = session.get(pdf_url, timeout=30, stream=True)
        pdf_response.raise_for_status()
        content_type = pdf_response.headers.get('Content-Type', '').lower()
        if 'application/pdf' not in content_type:
            print(f"Warning: URL content type is not PDF ('{content_type}').")
        pdf_content = io.BytesIO()
        for chunk in pdf_response.iter_content(chunk_size=8192):
            pdf_content.write(chunk)
        pdf_content.seek(0)
        print("PDF downloaded.")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None, None
    except Exception as e:
        print(f"Error during PDF download: {e}\n{traceback.format_exc()}")
        return None, None

    # --- Step 4: Extract data using pdfplumber ---
    try:
        print("Opening PDF with pdfplumber...")
        with pdfplumber.open(pdf_content) as pdf:
            print(f"PDF has {len(pdf.pages)} pages.")
            # ...(Keep the detailed PDF parsing logic from the previous version)...
            # ...(It searches pages for tables and regex patterns)...
            found_forecast_table = False
            found_observed_peak = False
            current_year = datetime.now().year

            for i, page in enumerate(pdf.pages):
                if found_forecast_table and found_observed_peak:
                    break
                print(f"\n--- Processing PDF Page {i+1} ---")
                page_text = page.extract_text(
                    x_tolerance=3, y_tolerance=3, layout=True)
                if not page_text:
                    print("No text extracted.")
                    continue

                # --- Forecast Table Extraction ---
                if not found_forecast_table and "dự báo mực nước cao nhất" in page_text.lower() and "phú an" in page_text.lower():
                    print("Forecast keywords found. Extracting tables...")
                    tables = page.extract_tables(table_settings={"vertical_strategy": "text", "horizontal_strategy": "text", "intersection_x_tolerance": 5, "join_y_tolerance": 5, "snap_x_tolerance": 5}) or \
                        page.extract_tables(table_settings={
                                            "vertical_strategy": "lines", "horizontal_strategy": "lines"})  # Fallback
                    print(f"Found {len(tables)} potential tables.")
                    for table_num, table in enumerate(tables):
                        if found_forecast_table:
                            break
                        if not table or len(table) < 2:
                            continue
                        header = [str(h).lower().strip()
                                  for h in table[0] if h]
                        if ('ngày' in header or 'ngay' in header) and ('giờ' in header or 'gio' in header) and ('mực nước' in str(header) or 'muc nuoc' in str(header)):
                            print(
                                f"Potential forecast table found (Table {table_num+1}). Processing...")
                            for row_idx, row in enumerate(table[1:]):
                                cells = [str(c).strip().replace('\n', ' ')
                                         for c in row if c is not None]
                                if len(cells) >= 3:
                                    try:
                                        date_str = cells[0]
                                        time_str = cells[1]
                                        level_str = cells[2].split(
                                            ' ')[0].replace(',', '.')
                                        if not re.match(r'\d{1,2}[/.]\d{1,2}', date_str):
                                            continue
                                        if not re.match(r'\d{1,2}h(?:\d{2})?', time_str, re.IGNORECASE):
                                            continue
                                        dt_obj = None
                                        date_match = re.match(
                                            r'(\d{1,2})[/.](\d{1,2})(?:[/.](\d{2,4}))?', date_str)
                                        if date_match:
                                            day, mon, yr_str = date_match.groups()
                                            if yr_str:
                                                dt_obj = datetime.strptime(
                                                    f"{day}/{mon}/{yr_str}", '%d/%m/%y' if len(yr_str) == 2 else '%d/%m/%Y')
                                            else:
                                                dt_obj = datetime.strptime(
                                                    f"{day}/{mon}/{current_year}", '%d/%m/%Y')
                                        if dt_obj:
                                            level = float(level_str)
                                            if datetime.now()-timedelta(days=1) <= dt_obj <= datetime.now()+timedelta(days=10):
                                                tidal_forecast.append({'date': dt_obj.strftime(
                                                    '%d/%m/%Y'), 'time': time_str, 'level': level})
                                                found_forecast_table = True  # Mark found
                                    except:
                                        pass  # Ignore row errors silently for now
                            # if found_forecast_table: print("Finished forecast table.")

                # --- Observed Peak Regex Extraction ---
                if not found_observed_peak and "mực nước cao nhất thực đo" in page_text.lower() and "phú an" in page_text.lower():
                    print("Observed keywords found. Applying regex...")
                    regex = r"Mực nước cao nhất (?:thực đo|quan trắc).*?Phú An.*?là\s*(\d[.,]\d{1,2})\s?m(?:\s*\(.*?(?:BĐ|báo động).*?\))?.*?xuất hiện lúc\s*(\d{1,2}h(?:\d{2})?).*?ngày\s*(\d{1,2}[/.]\d{1,2}(?:[/.]\d{2,4})?)"
                    match = re.search(regex, page_text,
                                      re.IGNORECASE | re.DOTALL)
                    if match:
                        print("Regex match found for observed peak.")
                        try:
                            level_str = match.group(1).replace(',', '.')
                            time_str = match.group(2)
                            date_str = match.group(3)
                            level = float(level_str)
                            dt_obj = None
                            date_match = re.match(
                                r'(\d{1,2})[/.](\d{1,2})(?:[/.](\d{2,4}))?', date_str)
                            if date_match:
                                day, mon, yr_str = date_match.groups()
                                if yr_str:
                                    dt_obj = datetime.strptime(
                                        f"{day}/{mon}/{yr_str}", '%d/%m/%y' if len(yr_str) == 2 else '%d/%m/%Y')
                                else:
                                    dt_this = datetime.strptime(
                                        f"{day}/{mon}/{current_year}", '%d/%m/%Y')
                                    dt_prev = datetime.strptime(
                                        f"{day}/{mon}/{current_year-1}", '%d/%m/%Y')
                                    dt_obj = dt_prev if dt_this > datetime.now()+timedelta(days=1) else dt_this
                            if dt_obj:
                                tidal_historical.append({'date': dt_obj.strftime(
                                    '%d/%m/%Y'), 'time': time_str, 'level': level})
                                print(
                                    f"Extracted historical peak: {tidal_historical[-1]}")
                                found_observed_peak = True
                        except Exception as e:
                            print(f"Error parsing observed regex: {e}")
                    # else: print("Observed regex did not match.")

        print("\n--- PDF Processing Finished ---")
        if not tidal_forecast:
            print("Warning: No forecast data extracted.")
        if not tidal_historical:
            print("Warning: No observed peak extracted.")
        return tidal_forecast, tidal_historical

    except pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect:
        print("Error: PDF password protected.")
        return None, None
    except Exception as e:
        print(f"Error during PDF parsing: {e}\n{traceback.format_exc()}")
        return None, None
    finally:
        session.close()


class WeatherCrawlerApp(QWidget):
    # ... (Keep __init__) ...
    # ... (Keep initUI) ...
    # ... (Keep toggle_gps_input) ...
    # ... (Keep get_coordinates) ...
    # ... (Keep crawl_data_and_generate_report) ...
    # ... (Keep create_requests_session) ...
    # ... (Keep fetch_weather_data) ...
    # ... (Keep process_forecast_data) ...
    # ... (Keep create_chart) ...
    # ... (Keep generate_pdf_report) ...

    # --- __init__ ---
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather & Tide Reporter")
        self.setGeometry(200, 200, 540, 300)
        icon_path = "weather_icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon {icon_path} not found")
        self.default_lat = 7.5783
        self.default_lon = 108.8694
        self.api_key = os.environ.get(
            "OPENWEATHERMAP_API_KEY", "e1a69775e0d7c149a4e2bdb69bb59a82")  # Replace or use env var
        if self.api_key.startswith("YOUR"):
            print("WARNING: Update OWM API key.")
        self.initUI()

    # --- initUI ---
    def initUI(self):
        main_layout = QVBoxLayout()
        input_group_box = QWidget()
        input_layout = QVBoxLayout(input_group_box)
        input_label = QLabel("Select Location:")
        input_label.setFont(QFont("Arial", 12, QFont.Bold))
        input_layout.addWidget(input_label)
        self.locations = {'Lan Tay Platform': (7.5783, 108.8694), 'Rong Doi Platform': (7.7925, 108.2021),
                          'An Phu Office (HCMC)': (10.809427, 106.736553), 'Vung Tau Airport': (10.376001, 107.093239)}
        self.location_radios = {}
        for name, coords in self.locations.items():
            radio = QRadioButton(f"{name} ({coords[0]:.4f}, {coords[1]:.4f})")
            self.location_radios[name] = radio
            input_layout.addWidget(radio)
            radio.toggled.connect(self.toggle_gps_input)
        self.gps_radio = QRadioButton("Enter Custom GPS Coordinates:")
        self.lat_label = QLabel("Latitude:")
        self.lat_input = QLineEdit()
        self.lon_label = QLabel("Longitude:")
        self.lon_input = QLineEdit()
        self.lat_input.setEnabled(False)
        self.lon_input.setEnabled(False)
        self.gps_radio.toggled.connect(self.toggle_gps_input)
        gps_input_layout = QHBoxLayout()
        gps_input_layout.addWidget(self.lat_label)
        gps_input_layout.addWidget(self.lat_input)
        gps_input_layout.addWidget(self.lon_label)
        gps_input_layout.addWidget(self.lon_input)
        input_layout.addWidget(self.gps_radio)
        input_layout.addLayout(gps_input_layout)
        self.location_radios['Lan Tay Platform'].setChecked(True)  # Default
        result_label = QLabel("Create Report")
        result_label.setFont(QFont("Arial", 12, QFont.Bold))
        result_label.setAlignment(Qt.AlignCenter)
        crawl_button = QPushButton("Generate Weather & Tide PDF Report")
        crawl_button.clicked.connect(self.crawl_data_and_generate_report)
        main_layout.addWidget(input_group_box)
        main_layout.addWidget(result_label)
        main_layout.addWidget(crawl_button)
        main_layout.addStretch()
        self.setLayout(main_layout)

    # --- toggle_gps_input ---
    def toggle_gps_input(self):
        is_gps = self.gps_radio.isChecked()
        self.lat_input.setEnabled(is_gps)
        self.lon_input.setEnabled(is_gps)

    # --- get_coordinates ---
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
                return lat, lon, f"Custom ({lat:.4f}, {lon:.4f})"
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Invalid Lat/Lon.")
                return None, None, None
        else:
            for name, radio in self.location_radios.items():
                if radio.isChecked():
                    return self.locations[name][0], self.locations[name][1], name
        QMessageBox.warning(self, "Input Error", "Select location.")
        return None, None, None

    # --- crawl_data_and_generate_report ---
    def crawl_data_and_generate_report(self):
        lat, lon, loc_name = self.get_coordinates()
        if lat is None:
            return
        weather_data = None
        location_info = None
        tidal_forecast = None
        tidal_historical = None
        default_loc_info = {'name': loc_name, 'country': 'N/A',
                            'sunrise': 'N/A', 'sunset': 'N/A', 'timezone': DEFAULT_TIMEZONE}
        try:  # Fetch Weather
            print("Fetching weather...")
            weather_data, location_info = self.fetch_weather_data(
                lat, lon, "forecast")
            if not location_info:
                location_info = default_loc_info
            if not weather_data:
                QMessageBox.warning(
                    self, "Weather", "Weather data fetch failed.")
            else:
                print("Weather fetched.")
        except Exception as e:
            QMessageBox.critical(
                self, "Weather Error", f"Weather fetch error: {e}\n{traceback.format_exc()}")
            location_info = default_loc_info
        if 'An Phu Office (HCMC)' in loc_name:  # Fetch Tidal PDF for HCMC
            print("HCMC selected, scraping tidal PDF...")
            if not pdfplumber:
                QMessageBox.warning(
                    self, "Tidal Error", "pdfplumber lib missing. Cannot scrape PDF.")
            else:
                try:
                    tidal_forecast, tidal_historical = scrape_tidal_data_from_pdf(
                        TIDAL_INDEX_URL)
                    if not tidal_forecast and not tidal_historical:
                        QMessageBox.warning(
                            self, "Tidal Warning", "No tidal data extracted from PDF.")
                    else:
                        print("Tidal PDF scraped.")
                except Exception as e:
                    QMessageBox.critical(
                        self, "Tidal Error", f"Tidal scrape error: {e}\n{traceback.format_exc()}")
                    tidal_forecast, tidal_historical = None, None
        else:
            print("Non-HCMC location, skipping tidal.")
        if weather_data or tidal_forecast or tidal_historical:  # Generate Report
            try:
                print("Generating PDF...")
                self.generate_pdf_report(
                    lat, lon, weather_data, location_info, tidal_forecast, tidal_historical)
                QMessageBox.information(self, "Success", "Report generated.")
                print("PDF generated.")
            except Exception as e:
                QMessageBox.critical(
                    self, "PDF Error", f"PDF generation error: {e}\n{traceback.format_exc()}")
                print(f"PDF failed: {e}")
        else:  # No data
            if location_info:
                QMessageBox.warning(
                    self, "Error", "No data to generate report.")
            print("Report skipped: No data.")

    # --- create_requests_session ---
    def create_requests_session(self):
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[
                        404, 408, 429, 500, 502, 503, 504], allowed_methods=["GET"])
        adapter = HTTPAdapter(
            max_retries=retries, pool_connections=3, pool_maxsize=3, pool_block=True)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    # --- fetch_weather_data ---
    def fetch_weather_data(self, lat, lon, data_type):
        # (Keep implementation)
        base_url = "https://api.openweathermap.org/data/2.5/"
        units = "metric"
        session = self.create_requests_session()
        timeout = (15, 30)
        current_data = None
        location_info = None
        processed_forecast = None
        try:
            current_url = f"{base_url}weather?lat={lat}&lon={lon}&appid={self.api_key}&units={units}"
            current_response = session.get(current_url, timeout=timeout)
            current_response.raise_for_status()
            current_data = current_response.json()
            forecast_url = f"{base_url}forecast?lat={lat}&lon={lon}&appid={self.api_key}&units={units}&cnt=40"
            forecast_response = session.get(forecast_url, timeout=timeout)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            country_code = current_data.get('sys', {}).get('country')
            tz_str = DEFAULT_TIMEZONE
            if country_code and country_code in LOCATION_TIMEZONES:
                tz_str = LOCATION_TIMEZONES[country_code]
            local_tz = pytz.timezone(tz_str)
            sys_info = current_data.get('sys', {})
            sunrise_ts = sys_info.get('sunrise')
            sunset_ts = sys_info.get('sunset')
            location_info = {'name': current_data.get('name', 'Unknown'), 'country': sys_info.get('country', 'N/A'),
                             'sunrise': datetime.fromtimestamp(sunrise_ts, tz=timezone.utc).astimezone(local_tz).strftime('%H:%M') if sunrise_ts else 'N/A',
                             'sunset': datetime.fromtimestamp(sunset_ts, tz=timezone.utc).astimezone(local_tz).strftime('%H:%M') if sunset_ts else 'N/A',
                             'timezone': tz_str}
            processed_forecast = self.process_forecast_data(
                forecast_data, local_tz)
        except requests.exceptions.Timeout as e:
            print(f"Timeout: {e}")
            raise e
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            name = "N/A"
            country = "N/A"
            tz = DEFAULT_TIMEZONE
            if current_data:
                name = current_data.get('name', 'Unknown')
                country = current_data.get('sys', {}).get('country', 'N/A')
                cc = current_data.get('sys', {}).get('country')
            if cc and cc in LOCATION_TIMEZONES:
                tz = LOCATION_TIMEZONES[cc]
            location_info = {'name': name, 'country': country,
                             'sunrise': 'N/A', 'sunset': 'N/A', 'timezone': tz}
        except Exception as e:
            print(f"Weather fetch error: {e}")
            traceback.print_exc()
            location_info = location_info or {
                'name': 'Error', 'country': 'N/A', 'sunrise': 'N/A', 'sunset': 'N/A', 'timezone': DEFAULT_TIMEZONE}
        finally:
            session.close()
        return processed_forecast, location_info

    # --- process_forecast_data ---
    def process_forecast_data(self, data, local_tz):
        # (Keep implementation)
        def degrees_to_direction(deg):
            dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                    'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
            idx = round((deg % 360)/(360./len(dirs))) % len(dirs)
            return dirs[idx]
        processed = []
        now = datetime.now(local_tz)
        end = now+timedelta(days=5)
        for item in data.get('list', []):
            try:
                dt_utc = item.get('dt')
                if not dt_utc:
                    continue
                local_time = datetime.fromtimestamp(
                    dt_utc, tz=timezone.utc).astimezone(local_tz)
                if now < local_time <= end:
                    main = item.get('main', {})
                    weather = item.get('weather', [{}])[0]
                    wind = item.get('wind', {})
                    rain = item.get('rain', {}).get('3h', 0)
                    pop = item.get('pop', 0)*100
                    temp = main.get('temp')
                    hum = main.get('humidity')
                    ws_mps = wind.get('speed')
                    wg_mps = wind.get('gust')
                    wd_deg = wind.get('deg')
                    desc = weather.get('description', 'N/A').capitalize()
                    ws_kn = round(ws_mps*1.94384,
                                  1) if ws_mps is not None else 'N/A'
                    wg_kn = 'N/A'
                    if wg_mps is not None:
                        try:
                            wg_kn = round(float(wg_mps)*1.94384449, 1)
                        except:
                            pass
                    wd_dir = degrees_to_direction(
                        wd_deg) if wd_deg is not None else 'N/A'
                    vis_val = item.get('visibility')
                    vis_fl = float(vis_val) if isinstance(
                        vis_val, (int, float)) else 'N/A'
                    processed.append({'datetime': local_time.strftime('%Y-%m-%d %H:%M:%S'), 'description': desc,
                                      'temperature': float(temp) if temp is not None else 'N/A',
                                      'humidity': float(hum) if hum is not None else 'N/A',
                                      'wind_speed': ws_kn, 'wind_gust': wg_kn, 'wind_direction': wd_dir,
                                      'rain': float(rain) if rain is not None else 0.0,
                                      'visibility': vis_fl, 'pop': float(pop) if pop is not None else 'N/A'})
            except Exception as e:
                print(f"Weather processing error: {e}")
                continue
        return processed

    # --- create_chart ---
    def create_chart(self, data, param, ylabel, title, date_key='datetime', date_fmt='%Y-%m-%d %H:%M:%S'):
        # (Keep implementation)
        plt.figure(figsize=(8.5, 2.8))
        dates = []
        values = []
        for item in data:
            val = item.get(param)
            dt = item.get(date_key)
            if val != 'N/A' and dt is not None:
                try:
                    cur_dt = dt if isinstance(
                        dt, datetime) else datetime.strptime(str(dt), date_fmt)
                    dates.append(cur_dt)
                    values.append(float(val))
                except:
                    continue
        if not dates or not values:
            plt.close()
            return None
        plt.plot(dates, values, marker='.', linestyle='-')
        plt.title(title, fontsize=10)
        plt.xlabel('Date/Time', fontsize=8)
        plt.ylabel(ylabel, fontsize=8)
        plt.xticks(rotation=30, ha='right', fontsize=7)
        plt.yticks(fontsize=7)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        img = Image(buf, width=7.5*inch, height=2.5*inch)
        img.hAlign = 'CENTER'
        return img

    # --- generate_pdf_report ---
    def generate_pdf_report(self, lat, lon, weather_data, location_info, tidal_forecast, tidal_historical):
        # (Keep implementation - handles potentially empty tidal lists)
        page_width = letter[1]
        page_height = letter[0]
        custom_page_size = (page_width, page_height)
        loc_safe = location_info.get('name', 'Unknown').replace(' ', '_').replace(
            '/', '_').replace('\\', '_').replace('(', '').replace(')', '')
        fname = f"Weather_Tide_Report_{loc_safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(fname, pagesize=custom_page_size, topMargin=0.8 *
                                inch, bottomMargin=0.5*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        # Styles
        title_style = styles['h1']
        title_style.alignment = 1
        sub_title_style = styles['h2']
        sub_title_style.spaceBefore = 10
        sub_title_style.spaceAfter = 2
        normal_style = styles['Normal']
        normal_style.leading = 14
        small_note_style = styles['Normal'].clone('SmallNote')
        small_note_style.fontSize = 8
        small_note_style.leading = 10
        tbl_hdr = ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
        tbl_grid = ('GRID', (0, 0), (-1, -1), 1, colors.black)
        tbl_align_c = ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        tbl_bg_hdr = ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey)
        tbl_txt_hdr = ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke)
        tbl_fs = ('FONTSIZE', (0, 0), (-1, -1), 9)
        tbl_pad = ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        # Header
        elements.append(Paragraph("Weather & Tide Report", title_style))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            f"Location: {location_info.get('name','N/A')} ({location_info.get('country','N/A')})", normal_style))
        elements.append(
            Paragraph(f"Coords: Lat: {lat:.4f}, Lon: {lon:.4f}", normal_style))
        sr = location_info.get('sunrise', 'N/A')
        ss = location_info.get('sunset', 'N/A')
        elements.append(Paragraph(
            f"Sunrise: {sr}, Sunset: {ss} (Local: {location_info.get('timezone','N/A')})", normal_style))
        elements.append(Spacer(1, 0.3*inch))
        # Weather Table
        if weather_data:
            elements.append(Paragraph("Weather Forecast", sub_title_style))
            elements.append(Spacer(1, 0.1*inch))
            hdrs = ["Date/Time", "Desc", "Temp", "Hum", "Wind",
                    "Gust", "Dir", "Rain", "PoP", "Vis"]  # Shorter headers
            tbl_data = [hdrs]

            def fmt(v, p=1): return f"{v:.{p}f}" if isinstance(
                v, (int, float)) else 'N/A'
            for item in weather_data:
                row = [item['datetime'], item['description'], fmt(item.get('temperature'), 1), fmt(item.get('humidity'), 0),
                       fmt(item.get('wind_speed'), 1), fmt(
                           item.get('wind_gust'), 1), item.get('wind_direction', 'N/A'),
                       fmt(item.get('rain'), 1), fmt(item.get('pop'), 0), fmt(item.get('visibility'), 0)]
                tbl_data.append(row)
            wids = [1.5*inch, 1.4*inch, 0.5*inch, 0.5*inch, 0.6*inch,
                    0.6*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.6*inch]  # Adjusted
            tbl = Table(tbl_data, colWidths=wids, repeatRows=1)
            sty = TableStyle([tbl_bg_hdr, tbl_txt_hdr, tbl_align_c, tbl_grid, tbl_hdr, tbl_fs, tbl_pad, ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                              ('ALIGN', (2, 1), (-1, -1), 'RIGHT'), ('FONTSIZE', (0, 1), (-1, -1), 8), ('LEFTPADDING', (1, 1), (1, -1), 4), ('RIGHTPADDING', (2, 1), (-1, -1), 4)])
            tbl.setStyle(sty)
            elements.append(tbl)
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(
                "Units: Temp(°C), Hum(%), Wind/Gust(kn), Rain(mm), PoP(%), Vis(m).", small_note_style))
            elements.append(Spacer(1, 0.3*inch))
        else:
            elements.append(Paragraph("Weather data N/A.", normal_style))
            elements.append(Spacer(1, 0.3*inch))
        # Tidal Forecast Table
        if tidal_forecast:
            elements.append(
                Paragraph("Tidal Forecast - Phu An", sub_title_style))
            elements.append(Spacer(1, 0.1*inch))
            tf_hdrs = ["Date", "Time", "Level (m)"]
            tf_data = [tf_hdrs]+[[i['date'], i['time'],
                                  f"{i['level']:.2f}"] for i in tidal_forecast]
            tf_wids = [1.5*inch, 1.5*inch, 1.5*inch]
            tf_tbl = Table(tf_data, colWidths=tf_wids)
            tf_sty = TableStyle(
                [tbl_bg_hdr, tbl_txt_hdr, tbl_align_c, tbl_grid, tbl_hdr, tbl_fs, tbl_pad])
            for r, row in enumerate(tidal_forecast, 1):
                clr = get_tidal_highlight_color(row.get('level'))
                if clr:
                    tf_sty.add('BACKGROUND', (0, r), (-1, r), clr)
            tf_tbl.setStyle(tf_sty)
            elements.append(tf_tbl)
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(
                f"Highlight: Yellow≥{TIDAL_ALARM_1}m, Red≥{TIDAL_ALARM_2}m", small_note_style))
            elements.append(Spacer(1, 0.3*inch))
        elif location_info.get('name', '').startswith('An Phu'):
            elements.append(Paragraph("Tidal forecast N/A.", normal_style))
            elements.append(Spacer(1, 0.3*inch))
        # Tidal Observed Table
        if tidal_historical:  # Display if not empty
            elements.append(
                Paragraph("Observed Tidal Peak - Phu An", sub_title_style))
            elements.append(Spacer(1, 0.1*inch))
            th_hdrs = ["Date", "Time", "Level (m)"]
            th_data = [th_hdrs]+[[i['date'], i['time'],
                                  f"{i['level']:.2f}"] for i in tidal_historical]
            th_tbl = Table(th_data, colWidths=tf_wids)
            th_sty = TableStyle(
                [tbl_bg_hdr, tbl_txt_hdr, tbl_align_c, tbl_grid, tbl_hdr, tbl_fs, tbl_pad])
            for r, row in enumerate(tidal_historical, 1):
                clr = get_tidal_highlight_color(row.get('level'))
                if clr:
                    th_sty.add('BACKGROUND', (0, r), (-1, r), clr)
            th_tbl.setStyle(th_sty)
            elements.append(th_tbl)
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(
                f"Highlight: Yellow≥{TIDAL_ALARM_1}m, Red≥{TIDAL_ALARM_2}m", small_note_style))
            elements.append(Spacer(1, 0.3*inch))
        # Only show message if HCMC loc and *no* historical data found
        elif location_info.get('name', '').startswith('An Phu') and not tidal_historical:
            elements.append(
                Paragraph("Observed tidal peak N/A.", normal_style))
            elements.append(Spacer(1, 0.3*inch))
        # Weather Charts
        if weather_data:
            elements.append(Paragraph("Weather Charts", sub_title_style))
            elements.append(Spacer(1, 0.2*inch))
            chart_params = [('temperature', '°C', 'Temp'), ('humidity', '%', 'Hum'), (
                'wind_speed', 'kn', 'Wind'), ('visibility', 'm', 'Vis'), ('rain', 'mm', 'Rain')]
            added = 0
            for p, u, t in chart_params:
                if any(isinstance(item.get(p), (int, float)) for item in weather_data):
                    chart = self.create_chart(weather_data, p, u, f"{t} Chart")
                    if chart:
                        elements.append(chart)
                        elements.append(Spacer(1, 0.1*inch))
                        added += 1
                else:
                    print(f"Skip chart '{t}': No data.")
            if added == 0:
                elements.append(
                    Paragraph("No data for charts.", small_note_style))
            elements.append(Spacer(1, 0.2*inch))
        # Footer
        elements.append(Spacer(1, 0.2*inch))
        footer_style = small_note_style.clone('Footer')
        footer_style.alignment = 1
        elements.append(Paragraph("--- Report End ---", footer_style))
        elements.append(Paragraph(
            "Weather: OpenWeatherMap. Tide: Extracted from kttv-nb.org.vn PDF.", footer_style))
        elements.append(Paragraph("2025 © TungTT", footer_style))
        # Build
        try:
            doc.build(elements)
        except Exception as e:
            print(f"PDF build error: {e}")
            raise


# --- Main execution block ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    if pdfplumber is None:
        QMessageBox.critical(None, "Dependency Error",
                             "Required library 'pdfplumber' not found.\nPlease install: pip install pdfplumber\n\nTidal PDF scraping disabled.")
    weather_app = WeatherCrawlerApp()
    weather_app.show()
    sys.exit(app.exec_())
