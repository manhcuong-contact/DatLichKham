import streamlit as st
import pandas as pd
from config import get_data_path
import plotly.express as px
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from logic import (find_nearest_clinic, find_doctors_by_symptom,
                   get_doctors, book_appointment, get_available_slots, ALL_TIME_SLOTS)
from location_service import get_vn_locations
from auth import register_user, login_user
from geo_service import address_to_coords
from ai_service import ai_triage_chat, rag_answer

# =============================================================================
# CẤU HÌNH TRANG
# =============================================================================
st.set_page_config(page_title="Đặt lịch khám", page_icon="🏥", layout="wide")

# Khởi tạo session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'


# =============================================================================
# TRANG ĐĂNG NHẬP
# =============================================================================
def page_login():
    st.markdown("<h1 style='text-align: center;'>🏥 Hệ Thống Đặt Lịch Khám Bệnh</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Vui lòng đăng nhập để sử dụng hệ thống</p>", unsafe_allow_html=True)
    st.markdown("---")

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        # Nếu vừa đăng ký thành công, hiển thị thông báo ở tab đăng nhập
        if st.session_state.get('just_registered', False):
            st.success("🎉 Đăng ký thành công! Vui lòng đăng nhập bằng tài khoản vừa tạo.")
            st.session_state['just_registered'] = False

        tab_login, tab_register = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký"])

        # --- TAB ĐĂNG NHẬP ---
        with tab_login:
            with st.form("login_form"):
                st.subheader("Đăng nhập")
                login_email = st.text_input("Email:", key="login_email")
                login_password = st.text_input("Mật khẩu:", type="password", key="login_password")
                submit_login = st.form_submit_button("Đăng nhập", use_container_width=True)

                if submit_login:
                    if not login_email or not login_password:
                        st.error("Vui lòng nhập đầy đủ Email và Mật khẩu!")
                    else:
                        success, user_data = login_user(login_email, login_password)
                        if success:
                            st.session_state['logged_in'] = True
                            st.session_state['user'] = user_data
                            st.success("Đăng nhập thành công!")
                            st.rerun()
                        else:
                            st.error("Email hoặc mật khẩu không đúng!")

            st.markdown("---")
            st.info("**Tài khoản demo:**\n"
                    "- Admin: `admin@hospital.com` / `admin123`\n"
                    "- Bệnh nhân: `benhnhan@gmail.com` / `patient123`")

        # --- TAB ĐĂNG KÝ ---
        with tab_register:
            st.subheader("Tạo tài khoản mới")
            reg_email = st.text_input("Email:", key="reg_email")
            reg_password = st.text_input("Mật khẩu:", type="password", key="reg_password")
            reg_password2 = st.text_input("Xác nhận mật khẩu:", type="password", key="reg_password2")
            
            locations = get_vn_locations()
            provinces = list(locations.keys())
            if not provinces:
                provinces = ["Chưa có dữ liệu"]
            selected_province = st.selectbox("Tỉnh / Thành phố:", provinces, key="reg_province")
            districts = locations.get(selected_province, ["Chưa có dữ liệu"])
            selected_district = st.selectbox("Quận / Huyện:", districts, key="reg_district")
            
            submit_register = st.button("Đăng ký", use_container_width=True)

            if submit_register:
                if not reg_email or not reg_password:
                    st.error("Vui lòng nhập đầy đủ Email và Mật khẩu!")
                elif reg_password != reg_password2:
                    st.error("Mật khẩu xác nhận không khớp!")
                elif len(reg_password) < 6:
                    st.error("Mật khẩu phải có ít nhất 6 ký tự!")
                else:
                    full_address = f"{selected_district}, {selected_province}"
                    
                    success, message = register_user(reg_email, reg_password, full_address, selected_province, selected_district)
                    if success:
                        st.session_state['just_registered'] = True
                        st.rerun()
                    else:
                        st.error(message)


