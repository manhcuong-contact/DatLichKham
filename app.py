import streamlit as st
import pandas as pd
from datetime import datetime
from logic import find_nearest_clinic, get_doctors, book_appointment

st.set_page_config(page_title="Đặt lịch khám", layout="centered")

st.title("🏥 Hệ Thống Đặt Lịch Khám Bệnh")
st.markdown("---")

# Phần 1: Nhập thông tin bệnh nhân
st.header("1. Thông tin của bạn")
email = st.text_input("Email liên hệ (để nhận lịch):")
col1, col2 = st.columns(2)
with col1:
    user_x = st.number_input("Tọa độ nhà (X):", value=10)
with col2:
    user_y = st.number_input("Tọa độ nhà (Y):", value=20)

# Phần 2: Chọn chuyên khoa
st.header("2. Nhu cầu khám")
specialty = st.selectbox("Chọn chuyên khoa:", ["Tim mạch", "Da liễu", "Nhi khoa", "Tai mũi họng"])

# Nút tìm kiếm
if st.button("Tìm phòng khám & Bác sĩ"):
    if email:
        clinic, dist = find_nearest_clinic(user_x, user_y)
        st.session_state['clinic'] = clinic
        st.session_state['doctors'] = get_doctors(clinic['clinic_id'], specialty)
        st.success(f"📍 Phòng khám gần nhất: **{clinic['name']}** (Cách {dist:.2f} km)")
    else:
        st.error("Vui lòng nhập Email!")

# Phần 3: Chốt lịch (Chỉ hiện khi đã tìm thấy bác sĩ)
if 'doctors' in st.session_state and not st.session_state['doctors'].empty:
    st.markdown("---")
    st.header("3. Chọn lịch khám")
    
    # Hiển thị danh sách bác sĩ để chọn
    doc_dict = dict(zip(st.session_state['doctors'].doctor_id, st.session_state['doctors'].name))
    selected_doc_id = st.selectbox("Chọn bác sĩ:", options=doc_dict.keys(), format_func=lambda x: doc_dict[x])
    
    col3, col4 = st.columns(2)
    with col3:
        # Chọn ngày (Mặc định là ngày hôm nay)
        selected_date = st.date_input("Chọn ngày khám:").strftime("%Y-%m-%d")
    with col4:
        # Chọn giờ (Bước nhảy 30 phút)
        selected_time = st.time_input("Chọn giờ khám:", step=1800).strftime("%H:%M")
        
    if st.button("Xác nhận Đặt lịch"):
        success, message = book_appointment(email, selected_doc_id, selected_date, selected_time)
        if success:
            st.success("🎉 " + message)
            st.balloons() # Hiệu ứng bóng bay chúc mừng của Streamlit
        else:
            st.warning("⚠️ " + message)
elif 'doctors' in st.session_state and st.session_state['doctors'].empty:
    st.warning("Hiện tại phòng khám này không có bác sĩ chuyên khoa bạn chọn.")