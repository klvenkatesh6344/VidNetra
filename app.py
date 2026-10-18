from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify, send_file
import os
import cv2
import time
import json
import pandas as pd
from datetime import datetime

from config import load_config, save_config
from data_manager import (
    get_all_students, save_student, delete_student_record,
    get_attendance_df, get_today_attendance, get_student_attendance_stats,
    get_recent_incidents, get_dashboard_summary, mark_attendance_record
)
from face_engine import face_engine
from camera import camera_stream
from notifier import send_email_async

app = Flask(__name__)
config = load_config()
app.secret_key = config.get("SECRET_KEY", "vidnetra_secret_key_2026")

# -------------------------------------------------------------
# Video Streaming Generator
# -------------------------------------------------------------
def generate_frames(mode="raw"):
    """Yields JPEG frames for HTTP multipart streaming"""
    while True:
        frame_bytes = camera_stream.get_processed_frame(mode=mode)
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033) # ~30 FPS

@app.route('/video_feed/<mode>')
def video_feed(mode):
    """Video streaming route. Mode can be: attendance, phone_detection, crowd_monitoring, exam_proctoring, raw"""
    return Response(generate_frames(mode), mimetype='multipart/x-mixed-replace; boundary=frame')

# -------------------------------------------------------------
# Web Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    """Main Executive Dashboard"""
    stats = get_dashboard_summary()
    return render_template('index.html', stats=stats, current_page='dashboard')

@app.route('/enroll', methods=['GET', 'POST'])
def enroll():
    """Student Enrollment Studio"""
    if request.method == 'POST':
        name = request.form.get('student_name', '').strip()
        roll_no = request.form.get('roll_no', '').strip()
        email = request.form.get('student_email', '').strip()
        dept = request.form.get('department', 'Computer Science & Engineering').strip()
        
        if not name:
            flash('Please provide student name!', 'danger')
            return redirect(url_for('enroll'))
            
        # Check if photo was uploaded
        if 'student_photo' in request.files and request.files['student_photo'].filename != '':
            file = request.files['student_photo']
            import numpy as np
            file_bytes = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            success, msg = face_engine.enroll_from_image(img, name, roll_no, email, dept)
            if success:
                flash(msg, 'success')
            else:
                flash(msg, 'danger')
            return redirect(url_for('enroll'))
            
    students = get_all_students()
    return render_template('enroll.html', students=students, current_page='enroll')

@app.route('/api/enroll_camera', methods=['POST'])
def api_enroll_camera():
    """AJAX endpoint to enroll student from webcam snapshot"""
    data = request.get_json() or {}
    name = data.get('student_name', '').strip()
    roll_no = data.get('roll_no', '').strip()
    email = data.get('student_email', '').strip()
    dept = data.get('department', 'Computer Science & Engineering').strip()
    image_b64 = data.get('image_base64', '')
    
    if not name or not image_b64:
        return jsonify({"success": False, "message": "Missing student name or image data."}), 400
        
    success, msg = face_engine.enroll_from_base64(image_b64, name, roll_no, email, dept)
    return jsonify({"success": success, "message": msg})

@app.route('/attendance_live')
def attendance_live():
    """Real-time Facial Recognition Attendance Monitor"""
    today_records = get_today_attendance()
    students = get_all_students()
    return render_template('attendance_live.html', 
                           today_records=today_records, 
                           total_enrolled=len(students),
                           current_page='attendance_live')

@app.route('/attendance_records')
def attendance_records():
    """Searchable Historical Attendance Logs"""
    df = get_attendance_df()
    date_filter = request.args.get('date', '')
    search_query = request.args.get('q', '').strip().lower()
    
    if not df.empty:
        if date_filter:
            df = df[df['Date'] == date_filter]
        if search_query:
            df = df[df['Name'].str.lower().str.contains(search_query)]
        df = df.sort_values(by=['Date', 'Time'], ascending=[False, False])
        records = df.to_dict('records')
    else:
        records = []
        
    unique_dates = []
    if not df.empty:
        raw_df = get_attendance_df()
        unique_dates = sorted(raw_df['Date'].unique().tolist(), reverse=True)
        
    return render_template('attendance_records.html', 
                           records=records, 
                           unique_dates=unique_dates, 
                           selected_date=date_filter, 
                           search_query=search_query,
                           current_page='attendance_records')

