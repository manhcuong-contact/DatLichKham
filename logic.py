import pandas as pd
import math
from datetime import datetime, timedelta

# Import hàm gửi email từ file email_service.py mà bạn vừa tạo
from email_service import send_confirmation_email 

# 1. Tìm phòng khám gần nhất (Áp dụng công thức khoảng cách Euclid)
def find_nearest_clinic(user_x, user_y):
    clinics = pd.read_csv('clinics.csv')
    nearest_clinic = None
    min_distance = float('inf')
    
    for index, row in clinics.iterrows():
        # Tính khoảng cách
        distance = math.sqrt((row['x_coord'] - user_x)**2 + (row['y_coord'] - user_y)**2)
        
        if distance < min_distance:
            min_distance = distance
            nearest_clinic = row
            
    return nearest_clinic, min_distance

# 2. Tìm bác sĩ theo chuyên khoa tại phòng khám đã chọn
def get_doctors(clinic_id, specialty):
    doctors = pd.read_csv('doctors.csv')
    # Lọc data theo clinic_id và specialty
    suitable_doctors = doctors[(doctors['clinic_id'] == clinic_id) & (doctors['specialty'] == specialty)]
    return suitable_doctors

# 3. Kiểm tra trùng lịch và gợi ý/Đặt lịch
def book_appointment(email, doctor_id, date, time_str):
    appointments = pd.read_csv('appointments.csv')
    doctors = pd.read_csv('doctors.csv')
    
    # Truy xuất tên bác sĩ để đưa vào nội dung email
    doctor_info = doctors[doctors['doctor_id'] == doctor_id]
    doctor_name = doctor_info.iloc[0]['name'] if not doctor_info.empty else "Bác sĩ"
    
    # Kiểm tra xem bác sĩ đã có lịch vào ngày và giờ đó chưa
    conflict = appointments[(appointments['doctor_id'] == doctor_id) & 
                            (appointments['date'] == date) & 
                            (appointments['time'] == time_str)]
    
    if not conflict.empty:
        # Xử lý khi trùng lịch: Đề xuất khung giờ thay thế (cộng thêm 30 phút)
        time_format = "%H:%M"
        current_time_obj = datetime.strptime(time_str, time_format)
        suggested_time = (current_time_obj + timedelta(minutes=30)).strftime(time_format)
        
        return False, f"Bác sĩ đã kín lịch lúc {time_str}. Hệ thống đề xuất chuyển sang {suggested_time}."
    
    # Nếu không trùng: Tiến hành tạo ID mới và lưu vào file CSV
    new_id = f"A{len(appointments) + 1:03d}" 
    new_appointment = pd.DataFrame({
        'appointment_id': [new_id],
        'patient_email': [email],
        'doctor_id': [doctor_id],
        'date': [date],
        'time': [time_str],
        'status': ['Confirmed']
    })
    
    # Ghi nối (append) dữ liệu mới vào file appointments.csv
    new_appointment.to_csv('appointments.csv', mode='a', header=False, index=False)
    
    # KÍCH HOẠT HỆ THỐNG NHẮC LỊCH QUA EMAIL
    # Hàm này sẽ chạy ngầm sau khi lưu file CSV thành công
    send_confirmation_email(email, doctor_name, date, time_str)
    
    return True, "Đặt lịch thành công! Vui lòng kiểm tra email của bạn để xem chi tiết."

# --- ĐOẠN CODE ĐỂ CHẠY THỬ TRỰC TIẾP TRONG TERMINAL ---
if __name__ == "__main__":
    print("--- DEMO LUỒNG ĐẶT LỊCH ---")
    
    user_x, user_y = 12, 25
    symptom_specialty = "Tim mạch"
    
    clinic, dist = find_nearest_clinic(user_x, user_y)
    print(f"1. Phòng khám gần nhất: {clinic['name']} (Khoảng cách: {dist:.2f})")
    
    doctors_list = get_doctors(clinic['clinic_id'], symptom_specialty)
    print(f"2. Bác sĩ {symptom_specialty} tại đây:")
    print(doctors_list[['doctor_id', 'name']])
    
    if not doctors_list.empty:
        chosen_doctor = doctors_list.iloc[0]['doctor_id']
        test_date = "2026-06-30"
        test_time = "09:00" 
        
        success, message = book_appointment("test_email@gmail.com", chosen_doctor, test_date, test_time)
        print(f"3. Kết quả đặt lịch: {message}")