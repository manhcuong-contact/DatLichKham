import os
import requests

def send_confirmation_email(patient_email, doctor_name, date, time):
    """
    Gửi email xác nhận đặt lịch khám qua Brevo (Sendinblue) API.
    Yêu cầu biến môi trường:
      - BREVO_API_KEY: API key từ tài khoản Brevo
      - SENDER_EMAIL:  Email đã xác minh trên Brevo (mặc định: no-reply@datllichkham.com)
      - SENDER_NAME:   Tên hiển thị (mặc định: Hệ thống Đặt lịch)
    """
    api_key = os.environ.get("BREVO_API_KEY", "")
    sender_email = os.environ.get("SENDER_EMAIL", "no-reply@datllichkham.com")
    sender_name = os.environ.get("SENDER_NAME", "Hệ thống Đặt lịch Khám")

    if not api_key:
        print("⚠️  BREVO_API_KEY chưa được cấu hình. Bỏ qua gửi email.")
        return False

    subject = "✅ Xác nhận Đặt lịch khám sức khỏe thành công"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; 
                background: #f8fafc; border-radius: 12px; overflow: hidden; 
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
      
      <!-- Header -->
      <div style="background: linear-gradient(135deg, #6366f1, #8b5cf6); 
                  padding: 32px 24px; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🏥 Đặt Lịch Khám Thành Công!</h1>
        <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 14px;">
          Hệ thống đã ghi nhận lịch hẹn của bạn
        </p>
      </div>
      
      <!-- Body -->
      <div style="padding: 32px 24px; background: white;">
        <p style="color: #374151; font-size: 16px; margin: 0 0 24px;">
          Xin chào,
        </p>
        <p style="color: #6b7280; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
          Lịch hẹn khám bệnh của bạn đã được xác nhận thành công. 
          Dưới đây là thông tin chi tiết:
        </p>
        
        <!-- Info Card -->
        <div style="background: #f1f5f9; border-radius: 10px; padding: 20px; margin-bottom: 24px;">
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 10px 0; color: #6b7280; font-size: 14px; width: 40%;">👨‍⚕️ Bác sĩ phụ trách</td>
              <td style="padding: 10px 0; color: #1e293b; font-weight: 600; font-size: 14px;">BS. {doctor_name}</td>
            </tr>
            <tr style="border-top: 1px solid #e2e8f0;">
              <td style="padding: 10px 0; color: #6b7280; font-size: 14px;">📅 Ngày khám</td>
              <td style="padding: 10px 0; color: #1e293b; font-weight: 600; font-size: 14px;">{date}</td>
            </tr>
            <tr style="border-top: 1px solid #e2e8f0;">
              <td style="padding: 10px 0; color: #6b7280; font-size: 14px;">🕐 Giờ khám</td>
              <td style="padding: 10px 0; color: #1e293b; font-weight: 600; font-size: 14px;">{time}</td>
            </tr>
          </table>
        </div>
        
        <!-- Note -->
        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; 
                    border-radius: 6px; padding: 14px 16px; margin-bottom: 24px;">
          <p style="color: #92400e; margin: 0; font-size: 14px;">
            ⚠️ Vui lòng đến đúng giờ và mang theo CMND/CCCD để đăng ký khám.
          </p>
        </div>
        
        <p style="color: #6b7280; font-size: 14px; margin: 0;">
          Trân trọng,<br>
          <strong style="color: #6366f1;">Hệ thống Đặt lịch Khám Bệnh</strong>
        </p>
      </div>
      
      <!-- Footer -->
      <div style="padding: 16px 24px; background: #f8fafc; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px; margin: 0;">
          Email này được gửi tự động, vui lòng không trả lời trực tiếp.
        </p>
      </div>
    </div>
    """

    # Gọi Brevo Transactional Email API
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": patient_email}],
        "subject": subject,
        "htmlContent": html_body
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code in (200, 201):
            print(f"✅ Đã gửi email Brevo thành công tới {patient_email}")
            return True
        else:
            print(f"❌ Brevo API lỗi {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Lỗi kết nối Brevo: {e}")
        return False


def send_reminder_email(patient_email, patient_name, doctor_name, clinic_name, date, time):
    """
    Gửi email nhắc lịch khám trước 30 phút qua Brevo API.
    """
    api_key = os.environ.get("BREVO_API_KEY", "")
    sender_email = os.environ.get("SENDER_EMAIL", "no-reply@datllichkham.com")
    sender_name = os.environ.get("SENDER_NAME", "Hệ thống Đặt lịch Khám")

    if not api_key:
        print("⚠️  BREVO_API_KEY chưa được cấu hình. Bỏ qua gửi email nhắc lịch.")
        return False

    subject = "⏰ Nhắc nhở: Lịch khám của bạn sắp đến!"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;
                background: #f8fafc; border-radius: 12px; overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);">

      <!-- Header -->
      <div style="background: linear-gradient(135deg, #f59e0b, #ef4444);
                  padding: 32px 24px; text-align: center;">
        <div style="font-size: 48px; margin-bottom: 8px;">⏰</div>
        <h1 style="color: white; margin: 0; font-size: 22px;">Nhắc nhở Lịch khám!</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0; font-size: 14px;">
          Lịch hẹn của bạn còn khoảng <strong>30 phút nữa</strong>
        </p>
      </div>

      <!-- Body -->
      <div style="padding: 32px 24px; background: white;">
        <p style="color: #374151; font-size: 16px; margin: 0 0 8px;">
          Xin chào <strong>{patient_name}</strong>,
        </p>
        <p style="color: #6b7280; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
          Đây là thông báo nhắc nhở lịch hẹn khám sắp đến của bạn:
        </p>

        <!-- Info Card -->
        <div style="background: #fff7ed; border: 2px solid #fed7aa; border-radius: 10px; padding: 20px; margin-bottom: 24px;">
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 10px 0; color: #6b7280; font-size: 14px; width: 40%;">👨‍⚕️ Bác sĩ phụ trách</td>
              <td style="padding: 10px 0; color: #1e293b; font-weight: 600; font-size: 14px;">BS. {doctor_name}</td>
            </tr>
            <tr style="border-top: 1px solid #fed7aa;">
              <td style="padding: 10px 0; color: #6b7280; font-size: 14px;">🏥 Phòng khám</td>
              <td style="padding: 10px 0; color: #1e293b; font-weight: 600; font-size: 14px;">{clinic_name}</td>
            </tr>
            <tr style="border-top: 1px solid #fed7aa;">
              <td style="padding: 10px 0; color: #6b7280; font-size: 14px;">📅 Ngày khám</td>
              <td style="padding: 10px 0; color: #1e293b; font-weight: 600; font-size: 14px;">{date}</td>
            </tr>
            <tr style="border-top: 1px solid #fed7aa;">
              <td style="padding: 10px 0; color: #6b7280; font-size: 14px;">🕐 Giờ khám</td>
              <td style="padding: 10px 0; color: #ef4444; font-weight: 700; font-size: 18px;">{time}</td>
            </tr>
          </table>
        </div>

        <!-- Action reminder -->
        <div style="background: #fef2f2; border-left: 4px solid #ef4444;
                    border-radius: 6px; padding: 14px 16px; margin-bottom: 24px;">
          <p style="color: #991b1b; margin: 0; font-size: 14px; font-weight: 600;">
            🚗 Hãy chuẩn bị lên đường ngay để đến đúng giờ!
          </p>
          <p style="color: #b91c1c; margin: 8px 0 0; font-size: 13px;">
            Nhớ mang theo: CMND/CCCD, bảo hiểm y tế (nếu có), và các kết quả xét nghiệm trước đây.
          </p>
        </div>

        <p style="color: #6b7280; font-size: 14px; margin: 0;">
          Trân trọng,<br>
          <strong style="color: #f59e0b;">Hệ thống Đặt lịch Khám Bệnh</strong>
        </p>
      </div>

      <!-- Footer -->
      <div style="padding: 16px 24px; background: #f8fafc; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px; margin: 0;">
          Email này được gửi tự động, vui lòng không trả lời trực tiếp.
        </p>
      </div>
    </div>
    """

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": patient_email}],
        "subject": subject,
        "htmlContent": html_body
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code in (200, 201):
            print(f"✅ Đã gửi email nhắc lịch Brevo tới {patient_email}")
            return True
        else:
            print(f"❌ Brevo nhắc lịch lỗi {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Lỗi kết nối Brevo (reminder): {e}")
        return False