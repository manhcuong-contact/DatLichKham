import pandas as pd
from config import get_data_path
import math
from datetime import datetime, timedelta

# Import hàm gửi email từ file email_service.py
from email_service import send_confirmation_email

# =============================================================================
# DANH SÁCH KHUNG GIỜ KHÁM TRONG NGÀY (Mỗi slot cách nhau 30 phút)
# =============================================================================
ALL_TIME_SLOTS = [
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"
]

# =============================================================================
# TASK 1.2: Tìm phòng khám gần nhất (Công thức khoảng cách Euclid)
# =============================================================================
def find_nearest_clinic(user_lat, user_lon):
    """
    Nhận vào tọa độ (lat, lon) của bệnh nhân.
    Tính khoảng cách Euclid đến tất cả phòng khám.
    Trả về phòng khám gần nhất và khoảng cách.
    """
    clinics = pd.read_csv(get_data_path('clinics.csv'))
    nearest_clinic = None
    min_distance = float('inf')

    for index, row in clinics.iterrows():
        distance = math.sqrt((row['lat'] - user_lat)**2 + (row['lon'] - user_lon)**2)

        if distance < min_distance:
            min_distance = distance
            nearest_clinic = row

    return nearest_clinic, min_distance

# =============================================================================
# TASK 1.3: Khớp triệu chứng và lọc bác sĩ (String Matching)
# =============================================================================
def find_doctors_by_symptom(symptom_text, clinic_id):
    """
    Nhận vào chuỗi triệu chứng bệnh nhân nhập (ví dụ: "đau đầu, mệt mỏi").
    Quét cột 'symptoms' trong doctors.csv, dùng string matching để tìm
    bác sĩ có triệu chứng khớp, chỉ lấy bác sĩ tại phòng khám đã chọn.
    Trả về DataFrame các bác sĩ phù hợp kèm số triệu chứng khớp.
    """
    doctors = pd.read_csv(get_data_path('doctors.csv'))

    # Lọc bác sĩ thuộc phòng khám gần nhất
    clinic_doctors = doctors[doctors['clinic_id'] == clinic_id].copy()

    if clinic_doctors.empty:
        return clinic_doctors

    # Chuẩn hóa chuỗi triệu chứng bệnh nhân nhập vào
    symptom_text_lower = symptom_text.lower().strip()
    # Tách các từ khóa triệu chứng (hỗ trợ cả dấu phẩy và dấu cách)
    patient_keywords = [kw.strip() for kw in symptom_text_lower.replace(',', '|').split('|') if kw.strip()]

    # Tính số triệu chứng khớp cho mỗi bác sĩ
    match_counts = []
    for _, doc_row in clinic_doctors.iterrows():
        doc_symptoms = str(doc_row['symptoms']).lower()
        count = 0
        for keyword in patient_keywords:
            if keyword in doc_symptoms:
                count += 1
        match_counts.append(count)

    clinic_doctors['match_count'] = match_counts

    # Chỉ giữ lại bác sĩ có ít nhất 1 triệu chứng khớp
    matched_doctors = clinic_doctors[clinic_doctors['match_count'] > 0]

    # Sắp xếp theo số triệu chứng khớp giảm dần (bác sĩ phù hợp nhất lên đầu)
    matched_doctors = matched_doctors.sort_values('match_count', ascending=False)

    return matched_doctors

# Hàm phụ: Lọc bác sĩ theo chuyên khoa (giữ lại để tương thích)
def get_doctors(clinic_id, specialty):
    """Lọc bác sĩ theo chuyên khoa tại phòng khám đã chọn."""
    doctors = pd.read_csv(get_data_path('doctors.csv'))
    suitable_doctors = doctors[(doctors['clinic_id'] == clinic_id) & (doctors['specialty'] == specialty)]
    return suitable_doctors

