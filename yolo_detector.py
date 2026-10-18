import cv2
import numpy as np
import time
from config import load_config
from data_manager import log_incident
from notifier import send_distraction_alert

# Try importing ultralytics YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[WARNING] ultralytics package not found. Running in fallback detection mode.")

class YOLODetector:
    def __init__(self):
        self.model = None
        self.last_alert_time = 0
        if YOLO_AVAILABLE:
            try:
                config = load_config()
                model_name = config.get("YOLO_MODEL", "yolov8n.pt")
                print(f"[YOLO] Loading model: {model_name}...")
                self.model = YOLO(model_name)
                print("[YOLO] Model loaded successfully.")
            except Exception as e:
                print(f"[YOLO ERROR] Failed to load YOLO model: {e}")
                self.model = None

    def process_phone_distraction(self, frame):
        """
        Detects students and cell phones in the classroom frame.
        Determines if a student is actively using a phone by bounding box spatial containment/overlap.
        """
        config = load_config()
        conf_thresh = config.get("YOLO_CONFIDENCE", 0.35)
        
        total_students = 0
        phone_users = 0
        phone_boxes = []
        person_boxes = []
        
        annotated_frame = frame.copy()
        
        if self.model is not None:
            results = self.model(frame, conf=conf_thresh, verbose=False)
            
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0])
                
                if label == "person":
                    total_students += 1
                    person_boxes.append(xyxy)
                elif label == "cell phone":
                    phone_boxes.append(xyxy)
            
            # Check overlap between persons and phones
            active_phone_indices = set()
            for p_idx, p_box in enumerate(person_boxes):
                for ph_box in phone_boxes:
                    # Check if phone is within or near person box
                    # Expand person box slightly for realistic detection
                    px1, py1, px2, py2 = p_box
                    phx1, phy1, phx2, phy2 = ph_box
                    
                    overlap_x = max(0, min(px2, phx2) - max(px1, phx1))
                    overlap_y = max(0, min(py2, phy2) - max(py1, phy1))
                    overlap_area = overlap_x * overlap_y
                    phone_area = max(1, (phx2 - phx1) * (phy2 - phy1))
                    
                    if overlap_area / phone_area > 0.4 or (phx1 >= px1 and phx2 <= px2 and phy1 >= py1 and phy2 <= py2):
                        active_phone_indices.add(p_idx)
                        break
            
            phone_users = len(active_phone_indices)
            
            # Draw stylish boxes
            for p_idx, p_box in enumerate(person_boxes):
                px1, py1, px2, py2 = p_box
                is_phone_user = p_idx in active_phone_indices
                
                color = (0, 0, 255) if is_phone_user else (0, 255, 0) # BGR
                tag = "DISTRACTED (PHONE)" if is_phone_user else "ATTENTIVE"
                
                cv2.rectangle(annotated_frame, (px1, py1), (px2, py2), color, 2)
                cv2.rectangle(annotated_frame, (px1, py1 - 25), (px1 + 180, py1), color, cv2.FILLED)
                cv2.putText(annotated_frame, tag, (px1 + 5, py1 - 7),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

            for ph_box in phone_boxes:
                x1, y1, x2, y2 = ph_box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                cv2.putText(annotated_frame, "Phone", (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
                            
        else:
            # Fallback mock/simulated detection for testing
            h, w, _ = frame.shape
            cv2.putText(annotated_frame, "YOLO Detection Engine Initializing...", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        non_phone_users = max(0, total_students - phone_users)
        distraction_rate = round((phone_users / total_students * 100), 1) if total_students > 0 else 0.0

        # HUD Overlay on top
        cv2.rectangle(annotated_frame, (10, 10), (320, 110), (15, 23, 42), cv2.FILLED)
        cv2.rectangle(annotated_frame, (10, 10), (320, 110), (56, 189, 248), 1)
        
        cv2.putText(annotated_frame, f"Total Students: {total_students}", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(annotated_frame, f"Attentive: {non_phone_users}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (34, 197, 94), 2)
        cv2.putText(annotated_frame, f"Phone Users: {phone_users}", (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 80, 255), 2)
        cv2.putText(annotated_frame, f"Distraction: {distraction_rate}%", (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (56, 189, 248), 1)

        # Trigger Alerts if phone users detected
        alert_triggered = False
        if phone_users > 0:
            alert_triggered = True
            log_incident("Phone Usage", f"{phone_users} student(s) detected using mobile phones.", "danger")
            send_distraction_alert(total_students, phone_users)
            
        return annotated_frame, {
            "total_students": total_students,
            "attentive_students": non_phone_users,
            "phone_users": phone_users,
            "distraction_rate": distraction_rate,
            "alert_triggered": alert_triggered
        }

    def process_crowd_monitoring(self, frame):
        """
        Analyzes crowd density and calculates stampede risk level.
        """
        config = load_config()
        warn_thresh = config.get("CROWD_WARNING_THRESHOLD", 5)
        danger_thresh = config.get("CROWD_DANGER_THRESHOLD", 10)
        
        headcount = 0
        annotated_frame = frame.copy()
        
        if self.model is not None:
            results = self.model(frame, conf=0.3, verbose=False)
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                if self.model.names[cls_id] == "person":
                    headcount += 1
                    xyxy = box.xyxy[0].cpu().numpy().astype(int)
                    x1, y1, x2, y2 = xyxy
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 200, 0), 2)
                    cv2.circle(annotated_frame, ((x1+x2)//2, (y1+y2)//2), 5, (0, 0, 255), -1)
        
        # Risk Evaluation
        if headcount >= danger_thresh:
            status = "CRITICAL - STAMPEDE RISK"
            status_color = (0, 0, 255) # Red
            log_incident("Stampede Risk", f"Critical crowd density: {headcount} persons in sector.", "critical")
        elif headcount >= warn_thresh:
            status = "WARNING - CONGESTED"
            status_color = (0, 165, 255) # Orange
        else:
            status = "NORMAL - SAFE DENSITY"
            status_color = (0, 255, 0) # Green
            
        # Draw status banner
        h, w, _ = annotated_frame.shape
        cv2.rectangle(annotated_frame, (0, h - 50), (w, h), (15, 23, 42), cv2.FILLED)
        cv2.putText(annotated_frame, f"CROWD HEADCOUNT: {headcount}  |  STATUS: {status}", (20, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                    
        return annotated_frame, {
            "headcount": headcount,
            "status": status,
            "color": "danger" if headcount >= danger_thresh else ("warning" if headcount >= warn_thresh else "success")
        }

    def process_exam_proctoring(self, frame):
        """
        Evaluates exam proctoring rules:
        - Exactly 1 person allowed in candidate zone
        - No cell phone allowed
        """
        annotated_frame = frame.copy()
        person_count = 0
        phone_count = 0
        violations = []
        
        if self.model is not None:
            results = self.model(frame, conf=0.35, verbose=False)
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                
                if label == "person":
                    person_count += 1
                    cv2.rectangle(annotated_frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0, 255, 0), 2)
                elif label == "cell phone":
                    phone_count += 1
                    cv2.rectangle(annotated_frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0, 0, 255), 2)
                    cv2.putText(annotated_frame, "PROHIBITED ITEM", (xyxy[0], xyxy[1] - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        if person_count == 0:
            violations.append("Candidate Missing / Left Seat")
        elif person_count > 1:
            violations.append(f"Multiple Persons Detected ({person_count})")
            
        if phone_count > 0:
            violations.append(f"Unauthorized Phone Detected ({phone_count})")
            
        if violations:
            log_incident("Proctoring Violation", " | ".join(violations), "critical")
            
        # Draw status
        cv2.rectangle(annotated_frame, (10, 10), (360, 90), (15, 23, 42), cv2.FILLED)
        color = (0, 0, 255) if violations else (0, 255, 0)
        status_text = "VIOLATION DETECTED" if violations else "SESSION CLEAN"
        cv2.putText(annotated_frame, f"Proctoring: {status_text}", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.putText(annotated_frame, f"Candidate: {'Present' if person_count == 1 else 'Anomaly'}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        if violations:
            cv2.putText(annotated_frame, violations[0][:30], (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)

        return annotated_frame, {
            "person_count": person_count,
            "phone_count": phone_count,
            "violations": violations,
            "is_clean": len(violations) == 0
        }

# Global detector instance
yolo_detector = YOLODetector()
