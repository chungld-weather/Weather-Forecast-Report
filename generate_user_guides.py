# -*- coding: utf-8 -*-
"""
generate_user_guides.py
Run: python generate_user_guides.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, PageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import os

# ── Font (falls back to Helvetica if NotoSans files not found) ─────────────
FONT_N = "Helvetica"
FONT_B = "Helvetica-Bold"
if os.path.exists("NotoSans-Regular.ttf"):
    try:
        pdfmetrics.registerFont(TTFont("NotoSans",     "NotoSans-Regular.ttf"))
        pdfmetrics.registerFont(TTFont("NotoSans-Bold","NotoSans-Bold.ttf"))
        pdfmetrics.registerFontFamily("NotoSans", normal="NotoSans", bold="NotoSans-Bold")
        FONT_N = "NotoSans"
        FONT_B = "NotoSans-Bold"
    except Exception as e:
        print("Font registration warning:", e)

# ── Colours ────────────────────────────────────────────────────────────────
NAVY  = colors.HexColor("#003366")
BLUE  = colors.HexColor("#1A6EA8")
LGRAY = colors.HexColor("#F2F4F7")
MGRAY = colors.HexColor("#CCCCCC")
LBLUE = colors.HexColor("#EAF4FB")
LYELL = colors.HexColor("#FFF8E1")
AMBER = colors.HexColor("#F0AD00")
WHITE = colors.white

def S():
    return {
        "title":    ParagraphStyle("TT", fontName=FONT_B, fontSize=22,
                                   textColor=WHITE, alignment=TA_CENTER, leading=28),
        "sub":      ParagraphStyle("TS", fontName=FONT_N, fontSize=11,
                                   textColor=WHITE, alignment=TA_CENTER),
        "foot":     ParagraphStyle("TF", fontName=FONT_N, fontSize=8,
                                   textColor=colors.HexColor("#888888"), alignment=TA_CENTER),
        "h2":       ParagraphStyle("H2", fontName=FONT_B, fontSize=14, textColor=NAVY,
                                   spaceBefore=14, spaceAfter=4, leading=18),
        "h3":       ParagraphStyle("H3", fontName=FONT_B, fontSize=11, textColor=BLUE,
                                   spaceBefore=10, spaceAfter=3, leading=15),
        "h4":       ParagraphStyle("H4", fontName=FONT_B, fontSize=10,
                                   textColor=colors.HexColor("#444"), spaceBefore=7, spaceAfter=2),
        "body":     ParagraphStyle("BD", fontName=FONT_N, fontSize=10, leading=15,
                                   spaceAfter=4, alignment=TA_JUSTIFY),
        "bullet":   ParagraphStyle("BL", fontName=FONT_N, fontSize=10, leading=15,
                                   spaceAfter=3, leftIndent=16),
        "note":     ParagraphStyle("NT", fontName=FONT_N, fontSize=9, leading=13,
                                   textColor=colors.HexColor("#444"), leftIndent=10),
    }

def ts():
    return TableStyle([
        ("BACKGROUND",    (0,0),(-1, 0), NAVY),
        ("TEXTCOLOR",     (0,0),(-1, 0), WHITE),
        ("FONTNAME",      (0,0),(-1, 0), FONT_B),
        ("FONTSIZE",      (0,0),(-1, 0), 10),
        ("ALIGN",         (0,0),(-1, 0), "CENTER"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [LGRAY, WHITE]),
        ("FONTNAME",      (0,1),(-1,-1), FONT_N),
        ("FONTSIZE",      (0,1),(-1,-1), 9),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("GRID",          (0,0),(-1,-1), 0.4, MGRAY),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
    ])

def cover(title, sub, ST):
    t = Table([[Paragraph(title, ST["title"])],
               [Paragraph(sub,   ST["sub"])]], colWidths=[17*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 20),
        ("BOTTOMPADDING", (0,0),(-1,-1), 20),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("RIGHTPADDING",  (0,0),(-1,-1), 12),
    ]))
    return t

def hr():
    return HRFlowable(width="100%", thickness=0.8, color=BLUE, spaceAfter=8, spaceBefore=4)

def tip(text, ST):
    t = Table([[Paragraph("Tip:  " + text, ST["note"])]], colWidths=[17*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), LBLUE),
        ("BOX",           (0,0),(-1,-1), 0.5, BLUE),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
    ]))
    return t

def nbox(text, ST):
    t = Table([[Paragraph("Note:  " + text, ST["note"])]], colWidths=[17*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), LYELL),
        ("BOX",           (0,0),(-1,-1), 0.5, AMBER),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
    ]))
    return t

SP = lambda h=0.2: Spacer(1, h*cm)


# ===========================================================================
#  ENGLISH
# ===========================================================================
def english(path):
    ST = S()
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    s = []
    s += [cover("Weather Reporter","User Guide (Web App) - Version 4.0", ST),
          SP(0.4), Paragraph("Developer: Tung TT  |  0906 921 885", ST["foot"]),
          SP(0.5), hr()]

    s.append(Paragraph("1.  Key Benefits", ST["h2"]))
    s.append(Paragraph("* <b>Multi-Source Precision:</b> Toggle between Open-Meteo, MET Norway, and OpenWeatherMap.", ST["bullet"]))
    s.append(Paragraph("* <b>Global Reach:</b> Search by name, select on an interactive map, or enter precise GPS coordinates.", ST["bullet"]))
    s.append(Paragraph("* <b>Professional Reporting:</b> Generate weather forecasts in PDF (English/Vietnamese) or Excel.", ST["bullet"]))
    s.append(Paragraph("* <b>Visual Analytics:</b> Interactive charts for temperature, wind, rain, UV index, and more.", ST["bullet"]))
    s.append(Paragraph("* <b>Aesthetic Experience:</b> Premium dark mode interface with real-time precipitation overlays.", ST["bullet"]))

    s.append(Paragraph("2.  Features & Functionality", ST["h2"]))
    s.append(Paragraph("2.1  Location Selection", ST["h3"]))
    s.append(Table(
        [["Tab","Description"],
         ["Saved Locations", "Choose from a pre-configured list of sites."],
         ["Search",          "Type any city or place name to get suggested coordinates."],
         ["Map",             "Click anywhere on the interactive map to select a point."],
         ["Coordinates",     "Manually enter Latitude and Longitude for technical precision."]],
        colWidths=[4*cm,13*cm], style=ts()))
    s.append(SP(0.3))

    s.append(Paragraph("2.2  Data Source Selection", ST["h3"]))
    s.append(Paragraph("Choose your preferred weather data provider:", ST["body"]))
    s.append(Paragraph("* <b>Open-Meteo:</b> Comprehensive forecast with marine data support.", ST["bullet"]))
    s.append(Paragraph("* <b>MET Norway:</b> High-accuracy European meteorological data.", ST["bullet"]))
    s.append(Paragraph("* <b>OpenWeatherMap:</b> Real-time metrics and medium-range forecasts.", ST["bullet"]))
    s.append(SP())

    s.append(Paragraph("2.3  Real-time Dashboard", ST["h3"]))
    s.append(Paragraph("Displays current weather at your confirmed location including Local Time, Temperature, Wind Speed, Rain, and UV Index.", ST["body"]))
    
    s.append(Paragraph("2.4  Precipitation Map", ST["h3"]))
    s.append(Paragraph("A live, interactive map powered by Windy.com showing rainfall overlays for the surrounding region.", ST["body"]))

    s.append(Paragraph("2.5  Visual Charts", ST["h3"]))
    s.append(Paragraph("Dynamic charts for Temperature, Humidity, Wind, Rain, Cloud Cover, UV Index, and Marine Data (Wave/Swell).", ST["body"]))

    s.append(Paragraph("2.6  Reporting & Exports", ST["h3"]))
    s.append(Table(
        [["Format","Output"],
         ["PDF Report",      "Choose English or Vietnamese for a branded weather brief."],
         ["Professional Excel","Detailed data tables and charts formatted for business use."],
         ["Historical PDF",  "Select a date range to generate a historical weather summary."],
         ["Raw CSV",         "Export raw forecast data for advanced analysis."]],
        colWidths=[4*cm,13*cm], style=ts()))
    s.append(SP(0.3))

    s.append(PageBreak())
    s.append(Paragraph("3.  How to Use: Step-by-Step", ST["h2"]))
    s.append(Paragraph("1. <b>Select a Location:</b> Use the Search or Map tab to find your target site.", ST["bullet"]))
    s.append(Paragraph("2. <b>Confirm:</b> Click 'Use this location' or 'Confirm coordinates'.", ST["bullet"]))
    s.append(Paragraph("3. <b>Fetch Data:</b> Click the <b>Fetch Data</b> button to load the latest weather.", ST["bullet"]))
    s.append(Paragraph("4. <b>Review:</b> Explore the dashboard, map, and charts.", ST["bullet"]))
    s.append(Paragraph("5. <b>Export:</b> Scroll to the bottom to generate your PDF or Excel report.", ST["bullet"]))

    s.append(Paragraph("4.  Troubleshooting", ST["h2"]))
    s.append(Table(
        [["Problem","Solution"],
         ["Failed to fetch data", "Check internet connection or try a different data source."],
         ["Coords not updating",  "Ensure you clicked 'Confirm' after selecting on the map."],
         ["Marine data missing", "Ensure you are using Open-Meteo as the data source."]],
        colWidths=[6*cm,11*cm], style=ts()))

    s.append(Paragraph("5.  Contact", ST["h2"]))
    s.append(Paragraph("For support: <b>Tung TT  -  0906 921 885</b>", ST["body"]))

    doc.build(s)
    print("Created: " + path)


# ===========================================================================
#  VIETNAMESE
# ===========================================================================
def vietnamese(path):
    ST = S()
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    s = []

    s += [cover("Weather Reporter",
                "Hướng Dẫn Sử Dụng (Web App) - Version 4.0", ST),
          SP(0.4),
          Paragraph("Người phát triển: Tùng TT  |  0906 921 885", ST["foot"]),
          SP(0.5), hr()]

    s.append(Paragraph("1. Lợi Ích Chính", ST["h2"]))
    s.append(Paragraph("* <b>Độ Chính Xác Từ Nhiều Nguồn:</b> Chuyển đổi linh hoạt giữa Open-Meteo, MET Norway, và OpenWeatherMap.", ST["bullet"]))
    s.append(Paragraph("* <b>Phạm Vi Toàn Cầu:</b> Tìm kiếm theo tên, chọn trên bản đồ, hoặc nhập tọa độ GPS.", ST["bullet"]))
    s.append(Paragraph("* <b>Báo Cáo Chuyên Nghiệp:</b> Xuất báo cáo dự báo PDF (Anh/Việt) hoặc Excel.", ST["bullet"]))
    s.append(Paragraph("* <b>Phân Tích Trực Quan:</b> Biểu đồ tương tác cho nhiệt độ, gió, mưa, UV...", ST["bullet"]))
    s.append(Paragraph("* <b>Giao Diện Hiện Đại:</b> Chế độ tối sang trọng với bản đồ lượng mưa trực tiếp.", ST["bullet"]))

    s.append(Paragraph("2. Các Tính Năng & Chức Năng", ST["h2"]))
    s.append(Paragraph("2.1 Chọn Địa Điểm", ST["h3"]))
    s.append(Table(
        [["Tab", "Mô tả"],
         ["Saved Locations", "Chọn nhanh từ danh sách các địa điểm đã lưu."],
         ["Search",          "Nhập tên thành phố hoặc địa danh."],
         ["Map",             "Nhấp vào bản đồ tương tác để chọn điểm."],
         ["Coordinates",     "Nhập tọa độ Vĩ độ và Kinh độ thủ công."]],
        colWidths=[4*cm, 13*cm], style=ts()))
    s.append(SP(0.3))

    s.append(Paragraph("2.2 Chọn Nguồn Dữ Liệu", ST["h3"]))
    s.append(Paragraph("Chọn nhà cung cấp dữ liệu thời tiết:", ST["body"]))
    s.append(Paragraph("* <b>Open-Meteo:</b> Dự báo toàn diện, hỗ trợ dữ liệu hải văn.", ST["bullet"]))
    s.append(Paragraph("* <b>MET Norway:</b> Dữ liệu khí tượng chính xác cao từ Châu Âu.", ST["bullet"]))
    s.append(Paragraph("* <b>OpenWeatherMap:</b> Chỉ số thời gian thực và dự báo tầm trung.", ST["bullet"]))

    s.append(Paragraph("2.3 Bảng Điều Khiển Thời Gian Thực", ST["h3"]))
    s.append(Paragraph("Hiển thị Giờ địa phương, Nhiệt độ, Tốc độ gió, Mưa và Chỉ số UV.", ST["body"]))

    s.append(Paragraph("2.4 Bản Đồ Lượng Mưa", ST["h3"]))
    s.append(Paragraph("Bản đồ tương tác trực tiếp từ Windy.com hiển thị lớp phủ lượng mưa.", ST["body"]))

    s.append(Paragraph("2.5 Biểu Đồ Trực Quan", ST["h3"]))
    s.append(Paragraph("Biểu đồ cho Nhiệt độ, Độ ẩm, Gió, Mưa, Mây, UV và Sóng.", ST["body"]))

    s.append(Paragraph("2.6 Báo Cáo & Xuất Dữ Liệu", ST["h3"]))
    s.append(Table(
        [["Định dạng", "Kết quả"],
         ["Báo cáo PDF", "Bản tin thời tiết tiếng Anh hoặc Việt."],
         ["Excel Chuyên Nghiệp", "Bảng dữ liệu và biểu đồ cho công việc."],
         ["PDF Lịch Sử", "Tóm tắt thời tiết trong quá khứ."],
         ["Raw CSV", "Xuất dữ liệu thô để tự phân tích."]],
        colWidths=[4*cm, 13*cm], style=ts()))

    s.append(PageBreak())
    s.append(Paragraph("3. Hướng Dẫn Sử Dụng: Các Bước Thực Hiện", ST["h2"]))
    s.append(Paragraph("1. <b>Chọn Địa Điểm:</b> Sử dụng tab Tìm kiếm hoặc Bản đồ.", ST["bullet"]))
    s.append(Paragraph("2. <b>Xác Nhận:</b> Nhấn 'Use this location' hoặc 'Confirm coordinates'.", ST["bullet"]))
    s.append(Paragraph("3. <b>Lấy Dữ Liệu:</b> Nhấn nút <b>Fetch Data</b>.", ST["bullet"]))
    s.append(Paragraph("4. <b>Xem Thông Tin:</b> Khám phá dashboard, bản đồ và biểu đồ.", ST["bullet"]))
    s.append(Paragraph("5. <b>Xuất Báo Cáo:</b> Cuối trang để tạo PDF hoặc Excel.", ST["bullet"]))

    s.append(Paragraph("4. Xử Lý Sự Cố", ST["h2"]))
    s.append(Table(
        [["Vấn đề", "Giải pháp"],
         ["Lỗi lấy dữ liệu", "Kiểm tra mạng hoặc đổi nguồn dữ liệu."],
         ["Tọa độ không cập nhật", "Đảm bảo đã nhấn 'Confirm' sau khi chọn."],
         ["Thiếu dữ liệu hải văn", "Hãy dùng Open-Meteo làm nguồn dữ liệu."]],
        colWidths=[6*cm, 11*cm], style=ts()))

    s.append(Paragraph("5. Liên Hệ", ST["h2"]))
    s.append(Paragraph("Hỗ trợ: <b>Tùng TT  -  0906 921 885</b>", ST["body"]))

    doc.build(s)
    print("Created: " + path)


if __name__ == "__main__":
    english("User_Guide_EN.pdf")
    vietnamese("User_Guide_VN.pdf")
    print("\nDone! Both PDF guides are ready.")