# =============================================================================
# TASK 1.4: Xử lý logic đặt lịch & Check trùng lịch (Cải tiến gợi ý đa khung giờ)
# =============================================================================
def find_available_doctors_and_clinics(symptom_text, date, time_slot, user_lat, user_lon, booking_province=""):
    """
    1. Lọc phòng khám theo booking_province.
    2. Lọc bác sĩ có triệu chứng khớp và thuộc các phòng khám trên.
    3. Lọc theo lịch làm việc chẵn/lẻ (schedule_type) dựa vào ngày khám.
    4. Loại bỏ những bác sĩ đã bị đặt lịch (Active) vào date và time_slot.
    5. Ghép với thông tin phòng khám và tính khoảng cách từ (user_lat, user_lon).
    6. Trả về DataFrame chứa các bác sĩ phù hợp, sắp xếp theo khoảng cách gần nhất.
    """
    doctors = pd.read_csv(get_data_path('doctors.csv'))
    clinics = pd.read_csv(get_data_path('clinics.csv'))
    appointments = pd.read_csv(get_data_path('appointments.csv'))

    # Nếu cột schedule_type chưa có (chạy phiên bản cũ), tạo mặc định
    if 'schedule_type' not in doctors.columns:
        doctors['schedule_type'] = 'All'

    # 1. Lọc phòng khám theo tỉnh
    if booking_province and booking_province != "Chưa có dữ liệu":
        # Chuẩn hóa tên tỉnh bằng cách bỏ tiền tố "Thành phố " hoặc "Tỉnh "
        clean_province = booking_province.replace("Thành phố ", "").replace("Tỉnh ", "").strip()
        clinics = clinics[clinics['address'].str.contains(clean_province, case=False, na=False)]
    
    if clinics.empty:
        return pd.DataFrame()
        
    valid_clinic_ids = clinics['id'].tolist()
    doctors = doctors[doctors['clinic_id'].isin(valid_clinic_ids)]

    # 2. Tìm các bác sĩ có triệu chứng khớp
    symptom_text_lower = symptom_text.lower().strip()
    patient_keywords = [kw.strip() for kw in symptom_text_lower.replace(',', '|').split('|') if kw.strip()]
    
    match_counts = []
    for _, doc_row in doctors.iterrows():
        doc_symptoms = str(doc_row['symptoms']).lower()
        count = 0
        for keyword in patient_keywords:
            if keyword in doc_symptoms:
                count += 1
        match_counts.append(count)
        
    doctors['match_count'] = match_counts
    matched_doctors = doctors[doctors['match_count'] > 0].copy()

    if matched_doctors.empty:
        return pd.DataFrame()

    # 3. Lọc theo schedule_type (Even/Odd)
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        day = dt.day
        is_even_day = (day % 2 == 0)
    except Exception:
        is_even_day = True # Fallback

    def is_working(schedule_type):
        if schedule_type == 'All': return True
        if schedule_type == 'Even' and is_even_day: return True
        if schedule_type == 'Odd' and not is_even_day: return True
        return False

    matched_doctors = matched_doctors[matched_doctors['schedule_type'].apply(is_working)].copy()

    if matched_doctors.empty:
        return pd.DataFrame()

    # 4. Loại bỏ các bác sĩ đã có lịch hẹn Active vào date và time_slot
    booked_appointments = appointments[
        (appointments['date'] == date) &
        (appointments['time_slot'] == time_slot) &
        (appointments['status'] == 'Active')
    ]
    booked_doctor_ids = booked_appointments['doctor_id'].tolist()
    available_doctors = matched_doctors[~matched_doctors['id'].isin(booked_doctor_ids)].copy()

    if available_doctors.empty:
        return pd.DataFrame()

    # 5. Tính khoảng cách và lấy thông tin clinic
    distances = []
    clinic_names = []
    clinic_lats = []
    clinic_lons = []
    
    for _, doc_row in available_doctors.iterrows():
        clinic_info = clinics[clinics['id'] == doc_row['clinic_id']]
        if not clinic_info.empty:
            c_row = clinic_info.iloc[0]
            dist = math.sqrt((c_row['lat'] - user_lat)**2 + (c_row['lon'] - user_lon)**2)
            distances.append(dist)
            clinic_names.append(c_row['name'])
            clinic_lats.append(c_row['lat'])
            clinic_lons.append(c_row['lon'])
        else:
            distances.append(float('inf'))
            clinic_names.append("Không xác định")
            clinic_lats.append(0.0)
            clinic_lons.append(0.0)

    available_doctors['distance'] = distances
    available_doctors['clinic_name'] = clinic_names
    available_doctors['clinic_lat'] = clinic_lats
    available_doctors['clinic_lon'] = clinic_lons

    # 6. Sắp xếp: Ưu tiên khoảng cách gần nhất, sau đó đến số triệu chứng khớp cao nhất
    result_df = available_doctors.sort_values(by=['distance', 'match_count'], ascending=[True, False])
    return result_df

def get_available_slots(doctor_id, date):
    """
    Trả về danh sách các khung giờ còn trống của bác sĩ trong ngày.
    So sánh toàn bộ ALL_TIME_SLOTS với các lịch hẹn Active đã tồn tại.
    """
    appointments = pd.read_csv(get_data_path('appointments.csv'))

    # Lọc các lịch hẹn Active của bác sĩ này trong ngày đó
    booked = appointments[
        (appointments['doctor_id'] == doctor_id) &
        (appointments['date'] == date) &
        (appointments['status'] == 'Active')
    ]
    booked_slots = booked['time_slot'].tolist()

    # Trả về các slot chưa bị đặt
    available = [slot for slot in ALL_TIME_SLOTS if slot not in booked_slots]
    return available