# =============================================================================
# SIDEBAR — Hiển thị thông tin user và điều hướng
# =============================================================================
def render_sidebar():
    user = st.session_state['user']
    st.sidebar.markdown(f"### 👤 {user['email']}")
    st.sidebar.markdown(f"**Vai trò:** {'🔴 Quản trị viên' if user['role'] == 'Admin' else '🟢 Bệnh nhân'}")
    st.sidebar.markdown("---")

    if user['role'] == 'Admin':
        page = st.sidebar.radio("📋 Điều hướng:", ["📊 Bảng quản lý", "📅 Đặt lịch khám", "📜 Lịch sử đặt lịch", "🤖 AI Lễ tân", "📚 Hỏi đáp AI"])
    else:
        page = st.sidebar.radio("📋 Điều hướng:", ["📅 Đặt lịch khám", "📜 Lịch sử đặt lịch", "🤖 AI Lễ tân", "📚 Hỏi đáp AI"])

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['user'] = None
        st.session_state['page'] = 'login'
        # Xóa các state liên quan đến booking
        for key in ['clinic', 'doctors', 'patient_name']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    return page


# =============================================================================
# TASK 2.3: GIAO DIỆN BỆNH NHÂN — ĐẶT LỊCH KHÁM
# =============================================================================
def page_booking():
    user = st.session_state['user']
    st.title("📅 Đặt Lịch Khám Bệnh")
    st.markdown("---")

    # --- Phần 1: Thông tin bệnh nhân ---
    st.header("1. Thông tin của bạn")
    col_name, col_email = st.columns(2)
    with col_name:
        patient_name = st.text_input("Họ và tên:", key="booking_name")
    with col_email:
        st.text_input("Email:", value=user['email'], disabled=True, key="booking_email")

    st.markdown("**📍 Vị trí tìm kiếm phòng khám:**")
    locations = get_vn_locations()
    provinces = list(locations.keys())
    if not provinces: provinces = ["Chưa có dữ liệu"]
    
    # Lấy thông tin mặc định của user nếu có
    import math
    def get_valid_value(val):
        return val if val and not (isinstance(val, float) and math.isnan(val)) else ''
        
    default_province = get_valid_value(user.get('province'))
    default_district = get_valid_value(user.get('district'))
    
    idx_p = provinces.index(default_province) if default_province in provinces else 0
    booking_province = st.selectbox("Tỉnh / Thành phố:", provinces, index=idx_p, key="booking_province")
    
    districts = locations.get(booking_province, ["Chưa có dữ liệu"])
    idx_d = districts.index(default_district) if default_district in districts else 0
    booking_district = st.selectbox("Quận / Huyện:", districts, index=idx_d, key="booking_district")
    
    user_address = f"{booking_district}, {booking_province}"

    # Hiển thị tọa độ nếu đã geocode
    if 'user_coords' in st.session_state:
        lat, lon = st.session_state['user_coords']
        st.caption(f"🌐 Tọa độ GPS: ({lat:.6f}, {lon:.6f})")

    # --- Phần 2: Nhập triệu chứng ---
    st.header("2. Mô tả triệu chứng")
    symptom_input = st.text_input(
        "Nhập triệu chứng của bạn:",
        placeholder="Ví dụ: đau đầu, mệt mỏi, chóng mặt...",
        key="booking_symptom"
    )

    if st.button("🔍 Tìm phòng khám & Bác sĩ phù hợp", key="btn_find"):
        if not patient_name:
            st.error("Vui lòng nhập Họ và tên!")
        elif not user_address:
            st.error("Vui lòng nhập địa chỉ nhà!")
        elif not symptom_input:
            st.error("Vui lòng nhập triệu chứng!")
        else:
            # Chuyển đổi địa chỉ → tọa độ GPS bằng Geopy
            with st.spinner("🔄 Đang xác định tọa độ từ địa chỉ..."):
                lat, lon, geo_msg = address_to_coords(user_address)

            if lat is None:
                st.error(f"❌ {geo_msg}")
            else:
                st.session_state['user_coords'] = (lat, lon)
                st.caption(f"🌐 Đã xác định tọa độ: ({lat:.6f}, {lon:.6f}) — {geo_msg}")

                clinic, dist = find_nearest_clinic(lat, lon)
                st.session_state['clinic'] = clinic
                st.session_state['patient_name'] = patient_name

                st.success(f"📍 Phòng khám gần nhất: **{clinic['name']}** ({clinic['address']}) — Khoảng cách: {dist:.4f}")

                matched_doctors = find_doctors_by_symptom(symptom_input, clinic['id'])
                st.session_state['doctors'] = matched_doctors

                if not matched_doctors.empty:
                    st.info(f"🩺 Tìm thấy **{len(matched_doctors)} bác sĩ** phù hợp:")
                    display_df = matched_doctors[['id', 'name', 'specialty', 'match_count']].copy()
                    display_df.columns = ['Mã BS', 'Tên bác sĩ', 'Chuyên khoa', 'Số triệu chứng khớp']
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.warning("Không tìm thấy bác sĩ phù hợp tại phòng khám này.")

    # --- Bản đồ Folium (Task 3.2) ---
    if 'user_coords' in st.session_state and 'clinic' in st.session_state:
        st.markdown("---")
        st.subheader("🗺️ Bản đồ vị trí")

        u_lat, u_lon = st.session_state['user_coords']
        clinic_data = st.session_state['clinic']

        # Tạo bản đồ tại vị trí bệnh nhân
        m = folium.Map(location=[u_lat, u_lon], zoom_start=13)

        # Marker đỏ: Vị trí nhà bệnh nhân
        folium.Marker(
            location=[u_lat, u_lon],
            popup="🏠 Nhà của bạn",
            tooltip="Vị trí của bạn",
            icon=folium.Icon(color='red', icon='home', prefix='fa')
        ).add_to(m)

        # Đọc tất cả phòng khám và cắm marker
        all_clinics = pd.read_csv(get_data_path('clinics.csv'))
        for _, c in all_clinics.iterrows():
            is_nearest = (c['id'] == clinic_data['id'])
            color = 'green' if is_nearest else 'blue'
            label = f"⭐ {c['name']} (GẦN NHẤT)" if is_nearest else c['name']

            folium.Marker(
                location=[c['lat'], c['lon']],
                popup=f"{c['name']}\n{c['address']}",
                tooltip=label,
                icon=folium.Icon(color=color, icon='plus-sign')
            ).add_to(m)

        # Vẽ đường nối từ nhà đến phòng khám gần nhất
        folium.PolyLine(
            locations=[[u_lat, u_lon], [clinic_data['lat'], clinic_data['lon']]],
            color='green', weight=3, opacity=0.7, dash_array='10'
        ).add_to(m)

        st_folium(m, width=None, height=400, use_container_width=True)

    # --- Phần 3: Chốt lịch ---
    if 'doctors' in st.session_state and not st.session_state['doctors'].empty:
        st.markdown("---")
        st.header("3. Chọn lịch khám")

        doctors_df = st.session_state['doctors']
        doc_dict = dict(zip(doctors_df['id'], doctors_df.apply(lambda r: f"{r['name']} ({r['specialty']})", axis=1)))
        selected_doc_id = st.selectbox("Chọn bác sĩ:", options=doc_dict.keys(), format_func=lambda x: doc_dict[x])

        col3, col4 = st.columns(2)
        with col3:
            selected_date = st.date_input("Chọn ngày khám:").strftime("%Y-%m-%d")
        with col4:
            available_slots = get_available_slots(selected_doc_id, selected_date)
            if available_slots:
                selected_time = st.selectbox("Chọn khung giờ:", options=available_slots)
            else:
                st.warning("⚠️ Bác sĩ đã kín lịch trong ngày này!")
                selected_time = None

        if selected_time and st.button("✅ Xác nhận Đặt lịch", key="btn_book"):
            p_name = st.session_state.get('patient_name', patient_name)
            success, message, slots = book_appointment(p_name, user['email'], selected_doc_id, selected_date, selected_time)
            if success:
                st.success("🎉 " + message)
                st.balloons()
            else:
                st.warning("⚠️ " + message)


