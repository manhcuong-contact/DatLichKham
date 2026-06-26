import os
import shutil

DATA_DIR = os.getenv("DATA_DIR", ".")
CSV_FILES = ['clinics.csv', 'doctors.csv', 'appointments.csv', 'users.csv']

def init_data_dir():
    if DATA_DIR != ".":
        os.makedirs(DATA_DIR, exist_ok=True)
        for f in CSV_FILES:
            src = f
            dst = os.path.join(DATA_DIR, f)
            if not os.path.exists(dst) and os.path.exists(src):
                shutil.copy(src, dst)

def get_data_path(filename):
    return os.path.join(DATA_DIR, filename)

init_data_dir()
