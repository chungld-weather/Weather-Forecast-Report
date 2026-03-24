# Weather Reporter — Hướng Dẫn Sử Dụng (Ứng Dụng Web)

Chào mừng bạn đến với **Weather Reporter**, ứng dụng web chuyên nghiệp cung cấp thông tin thời tiết thời gian thực và báo cáo chất lượng cao cho bất kỳ địa điểm nào trên thế giới.

---

## 1. Lợi Ích Chính
*   **Độ Chính Xác Từ Nhiều Nguồn:** Chuyển đổi linh hoạt giữa **Open-Meteo**, **MET Norway**, và **OpenWeatherMap** để có dự báo tin cậy nhất.
*   **Phạm Vi Toàn Cầu:** Tìm kiếm theo tên, chọn trên bản đồ tương tác, hoặc nhập tọa độ GPS chính xác (lý tưởng cho các giàn khoan dầu khí hoặc vị trí xa xôi).
*   **Báo Cáo Chuyên Nghiệp:** Xuất báo cáo dự báo thời tiết chi tiết dưới dạng PDF (Tiếng Anh/Tiếng Việt) hoặc bảng tính Excel chuyên nghiệp chỉ với một cú nhấp chuột.
*   **Phân Tích Trực Quan:** Biểu đồ tương tác cho nhiệt độ, gió, mưa, chỉ số UV và nhiều thông số khác.
*   **Giao Diện Hiện Đại:** Chế độ tối (dark mode) sang trọng với bản đồ lượng mưa thời gian thực.

---

## 2. Các Tính Năng & Chức Năng

### 2.1 Chọn Địa Điểm
Sử dụng phần **Search Location** với bốn tab chuyên biệt:
1.  **📋 Saved Locations:** Chọn nhanh từ danh sách các điểm đã lưu (ví dụ: Rong Doi Platform, An Phu Office).
2.  **🔍 Search:** Nhập tên thành phố hoặc địa danh (ví dụ: "Vũng Tàu") để nhận gợi ý tọa độ.
3.  **🗺️ Map:** Nhấp vào bất kỳ đâu trên bản đồ tương tác để chọn điểm. Dấu đỏ chỉ vị trí đã xác nhận, dấu xanh chỉ vị trí bạn vừa nhấp chuột.
4.  **📍 Coordinates:** Nhập tọa độ Vĩ độ (Latitude) và Kinh độ (Longitude) thủ công để đạt độ chính xác kỹ thuật cao nhất.

### 2.2 Chọn Nguồn Dữ Liệu
Chọn nhà cung cấp dữ liệu thời tiết bạn ưu tiên:
*   **Open-Meteo:** Dự báo toàn diện, hỗ trợ cả dữ liệu hải văn (sóng, gió).
*   **MET Norway:** Dữ liệu khí tượng Thụy Điển/Na Uy với độ chính xác cao.
*   **OpenWeatherMap:** Các chỉ số thời gian thực và dự báo tầm trung.

### 2.3 Bảng Điều Khiển Thời Gian Thực
Hiển thị thời tiết hiện tại tại vị trí đã xác nhận:
*   **Giờ Địa Phương:** Tự động điều chỉnh theo múi giờ của địa điểm.
*   **Các Chỉ Số Chính:** Nhiệt độ, Tốc độ gió (knots), Lượng mưa (mm), và Chỉ số UV.

### 2.4 Bản Đồ Lượng Mưa
Bản đồ tương tác trực tiếp từ Windy.com, hiển thị lớp phủ lượng mưa cho khu vực xung quanh, kèm theo logo chuyên nghiệp phía trên.

### 2.5 Biểu Đồ Trực Quan
Cuộn xuống để xem các biểu đồ tương tác động cho:
*   **Nhiệt Độ & Độ Ẩm**
*   **Tốc Độ Gió & Gió Giật** (kèm hướng gió)
*   **Mưa & Xác Suất Có Mưa (PoP)**
*   **Độ Che Phủ Mây & Chỉ Số UV**
*   **Dữ Liệu Hải Văn:** Chiều cao và chu kỳ sóng/sóng lừng (chỉ có ở nguồn Open-Meteo).

### 2.6 Báo Cáo & Xuất Dữ Liệu
Nằm ở cuối trang:
*   **Báo Cáo PDF:** Chọn ngôn ngữ Tiếng Anh hoặc Tiếng Việt và nhấn "Generate PDF Report" để tải bản tin thời tiết có thương hiệu.
*   **Excel Chuyên Nghiệp:** Bảng dữ liệu và biểu đồ được định dạng sẵn cho mục đích công việc.
*   **PDF Lịch Sử:** Chọn khoảng thời gian để tạo tóm tắt thời tiết trong quá khứ.
*   **Raw CSV:** Xuất dữ liệu dự báo thô để tự phân tích.

---

## 3. Hướng Dẫn Sử Dụng: Các Bước Thực Hiện
1.  **Chọn Địa Điểm:** Sử dụng tab Tìm kiếm hoặc Bản đồ để tìm vị trí mục tiêu.
2.  **Xác Nhận:** Nhấn "Use this location" hoặc "Confirm coordinates".
3.  **Lấy Dữ Liệu:** Nhấn nút **Fetch Data** để tải thông tin thời tiết mới nhất.
4.  **Xem Thông Tin:** Khám phá bảng điều khiển, bản đồ và biểu đồ.
5.  **Xuất Báo Cáo:** Cuộn xuống cuối trang để tạo báo cáo PDF hoặc Excel.

---

## 4. Xử Lý Sự Cố
*   **"Failed to fetch data":** Kiểm tra kết nối internet hoặc thử chọn một nguồn dữ liệu khác.
*   **Tọa độ không cập nhật:** Đảm bảo bạn đã nhấn "Confirm" sau khi chọn trên bản đồ hoặc nhập thủ công.
*   **Thiếu dữ liệu hải văn:** Đảm bảo bạn đang sử dụng nguồn **Open-Meteo**.

---
**Phát triển bởi:** Tung TT
**Hỗ trợ:** 0906 921 885
