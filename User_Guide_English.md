# Weather Reporter — User Guide

**Version 3** | Developer: Tung TT (0906 921 885)

---

## 1. Overview

**Weather Reporter** is a desktop application that fetches real-time and historical weather data and generates professional PDF and Excel reports. It supports two weather data sources (Open-Meteo and OpenWeatherMap), provides a live dashboard for up to four locations, and allows custom GPS coordinates with optional marine forecasts.

---

## 2. Application Layout

The window is split into two panels:

| Panel | Contents |
|---|---|
| **Left** | API source selector, Location selector, Report action buttons |
| **Right** | Real-time weather dashboard (up to 4 locations) |

---

## 3. Left Panel — Step-by-Step

### 3.1 Select Weather API Source

Choose the data provider for report generation:

- **Open-Meteo** *(recommended)* — 14-day forecast, marine data, historical archive. No API key required.
- **OpenWeatherMap** — 5-day forecast. Requires a valid API key in `config.json`.

### 3.2 Select Location for Weather Reports

Pick the target location for the next report:

- **Predefined locations** — Select one from the radio-button list. Latitude and longitude are shown next to each name.
- **Custom GPS** — Select *"Enter Custom GPS Coordinates"*, then fill in:
  - **Custom Name** — Label used in the report filename and header.
  - **Lat / Lon** — Decimal degrees. The border turns **green** when the value is valid, **red** when invalid.
  - **With Marine Forecast** — Check this box to include wind wave, swell, and wave period data (Open-Meteo only).

> **Tip:** The last GPS coordinates you entered are automatically saved and restored next time you open the app.

### 3.3 Manage Locations

Click **⚙ Manage Locations...** to open the Location Manager dialog:

| Action | How to |
|---|---|
| **View** locations | All saved locations are listed in the table with name, coordinates, PDF name, and Marine status |
| **Add** a location | Fill in Display Name, Latitude, Longitude (and optional PDF Name),<br>optionally check **🌊 Include Marine Forecast in Report**, then click **➕ Add Location** |
| **Delete** a location | Click a row to select it, then click **🗑 Delete Selected** and confirm |

> **Marine Forecast checkbox:** When checked, wave height, wave period, swell, and sea-state data will be fetched from the Open-Meteo Marine API and included in the PDF report for that location. The **Marine** column in the table shows **🌊 ✓** for any location with this option enabled. Only applies when using the Open-Meteo API source.

Changes are saved to `config.json` immediately. The radio-button list and dashboard selector update **without restarting** the app.

### 3.4 Select Locations for Dashboard (up to 4)

Check up to four locations in the list below the location group. These will appear as live weather cards on the right panel. Your selection is saved automatically.

### 3.5 Report Actions

#### Weather Forecast Reports

| Button | Output |
|---|---|
| **Generate Report (English)** | PDF forecast report in English |
| **Tạo Báo Cáo Thời Tiết (Tiếng Việt)** | PDF forecast report in Vietnamese |

#### Historical Data Reports

Set the **From** and **To** dates (up to 2 years range), then click:

| Button | Output |
|---|---|
| **Generate Historical Report (PDF)** | Multi-page PDF with charts for the selected date range |
| **Generate Historical Report (Excel)** | Excel workbook with data table + embedded line charts |

> **Note:** Only Open-Meteo supports historical data. Historical reports always use Open-Meteo regardless of the API selector.

#### During Report Generation

- All action buttons are **disabled** while a report is being generated to prevent duplicate requests.
- A **progress bar** and status message appear at the bottom of the left panel.
- A spinning progress indicator shows which step is running (fetching data, generating PDF, etc.).
- When finished, a **Success** dialog appears with an **"Open Folder"** button to go directly to the output directory.

---

## 4. Right Panel — Real-time Dashboard

The dashboard auto-refreshes every **15 minutes**. Click **Refresh Now** to update immediately.

### 4.1 Clock

The top of the dashboard shows the current local time and timezone abbreviation (e.g., `14:30:00 (ICT)`).

### 4.2 Location Cards

Each selected location shows:

- **Description** — Current weather condition (e.g., "Partly cloudy")
- **Temperature** — Current temperature in °C
- **Wind Speed** — In knots
- **Rain** — Precipitation in mm/h
- **Location image** — If a matching image exists in the `Pictures/` folder (`<Location_Name_with_underscores>.png`), it is shown. Otherwise, a default placeholder image is displayed.

Cards flash with a blue highlight every time new data is received.

### 4.3 Wind Speed Alert

If wind speed at any location exceeds the alert threshold, the alert label at the bottom of the dashboard displays the affected locations.

---

## 5. Output Files

All generated files are saved in the **same folder as the application**:

| File type | Naming convention |
|---|---|
| Forecast PDF (English) | `Weather_Report_<Location>_<Date>.pdf` |
| Forecast PDF (Vietnamese) | `BaoCaoThoiTiet_<Location>_<Date>.pdf` |
| Historical PDF | `Historical_Weather_Report_<Location>_<From>_to_<To>.pdf` |
| Historical Excel | `Historical_Weather_Report_OpenMeteo_<Location>_<From>_to_<To>.xlsx` |

---

## 6. Customizing the App

### Adding a Location Image

Place a PNG image named exactly `<Display_Name_with_spaces_replaced_by_underscores>.png` in the `Pictures/` folder.

*Example:* For a location named `"Vung Tau Airport - Vung Tau"`, the file should be `Pictures/Vung_Tau_Airport_-_Vung_Tau.png`.

### Default Placeholder Images

If no location-specific image is found, the app cycles through `Pictures/default_location_1.png` … `default_location_4.png` based on the slot position (1st location → image 1, 2nd → image 2, etc.).

### Editing `config.json` Directly

Advanced users can edit `config.json` to:

- Change the OpenWeatherMap API key (`api_key_openweathermap`)
- Add/remove locations manually under the `locations` key
- Change default dashboard selections (`dashboard_locations`)

---

## 7. Troubleshooting

| Problem | Solution |
|---|---|
| "Weather data fetch failed" | Check internet connection; try switching to the other API source |
| GPS border stays red | Verify latitude is between −90 and 90, longitude between −180 and 180 |
| Dashboard shows no cards | Check at least one location in the Dashboard selection list |
| Report font appears incorrect | Ensure font files (NotoSans, Arial) are available on your system |

---

## 8. Contact

For support, contact: **Tung TT — 0906 921 885**
