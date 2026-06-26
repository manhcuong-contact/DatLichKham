import pandas as pd

clinics = pd.read_csv('clinics.csv')
doctors = pd.read_csv('doctors.csv')

# Danh sách 5 bệnh viện Hà Nội đã tạo
hn_clinic_names = [
    "Bệnh viện Bạch Mai", 
    "Bệnh viện Hữu Nghị Việt Đức", 
    "Bệnh viện Trung ương Quân đội 108", 
    "Bệnh viện Phụ sản Trung ương", 
    "Bệnh viện Đại học Y Hà Nội"
]

# Lấy ID của 5 bệnh viện này
hn_clinics = clinics[clinics['name'].isin(hn_clinic_names)]
hn_clinic_ids = hn_clinics['id'].tolist()

# Xóa các bác sĩ cũ thuộc 5 bệnh viện này
doctors = doctors[~doctors['clinic_id'].isin(hn_clinic_ids)]

# Định nghĩa 5 chuyên khoa
departments = [
    {"spec": "Nội tổng hợp", "symp": "đau đầu, mệt mỏi, ho, sốt, chóng mặt"},
    {"spec": "Cơ xương khớp", "symp": "đau lưng, nhức mỏi, đau khớp, mỏi gối, tê tay chân"},
    {"spec": "Tai Mũi Họng", "symp": "ho, sổ mũi, đau họng, nghẹt mũi, ù tai"},
    {"spec": "Tiêu hóa", "symp": "đau bụng, buồn nôn, tiêu chảy, ợ chua, khó tiêu"},
    {"spec": "Tim mạch", "symp": "tức ngực, khó thở, hồi hộp, tim đập nhanh"}
]

new_doctors = []
# Lấy ID bác sĩ lớn nhất hiện có để tiếp tục tăng
# IDs hiện tại có dạng D001, D002...
existing_ids = doctors['id'].apply(lambda x: int(x[1:])).tolist()
max_id = max(existing_ids) if existing_ids else 0
doc_id_counter = max_id + 1

# Thêm bác sĩ mới
for cid in hn_clinic_ids:
    clinic_name = hn_clinics[hn_clinics['id'] == cid].iloc[0]['name'].split()[-2:] # Lấy 2 từ cuối của tên BV để đặt tên BS cho dễ phân biệt
    c_short = " ".join(clinic_name)
    for dept in departments:
        new_doctors.append({
            'id': f"D{doc_id_counter:03d}",
            'name': f"BS. {dept['spec']} ({c_short})",
            'specialty': dept['spec'],
            'clinic_id': cid,
            'symptoms': dept['symp']
        })
        doc_id_counter += 1

# Gộp và lưu lại
doctors = pd.concat([doctors, pd.DataFrame(new_doctors)], ignore_index=True)
doctors.to_csv('doctors.csv', index=False)

print("Đã cập nhật xong 25 bác sĩ cho 5 bệnh viện tại Hà Nội!")
