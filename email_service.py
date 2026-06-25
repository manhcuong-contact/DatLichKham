import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_confirmation_email(patient_email, doctor_name, date, time):
    # Cấu hình tài khoản gửi lấy từ biến môi trường
    sender_email = os.environ.get("SENDER_EMAIL", "email_cua_ban@gmail.com") 
    # Mật khẩu ứng dụng (App Password) lấy từ biến môi trường
    sender_password = os.environ.get("SENDER_PASSWORD", "nhap_app_password_vao_day") 

    # Nội dung Email
    subject = "Xác nhận Đặt lịch khám sức khỏe thành công"
    body = f"""
    Chào bạn,
    
    Hệ thống đã ghi nhận lịch hẹn khám của bạn thành công.
    - Bác sĩ phụ trách: {doctor_name}
    - Ngày khám: {date}
    - Giờ khám: {time}
    
    Vui lòng đến đúng giờ để được phục vụ tốt nhất.
    Trân trọng,
    Hệ thống Đặt lịch.
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = patient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        # Kết nối tới server của Google
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"Đã gửi email thành công tới {patient_email}")
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False