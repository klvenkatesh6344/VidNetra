import cv2
import threading
import time
import numpy as np
from config import load_config
from face_engine import face_engine
from yolo_detector import yolo_detector

class VideoCamera:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.lock = threading.Lock()
        self.raw_frame = None
        self.mode = "raw"
        self.metrics = {}
        self.frame_counter = 0
        
        # Start background capture thread
        self.start_capture()

    def start_capture(self):
        """Initializes and runs the webcam in a separate worker thread"""
        if self.is_running:
            return
            
        config = load_config()
        cam_idx = config.get("CAMERA_INDEX", 0)
        
        try:
            self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW) # Fast DirectShow on Windows
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(cam_idx)
        except Exception as e:
            print(f"[CAMERA ERROR] Could not initialize camera {cam_idx}: {e}")
            self.cap = None

        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        """Continuous background thread grabbing raw camera frames"""
        while self.is_running:
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.raw_frame = frame
                else:
                    time.sleep(0.03)
            else:
                # Generate placeholder frame if camera is unavailable
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                placeholder[:] = (15, 23, 42) # Slate background
                cv2.putText(placeholder, "VIDNETRA AI VISION FEED", (140, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (56, 189, 248), 2)
                cv2.putText(placeholder, "Camera Initializing / Standby...", (180, 250),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (148, 163, 184), 1)
                with self.lock:
                    self.raw_frame = placeholder
                time.sleep(0.05)
            time.sleep(0.01)

    def get_processed_frame(self, mode="raw"):
        """Applies the selected AI vision pipeline to the current frame and yields JPEG bytes"""
        with self.lock:
            if self.raw_frame is None:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
            else:
                frame = self.raw_frame.copy()

        self.frame_counter += 1
        
        # Process frame based on active AI mode
        if mode == "attendance":
            # Process face recognition
            processed_frame, info = face_engine.process_frame_attendance(frame)
            self.metrics["attendance"] = {
                "detected": info,
                "timestamp": time.time()
            }
        elif mode == "phone_detection":
            # Process YOLO phone and distraction detection
            processed_frame, info = yolo_detector.process_phone_distraction(frame)
            self.metrics["phone_detection"] = info
        elif mode == "crowd_monitoring":
            # Process crowd density & stampede
            processed_frame, info = yolo_detector.process_crowd_monitoring(frame)
            self.metrics["crowd_monitoring"] = info
        elif mode == "exam_proctoring":
            # Process exam proctoring
            processed_frame, info = yolo_detector.process_exam_proctoring(frame)
            self.metrics["exam_proctoring"] = info
        else:
            processed_frame = frame

        # Add global VidNetra watermark and timestamp
        h, w, _ = processed_frame.shape
        cv2.putText(processed_frame, "VIDNETRA AI", (w - 140, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Encode to JPEG
        ret, jpeg = cv2.imencode('.jpg', processed_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ret:
            return b''
        return jpeg.tobytes()

    def get_latest_metrics(self, mode):
        """Returns the latest calculated metrics for frontend polling"""
        return self.metrics.get(mode, {})

    def stop(self):
        """Gracefully release camera resources"""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()

# Global camera instance
camera_stream = VideoCamera()
