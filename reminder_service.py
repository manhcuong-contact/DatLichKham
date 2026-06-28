"""
reminder_service.py
Kiểm tra các lịch hẹn sắp diễn ra trong vòng 25-35 phút tới
và gửi email nhắc nhở nếu chưa được gửi.
Được gọi bởi APScheduler chạy ngầm trong app.py (mỗi 5 phút 1 lần).
"""
import pandas as pd
import threading
from datetime import datetime, timedelta
from config import get_data_path
from email_service import send_reminder_email

try:
    from zoneinfo import ZoneInfo
    _VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except ImportError:
    import pytz
    _VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

# Lock để tránh 2 thread cùng ghi file appointments.csv một lúc
_csv_lock = threading.Lock()

def check_and_send_reminders():
    """
    Hàm chính - được gọi định kỳ bởi scheduler.
    Tìm các lịch hẹn Active còn 25-35 phút nữa và chưa gửi reminder,
    sau đó gửi email nhắc lịch và đánh dấu reminder_sent = True.
    """
    try:
        now = datetime.now(_VN_TZ)
        window_start = now + timedelta(minutes=25)
        window_end   = now + timedelta(minutes=35)

        with _csv_lock:
            appointments = pd.read_csv(get_data_path('appointments.csv'))
            doctors      = pd.read_csv(get_data_path('doctors.csv'))
            clinics      = pd.read_csv(get_data_path('clinics.csv'))

            # Đảm bảo cột reminder_sent tồn tại
            if 'reminder_sent' not in appointments.columns:
                appointments['reminder_sent'] = False

            # Lọc các lịch hẹn cần gửi nhắc
            active = appointments[
                (appointments['status'] == 'Active') &
                (appointments['reminder_sent'] != True)
            ].copy()

            sent_count = 0
            for idx, row in active.iterrows():
                try:
                    apt_dt_str = f"{row['date']} {row['time_slot']}"
                    apt_dt = datetime.strptime(apt_dt_str, "%Y-%m-%d %H:%M")
                    # Gán timezone VN
                    if hasattr(_VN_TZ, 'localize'):  # pytz
                        apt_dt = _VN_TZ.localize(apt_dt)
                    else:  # zoneinfo
                        apt_dt = apt_dt.replace(tzinfo=_VN_TZ)
                except Exception:
                    continue

                # Kiểm tra nằm trong cửa sổ 25-35 phút
                if not (window_start <= apt_dt <= window_end):
                    continue

                # Lấy thông tin bác sĩ & phòng khám
                doctor_row = doctors[doctors['id'] == row['doctor_id']]
                if doctor_row.empty:
                    continue
                doctor_name = doctor_row.iloc[0]['name']
                clinic_id   = doctor_row.iloc[0]['clinic_id']

                clinic_row = clinics[clinics['id'] == clinic_id]
                clinic_name = clinic_row.iloc[0]['name'] if not clinic_row.empty else "Phòng khám"

                # Gửi email nhắc lịch
                success = send_reminder_email(
                    patient_email=row['patient_email'],
                    patient_name=row['patient_name'],
                    doctor_name=doctor_name,
                    clinic_name=clinic_name,
                    date=row['date'],
                    time=row['time_slot']
                )

                if success:
                    appointments.loc[idx, 'reminder_sent'] = True
                    sent_count += 1

            if sent_count > 0:
                appointments.to_csv(get_data_path('appointments.csv'), index=False)
                print(f"[Reminder] Đã gửi {sent_count} email nhắc lịch lúc {now.strftime('%H:%M:%S')}")
            else:
                print(f"[Reminder] Kiểm tra lúc {now.strftime('%H:%M:%S')} — Không có lịch hẹn sắp tới.")

    except Exception as e:
        print(f"[Reminder] Lỗi khi kiểm tra nhắc lịch: {e}")