# =============================================================================
# TASK 2.3: LỊCH SỬ ĐẶT LỊCH CỦA BỆNH NHÂN
# =============================================================================
def page_history():
    user = st.session_state['user']
    st.title("📜 Lịch Sử Đặt Lịch")
    st.markdown("---")

    appointments = pd.read_csv(get_data_path('appointments.csv'))
    doctors = pd.read_csv(get_data_path('doctors.csv'))
    clinics = pd.read_csv(get_data_path('clinics.csv'))

    # Lọc lịch hẹn của bệnh nhân hiện tại
    my_appointments = appointments[appointments['patient_email'] == user['email']]

    if my_appointments.empty:
        st.info("Bạn chưa có lịch hẹn nào. Hãy đặt lịch khám ngay!")
        return

    # Join thông tin bác sĩ và phòng khám
    merged = my_appointments.merge(doctors, left_on='doctor_id', right_on='id', suffixes=('', '_doc'))
    merged = merged.merge(clinics, left_on='clinic_id', right_on='id', suffixes=('', '_clinic'))

    # Hiển thị bảng lịch sử
    display_df = merged[['id', 'patient_name', 'date', 'time_slot', 'name', 'specialty', 'name_clinic', 'status']].copy()
    display_df.columns = ['Mã lịch hẹn', 'Tên bệnh nhân', 'Ngày khám', 'Giờ khám', 'Bác sĩ', 'Chuyên khoa', 'Phòng khám', 'Trạng thái']

    # Đánh màu trạng thái
    def color_status(val):
        if val == 'Active':
            return 'background-color: #d4edda; color: #155724;'
        elif val == 'Cancelled':
            return 'background-color: #f8d7da; color: #721c24;'
        elif val == 'Completed':
            return 'background-color: #cce5ff; color: #004085;'
        return ''

    st.dataframe(
        display_df.style.applymap(color_status, subset=['Trạng thái']),
        use_container_width=True,
        hide_index=True
    )

    # Thống kê nhanh
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📋 Tổng lịch hẹn", len(my_appointments))
    with col2:
        active_count = len(my_appointments[my_appointments['status'] == 'Active'])
        st.metric("✅ Đang hoạt động", active_count)
    with col3:
        completed_count = len(my_appointments[my_appointments['status'] == 'Completed'])
        st.metric("🏁 Đã khám xong", completed_count)


