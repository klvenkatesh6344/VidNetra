import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "APP_NAME": "VidNetra",
    "TAGLINE": "Securing Every Learning Moment",
    "SECRET_KEY": "vidnetra_super_secret_ai_key_2026",
    
    # Camera Settings
    "CAMERA_INDEX": 0,
    "CAMERA_WIDTH": 640,
    "CAMERA_HEIGHT": 480,
    "CAMERA_FPS": 30,
    
    # Face Recognition Settings
    "FACE_TOLERANCE": 0.50, # Lower = stricter, Higher = looser
    "FACE_FRAME_SKIP": 2,   # Process every Nth frame for performance
    
    # YOLO & Distraction Detection Settings
    "YOLO_MODEL": "yolov8n.pt",
    "YOLO_CONFIDENCE": 0.35,
    "PHONE_DETECTION_COOLDOWN": 180, # Seconds between email alerts
    "AUDIO_ALARM_ENABLED": True,
    
    # Crowd Density Settings
    "CROWD_WARNING_THRESHOLD": 5,
    "CROWD_DANGER_THRESHOLD": 10,
    
    # Email / SMTP Settings
    "EMAIL_ENABLED": False,
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587,
    "SENDER_EMAIL": "2303031240571@paruluniversity.ac.in",
    "SENDER_PASSWORD": "",
    "FACULTY_ALERT_EMAIL": "kuchipudilakshmivenkatesh@gmail.com",
    
    # File Paths
    "FACE_DATA_DIR": os.path.join(BASE_DIR, "face_data"),
    "ATTENDANCE_CSV": os.path.join(BASE_DIR, "attendance.csv"),
    "STUDENTS_JSON": os.path.join(BASE_DIR, "students.json"),
    "INCIDENTS_JSON": os.path.join(BASE_DIR, "incidents.json")
}

def load_config():
    """Load configuration from config.json or create with defaults"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(saved)
                return config
        except Exception as e:
            print(f"Error loading config.json: {e}. Using defaults.")
    
    # Save default config
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG

def save_config(config_dict):
    """Save configuration to config.json"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_dict, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
