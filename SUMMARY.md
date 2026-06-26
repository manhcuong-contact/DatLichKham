# 🏥 Tổng Kết Quá Trình Phát Triển & Triển Khai Hệ Thống DatLichKham

Tài liệu này tóm tắt toàn bộ các giai đoạn phát triển dự án và giải pháp tối ưu hóa việc lưu trữ dữ liệu bền vững khi triển khai trên nền tảng **Railway**.

---

## 🛠️ 1. Tổng Quan Các Giai Đoạn Phát Triển

Dự án **DatLichKham** đã hoàn thành trọn vẹn 4 giai đoạn yêu cầu:

* **Giai đoạn 1: Core Logic**
  * Thiết lập cấu trúc dữ liệu mẫu (`clinics.csv`, `doctors.csv`, `appointments.csv`).
  * Xây dựng thuật toán tìm kiếm phòng khám gần nhất (Khoảng cách Euclid).
  * Lọc bác sĩ theo chuyên khoa và khớp từ khóa triệu chứng (String Matching).
  * Xây dựng logic đặt lịch khám thông minh (Kiểm tra trùng slot, tự động gợi ý các khung giờ còn trống trong ngày nếu trùng lịch).
* **Giai đoạn 2: User Auth & Admin UI**
  * Hệ thống Đăng nhập / Đăng ký phân quyền (Bệnh nhân / Admin).
  * Lưu trữ thông tin người dùng vào file `users.csv` (Mật khẩu được mã hóa SHA-256).
  * Trang Lịch sử đặt lịch cho bệnh nhân.
  * Trang Admin Dashboard quản lý danh sách lịch hẹn và biểu đồ thống kê trực quan (sử dụng Plotly).
* **Giai đoạn 3: Tích Hợp Geocoding, Bản Đồ & Auto-refresh**
  * Tích hợp dịch vụ Geocoding (`geopy`) để chuyển đổi địa chỉ người dùng sang tọa độ GPS.
  * Bản đồ tương tác (`folium` / `streamlit-folium`) đánh dấu vị trí người dùng, phòng khám gần nhất và vẽ lộ trình di chuyển.
  * Thiết lập tính năng tự động cập nhật dữ liệu (Auto-refresh) mỗi 10 giây trên Admin Dashboard để đảm bảo dữ liệu real-time.
* **Giai đoạn 4: Trợ Lý AI Chatbot & Hỏi Đáp RAG**
  * **AI Lễ Tân (Triage Chatbot):** Tích hợp Gemini API để trò chuyện với bệnh nhân, phân loại triệu chứng và tự động điền form đặt lịch với bác sĩ/phòng khám phù hợp nhất.
  * **RAG Q&A:** Xây dựng hệ thống hỏi đáp dựa trên tài liệu nội bộ của bệnh viện (`hospital_docs/`), trả lời về quy trình, BHYT, bảng giá kèm trích dẫn nguồn tài liệu tham khảo cụ thể.

---

## ☁️ 2. Các Lỗi Đã Gặp Và Giải Pháp Khắc Phục Trên Railway

### Lỗi 1: Railway không tự động cập nhật code mới từ GitHub
* **Hiện tượng:** Dù đã push các commit mới nhất chứa tính năng AI Chatbot lên GitHub, Railway vẫn hiển thị phiên bản cũ từ lúc khởi tạo và không chạy build mới.
* **Nguyên nhân:** Bị nghẽn/kẹt Webhook giữa GitHub và Railway, khiến Railway không nhận thức được lệnh `git push`. Nút `Redeploy` trên bản build cũ của Railway chỉ có tác dụng build lại chính xác mã băm (commit hash) cũ đó.
* **Giải pháp khắc phục:** Thực hiện đẩy một commit trống để tạo tín hiệu trigger mới kích hoạt lại Webhook:
  ```bash
  git commit --allow-empty -m "force deploy"
  git push origin main
  ```
  Sau khi chạy lệnh này, Railway đã nhận diện được webhook và tự động cập nhật phiên bản code mới nhất thành công.

### Lỗi 2: Mất dữ liệu (tài khoản, lịch hẹn) khi cập nhật code hoặc restart server
* **Hiện tượng:** Sau khi deploy code mới, các tài khoản đã đăng ký hoặc lịch hẹn đã đặt trước đó đều biến mất sạch sẽ.
* **Nguyên nhân:** Railway sử dụng cơ chế **Ephemeral File System** (Hệ thống file tạm thời). Mỗi khi server ảo khởi động lại hoặc deploy bản mới, ổ đĩa sẽ bị "reset" về trạng thái gốc của mã nguồn trên GitHub. Các file CSV ghi trực tiếp tại local như `users.csv`, `appointments.csv` bị ghi đè/xóa trắng.
* **Giải pháp khắc phục (Railway Volume):**
  1. **Refactor Code:** Tạo file [config.py](file:///D:/DatLichKham/config.py) để quản lý đường dẫn file động qua biến môi trường `DATA_DIR` (nếu không cấu hình thì mặc định lưu tại thư mục hiện tại `.`). Khi khởi chạy, nếu phát hiện thư mục lưu dữ liệu mới chưa có các file CSV cơ bản, code sẽ tự động sao chép các file mẫu sang để tránh lỗi `FileNotFoundError`.
  2. **Tạo Volume trên Railway:** Tạo một ổ đĩa ảo độc lập trên Railway và mount (gắn) nó vào thư mục `/app/data` của ứng dụng. Ổ đĩa này sẽ được giữ lại vĩnh viễn và không bị xóa khi deploy lại app.
  3. **Đặt biến môi trường:** Thêm biến `DATA_DIR=/app/data` trên Railway Variables để điều hướng toàn bộ hành vi đọc/ghi CSV của ứng dụng vào ổ đĩa ảo này.

---

## 📂 3. Hướng Dẫn Xem Dữ Liệu CSV Lưu Trên Volume của Railway

Để quản lý hoặc tải về các file dữ liệu (ví dụ: danh sách tài khoản hoặc lịch hẹn thực tế) đang lưu ở Volume:

* **Cách 1 (Giao diện trực quan):** Click vào khối vuông **Volume** trên Dashboard của Railway -> Chọn tab **Data** ở phía trên. Bạn sẽ thấy trực tiếp danh sách file và có thể xem trực tuyến hoặc nhấn **Download** về máy.
* **Cách 2 (Dòng lệnh):** Click vào dịch vụ **DatLichKham** -> Chọn tab **Console** -> Gõ lệnh:
  ```bash
  cat /app/data/users.csv
  cat /app/data/appointments.csv
  ```