@app.route('/export_attendance_csv')
def export_attendance_csv():
    """Download attendance CSV"""
    config = load_config()
    csv_path = config.get("ATTENDANCE_CSV", "attendance.csv")
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True, download_name="vidnetra_attendance_report.csv")
    flash("Attendance file not found.", "warning")
    return redirect(url_for('attendance_records'))

@app.route('/classroom_monitor')
def classroom_monitor():
    """Classroom Distraction & Phone Usage AI Monitor"""
    incidents = get_recent_incidents(15)
    return render_template('classroom_monitor.html', 
                           incidents=incidents,
                           current_page='classroom_monitor')

@app.route('/crowd_monitor')
def crowd_monitor():
    """Crowd Density & Stampede Prevention Monitor"""
    return render_template('crowd_monitor.html', current_page='crowd_monitor')

@app.route('/exam_proctoring')
def exam_proctoring():
    """AI Exam Proctoring Module"""
    incidents = [i for i in get_recent_incidents(20) if i.get("type") == "Proctoring Violation"]
    return render_template('exam_proctoring.html', incidents=incidents, current_page='exam_proctoring')

@app.route('/student_portal')
def student_portal():
    """Student & Parent Lookup Portal"""
    query = request.args.get('search', '').strip()
    result = None
    if query:
        result = get_student_attendance_stats(query)
    return render_template('student_portal.html', result=result, query=query, current_page='student_portal')

@app.route('/about')
def about():
    """About VidNetra, Team & Mentor Showcase"""
    return render_template('about.html', current_page='about')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """System & Alert Configuration"""
    current_config = load_config()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'save_config':
            current_config['SENDER_EMAIL'] = request.form.get('sender_email', '').strip()
            current_config['SENDER_PASSWORD'] = request.form.get('sender_password', '').strip()
            current_config['FACULTY_ALERT_EMAIL'] = request.form.get('faculty_email', '').strip()
            current_config['CAMERA_INDEX'] = int(request.form.get('camera_index', 0))
            current_config['FACE_TOLERANCE'] = float(request.form.get('face_tolerance', 0.5))
            current_config['YOLO_CONFIDENCE'] = float(request.form.get('yolo_confidence', 0.35))
            current_config['EMAIL_ENABLED'] = True if request.form.get('email_enabled') else False
            current_config['AUDIO_ALARM_ENABLED'] = True if request.form.get('audio_enabled') else False
            
            if save_config(current_config):
                flash("Settings updated successfully!", "success")
            else:
                flash("Failed to save settings.", "danger")
                
        elif action == 'test_email':
            recipient = request.form.get('test_recipient', '').strip() or current_config.get('FACULTY_ALERT_EMAIL')
            subject = "VidNetra SMTP Test Verification"
            html = f"""
            <div style="font-family: Arial, sans-serif; background-color: #0f172a; color: #fff; padding: 20px; border-radius: 8px;">
                <h2 style="color: #38bdf8;">VidNetra System Email Test</h2>
                <p>Congratulations! Your SMTP email notifications for VidNetra are configured properly.</p>
                <p style="color: #94a3b8; font-size: 12px;">Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            """
            if send_email_async(subject, html, receiver_email=recipient):
                flash(f"Test email dispatched to {recipient}!", "info")
            else:
                flash("Failed to dispatch test email. Check credentials.", "danger")
                
        return redirect(url_for('settings'))
        
    return render_template('settings.html', config=current_config, current_page='settings')

@app.route('/delete_student/<name>')
def delete_student(name):
    """Delete a student record"""
    delete_student_record(name)
    face_engine.reload_known_faces()
    flash(f"Student '{name}' has been deleted.", "success")
    return redirect(url_for('enroll'))

