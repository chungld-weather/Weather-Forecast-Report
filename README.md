# Weather Reporter

A powerful Streamlit-based weather application that provides real-time forecasts, historical data, and detailed marine reports (wave and swell data). It supports multiple data sources, including Open-Meteo and OpenWeatherMap, and exports professional PDF and Excel reports.

## Features
- **Real-Time Forecasting**: 14-day weather forecasts dynamically visualized with Plotly charts.
- **Marine Data**: Displays wave height, wave period, swell height, and swell period (supported via Open-Meteo).
- **Historical Reports**: Export comprehensive historical weather data into Excel (`.xlsx`) or professional PDF reports (supports English and Vietnamese formats).
- **Multi-API Support**: Seamlessly switch between Open-Meteo (default, free) and OpenWeatherMap (requires API key).
- **Interactive UI**: View interactive charts for temperature, humidity, wind, UV index, and precipitation.

## Requirements
- Python 3.8+
- `streamlit`
- `pandas`
- `requests`
- `plotly`
- `reportlab`
- `xlsxwriter`
- `pytz`

## Installation
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd "Weather Reporter"
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` is missing, manually install: `pip install streamlit pandas requests plotly reportlab XlsxWriter pytz`)*

3. (Optional) If you plan to use OpenWeatherMap, set your API key as an environment variable:
   ```bash
   # Windows (PowerShell)
   $env:OPENWEATHERMAP_API_KEY="your_api_key_here"
   
   # Linux/Mac
   export OPENWEATHERMAP_API_KEY="your_api_key_here"
   ```

## Usage
Run the Streamlit application:
```bash
streamlit run app.py
```
This will open the application in your default web browser (usually at `http://localhost:8501`).

## Data Export
- **PDF Report**: Scroll to the "PDF Report" section, select a language (English/Vietnamese), and click "Generate PDF Report" for the current forecast.
- **Historical Data**: Set `History From` and `History To` to generate and download Excel or PDF records from the Open-Meteo Archive API. You will see a convenient preview in the UI before downloading.

## Credits
- Weather & Marine data provided by [Open-Meteo](https://open-meteo.com/) and [OpenWeatherMap](https://openweathermap.org/).
