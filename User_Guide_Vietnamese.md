# Weather Reporter — Hướng Dẫn Sử Dụng

**Phiên bản 3** | Người phát triển: Tùng TT (0906 921 885)

---

## 1. Giới Thiệu

**Weather Reporter** là ứng dụng máy tính để bàn giúp truy xuất dữ liệu thời tiết theo thời gian thực và dữ liệu lịch sử, đồng thời tạo báo cáo chuyên nghiệp dưới dạng PDF và Excel. Ứng dụng hỗ trợ hai nguồn dữ liệu thời tiết (Open-Meteo và OpenWeatherMap), hiển thị bảng điều khiển (dashboard) trực tiếp cho tối đa bốn địa điểm, và cho phép nhập tọa độ GPS tùy chỉnh kèm tùy chọn dự báo hàng hải.

---

## 2. Bố Cục Giao Diện

Cửa sổ ứng dụng được chia thành hai bảng:

| Bảng | Nội dung |
|---|---|
| **Trái** | Chọn nguồn API, chọn địa điểm, nút tạo báo cáo |
| **Phải** | Bảng thời tiết trực tiếp (tối đa 4 địa điểm) |

---

## 3. Bảng Điều Khiển Bên Trái

### 3.1 Chọn Nguồn Dữ Liệu Thời Tiết

Chọn nhà cung cấp dữ liệu để tạo báo cáo:

- **Open-Meteo** *(khuyến nghị)* — Dự báo 14 ngày, dữ liệu hàng hải, kho lưu trữ lịch sử. Không cần API key.
- **OpenWeatherMap** — Dự báo 5 ngày. Cần API key hợp lệ trong tệp `config.json`.

### 3.2 Chọn Địa Điểm

Chọn địa điểm mục tiêu cho báo cáo tiếp theo:

- **Địa điểm có sẵn** — Chọn từ danh sách radio button. Vĩ độ và kinh độ được hiển thị bên cạnh tên.
- **GPS tùy chỉnh** — Chọn *"Enter Custom GPS Coordinates"*, rồi điền:
  - **Custom Name** — Tên xuất hiện trong tiêu đề và tên tệp báo cáo.
  - **Lat / Lon** — Độ thập phân. Viền ô chuyển **xanh lá** khi giá trị hợp lệ, **đỏ** khi không hợp lệ.
  - **With Marine Forecast** — Tích ô này để thêm dữ liệu sóng gió, sóng lừng và kỳ sóng (chỉ áp dụng với Open-Meteo).

> **Mẹo:** Tọa độ GPS nhập lần cuối được tự động lưu lại và khôi phục vào lần mở ứng dụng tiếp theo.

### 3.3 Quản Lý Địa Điểm

Nhấn **⚙ Manage Locations...** để mở hộp thoại Quản lý Địa điểm:

| Thao tác | Cách thực hiện |
|---|---|
| **Xem** danh sách | Tất cả địa điểm được liệt kê trong bảng với tên, tọa độ, tên PDF và trạng thái Hàng hải |
| **Thêm** địa điểm | Nhập Tên hiển thị, Vĩ độ, Kinh độ (và Tên PDF tùy chọn),<br>tùy chọn tích **🌊 Include Marine Forecast in Report**, rồi nhấn **➕ Add Location** |
| **Xóa** địa điểm | Nhấp chọn một hàng, rồi nhấn **🗑 Delete Selected** và xác nhận |

> **Ô chọn Dự báo Hàng hải:** Khi tích chọn, dữ liệu chiều cao sóng, chu kỳ sóng, sóng lừng và trạng thái biển sẽ được lấy từ Open-Meteo Marine API và đưa vào báo cáo PDF cho địa điểm đó. Cột **Marine** trong bảng hiển thị **🌊 ✓** cho các địa điểm được bật tùy chọn này. Chỉ áp dụng khi dùng nguồn API Open-Meteo.

Thay đổi được lưu vào `config.json` ngay lập tức. Danh sách radio button và bộ chọn dashboard cập nhật **mà không cần khởi động lại** ứng dụng.

### 3.4 Chọn Địa Điểm Cho Dashboard (tối đa 4)

Tích chọn tối đa bốn địa điểm trong danh sách phía dưới nhóm chọn địa điểm. Các địa điểm này sẽ hiển thị thẻ thời tiết trực tiếp ở bảng bên phải. Lựa chọn được lưu tự động.

### 3.5 Các Nút Tạo Báo Cáo

#### Báo Cáo Dự Báo Thời Tiết

| Nút | Kết quả |
|---|---|
| **Generate Report (English)** | Báo cáo PDF dự báo bằng tiếng Anh |
| **Tạo Báo Cáo Thời Tiết (Tiếng Việt)** | Báo cáo PDF dự báo bằng tiếng Việt |

#### Báo Cáo Dữ Liệu Lịch Sử

Đặt ngày **Từ** và **Đến** (tối đa 2 năm), rồi nhấn:

