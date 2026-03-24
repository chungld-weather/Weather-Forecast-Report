def download_tidal_report_action(self):
    selected_date_qdate = self.date_edit.date()
    selected_date = selected_date_qdate.toPyDate()

    # --- Start Progress Bar EARLIER ---
    self.progress_bar.setRange(0, 0)
    self.progress_bar.setFormat("Preparing to fetch tide data...")
    self.progress_bar.setVisible(True)
    QApplication.processEvents()

    QApplication.setOverrideCursor(Qt.WaitCursor)
    tidal_pdf_path = None
    tidal_pdf_url = None
    success = False

    try:
        print(
            f"\n--- Starting Tidal PDF Download for Date: {selected_date.strftime('%d/%m/%Y')} ---")

        # Update progress message before scraping
        self.progress_bar.setFormat("Searching for tide report...")
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
            self.progress_bar.setFormat("Download completed successfully!")
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
        if success:
            QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
        else:
            self.progress_bar.setVisible(False)
        QApplication.restoreOverrideCursor()


def generate_weather_report_action(self):
    lat, lon, location_name_selected = self.get_coordinates()
    if lat is None:
        return

    # --- Start Progress Bar EARLIER ---
    self.progress_bar.setRange(0, 0)  # Set to indeterminate
    self.progress_bar.setFormat("Fetching weather data...")
    self.progress_bar.setVisible(True)
    QApplication.processEvents()  # Ensure UI updates immediately

    QApplication.setOverrideCursor(Qt.WaitCursor)
    weather_data = None
    location_info = None
    success = False

    try:
        print("--- Starting Weather Data Fetch for Report ---")

        # Update progress message before fetching
        self.progress_bar.setFormat("Connecting to weather service...")
        QApplication.processEvents()

        weather_data, location_info = self.fetch_weather_data(lat, lon)

        if not weather_data:
            if not location_info:
                location_info = {'name': location_name_selected, 'country': 'N/A',
                                 'sunrise': 'N/A', 'sunset': 'N/A', 'timezone': DEFAULT_TIMEZONE}
            QMessageBox.warning(
                self, "Weather Error", "Failed to fetch weather data. Report generation stopped.")
            return

        # Update progress message before PDF generation
        self.progress_bar.setFormat("Generating PDF report...")
        QApplication.processEvents()

        self.generate_pdf_report(
            lat, lon, weather_data, location_info, location_name_selected)

        success = True
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Report generated successfully!")
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
            QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
        else:
            self.progress_bar.setVisible(False)
        QApplication.restoreOverrideCursor()
