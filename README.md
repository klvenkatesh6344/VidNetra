# 👁️ VidNetra: Securing Every Learning Moment

> **A Computer Vision & AI Blended Solution for Smart Classrooms, Campus Safety & Lecture Intelligence**  
> *Faculty of Engineering & Technology, Parul University*

[![Python Version](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-000000.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.12-5C3EE8.svg?logo=opencv&logoColor=white)](https://opencv.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF.svg)](https://ultralytics.com/)
[![License](https://img.shields.io/badge/License-Academic_Use-brightgreen.svg)]()

---

## 🌟 About VidNetra

**VidNetra** ("Visual Third Eye") is an enterprise-grade AI and Computer Vision platform designed to safeguard the modern educational ecosystem. By transforming raw visual streams from classroom cameras and CCTV feeds into actionable intelligence, VidNetra empowers educators, parents, and institutional management with real-time analytics on attendance, academic engagement, campus safety, and faculty pedagogy.

---

## 👥 Project Team & Academic Mentorship

- **Academic Mentor**: **Md Mehedi Hasan** (Assistant Professor, Faculty of Engineering & Technology, Parul University)
- **Team Lead & Backend Developer**: **Kuchipudi Lakshmi Venkatesh**
- **Core Lead & Ideator**: **M Kalyan**
- **Frontend Developer**: **M Sunder**
- **Resource & Frontend Developer**: **S Sravan**

Institutional Emails: `2303031240571@paruluniversity.ac.in` | `2303031240599@paruluniversity.ac.in` | `2303031241174@paruluniversity.ac.in` | `2303031240608@paruluniversity.ac.in`

---

## 🚀 Key Modules & Capabilities

### 1. 👤 Facial Recognition Attendance System
- **Student Enrollment Studio (`/enroll`)**: Live webcam snapshot or photo upload to generate 128-dimensional biometric embeddings (`dlib` ResNet).
- **Live Recognition Camera (`/attendance_live`)**: Real-time Euclidean distance matching with confidence scoring, once-per-day check-in deduplication, and audio chimes.
- **Historical Records & CSV Export (`/attendance_records`)**: Date/student query filters with 1-click CSV download.

### 2. 📱 Classroom Distraction & Phone Usage Monitor
- **YOLOv8 Deep Learning**: Concurrent detection of students and mobile phones.
- **Spatial Containment Algorithm**: Flags active phone usage when phone coordinates intersect upper-body bounding boxes.
- **Automated Alerts**: Real-time visual warning badges, Web Audio API alarm buzzer, and asynchronous SMTP email dispatch to faculty.

### 3. 👥 Crowd Density & Stampede Prevention
- **Centroid Headcount**: Real-time tracking of student clusters in hallways and auditoriums.
- **Dynamic Risk Levels**:
  - 🟢 **Safe** (< 5 persons)
  - 🟡 **Warning** (5 – 10 persons)
  - 🔴 **Stampede Risk** (> 10 persons with critical sirens)

### 4. 🛡️ AI Exam Proctoring Suite
- **Single-Candidate Verification**: Ensures the enrolled candidate remains seated in the designated exam zone.
- **Anomaly Detection**: Flags secondary persons assisting candidates, prohibited electronics, and candidate absence.

### 5. 🎓 AI Teaching Auditor & Lecture Intelligence
- **5-Stage Multimodal Audit**: Ingests 5–15 min POC videos (or 45 min CCTV footage) using keyframe sampling for rapid local processing.
- **Linguistic Breakdown**: Analyzes speech tempo (Words Per Minute) and English vs. Vernacular / Regional language code-switching.
- **Bloom's Taxonomy Cognitive Depth**: Grades conceptual rigor across *Remember*, *Understand*, *Apply*, *Analyze*, and *Evaluate*.
- **Leftover Topics Detection**: Identifies curriculum concepts deferred or rushed due to lecture time shortages.
- **Movement Heatmap**: Tracks teacher time distribution (% Whiteboard, % Podium, % Roaming) and writing episodes.
- **Actionable Suggestions & Printable Dossier**: Generates constructive, rubric-scored recommendations for faculty development.

### 6. 🔍 Student & Parent Attendance Portal
- Roll number and name search providing attendance percentages, status timelines, and compliance with the 75% minimum academic threshold.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.12, Flask 3.1.2 (WSGI, Jinja2, REST APIs) |
| **Computer Vision** | OpenCV 4.12, DirectShow capture |
| **Deep Learning** | Ultralytics YOLOv8n (nano weights), `face_recognition` (dlib 128-d ResNet) |
| **Data Processing** | NumPy 2.2, Pandas 2.3 |
| **Frontend UI** | HTML5, CSS3 (Glassmorphism Dark Theme), Bootstrap 5, Bootstrap Icons, Chart.js, Web Audio API |
| **Notifications** | Threaded Python `smtplib` (Gmail SSL/TLS Port 587) |

---

## ⚡ Quick Start Guide

### 1. Prerequisites
- Python **3.12** installed.
- Git installed.

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/klvenkatesh6344/VidNetra.git
cd VidNetra

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy the configuration template:
```bash
# Windows
copy config.example.json config.json

# Linux / Mac
cp config.example.json config.json
```
*(Optional)* Configure your email credentials in `config.json` or via the web UI at `http://127.0.0.1:5000/settings`.

### 4. Launch VidNetra
#### Option A: 1-Click Launch (Windows)
Double-click [`run_vidnetra.bat`](file:///C:/Users/kuchi/.gemini/antigravity/scratch/vidnetra/run_vidnetra.bat).

#### Option B: Terminal Command
```bash
python run.py
```
*The launcher will automatically open your default web browser at `http://127.0.0.1:5000`.*

---

## 📂 Project Directory Structure

```
vidnetra/
├── run.py                          # Universal launcher with auto-environment selection
├── run_vidnetra.bat                # 1-Click Windows launch script
├── app.py                          # Flask application & 23 REST API routes
├── config.py                       # Configuration loader
├── config.example.json             # Safe configuration template (for GitHub)
├── camera.py                       # Threaded camera frame distributor & telemetry
├── face_engine.py                  # 128-d face recognition & enrollment engine
├── yolo_detector.py                # YOLOv8 distraction, crowd, and proctoring algorithms
├── notifier.py                     # Asynchronous SMTP alert dispatcher
├── data_manager.py                 # CSV & JSON data store manager
├── requirements.txt                # Python package dependencies
├── README.md                       # Main GitHub documentation
├── WORKFLOWS_AND_REQUIREMENTS.md   # Deep-dive architecture and workflows guide
├── attendance.csv                  # Attendance log storage
├── students.json                   # Enrolled student profiles
├── incidents.json                  # Security and distraction incidents log
├── face_data/                      # Biometric face embeddings (.npy)
├── teaching_auditor/               # Multimodal lecture auditing package
│   ├── audio_analytics.py          # Speech transcription, WPM & language distribution
│   ├── vision_analytics.py         # Zone tracking, movement & board activity
│   ├── pedagogy_engine.py          # Bloom's taxonomy & leftover topic analysis
│   └── audit_manager.py            # Audit pipeline runner & benchmark suites
├── static/                         # Glassmorphism CSS & Web Audio JS
└── templates/                      # Responsive HTML5 Jinja2 web views
```

---

## 📄 Documentation
For detailed system flowcharts, sequence diagrams, and API specifications, see **[WORKFLOWS_AND_REQUIREMENTS.md](WORKFLOWS_AND_REQUIREMENTS.md)**.
