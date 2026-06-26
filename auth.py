import pandas as pd
from config import get_data_path
import hashlib
import os

USERS_FILE = get_data_path('users.csv')

def hash_password(password):
    """Mã hóa mật khẩu bằng SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, password, address, role="Patient"):
    """
    Đăng ký tài khoản mới.
    - Kiểm tra email trùng lặp.
    - Mã hóa mật khẩu trước khi lưu.
    - Trả về (True, message) nếu thành công, (False, message) nếu thất bại.
    """
    users = pd.read_csv(USERS_FILE)

    # Kiểm tra email đã tồn tại chưa
    if email in users['email'].values:
        return False, "Email này đã được đăng ký. Vui lòng dùng email khác."

    # Tạo ID mới
    new_id = f"U{len(users) + 1:03d}"
    password_hash = hash_password(password)

    new_user = pd.DataFrame({
        'id': [new_id],
        'email': [email],
        'password_hash': [password_hash],
        'role': [role],
        'address': [address]
    })

    # Đảm bảo file có dấu xuống dòng ở cuối trước khi append
    with open(USERS_FILE, 'r+') as f:
        content = f.read()
        if content and not content.endswith('\n'):
            f.write('\n')
    new_user.to_csv(USERS_FILE, mode='a', header=False, index=False)

    return True, "Đăng ký thành công! Bạn có thể đăng nhập ngay."

def login_user(email, password):
    """
    Xác thực đăng nhập.
    - So sánh hash mật khẩu nhập vào với hash đã lưu.
    - Trả về (True, user_data) nếu đúng, (False, None) nếu sai.
    """
    users = pd.read_csv(USERS_FILE)

    user = users[users['email'] == email]
    if user.empty:
        return False, None

    stored_hash = user.iloc[0]['password_hash']
    input_hash = hash_password(password)

    if stored_hash == input_hash:
        return True, user.iloc[0]
    else:
        return False, None

def get_user_by_email(email):
    """Trả về thông tin user theo email."""
    users = pd.read_csv(USERS_FILE)
    user = users[users['email'] == email]
    if not user.empty:
        return user.iloc[0]
    return None