# =============================================================================
# TASK 2.4: ADMIN DASHBOARD
# =============================================================================
def page_admin_dashboard():
    # Task 3.3: Tự động làm mới trang mỗi 10 giây để cập nhật trạng thái lịch hẹn
    st_autorefresh(interval=10000, limit=None, key="admin_autorefresh")

    st.title("📊 Bảng Quản Lý — Admin Dashboard")
    st.caption("⚡ Trang tự động cập nhật mỗi 10 giây")
    st.markdown("---")

    appointments = pd.read_csv(get_data_path('appointments.csv'))
    doctors = pd.read_csv(get_data_path('doctors.csv'))
    clinics = pd.read_csv(get_data_path('clinics.csv'))

    # --- Thống kê tổng quan ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Tổng lịch hẹn", len(appointments))
    with col2:
        active = len(appointments[appointments['status'] == 'Active'])
        st.metric("✅ Đang hoạt động", active)
    with col3:
        completed = len(appointments[appointments['status'] == 'Completed'])
        st.metric("🏁 Đã khám xong", completed)
    with col4:
        cancelled = len(appointments[appointments['status'] == 'Cancelled'])
        st.metric("❌ Đã hủy", cancelled)

    st.markdown("---")

    # --- Bảng danh sách tất cả lịch hẹn ---
    st.subheader("📋 Danh sách toàn bộ lịch hẹn")

    if appointments.empty:
        st.info("Chưa có lịch hẹn nào trong hệ thống.")
        return

    # Join thông tin bác sĩ
    merged = appointments.merge(doctors, left_on='doctor_id', right_on='id', suffixes=('', '_doc'))
    merged = merged.merge(clinics, left_on='clinic_id', right_on='id', suffixes=('', '_clinic'))

    display_cols = ['id', 'patient_name', 'patient_email', 'date', 'time_slot',
                    'name', 'specialty', 'name_clinic', 'status']
    display_df = merged[display_cols].copy()
    display_df.columns = ['Mã', 'Bệnh nhân', 'Email', 'Ngày', 'Giờ',
                          'Bác sĩ', 'Chuyên khoa', 'Phòng khám', 'Trạng thái']

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # --- Nút hành động: Hủy lịch / Xác nhận đã khám ---
    st.markdown("---")
    st.subheader("⚙️ Cập nhật trạng thái lịch hẹn")

    active_appointments = appointments[appointments['status'] == 'Active']
    if active_appointments.empty:
        st.info("Không có lịch hẹn nào đang hoạt động.")
    else:
        col_select, col_action = st.columns([3, 1])
        with col_select:
            # Tạo label hiển thị cho mỗi lịch hẹn
            options_dict = {}
            for _, row in active_appointments.iterrows():
                doc_name = doctors[doctors['id'] == row['doctor_id']]['name'].values
                doc_label = doc_name[0] if len(doc_name) > 0 else row['doctor_id']
                label = f"{row['id']} | {row['patient_name']} | {doc_label} | {row['date']} {row['time_slot']}"
                options_dict[row['id']] = label

            selected_apt = st.selectbox(
                "Chọn lịch hẹn cần cập nhật:",
                options=options_dict.keys(),
                format_func=lambda x: options_dict[x]
            )

        with col_action:
            new_status = st.selectbox("Chuyển sang:", ["Completed", "Cancelled"])

        if st.button("🔄 Cập nhật trạng thái", key="btn_update_status"):
            # Đọc lại file CSV, cập nhật status, ghi lại toàn bộ
            all_appointments = pd.read_csv(get_data_path('appointments.csv'))
            all_appointments.loc[all_appointments['id'] == selected_apt, 'status'] = new_status
            all_appointments.to_csv(get_data_path('appointments.csv'), index=False)

            status_vn = "Đã khám xong" if new_status == "Completed" else "Đã hủy"
            st.success(f"✅ Đã cập nhật lịch hẹn **{selected_apt}** → **{status_vn}**")
            st.rerun()

    # --- Biểu đồ thống kê ---
    st.markdown("---")
    st.subheader("📈 Biểu đồ thống kê")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Biểu đồ: Số lượng đặt lịch theo chuyên khoa
        if not appointments.empty:
            merged_chart = appointments.merge(doctors, left_on='doctor_id', right_on='id', suffixes=('', '_doc'))
            specialty_counts = merged_chart['specialty'].value_counts().reset_index()
            specialty_counts.columns = ['Chuyên khoa', 'Số lượng']

            fig1 = px.bar(
                specialty_counts,
                x='Chuyên khoa',
                y='Số lượng',
                title='📊 Số lượng đặt lịch theo Chuyên khoa',
                color='Chuyên khoa',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig1.update_layout(showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)

    with chart_col2:
        # Biểu đồ: Số ca khám theo khung giờ trong ngày
        if not appointments.empty:
            timeslot_counts = appointments['time_slot'].value_counts().reset_index()
            timeslot_counts.columns = ['Khung giờ', 'Số lượng']
            timeslot_counts = timeslot_counts.sort_values('Khung giờ')

            fig2 = px.bar(
                timeslot_counts,
                x='Khung giờ',
                y='Số lượng',
                title='🕐 Số ca khám theo Khung giờ',
                color='Số lượng',
                color_continuous_scale='Tealgrn'
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Biểu đồ tròn: Tỷ lệ trạng thái
    if not appointments.empty:
        status_counts = appointments['status'].value_counts().reset_index()
        status_counts.columns = ['Trạng thái', 'Số lượng']
        fig3 = px.pie(
            status_counts,
            names='Trạng thái',
            values='Số lượng',
            title='📊 Tỷ lệ trạng thái lịch hẹn',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig3, use_container_width=True)


# =============================================================================
# TASK 4.1: AI LỄ TÂN CHATBOT
# =============================================================================
def page_ai_chatbot():
    st.title("🤖 AI Lễ tân — Tư vấn triệu chứng")
    st.caption("Mô tả triệu chứng của bạn, AI sẽ gợi ý chuyên khoa phù hợp.")
    st.markdown("---")

    # Khởi tạo lịch sử chat
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = [
            {"role": "assistant", "content": "Xin chào! Tôi là trợ lý AI lễ tân bệnh viện. Bạn hãy mô tả triệu chứng của mình, tôi sẽ giúp bạn tìm chuyên khoa phù hợp nhé! 😊"}
        ]
    if 'chat_history_gemini' not in st.session_state:
        st.session_state['chat_history_gemini'] = [
            {"role": "user", "parts": ["Bạn là một AI lễ tân bệnh viện thông minh. Nhiệm vụ của bạn là lắng nghe mô tả triệu chứng của bệnh nhân, phân tích và xác định chuyên khoa phù hợp nhất. Trả lời bằng tiếng Việt, thân thiện. Cuối câu trả lời, luôn đính kèm JSON: {\"specialty\": \"Tên chuyên khoa\", \"symptoms\": \"triệu chứng\", \"urgency\": \"low/medium/high\"}"]},
            {"role": "model", "parts": ["Xin chào! Tôi là trợ lý AI lễ tân bệnh viện. Bạn hãy mô tả triệu chứng của mình, tôi sẽ giúp bạn tìm chuyên khoa phù hợp nhé! 😊"]},
        ]
    if 'ai_specialty' not in st.session_state:
        st.session_state['ai_specialty'] = None

    # Hiển thị lịch sử chat
    for msg in st.session_state['chat_messages']:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # Nhập tin nhắn mới
    if user_input := st.chat_input("Đại loại bạn đang có triệu chứng gì?"):
        # Hiển thị tin nhắn của user
        st.session_state['chat_messages'].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Gọi AI Gemini
        with st.chat_message("assistant"):
            with st.spinner("🧠 AI đang phân tích..."):
                ai_response, parsed_json = ai_triage_chat(
                    user_input,
                    chat_history=st.session_state['chat_history_gemini']
                )
            st.markdown(ai_response)

        # Lưu vào lịch sử
        st.session_state['chat_messages'].append({"role": "assistant", "content": ai_response})
        st.session_state['chat_history_gemini'].append({"role": "user", "parts": [user_input]})
        st.session_state['chat_history_gemini'].append({"role": "model", "parts": [ai_response]})

        # Nếu AI đã xác định được chuyên khoa
        if parsed_json and parsed_json.get('specialty') and parsed_json['specialty'] != 'Chưa xác định':
            st.session_state['ai_specialty'] = parsed_json

    # Hiển thị kết quả phân loại của AI (nếu đã có)
    if st.session_state.get('ai_specialty'):
        result = st.session_state['ai_specialty']
        st.markdown("---")
        st.subheader("🎯 Kết quả phân loại từ AI")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏥 Chuyên khoa", result.get('specialty', 'N/A'))
        with col2:
            st.metric("🩺 Triệu chứng", result.get('symptoms', 'N/A'))
        with col3:
            urgency = result.get('urgency', 'low')
            urgency_label = {"low": "🟢 Thấp", "medium": "🟡 Trung bình", "high": "🔴 Cao"}
            st.metric("⚠️ Mức độ khẩn cấp", urgency_label.get(urgency, urgency))

        if st.button("📅 Đặt lịch khám theo kết quả AI", key="btn_ai_book"):
            st.info(f"Hãy chuyển sang trang **📅 Đặt lịch khám** và nhập triệu chứng: **{result.get('symptoms', '')}** để hệ thống tự động tìm bác sĩ phù hợp!")

    # Nút xóa lịch sử chat
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Xóa lịch sử chat", key="btn_clear_chat"):
        st.session_state['chat_messages'] = [
            {"role": "assistant", "content": "Xin chào! Tôi là trợ lý AI lễ tân bệnh viện. Bạn hãy mô tả triệu chứng của mình, tôi sẽ giúp bạn tìm chuyên khoa phù hợp nhé! 😊"}
        ]
        st.session_state['chat_history_gemini'] = [
            {"role": "user", "parts": ["Bạn là AI lễ tân bệnh viện."]},
            {"role": "model", "parts": ["Xin chào! Tôi sẵn sàng giúp bạn."]},
        ]
        st.session_state['ai_specialty'] = None
        st.rerun()


# =============================================================================
# TASK 4.2: RAG HỎI ĐÁP TÀI LIỆU BỆNH VIỆN
# =============================================================================
def page_rag_qa():
    st.title("📚 Hỏi đáp AI — Tài liệu bệnh viện")
    st.caption("Hỏi bất kỳ câu hỏi nào về bảng giá dịch vụ, chính sách BHYT, quy trình khám bệnh...")
    st.markdown("---")

    # Gợi ý câu hỏi mẫu
    st.subheader("💡 Câu hỏi mẫu")
    sample_cols = st.columns(3)
    sample_questions = [
        "Khám chuyên khoa giá bao nhiêu?",
        "Thủ tục khám BHYT như thế nào?",
        "Quy trình khám bệnh gồm những bước nào?"
    ]
    for i, q in enumerate(sample_questions):
        with sample_cols[i]:
            if st.button(q, key=f"sample_q_{i}", use_container_width=True):
                st.session_state['rag_question'] = q

    st.markdown("---")

    # Ô nhập câu hỏi
    default_q = st.session_state.get('rag_question', '')
    question = st.text_input("❓ Nhập câu hỏi của bạn:", value=default_q, key="rag_input")

    if st.button("🔍 Tìm câu trả lời", key="btn_rag") and question:
        with st.spinner("🧠 AI đang tra cứu tài liệu..."):
            answer, sources = rag_answer(question)

        st.subheader("📝 Câu trả lời")
        st.markdown(answer)

        if sources:
            st.markdown("---")
            st.caption("📁 Nguồn tài liệu tham khảo:")
            for src in sources:
                st.caption(f"  • {src}")

        # Xóa giá trị mặc định
        if 'rag_question' in st.session_state:
            del st.session_state['rag_question']


# =============================================================================
# ĐIỀU HƯỚNG CHÍNH (MAIN APP)
# =============================================================================
def main():
    if not st.session_state['logged_in']:
        page_login()
    else:
        selected_page = render_sidebar()

        if selected_page == "📅 Đặt lịch khám":
            page_booking()
        elif selected_page == "📜 Lịch sử đặt lịch":
            page_history()
        elif selected_page == "📊 Bảng quản lý":
            page_admin_dashboard()
        elif selected_page == "🤖 AI Lễ tân":
            page_ai_chatbot()
        elif selected_page == "📚 Hỏi đáp AI":
            page_rag_qa()

if __name__ == "__main__":
    main()