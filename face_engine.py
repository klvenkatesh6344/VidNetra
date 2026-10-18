import os
import cv2
import numpy as np
import base64
from config import load_config
from data_manager import save_student, mark_attendance_record, get_all_students
from notifier import send_enrollment_confirmation

# Try importing face_recognition
try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False
    print("[WARNING] face_recognition package not found. Using OpenCV Haar Cascade fallback.")

class FaceEngine:
    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.reload_known_faces()

    def reload_known_faces(self):
        """Loads all face encodings from the face_data directory"""
        config = load_config()
        face_dir = config.get("FACE_DATA_DIR", "face_data")
        os.makedirs(face_dir, exist_ok=True)
        
        self.known_encodings = []
        self.known_names = []
        
        files = [f for f in os.listdir(face_dir) if f.endswith(".npy")]
        for file in files:
            name = file.replace(".npy", "")
            path = os.path.join(face_dir, file)
            try:
                encoding = np.load(path)
                self.known_encodings.append(encoding)
                self.known_names.append(name)
            except Exception as e:
                print(f"[FACE_ENGINE] Error loading {file}: {e}")
                
        print(f"[FACE_ENGINE] Loaded {len(self.known_names)} enrolled student face(s).")
        return len(self.known_names)

    def enroll_from_image(self, image_np, name, roll_no="", email="", department=""):
        """Extracts face encoding and saves to .npy and students.json"""
        config = load_config()
        face_dir = config.get("FACE_DATA_DIR", "face_data")
        os.makedirs(face_dir, exist_ok=True)
        
        rgb_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        
        if FACE_REC_AVAILABLE:
            locations = face_recognition.face_locations(rgb_image)
            if not locations:
                return False, "No face detected in image. Please center your face in good lighting."
            
            encodings = face_recognition.face_encodings(rgb_image, locations)
            if not encodings:
                return False, "Could not compute face features. Please try again."
            
            face_encoding = encodings[0]
        else:
            # OpenCV Fallback: simple normalized color histogram encoding
            gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) == 0:
                return False, "No face detected by OpenCV cascade."
            (x, y, w, h) = faces[0]
            roi = gray[y:y+h, x:x+w]
            roi_resized = cv2.resize(roi, (64, 64))
            face_encoding = (roi_resized.flatten() / 255.0).astype(np.float32)

        # Save .npy file
        npy_path = os.path.join(face_dir, f"{name}.npy")
        np.save(npy_path, face_encoding)
        
        # Save metadata
        save_student(name, roll_no, email, department)
        
        # Reload memory
        self.reload_known_faces()
        
        # Send confirmation email if email is provided
        if email:
            send_enrollment_confirmation(name, email, roll_no, department)
            
        return True, f"Student '{name}' enrolled successfully!"

    def enroll_from_base64(self, b64_string, name, roll_no="", email="", department=""):
        """Decodes base64 string from browser webcam snapshot and enrolls face"""
        try:
            if "," in b64_string:
                b64_string = b64_string.split(",")[1]
            img_bytes = base64.b64decode(b64_string)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                return False, "Invalid image data."
            return self.enroll_from_image(img, name, roll_no, email, department)
        except Exception as e:
            return False, f"Enrollment decoding failed: {str(e)}"

    def process_frame_attendance(self, frame):
        """
        Runs face recognition on a frame.
        Returns:
            annotated_frame: Frame with drawn bounding boxes and names
            detected_students: List of identified students (name, confidence, marked)
        """
        config = load_config()
        tolerance = config.get("FACE_TOLERANCE", 0.50)
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detected_students = []
        
        if FACE_REC_AVAILABLE:
            face_locations = face_recognition.face_locations(rgb_frame)
            if not face_locations or len(self.known_encodings) == 0:
                # No faces or no known faces registered
                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.putText(frame, "Unknown", (left, bottom + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                return frame, detected_students
                
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(self.known_encodings, face_encoding, tolerance=tolerance)
                face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                
                name = "Unknown"
                confidence = 0.0
                marked = False
                
                if True in matches and len(face_distances) > 0:
                    best_match_idx = np.argmin(face_distances)
                    if matches[best_match_idx]:
                        name = self.known_names[best_match_idx]
                        dist = face_distances[best_match_idx]
                        confidence = round((1.0 - dist) * 100, 1)
                        
                        # Mark attendance
                        marked, _ = mark_attendance_record(name)
                        
                        detected_students.append({
                            "name": name,
                            "confidence": f"{confidence}%",
                            "just_marked": marked
                        })
                
                top, right, bottom, left = face_location
                color = (0, 220, 100) if name != "Unknown" else (68, 68, 255) # Green / Red in BGR
                
                # Draw stylish bounding box
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Header tag
                tag = f"{name} ({confidence}%)" if name != "Unknown" else "Unknown"
                cv2.rectangle(frame, (left, top - 28), (right, top), color, cv2.FILLED)
                cv2.putText(frame, tag, (left + 6, top - 8), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1)
                
                if marked:
                    cv2.putText(frame, "[PRESENT]", (left + 6, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            # OpenCV Cascade Mode
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (56, 189, 248), 2)
                cv2.putText(frame, "Face Detected (OpenCV Mode)", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (56, 189, 248), 1)

        return frame, detected_students

# Global instance
face_engine = FaceEngine()
