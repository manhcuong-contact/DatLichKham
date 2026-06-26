import pandas as pd

# Tọa độ trung tâm chính xác của 63 tỉnh thành - hardcoded để tránh lỗi geocoding
PROVINCE_COORDS = {
    "An Giang":            (10.3660, 105.4380),
    "Bà Rịa - Vũng Tàu":  (10.5417, 107.2429),
    "Bắc Giang":           (21.2731, 106.1946),
    "Bắc Kạn":             (22.1474, 105.8348),
    "Bạc Liêu":            (9.2900,  105.7241),
    "Bắc Ninh":            (21.1861, 106.0763),
    "Bến Tre":             (10.2333, 106.3750),
    "Bình Định":           (13.7760, 109.2235),
    "Bình Dương":          (11.3254, 106.4770),
    "Bình Phước":          (11.7512, 106.7235),
    "Bình Thuận":          (10.9289, 108.1021),
    "Cà Mau":              (9.1769,  105.1503),
    "Cao Bằng":            (22.6650, 106.2638),
    "Đắk Lắk":            (12.7100, 108.2378),
    "Đắk Nông":           (12.0046, 107.6879),
    "Điện Biên":          (21.3857, 103.0230),
    "Đồng Nai":           (10.9452, 106.8245),
    "Đồng Tháp":          (10.4933, 105.6882),
    "Gia Lai":             (13.9833, 108.0000),
    "Hà Giang":            (22.8232, 104.9836),
    "Hà Nam":              (20.5464, 105.9130),
    "Hà Tĩnh":             (18.3559, 105.8877),
    "Hải Dương":           (20.9399, 106.3309),
    "Hậu Giang":           (9.7583,  105.6405),
    "Hòa Bình":            (20.8133, 105.3383),
    "Hưng Yên":            (20.6530, 106.0510),
    "Khánh Hòa":           (12.2388, 109.1967),
    "Kiên Giang":          (10.0125, 105.0809),
    "Kon Tum":             (14.3490, 107.9838),
    "Lai Châu":            (22.3964, 103.4582),
    "Lâm Đồng":           (11.9465, 108.4419),
    "Lạng Sơn":           (21.8462, 106.7612),
    "Lào Cai":             (22.4856, 103.9754),
    "Long An":             (10.6956, 106.2431),
    "Nam Định":            (20.4251, 106.1682),
    "Nghệ An":             (18.9000, 105.6761),
    "Ninh Bình":           (20.2506, 105.9745),
    "Ninh Thuận":          (11.5647, 108.9888),
    "Phú Thọ":             (21.4220, 105.2284),
    "Quảng Bình":          (17.4680, 106.6220),
    "Quảng Nam":           (15.5394, 108.0191),
    "Quảng Ngãi":          (15.1214, 108.8044),
    "Quảng Ninh":          (21.0064, 107.2925),
    "Quảng Trị":           (16.7490, 107.1853),
    "Sóc Trăng":           (9.6025,  105.9739),
    "Sơn La":              (21.3256, 103.9141),
    "Tây Ninh":            (11.3100, 106.0980),
    "Thái Bình":           (20.4463, 106.3366),
    "Thái Nguyên":         (21.5671, 105.8252),
    "Thanh Hóa":           (19.8077, 105.7769),
    "Thừa Thiên Huế":     (16.4675, 107.5905),
    "Tiền Giang":          (10.4493, 106.3420),
    "Trà Vinh":            (9.9348,  106.3456),
    "Tuyên Quang":         (21.8235, 105.2140),
    "Vĩnh Long":           (10.2397, 105.9723),
    "Vĩnh Phúc":           (21.3608, 105.5474),
    "Yên Bái":             (21.7051, 104.8751),
    "Phú Yên":             (13.0955, 109.2924),
    "Cần Thơ":             (10.0452, 105.7469),
    "Đà Nẵng":            (16.0544, 108.2022),
    "Hải Phòng":           (20.8449, 106.6881),
}

clinics = pd.read_csv('clinics.csv')

# Các bệnh viện HN, HCM và đúng tọa độ thì không cần sửa
skip_ids = ['C062','C063','C064','C065','C066','C067','C068','C069','C070','C071']

updated = 0
for idx, row in clinics.iterrows():
    if row['id'] in skip_ids:
        continue
    # Tìm tỉnh từ tên bệnh viện: "Bệnh viện Đa khoa tỉnh {Tên Tỉnh}"
    prov_name = row['name'].replace("Bệnh viện Đa khoa tỉnh ", "").strip()
    if prov_name in PROVINCE_COORDS:
        new_lat, new_lon = PROVINCE_COORDS[prov_name]
        if abs(clinics.at[idx, 'lat'] - new_lat) > 0.01 or abs(clinics.at[idx, 'lon'] - new_lon) > 0.01:
            print(f"Fix {row['id']} {prov_name}: ({row['lat']:.4f},{row['lon']:.4f}) → ({new_lat},{new_lon})")
            clinics.at[idx, 'lat'] = new_lat
            clinics.at[idx, 'lon'] = new_lon
            updated += 1
    else:
        print(f"KHÔNG TÌM THẤY: {prov_name}")

clinics.to_csv('clinics.csv', index=False)
print(f"\nĐã sửa {updated} bệnh viện bị lệch tọa độ.")
