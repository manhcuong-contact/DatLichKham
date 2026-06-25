from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time

# Khởi tạo Geocoder (Nominatim miễn phí, dùng OpenStreetMap)
geolocator = Nominatim(user_agent="dat_lich_kham_app", timeout=10)

def address_to_coords(address_text):
    """
    Task 3.1: Dịch địa chỉ văn bản thành tọa độ GPS (lat, lon).
    Sử dụng Nominatim (OpenStreetMap) qua thư viện Geopy.
    
    Tham số:
        address_text (str): Địa chỉ nhà, ví dụ: "55 Nguyễn Trãi, Thanh Xuân, Hà Nội"
    
    Trả về:
        (lat, lon, display_name) nếu thành công
        (None, None, error_message) nếu thất bại
    """
    if not address_text or not address_text.strip():
        return None, None, "Vui lòng nhập địa chỉ."
    
    try:
        location = geolocator.geocode(address_text, language='vi')
        if location:
            return location.latitude, location.longitude, location.address
        else:
            return None, None, f"Không tìm thấy tọa độ cho địa chỉ: '{address_text}'. Hãy thử nhập chi tiết hơn."
    except GeocoderTimedOut:
        return None, None, "Hết thời gian kết nối. Vui lòng thử lại."
    except GeocoderUnavailable:
        return None, None, "Dịch vụ bản đồ không khả dụng. Vui lòng thử lại sau."
    except Exception as e:
        return None, None, f"Lỗi: {str(e)}"