def book_appointment(patient_name, email, doctor_id, date, time_slot):
    """
    Đặt lịch hẹn cho bệnh nhân.
    - Kiểm tra trùng lịch (doctor_id + date + time_slot + status Active).
    - Nếu trùng: Trả về danh sách TẤT CẢ khung giờ còn trống trong ngày.
    - Nếu không trùng: Ghi lịch hẹn mới vào CSV và gửi email xác nhận.
    """
    appointments = pd.read_csv(get_data_path('appointments.csv'))
    doctors = pd.read_csv(get_data_path('doctors.csv'))

    # Truy xuất tên bác sĩ để đưa vào nội dung email
    doctor_info = doctors[doctors['id'] == doctor_id]
    doctor_name = doctor_info.iloc[0]['name'] if not doctor_info.empty else "Bác sĩ"

    # Kiểm tra trùng lịch (chỉ xét các lịch hẹn có status = Active)
    conflict = appointments[
        (appointments['doctor_id'] == doctor_id) &
        (appointments['date'] == date) &
        (appointments['time_slot'] == time_slot) &
        (appointments['status'] == 'Active')
    ]

    if not conflict.empty:
        # Tìm TẤT CẢ khung giờ còn trống trong ngày để gợi ý
        available_slots = get_available_slots(doctor_id, date)
        if available_slots:
            slots_str = ", ".join(available_slots)
            return False, f"Bác sĩ đã kín lịch lúc {time_slot}. Các khung giờ còn trống: {slots_str}", available_slots
        else:
            return False, f"Bác sĩ đã kín toàn bộ lịch trong ngày {date}. Vui lòng chọn ngày khác.", []

    # Nếu không trùng: Tạo ID mới và lưu vào file CSV
    new_id = f"A{len(appointments) + 1:03d}"
    new_appointment = pd.DataFrame({
        'id': [new_id],
        'patient_name': [patient_name],
        'patient_email': [email],
        'doctor_id': [doctor_id],
        'date': [date],
        'time_slot': [time_slot],
        'status': ['Active']
    })

    # Ghi nối dữ liệu mới vào file appointments.csv
    # Đảm bảo file có dấu xuống dòng ở cuối trước khi append
    with open(get_data_path('appointments.csv'), 'r+') as f:
        content = f.read()
        if content and not content.endswith('\n'):
            f.write('\n')
    new_appointment.to_csv(get_data_path('appointments.csv'), mode='a', header=False, index=False)

    # Gửi email xác nhận tự động
    send_confirmation_email(email, doctor_name, date, time_slot)

    return True, "Đặt lịch thành công! Vui lòng kiểm tra email của bạn để xem chi tiết.", []


# =============================================================================
# ĐOẠN CODE ĐỂ CHẠY THỬ TRỰC TIẾP TRONG TERMINAL
# =============================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("--- DEMO LUỒNG ĐẶT LỊCH (Giai đoạn 1 hoàn chỉnh) ---")
    print("=" * 50)

    # Giả lập tọa độ nhà bệnh nhân (gần phòng khám C01)
    user_lat, user_lon = 21.025, 105.842

    # TASK 1.2: Tìm phòng khám gần nhất
    clinic, dist = find_nearest_clinic(user_lat, user_lon)
    print(f"\n1. Phòng khám gần nhất: {clinic['name']}")
    print(f"   Địa chỉ: {clinic['address']}")
    print(f"   Khoảng cách: {dist:.4f}")

    # TASK 1.3: Khớp triệu chứng
    symptom = "đau đầu, mệt mỏi"
    print(f"\n2. Tìm bác sĩ theo triệu chứng: \"{symptom}\"")
    matched = find_doctors_by_symptom(symptom, clinic['id'])
    if not matched.empty:
        print(matched[['id', 'name', 'specialty', 'match_count']].to_string(index=False))
    else:
        print("   Không tìm thấy bác sĩ phù hợp.")

    # TASK 1.4: Đặt lịch (thử trùng lịch)
    if not matched.empty:
        chosen_doc = matched.iloc[0]['id']
        test_date = "2026-06-30"

        print(f"\n3. Khung giờ trống của BS {chosen_doc} ngày {test_date}:")
        free_slots = get_available_slots(chosen_doc, test_date)
        print(f"   {free_slots}")

        print(f"\n4. Thử đặt lịch lúc 09:00 (đã bị trùng):")
        success, msg, slots = book_appointment("Bệnh nhân Test", "test@gmail.com", chosen_doc, test_date, "09:00")
        print(f"   Kết quả: {msg}")

        print(f"\n5. Thử đặt lịch lúc 10:00 (còn trống):")
        success, msg, slots = book_appointment("Bệnh nhân Test", "test@gmail.com", chosen_doc, test_date, "10:00")
        print(f"   Kết quả: {msg}")