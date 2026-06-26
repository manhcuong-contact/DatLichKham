import requests
import streamlit as st

@st.cache_data
def get_vn_locations():
    """
    Tải danh sách 63 Tỉnh/Thành và các Quận/Huyện của Việt Nam từ open-api.vn
    Kết quả trả về một dict dạng: {'Tên Tỉnh': ['Tên Huyện 1', 'Tên Huyện 2', ...]}
    Nếu lỗi, trả về một dict dự phòng (fallback).
    """
    try:
        response = requests.get('https://provinces.open-api.vn/api/?depth=2', timeout=5)
        response.raise_for_status()
        data = response.json()
        
        locations = {}
        for province in data:
            province_name = province.get('name', '')
            districts = [d.get('name', '') for d in province.get('districts', [])]
            if province_name:
                locations[province_name] = districts
                
        return locations
    except Exception as e:
        # Fallback cơ bản nếu API lỗi
        return {
            "Hà Nội": ["Quận Ba Đình", "Quận Hoàn Kiếm", "Quận Đống Đa", "Quận Cầu Giấy"],
            "Hồ Chí Minh": ["Quận 1", "Quận 3", "Quận 10", "Quận Bình Thạnh", "Thành phố Thủ Đức"],
            "Đà Nẵng": ["Quận Hải Châu", "Quận Thanh Khê", "Quận Sơn Trà"]
        }
