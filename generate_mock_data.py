import pandas as pd
from geopy.geocoders import Nominatim
import time
import os

geolocator = Nominatim(user_agent="dat_lich_kham_data_gen")

provinces = [
    "An Giang", "Bà Rịa - Vũng Tàu", "Bắc Giang", "Bắc Kạn", "Bạc Liêu", "Bắc Ninh",
    "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước", "Bình Thuận", "Cà Mau",
    "Cao Bằng", "Đắk Lắk", "Đắk Nông", "Điện Biên", "Đồng Nai", "Đồng Tháp",
    "Gia Lai", "Hà Giang", "Hà Nam", "Hà Tĩnh", "Hải Dương", "Hậu Giang", "Hòa Bình",
    "Hưng Yên", "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu", "Lâm Đồng",
    "Lạng Sơn", "Lào Cai", "Long An", "Nam Định", "Nghệ An", "Ninh Bình", "Ninh Thuận",
    "Phú Thọ", "Quảng Bình", "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị",
    "Sóc Trăng", "Sơn La", "Tây Ninh", "Thái Bình", "Thái Nguyên", "Thanh Hóa",
    "Thừa Thiên Huế", "Tiền Giang", "Trà Vinh", "Tuyên Quang", "Vĩnh Long", "Vĩnh Phúc", "Yên Bái",
    "Phú Yên", "Cần Thơ", "Đà Nẵng", "Hải Phòng", "Hà Nội", "Hồ Chí Minh"
]

clinics = []
doctors = []
clinic_id = 1
doctor_id = 1

def add_clinic_and_doctor(name, address, prov_name):
    global clinic_id, doctor_id
    try:
        location = geolocator.geocode(address + ", Việt Nam", timeout=10)
        if location:
            lat, lon = location.latitude, location.longitude
        else:
            location = geolocator.geocode(prov_name + ", Việt Nam", timeout=10)
            lat, lon = location.latitude if location else 16.0, location.longitude if location else 108.0
    except Exception as e:
        print(f"Lỗi geocode {address}: {e}")
        lat, lon = 16.0, 108.0

    c_id = f"C{clinic_id:03d}"
    clinics.append({
        'id': c_id,
        'name': name,
        'address': address,
        'lat': lat,
        'lon': lon
    })
    
    # Add a doctor for this clinic
    d_id = f"D{doctor_id:03d}"
    doctors.append({
        'id': d_id,
        'name': f"BS. {prov_name} {doctor_id}",
        'specialty': 'Đa khoa',
        'clinic_id': c_id,
        'symptoms': 'đau đầu, mệt mỏi, ho, sốt, đau bụng, nhức mỏi, chóng mặt, đau lưng'
    })
    clinic_id += 1
    doctor_id += 1
    time.sleep(1) # Tránh bị rate limit bởi OpenStreetMap

print("Đang tạo dữ liệu cho 63 tỉnh thành...")
for prov in provinces:
    if prov == "Hà Nội":
        # 5 bệnh viện Hà Nội
        add_clinic_and_doctor("Bệnh viện Bạch Mai", "789 Giải Phóng, Đống Đa, Hà Nội", prov)
        add_clinic_and_doctor("Bệnh viện Hữu Nghị Việt Đức", "40 Tràng Thi, Hoàn Kiếm, Hà Nội", prov)
        add_clinic_and_doctor("Bệnh viện Trung ương Quân đội 108", "1 Trần Hưng Đạo, Hai Bà Trưng, Hà Nội", prov)
        add_clinic_and_doctor("Bệnh viện Phụ sản Trung ương", "43 Tràng Thi, Hoàn Kiếm, Hà Nội", prov)
        add_clinic_and_doctor("Bệnh viện Đại học Y Hà Nội", "1 Tôn Thất Tùng, Đống Đa, Hà Nội", prov)
    elif prov == "Hồ Chí Minh":
        # 5 bệnh viện HCM
        add_clinic_and_doctor("Bệnh viện Chợ Rẫy", "201B Nguyễn Chí Thanh, Quận 5, Hồ Chí Minh", prov)
        add_clinic_and_doctor("Bệnh viện Từ Dũ", "284 Cống Quỳnh, Quận 1, Hồ Chí Minh", prov)
        add_clinic_and_doctor("Bệnh viện Đại học Y Dược", "215 Hồng Bàng, Quận 5, Hồ Chí Minh", prov)
        add_clinic_and_doctor("Bệnh viện Nhi Đồng 1", "341 Sư Vạn Hạnh, Quận 10, Hồ Chí Minh", prov)
        add_clinic_and_doctor("Bệnh viện Nhân dân 115", "527 Sư Vạn Hạnh, Quận 10, Hồ Chí Minh", prov)
    else:
        # Mỗi tỉnh 1 bệnh viện đa khoa
        add_clinic_and_doctor(f"Bệnh viện Đa khoa tỉnh {prov}", f"Thành phố {prov}, {prov}", prov)
    print(f"Đã xử lý xong: {prov}")
        
df_clinics = pd.DataFrame(clinics)
df_doctors = pd.DataFrame(doctors)
df_clinics.to_csv('clinics.csv', index=False)
df_doctors.to_csv('doctors.csv', index=False)

print("Tạo dữ liệu hoàn tất! Đã lưu vào clinics.csv và doctors.csv.")
