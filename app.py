import streamlit as st
import pandas as pd
from datetime import datetime
from logic import find_nearest_clinic, find_doctors_by_symptom, get_doctors, book_appointment, get_available_slots, ALL_TIME_SLOTS

st.set_page_config(page_title="Đặt lịch khám", layout="centered")

st.title("🏥 Hệ Thống Đặt Lịch Khám Bệnh")
st.markdown("---")

# =============================================================================
# Phần 1: Nhập thông tin bệnh nhân
# =============================================================================
st.header("1. Thông tin của bạn")
col_name, col_email = st.columns(2)
with col_name:
    patient_name = st.text_input("Họ và tên:")
with col_email:
    email = st.text_input("Email liên hệ (để nhận lịch):")

col1, col2 = st.columns(2)
with col1:
    user_lat = st.number_input("Vĩ độ nhà (Lat):", value=21.0245, format="%.4f")
with col2:
    user_lon = st.number_input("Kinh độ nhà (Lon):", value=105.8412, format="%.4f")

# =============================================================================
# Phần 2: Nhập triệu chứng để tìm bác sĩ phù hợp
# =============================================================================
st.header("2. Mô tả triệu chứng")
symptom_input = st.text_input(
    "Nhập triệu chứng của bạn:",
    placeholder="Ví dụ: đau đầu, mệt mỏi, chóng mặt..."
)

# Nút tìm kiếm
if st.button("🔍 Tìm phòng khám & Bác sĩ phù hợp"):
    if not patient_name:
        st.error("Vui lòng nhập Họ và tên!")
    elif not email:
        st.error("Vui lòng nhập Email!")
    elif not symptom_input:
        st.error("Vui lòng nhập triệu chứng!")
    else:
        # Tìm phòng khám gần nhất
        clinic, dist = find_nearest_clinic(user_lat, user_lon)
        st.session_state['clinic'] = clinic
        st.session_state['patient_name'] = patient_name

        st.success(f"📍 Phòng khám gần nhất: **{clinic['name']}** ({clinic['address']}) — Khoảng cách: {dist:.4f}")

        # Tìm bác sĩ theo triệu chứng (Task 1.3)
        matched_doctors = find_doctors_by_symptom(symptom_input, clinic['id'])
        st.session_state['doctors'] = matched_doctors

        if not matched_doctors.empty:
            st.info(f"🩺 Tìm thấy **{len(matched_doctors)} bác sĩ** phù hợp với triệu chứng của bạn:")
            # Hiển thị bảng bác sĩ phù hợp
            display_df = matched_doctors[['id', 'name', 'specialty', 'match_count']].copy()
            display_df.columns = ['Mã BS', 'Tên bác sĩ', 'Chuyên khoa', 'Số triệu chứng khớp']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Không tìm thấy bác sĩ phù hợp với triệu chứng bạn mô tả tại phòng khám này.")

# =============================================================================
# Phần 3: Chốt lịch (Chỉ hiện khi đã tìm thấy bác sĩ)
# =============================================================================
if 'doctors' in st.session_state and not st.session_state['doctors'].empty:
    st.markdown("---")
    st.header("3. Chọn lịch khám")

    doctors_df = st.session_state['doctors']

    # Hiển thị danh sách bác sĩ để chọn
    doc_dict = dict(zip(doctors_df['id'], doctors_df.apply(lambda r: f"{r['name']} ({r['specialty']})", axis=1)))
    selected_doc_id = st.selectbox("Chọn bác sĩ:", options=doc_dict.keys(), format_func=lambda x: doc_dict[x])

    col3, col4 = st.columns(2)
    with col3:
        selected_date = st.date_input("Chọn ngày khám:").strftime("%Y-%m-%d")
    with col4:
        # Lấy danh sách khung giờ trống để hiển thị
        available_slots = get_available_slots(selected_doc_id, selected_date)
        if available_slots:
            selected_time = st.selectbox("Chọn khung giờ:", options=available_slots)
        else:
            st.warning("⚠️ Bác sĩ đã kín lịch trong ngày này. Vui lòng chọn ngày khác.")
            selected_time = None

    if selected_time and st.button("✅ Xác nhận Đặt lịch"):
        p_name = st.session_state.get('patient_name', patient_name)
        success, message, slots = book_appointment(p_name, email, selected_doc_id, selected_date, selected_time)
        if success:
            st.success("🎉 " + message)
            st.balloons()
        else:
            st.warning("⚠️ " + message)

elif 'doctors' in st.session_state and st.session_state['doctors'].empty:
    st.warning("Không tìm thấy bác sĩ phù hợp với triệu chứng bạn mô tả tại phòng khám này.")