import pandas as pd
import random

clinics = pd.read_csv('clinics.csv')
doctors = pd.read_csv('doctors.csv')

# Nếu doctors.csv chưa có cột schedule_type, thêm vào với giá trị mặc định là 'All'
if 'schedule_type' not in doctors.columns:
    doctors['schedule_type'] = 'All'

# Danh sách 5 phòng khám Hà Nội
hn_clinic_names = [
    "Phòng khám Đa khoa Bạch Mai", 
    "Phòng khám Y khoa Việt Đức", 
    "Phòng khám Đa khoa 108", 
    "Phòng khám Phụ sản Trung ương", 
    "Phòng khám Đại học Y Hà Nội"
]

hn_clinics = clinics[clinics['name'].isin(hn_clinic_names)]
hn_clinic_ids = hn_clinics['id'].tolist()

# Xóa các bác sĩ cũ thuộc 5 phòng khám này
doctors = doctors[~doctors['clinic_id'].isin(hn_clinic_ids)]

# Định nghĩa 5 chuyên khoa
departments = [
    {"spec": "Nội tổng hợp", "symp": "đau đầu, mệt mỏi, ho, sốt, chóng mặt"},
    {"spec": "Cơ xương khớp", "symp": "đau lưng, nhức mỏi, đau khớp, mỏi gối, tê tay chân"},
    {"spec": "Tai Mũi Họng", "symp": "ho, sổ mũi, đau họng, nghẹt mũi, ù tai"},
    {"spec": "Tiêu hóa", "symp": "đau bụng, buồn nôn, tiêu chảy, ợ chua, khó tiêu"},
    {"spec": "Tim mạch", "symp": "tức ngực, khó thở, hồi hộp, tim đập nhanh"}
]

first_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
middle_names = ["Văn", "Thị", "Hữu", "Hoàng", "Thanh", "Minh", "Thu", "Ngọc", "Xuân", "Thành", "Đức", "Trọng", "Gia", "Bảo", "Hải"]
last_names = ["Anh", "Bình", "Châu", "Dũng", "Dương", "Giang", "Hải", "Hào", "Hương", "Huy", "Khang", "Khánh", "Lâm", "Linh", "Long", "Mai", "Nam", "Nga", "Ngọc", "Nhi", "Nhung", "Phong", "Phú", "Phúc", "Phương", "Quân", "Quang", "Quyên", "Sơn", "Tâm", "Thái", "Thành", "Thảo", "Thắng", "Thi", "Thịnh", "Thu", "Thủy", "Tiên", "Toàn", "Trang", "Trí", "Trung", "Tuấn", "Tùng", "Uyên", "Vân", "Việt", "Vũ", "Vy"]

def generate_random_name():
    return f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_names)}"

new_doctors = []
existing_ids = doctors['id'].apply(lambda x: int(x[1:]) if str(x).startswith('D') else 0).tolist()
max_id = max(existing_ids) if existing_ids else 0
doc_id_counter = max_id + 1

# Thêm bác sĩ mới (5 phòng khám x 5 khoa x 4 người)
for cid in hn_clinic_ids:
    for dept in departments:
        for i in range(4):
            # i=0, 1 -> Even, i=2, 3 -> Odd
            schedule = 'Even' if i < 2 else 'Odd'
            new_doctors.append({
                'id': f"D{doc_id_counter:03d}",
                'name': f"{generate_random_name()}",
                'specialty': dept['spec'],
                'clinic_id': cid,
                'symptoms': dept['symp'],
                'schedule_type': schedule
            })
            doc_id_counter += 1

# Gộp và lưu lại
doctors = pd.concat([doctors, pd.DataFrame(new_doctors)], ignore_index=True)
doctors.to_csv('doctors.csv', index=False)

print(f"Đã tạo {len(new_doctors)} bác sĩ mới cho 5 phòng khám Hà Nội và lưu vào doctors.csv.")