# -------------------------------------------------------------
# AI Teaching Auditor Routes
# -------------------------------------------------------------
from teaching_auditor import audit_manager

@app.route('/teaching_auditor')
def teaching_auditor():
    """Teaching Auditor Studio"""
    benchmarks = audit_manager.get_sample_benchmarks()
    reports = audit_manager.get_all_reports()
    return render_template('teaching_auditor.html', 
                           benchmarks=benchmarks, 
                           reports=reports, 
                           current_page='teaching_auditor')

@app.route('/api/run_audit', methods=['POST'])
def api_run_audit():
    """Executes Multimodal Video & Pedagogical Audit"""
    faculty_name = request.form.get('faculty_name', '').strip() or "Faculty Instructor"
    subject = request.form.get('subject', '').strip() or "Computer Science Core"
    topic = request.form.get('topic', '').strip() or "General Academic Lecture"
    department = request.form.get('department', 'Computer Science & Engineering').strip()
    benchmark_id = request.form.get('benchmark_id', '')

    video_path = ""
    
    # Check if a custom video file was uploaded
    if 'lecture_video' in request.files and request.files['lecture_video'].filename != '':
        video_file = request.files['lecture_video']
        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teaching_audits", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        video_path = os.path.join(upload_dir, f"{int(time.time())}_{video_file.filename}")
        video_file.save(video_path)
    elif benchmark_id:
        video_path = f"benchmark_{benchmark_id}.mp4"
    else:
        video_path = f"lecture_{topic.lower().replace(' ', '_')}.mp4"

    try:
        report = audit_manager.execute_audit(
            video_path=video_path,
            faculty_name=faculty_name,
            subject=subject,
            topic=topic,
            department=department,
            duration_sec=600
        )
        return jsonify({"success": True, "report_id": report["audit_id"]})
    except Exception as e:
        print(f"[AUDIT RUN ERROR] {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/audit_progress/<audit_id>')
def api_audit_progress(audit_id):
    """Returns real-time progress for live audit modal"""
    progress = audit_manager.get_progress(audit_id)
    return jsonify(progress)

@app.route('/teaching_report/<audit_id>')
def teaching_report(audit_id):
    """Interactive Teaching Audit Report View"""
    report = audit_manager.get_report_by_id(audit_id)
    if not report:
        flash("Teaching audit report not found.", "warning")
        return redirect(url_for('teaching_auditor'))
    return render_template('teaching_report.html', report=report, current_page='teaching_auditor')

@app.route('/delete_teaching_audit/<audit_id>')
def delete_teaching_audit(audit_id):
    """Delete an audit report"""
    audit_manager.delete_report(audit_id)
    flash("Teaching audit report removed.", "info")
    return redirect(url_for('teaching_auditor'))

# -------------------------------------------------------------
# REST APIs for Real-time Polling
# -------------------------------------------------------------
@app.route('/api/live_stats/<mode>')
def api_live_stats(mode):
    """Returns real-time metrics calculated by the camera thread"""
    stats = camera_stream.get_latest_metrics(mode)
    return jsonify(stats)

@app.route('/api/today_attendance')
def api_today_attendance():
    """Returns today's marked attendance list"""
    records = get_today_attendance()
    return jsonify(records)

@app.route('/api/mark_manual', methods=['POST'])
def api_mark_manual():
    """Manually mark attendance for a student"""
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"success": False, "message": "Student name required"}), 400
    success, msg = mark_attendance_record(name)
    return jsonify({"success": success, "message": msg})

# -------------------------------------------------------------
# Server Entrypoint
# -------------------------------------------------------------
if __name__ == '__main__':
    # Ensure necessary folders exist
    os.makedirs('face_data', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("\n" + "="*60)
    print("      VIDNETRA - SECURING EVERY LEARNING MOMENT")
    print("      AI & Computer Vision Classroom Intelligence Platform")
    print("="*60)
    print(" Server online at: http://127.0.0.1:5000")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