| Nút | Kết quả |
|---|---|
| **Generate Historical Report (PDF)** | File PDF nhiều trang kèm biểu đồ cho khoảng thời gian đã chọn |
| **Generate Historical Report (Excel)** | File Excel với bảng dữ liệu và biểu đồ đường nhúng |

> **Lưu ý:** Chỉ Open-Meteo hỗ trợ dữ liệu lịch sử. Báo cáo lịch sử luôn dùng Open-Meteo dù bộ chọn API đang ở vị trí nào.

#### Trong Quá Trình Tạo Báo Cáo

- Tất cả nút tạo báo cáo bị **vô hiệu hóa** trong khi đang xử lý để tránh yêu cầu trùng lặp.
- Thanh **tiến trình** và thông báo trạng thái xuất hiện ở cuối bảng bên trái.
- Khi hoàn thành, hộp thoại **Thành công** hiển thị kèm nút **"Open Folder"** để mở trực tiếp thư mục chứa tệp đầu ra.

---

## 4. Bảng Điều Khiển Bên Phải — Dashboard Thời Tiết Trực Tiếp

Dashboard tự động làm mới mỗi **15 phút**. Nhấn **Refresh Now** để cập nhật ngay lập tức.

### 4.1 Đồng Hồ

Góc trên hiển thị giờ địa phương hiện tại và tên múi giờ (ví dụ: `14:30:00 (ICT)`).

### 4.2 Thẻ Địa Điểm

Mỗi địa điểm được chọn hiển thị một thẻ thông tin gồm:

- **Mô tả** — Tình trạng thời tiết hiện tại (ví dụ: "Partly cloudy")
- **Nhiệt độ** — Nhiệt độ hiện tại tính bằng °C
- **Tốc độ gió** — Tính bằng knot
- **Mưa** — Lượng mưa tính bằng mm/h
- **Hình ảnh địa điểm** — Nếu có file ảnh tương ứng trong thư mục `Pictures/`, ảnh đó sẽ được hiển thị. Nếu không, ảnh mặc định sẽ được dùng thay thế.

Thẻ nhấp nháy màu xanh lam mỗi khi nhận được dữ liệu mới.

### 4.3 Cảnh Báo Tốc Độ Gió

Nếu tốc độ gió tại bất kỳ địa điểm nào vượt ngưỡng cảnh báo, nhãn cảnh báo ở cuối dashboard sẽ hiển thị các địa điểm bị ảnh hưởng.

---

## 5. Tệp Đầu Ra

Tất cả tệp được lưu trong **cùng thư mục với ứng dụng**:

| Loại tệp | Quy tắc đặt tên |
|---|---|
| PDF dự báo (tiếng Anh) | `Weather_Report_<Địa điểm>_<Ngày>.pdf` |
| PDF dự báo (tiếng Việt) | `BaoCaoThoiTiet_<Địa điểm>_<Ngày>.pdf` |
| PDF lịch sử | `Historical_Weather_Report_<Địa điểm>_<Từ>_to_<Đến>.pdf` |
| Excel lịch sử | `Historical_Weather_Report_OpenMeteo_<Địa điểm>_<Từ>_to_<Đến>.xlsx` |

---

## 6. Tùy Chỉnh Ứng Dụng

### Thêm Ảnh Cho Địa Điểm

Đặt file ảnh PNG có tên đúng theo định dạng `<Tên_hiển_thị_thay_dấu_cách_bằng_gạch_dưới>.png` vào thư mục `Pictures/`.

*Ví dụ:* Với địa điểm tên `"Vung Tau Airport - Vung Tau"`, tệp phải là `Pictures/Vung_Tau_Airport_-_Vung_Tau.png`.

### Ảnh Mặc Định

Nếu không tìm thấy ảnh riêng cho địa điểm, ứng dụng sẽ luân phiên dùng `Pictures/default_location_1.png` … `default_location_4.png` theo vị trí slot (vị trí 1 → ảnh 1, vị trí 2 → ảnh 2, v.v.).

### Chỉnh Sửa `config.json` Trực Tiếp

Người dùng nâng cao có thể chỉnh sửa `config.json` để:

- Thay đổi API key OpenWeatherMap (`api_key_openweathermap`)
- Thêm/xóa địa điểm thủ công trong mục `locations`
- Thay đổi lựa chọn dashboard mặc định (`dashboard_locations`)

---

## 7. Xử Lý Sự Cố

| Vấn đề | Giải pháp |
|---|---|
| "Weather data fetch failed" | Kiểm tra kết nối mạng; thử chuyển sang nguồn API khác |
| Viền ô GPS vẫn đỏ | Kiểm tra vĩ độ trong khoảng −90 đến 90, kinh độ −180 đến 180 |
| Dashboard không hiển thị thẻ nào | Tích chọn ít nhất một địa điểm trong danh sách Dashboard |
| Font chữ báo cáo hiển thị sai | Đảm bảo các file font (NotoSans, Arial) có sẵn trên máy tính |

---

## 8. Liên Hệ

Để được hỗ trợ, vui lòng liên hệ: **Tùng TT — 0906 921 885**
