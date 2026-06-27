import streamlit as st
import pandas as pd
import os
from config import get_data_path
import plotly.express as px
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from logic import (find_nearest_clinic, find_doctors_by_symptom,
                   get_doctors, book_appointment, get_available_slots, ALL_TIME_SLOTS,
                   find_available_doctors_and_clinics)
from location_service import get_vn_locations
from auth import register_user, login_user
from geo_service import address_to_coords
from ai_service import unified_ai_chat, UNIFIED_SYSTEM_PROMPT

# ===========================================================================
# CẤU HÌNH TRANG
# ===========================================================================
st.set_page_config(
    page_title="Đặt Lịch Khám Bệnh",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===========================================================================
# CSS GLOBAL — DARK THEME
# ===========================================================================
_css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
if os.path.exists(_css_path):
    with open(_css_path, encoding='utf-8') as _f:
        st.markdown(f'<style>{_f.read()}</style>', unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'


# ===========================================================================
# TRANG ĐĂNG NHẬP
# ===========================================================================
def page_login():
    col_left, col_center, col_right = st.columns([1, 1.6, 1])
    with col_center:
        st.markdown("""
        <div class="login-hero">
            <span class="hospital-icon">🏥</span>
            <h1>Hệ Thống Đặt Lịch Khám Bệnh</h1>
            <p>Vui lòng đăng nhập để sử dụng hệ thống</p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.get('just_registered', False):
            st.success("🎉 Đăng ký thành công! Vui lòng đăng nhập.")
            st.session_state['just_registered'] = False

        tab_login, tab_register = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("login_form"):
                login_email = st.text_input("✉️  Email:", placeholder="Nhập email của bạn", key="login_email")
                login_password = st.text_input("🔒  Mật khẩu:", type="password", placeholder="Nhập mật khẩu", key="login_password")
                st.markdown("<br>", unsafe_allow_html=True)
                submit_login = st.form_submit_button("🚀 Đăng nhập", use_container_width=True)
                if submit_login:
                    if not login_email or not login_password:
                        st.error("⚠️ Vui lòng nhập đầy đủ Email và Mật khẩu!")
                    else:
                        success, user_data = login_user(login_email, login_password)
                        if success:
                            st.session_state['logged_in'] = True
                            st.session_state['user'] = user_data
                            st.rerun()
                        else:
                            st.error("❌ Email hoặc mật khẩu không đúng!")
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("**💡 Tài khoản demo:**\n- **Admin:** `admin@hospital.com` / `admin123`\n- **Bệnh nhân:** `benhnhan@gmail.com` / `patient123`")

        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            reg_email = st.text_input("✉️  Email:", placeholder="Nhập email của bạn", key="reg_email")
            reg_password = st.text_input("🔒  Mật khẩu:", type="password", placeholder="Ít nhất 6 ký tự", key="reg_password")
            reg_password2 = st.text_input("🔒  Xác nhận mật khẩu:", type="password", placeholder="Nhập lại mật khẩu", key="reg_password2")
            locations = get_vn_locations()
            provinces = list(locations.keys()) or ["Chưa có dữ liệu"]
            selected_province = st.selectbox("🗺️  Tỉnh / Thành phố:", provinces, key="reg_province")
            districts = locations.get(selected_province, ["Chưa có dữ liệu"])
            selected_district = st.selectbox("📍  Quận / Huyện:", districts, key="reg_district")
            st.markdown("<br>", unsafe_allow_html=True)
            submit_register = st.button("✨ Tạo tài khoản", use_container_width=True, key="btn_register")
            if submit_register:
                if not reg_email or not reg_password:
                    st.error("⚠️ Vui lòng nhập đầy đủ Email và Mật khẩu!")
                elif reg_password != reg_password2:
                    st.error("❌ Mật khẩu xác nhận không khớp!")
                elif len(reg_password) < 6:
                    st.error("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")
                else:
                    full_address = f"{selected_district}, {selected_province}"
                    success, message = register_user(reg_email, reg_password, full_address, selected_province, selected_district)
                    if success:
                        st.session_state['just_registered'] = True
                        st.rerun()
                    else:
                        st.error(message)


# ===========================================================================
# SIDEBAR
# ===========================================================================
def render_sidebar():
    user = st.session_state['user']
    icon = "👑" if user['role'] == 'Admin' else "👤"
    role_bg = "rgba(239,68,68,0.2)" if user['role'] == 'Admin' else "rgba(16,185,129,0.2)"
    role_color = "#fca5a5" if user['role'] == 'Admin' else "#6ee7b7"
    role_border = "rgba(239,68,68,0.4)" if user['role'] == 'Admin' else "rgba(16,185,129,0.4)"
    role_label = "🔴 Quản trị viên" if user['role'] == 'Admin' else "🟢 Bệnh nhân"
    email_short = user['email'].split('@')[0]
    st.sidebar.markdown(f"""
    <div style="padding:0.5rem 0 1rem;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <div style="width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center;font-size:1.1rem;">{icon}</div>
            <div>
                <div style="color:#e2e8f0;font-weight:600;font-size:0.9rem;">{email_short}</div>
                <div style="color:#64748b;font-size:0.75rem;">{user['email']}</div>
            </div>
        </div>
        <div style="display:inline-block;background:{role_bg};color:{role_color};border:1px solid {role_border};padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;">{role_label}</div>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='color:#64748b;font-size:0.78rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;'>ĐIỀU HƯỚNG</p>", unsafe_allow_html=True)
    if user['role'] == 'Admin':
        page = st.sidebar.radio("menu", ["📊 Bảng quản lý"], label_visibility="collapsed")
    else:
        page = st.sidebar.radio("menu", ["📅 Đặt lịch khám", "📜 Lịch sử đặt lịch", "🤖 Trợ lý AI"], label_visibility="collapsed")
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state['logged_in'] = False
        st.session_state['user'] = None
        st.rerun()
    return page


# ===========================================================================
# TRANG ĐẶT LỊCH KHÁM
# ===========================================================================
def page_booking():
    user = st.session_state['user']
    st.title("📅 Đặt Lịch Khám Bệnh")
    st.caption("Chọn thời gian bạn muốn khám trước, hệ thống sẽ tìm phòng khám gần nhất và bác sĩ còn lịch trống phù hợp với triệu chứng của bạn.")
    st.markdown("---")

    # ==========================
    # 1. FORM NHẬP LIỆU (UI)
    # ==========================
    st.markdown("### 1. Thông tin & Thời gian mong muốn")
    
    col_name, col_email = st.columns(2)
    with col_name:
        patient_name = st.text_input("Họ và tên:", placeholder="Nguyễn Văn A", key="booking_name")
    with col_email:
        st.text_input("Email:", value=user['email'], disabled=True, key="booking_email")
        
    locations = get_vn_locations()
    provinces = list(locations.keys()) or ["Chưa có dữ liệu"]
    import math
    def get_valid_value(val):
        return val if val and not (isinstance(val, float) and math.isnan(val)) else ''
    default_province = get_valid_value(user.get('province'))
    default_district = get_valid_value(user.get('district'))
    
    col_p, col_d = st.columns(2)
    with col_p:
        idx_p = provinces.index(default_province) if default_province in provinces else 0
        booking_province = st.selectbox("🗺️ Tỉnh / Thành phố:", provinces, index=idx_p, key="booking_province")
    with col_d:
        districts = locations.get(booking_province, ["Chưa có dữ liệu"])
        idx_d = districts.index(default_district) if default_district in districts else 0
        booking_district = st.selectbox("📍 Quận / Huyện:", districts, index=idx_d, key="booking_district")
    user_address = f"{booking_district}, {booking_province}"

    col_date, col_time = st.columns(2)
    with col_date:
        selected_date = st.date_input("📅 Ngày khám muốn đặt:").strftime("%Y-%m-%d")
    with col_time:
        selected_time = st.selectbox("⏰ Khung giờ muốn đặt:", options=ALL_TIME_SLOTS)

    symptom_input = st.text_input("🩺 Nhập triệu chứng:", placeholder="Ví dụ: đau đầu, mệt mỏi, chóng mặt, đau bụng...", key="booking_symptom")

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================
    # 2. XỬ LÝ TÌM KIẾM
    # ==========================
    if st.button("🔍 Tìm phòng khám & Bác sĩ phù hợp", key="btn_find"):
        if not patient_name:
            st.error("⚠️ Vui lòng nhập Họ và tên!")
        elif not symptom_input:
            st.error("⚠️ Vui lòng nhập triệu chứng!")
        else:
            with st.spinner("🔄 Đang xác định tọa độ từ địa chỉ..."):
                lat, lon, geo_msg = address_to_coords(user_address)
            
            if lat is None:
                st.error(f"❌ {geo_msg}")
            else:
                st.session_state['user_coords'] = (lat, lon)
                st.session_state['patient_name'] = patient_name
                st.session_state['booking_date'] = selected_date
                st.session_state['booking_time'] = selected_time
                
                with st.spinner("🔄 Đang tìm bác sĩ còn lịch trống..."):
                    # Gọi hàm logic mới
                    result_df = find_available_doctors_and_clinics(symptom_input, selected_date, selected_time, lat, lon, booking_province)
                    st.session_state['search_results'] = result_df

    # ==========================
    # 3. HIỂN THỊ KẾT QUẢ VÀ BẢN ĐỒ
    # ==========================
    if 'search_results' in st.session_state and 'user_coords' in st.session_state:
        result_df = st.session_state['search_results']
        
        st.markdown("---")
        st.markdown("### 2. Kết quả tìm kiếm")
        
        if result_df.empty:
            st.warning("⚠️ Rất tiếc, không tìm thấy bác sĩ nào phù hợp với triệu chứng của bạn và CÒN TRỐNG LỊCH vào thời gian này. Vui lòng thử khung giờ khác hoặc ngày khác!")
        else:
            st.success(f"🩺 Tìm thấy **{len(result_df)} bác sĩ** phù hợp và đang rảnh vào **{st.session_state['booking_time']} ngày {st.session_state['booking_date']}**:")
            
            # Hiển thị bảng
            display_df = result_df[['id', 'name', 'specialty', 'clinic_name', 'distance']].copy()
            display_df['distance'] = display_df['distance'].apply(lambda x: f"{x:.2f} km")
            display_df.columns = ['Mã BS', 'Tên bác sĩ', 'Chuyên khoa', 'Tên phòng khám', 'Khoảng cách']
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Bản đồ
            st.markdown("#### 🗺️ Bản đồ các phòng khám phù hợp")
            u_lat, u_lon = st.session_state['user_coords']
            m = folium.Map(location=[u_lat, u_lon], zoom_start=13, tiles="CartoDB dark_matter")
            folium.Marker(location=[u_lat, u_lon], popup="🏠 Nhà của bạn", tooltip="Vị trí của bạn", icon=folium.Icon(color='red', icon='home', prefix='fa')).add_to(m)
            
            # Đánh dấu các phòng khám trong kết quả (có thể có nhiều bác sĩ cùng phòng khám, dùng set để lọc trùng)
            unique_clinics = result_df.drop_duplicates(subset=['clinic_name'])
            
            for i, row in unique_clinics.iterrows():
                is_nearest = (i == unique_clinics.index[0]) # Dòng đầu tiên luôn là gần nhất do đã sort
                color = 'green' if is_nearest else 'blue'
                label = f"⭐ {row['clinic_name']} (GẦN NHẤT)" if is_nearest else row['clinic_name']
                folium.Marker(location=[row['clinic_lat'], row['clinic_lon']], popup=row['clinic_name'], tooltip=label, icon=folium.Icon(color=color, icon='plus-sign')).add_to(m)
                
                # Vẽ đường thẳng đến phòng khám gần nhất
                if is_nearest:
                    folium.PolyLine(locations=[[u_lat, u_lon], [row['clinic_lat'], row['clinic_lon']]], color='#818cf8', weight=3, opacity=0.8, dash_array='10').add_to(m)
            
            st_folium(m, width=None, height=420, use_container_width=True)

            # ==========================
            # 4. CHỌN BÁC SĨ ĐỂ ĐẶT LỊCH
            # ==========================
            st.markdown("---")
            st.markdown("### 3. Xác nhận Đặt lịch")
            
            # Tạo dictionary cho selectbox
            doc_dict = dict(zip(result_df['id'], result_df.apply(lambda r: f"BS. {r['name']} — {r['specialty']} ({r['clinic_name']} - Cách {r['distance']:.2f} km)", axis=1)))
            
            selected_doc_id = st.selectbox("👨‍⚕️ Chọn một bác sĩ từ danh sách trên để chốt lịch:", options=doc_dict.keys(), format_func=lambda x: doc_dict[x])
            
            st.info(f"Bạn đang đặt lịch khám với **BS. {result_df[result_df['id'] == selected_doc_id].iloc[0]['name']}** vào lúc **{st.session_state['booking_time']}** ngày **{st.session_state['booking_date']}**.")
            
            if st.button("✅ Xác nhận Đặt lịch", key="btn_book"):
                p_name = st.session_state['patient_name']
                b_date = st.session_state['booking_date']
                b_time = st.session_state['booking_time']
                
                success, message, slots = book_appointment(p_name, user['email'], selected_doc_id, b_date, b_time)
                if success:
                    st.success("🎉 " + message)
                    st.balloons()
                    # Xóa search_results để reset trang sau khi đặt thành công
                    del st.session_state['search_results']
                else:
                    st.warning("⚠️ " + message)



# ===========================================================================
# TRANG LỊCH SỬ
# ===========================================================================
def page_history():
    user = st.session_state['user']
    st.title("📜 Lịch Sử Đặt Lịch")
    st.caption("Xem toàn bộ các lịch hẹn khám bệnh của bạn.")
    st.markdown("---")
    appointments = pd.read_csv(get_data_path('appointments.csv'))
    doctors = pd.read_csv(get_data_path('doctors.csv'))
    clinics = pd.read_csv(get_data_path('clinics.csv'))
    my_appointments = appointments[appointments['patient_email'] == user['email']]
    if my_appointments.empty:
        st.info("📭 Bạn chưa có lịch hẹn nào. Hãy đặt lịch khám ngay!")
        return
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("📋 Tổng lịch hẹn", len(my_appointments))
    with col2: st.metric("✅ Đang hoạt động", len(my_appointments[my_appointments['status'] == 'Active']))
    with col3: st.metric("🏁 Đã khám xong", len(my_appointments[my_appointments['status'] == 'Completed']))
    st.markdown("---")
    merged = my_appointments.merge(doctors, left_on='doctor_id', right_on='id', suffixes=('', '_doc'))
    merged = merged.merge(clinics, left_on='clinic_id', right_on='id', suffixes=('', '_clinic'))
    display_df = merged[['id', 'patient_name', 'date', 'time_slot', 'name', 'specialty', 'name_clinic', 'status']].copy()
    display_df.columns = ['Mã lịch hẹn', 'Tên bệnh nhân', 'Ngày khám', 'Giờ khám', 'Bác sĩ', 'Chuyên khoa', 'Phòng khám', 'Trạng thái']
    def color_status(val):
        if val == 'Active': return 'background-color: rgba(16,185,129,0.2); color: #34d399;'
        elif val == 'Cancelled': return 'background-color: rgba(239,68,68,0.2); color: #f87171;'
        elif val == 'Completed': return 'background-color: rgba(99,102,241,0.2); color: #818cf8;'
        return ''
    st.dataframe(display_df.style.map(color_status, subset=['Trạng thái']), use_container_width=True, hide_index=True)


# ===========================================================================
# ADMIN DASHBOARD
# ===========================================================================
def page_admin_dashboard():
    st_autorefresh(interval=30000, limit=None, key="admin_autorefresh")
    st.title("📊 Bảng Quản Lý Hệ Thống")
    st.caption("⚡ Dữ liệu tự động làm mới mỗi 30 giây")
    st.markdown("---")
    appointments = pd.read_csv(get_data_path('appointments.csv'))
    doctors = pd.read_csv(get_data_path('doctors.csv'))
    clinics = pd.read_csv(get_data_path('clinics.csv'))
    total = len(appointments)
    active = len(appointments[appointments['status'] == 'Active'])
    completed = len(appointments[appointments['status'] == 'Completed'])
    cancelled = len(appointments[appointments['status'] == 'Cancelled'])
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("📋 Tổng lịch hẹn", total)
    with col2: st.metric("✅ Đang hoạt động", active)
    with col3: st.metric("🏁 Đã khám xong", completed)
    with col4: st.metric("❌ Đã hủy", cancelled)
    st.markdown("---")
    if appointments.empty:
        st.info("📭 Chưa có lịch hẹn nào trong hệ thống.")
        return
    merged = appointments.merge(doctors, left_on='doctor_id', right_on='id', suffixes=('', '_doc'))
    merged = merged.merge(clinics, left_on='clinic_id', right_on='id', suffixes=('', '_clinic'))

    def render_apt_table(df, show_actions=False, key_prefix=""):
        if df.empty:
            st.info("Không có lịch hẹn nào.")
            return
        col_widths = [0.8, 1.5, 2, 1.2, 1, 2, 1.5, 2, 1.5]
        if show_actions:
            col_widths.append(1.5)
        header_cols = st.columns(col_widths)
        headers = ["Mã", "Bệnh nhân", "Email", "Ngày", "Giờ", "Bác sĩ", "Chuyên khoa", "Phòng khám", "Trạng thái"]
        if show_actions:
            headers.append("Hành động")
        for col, h in zip(header_cols, headers):
            col.markdown(f"<p style='color:#a5b4fc;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin:0;padding:8px 2px;border-bottom:2px solid rgba(99,102,241,0.3);'>{h}</p>", unsafe_allow_html=True)
        for _, row in df.iterrows():
            row_cols = st.columns(col_widths)
            status = row.get('status', 'Active')
            if status == 'Active':
                badge = "<span class='badge-active'>● Đang HĐ</span>"
            elif status == 'Completed':
                badge = "<span class='badge-completed'>✓ Hoàn thành</span>"
            else:
                badge = "<span class='badge-cancelled'>✕ Đã hủy</span>"
            style = "color:#cbd5e1;font-size:0.82rem;margin:0;padding:10px 2px;border-bottom:1px solid rgba(99,102,241,0.08);"
            vals = [row['id'], row['patient_name'], row['patient_email'], row['date'], row['time_slot'], row['name'], row['specialty'], row['name_clinic']]
            for col, val in zip(row_cols[:8], vals):
                col.markdown(f"<p style='{style}'>{val}</p>", unsafe_allow_html=True)
            row_cols[8].markdown(f"<p style='margin:0;padding:10px 2px;border-bottom:1px solid rgba(99,102,241,0.08);'>{badge}</p>", unsafe_allow_html=True)
            if show_actions and status == 'Active':
                with row_cols[9]:
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("✅", key=f"{key_prefix}done_{row['id']}", help="Đánh dấu Hoàn thành"):
                            all_apts = pd.read_csv(get_data_path('appointments.csv'))
                            all_apts.loc[all_apts['id'] == row['id'], 'status'] = 'Completed'
                            all_apts.to_csv(get_data_path('appointments.csv'), index=False)
                            st.success(f"✅ {row['id']} → Hoàn thành")
                            st.rerun()
                    with b2:
                        if st.button("❌", key=f"{key_prefix}cancel_{row['id']}", help="Hủy lịch hẹn"):
                            all_apts = pd.read_csv(get_data_path('appointments.csv'))
                            all_apts.loc[all_apts['id'] == row['id'], 'status'] = 'Cancelled'
                            all_apts.to_csv(get_data_path('appointments.csv'), index=False)
                            st.success(f"🗑️ {row['id']} → Đã hủy")
                            st.rerun()
            elif show_actions:
                row_cols[9].markdown(f"<p style='margin:0;padding:10px 2px;border-bottom:1px solid rgba(99,102,241,0.08);color:#475569;font-size:0.78rem;'>—</p>", unsafe_allow_html=True)

    tab_all, tab_active, tab_done, tab_cancel = st.tabs([
        f"📋 Tất cả ({total})",
        f"✅ Đang hoạt động ({active})",
        f"🏁 Hoàn thành ({completed})",
        f"❌ Đã hủy ({cancelled})"
    ])
    with tab_all:
        st.markdown("<p style='color:#a5b4fc;font-size:0.85rem;'>💡 Bấm <b>✅</b> để hoàn thành hoặc <b>❌</b> để hủy lịch hẹn (chỉ áp dụng cho lịch đang hoạt động).</p>", unsafe_allow_html=True)
        render_apt_table(merged, show_actions=True, key_prefix="all_")
    with tab_active:
        st.markdown("<p style='color:#a5b4fc;font-size:0.85rem;'>💡 Bấm <b>✅</b> để hoàn thành hoặc <b>❌</b> để hủy lịch hẹn ngay trên bảng.</p>", unsafe_allow_html=True)
        render_apt_table(merged[merged['status'] == 'Active'], show_actions=True, key_prefix="active_")
    with tab_done:
        render_apt_table(merged[merged['status'] == 'Completed'], show_actions=False, key_prefix="done_")
    with tab_cancel:
        render_apt_table(merged[merged['status'] == 'Cancelled'], show_actions=False, key_prefix="cancel_")

    st.markdown("---")
    st.markdown("### 📈 Biểu đồ thống kê")
    chart_col1, chart_col2 = st.columns(2)
    CHART_LAYOUT = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8', family='Inter'), title_font=dict(color='#e2e8f0', size=14), xaxis=dict(gridcolor='rgba(99,102,241,0.1)', color='#64748b'), yaxis=dict(gridcolor='rgba(99,102,241,0.1)', color='#64748b'))
    with chart_col1:
        merged_chart = appointments.merge(doctors, left_on='doctor_id', right_on='id', suffixes=('', '_doc'))
        sc = merged_chart['specialty'].value_counts().reset_index()
        sc.columns = ['Chuyên khoa', 'Số lượng']
        fig1 = px.bar(sc, x='Chuyên khoa', y='Số lượng', title='Đặt lịch theo Chuyên khoa', color='Chuyên khoa', color_discrete_sequence=['#6366f1','#8b5cf6','#a78bfa','#818cf8','#c084fc'])
        fig1.update_layout(showlegend=False, **CHART_LAYOUT)
        st.plotly_chart(fig1, use_container_width=True)
    with chart_col2:
        tc = appointments['time_slot'].value_counts().reset_index()
        tc.columns = ['Khung giờ', 'Số lượng']
        tc = tc.sort_values('Khung giờ')
        fig2 = px.bar(tc, x='Khung giờ', y='Số lượng', title='Ca khám theo Khung giờ', color='Số lượng', color_continuous_scale=[[0,'#312e81'],[0.5,'#6366f1'],[1,'#c084fc']])
        fig2.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)
    sc2 = appointments['status'].value_counts().reset_index()
    sc2.columns = ['Trạng thái', 'Số lượng']
    fig3 = px.pie(sc2, names='Trạng thái', values='Số lượng', title='Tỷ lệ trạng thái lịch hẹn', color_discrete_sequence=['#6366f1','#10b981','#ef4444'])
    fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8', family='Inter'), title_font=dict(color='#e2e8f0', size=14), legend=dict(font=dict(color='#94a3b8')))
    st.plotly_chart(fig3, use_container_width=True)


# ===========================================================================
# TRỢ LÝ AI TỔNG HỢP (UNIFIED AI)
# ===========================================================================
def page_unified_ai():
    st.title("🤖 Trợ lý AI phòng khám")
    st.caption("Hỗ trợ tư vấn triệu chứng, hỏi đáp dịch vụ, bảng giá và thủ tục phòng khám.")
    st.markdown("---")

    # Hiển thị câu hỏi mẫu
    st.markdown("<p style='color:#a5b4fc;font-size:0.9rem;margin-bottom:0.5rem;'>💡 <b>Câu hỏi mẫu:</b></p>", unsafe_allow_html=True)
    sample_cols = st.columns(3)
    sample_questions = ["Khám chuyên khoa giá bao nhiêu?", "Thủ tục khám BHYT thế nào?", "Quy trình khám bệnh ra sao?"]
    
    # Khởi tạo state
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = [{"role": "assistant", "content": "Xin chào! Tôi là Trợ lý AI của phòng khám. Tôi có thể giúp gì cho bạn hôm nay?"}]
    if 'chat_history_gemini' not in st.session_state:
        st.session_state['chat_history_gemini'] = [
            {"role": "user", "parts": [UNIFIED_SYSTEM_PROMPT]},
            {"role": "model", "parts": ["Xin chào! Tôi là Trợ lý AI của phòng khám. Tôi có thể giúp gì cho bạn hôm nay?"]}
        ]
    if 'ai_specialty' not in st.session_state:
        st.session_state['ai_specialty'] = None

    for i, q in enumerate(sample_questions):
        with sample_cols[i]:
            if st.button(q, key=f"sample_q_{i}", use_container_width=True):
                st.session_state['pending_user_input'] = q

    st.markdown("<br>", unsafe_allow_html=True)

    # Khung hiển thị tin nhắn
    for msg in st.session_state['chat_messages']:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # Lấy input (từ ô chat hoặc từ nút bấm mẫu)
    user_input = st.chat_input("Hỏi tôi bất cứ điều gì (VD: Tôi bị đau đầu, hoặc Giá khám là bao nhiêu?)...")
    
    if st.session_state.get('pending_user_input'):
        user_input = st.session_state['pending_user_input']
        del st.session_state['pending_user_input']

    if user_input:
        st.session_state['chat_messages'].append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)
        
        with st.chat_message("assistant"):
            with st.spinner("🧠 AI đang suy nghĩ..."):
                ai_response, parsed_json = unified_ai_chat(user_input, chat_history=st.session_state['chat_history_gemini'])
            st.markdown(ai_response)
        
        st.session_state['chat_messages'].append({"role": "assistant", "content": ai_response})
        st.session_state['chat_history_gemini'].append({"role": "user", "parts": [user_input]})
        st.session_state['chat_history_gemini'].append({"role": "model", "parts": [ai_response]})
        
        if parsed_json and parsed_json.get('specialty') and parsed_json['specialty'] != 'Chưa xác định':
            st.session_state['ai_specialty'] = parsed_json

    # Hiển thị thẻ kết quả Triage nếu có
    if st.session_state.get('ai_specialty'):
        result = st.session_state['ai_specialty']
        st.markdown("---")
        st.subheader("🎯 Kết quả tư vấn chuyên khoa")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("🏥 Chuyên khoa", result.get('specialty', 'N/A'))
        with col2: st.metric("🩺 Triệu chứng", result.get('symptoms', 'N/A'))
        with col3:
            urgency = result.get('urgency', 'low')
            st.metric("⚠️ Mức độ khẩn cấp", {"low": "🟢 Thấp", "medium": "🟡 Trung bình", "high": "🔴 Cao"}.get(urgency, urgency))

    # Nút xóa lịch sử bên sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Xóa lịch sử chat AI", key="btn_clear_chat"):
        st.session_state['chat_messages'] = [{"role": "assistant", "content": "Xin chào! Tôi là Trợ lý AI phòng khám. Tôi có thể giúp gì cho bạn hôm nay?"}]
        st.session_state['chat_history_gemini'] = [
            {"role": "user", "parts": [UNIFIED_SYSTEM_PROMPT]},
            {"role": "model", "parts": ["Xin chào! Tôi là Trợ lý AI phòng khám. Tôi có thể giúp gì cho bạn hôm nay?"]}
        ]
        st.session_state['ai_specialty'] = None
        st.rerun()


# ===========================================================================
# MAIN
# ===========================================================================
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
        elif selected_page == "🤖 Trợ lý AI":
            page_unified_ai()

if __name__ == "__main__":
    main()
