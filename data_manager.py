import os
import json
import pandas as pd
from datetime import datetime, timedelta
from config import load_config

def get_paths():
    config = load_config()
    return (
        config.get("ATTENDANCE_CSV", "attendance.csv"),
        config.get("STUDENTS_JSON", "students.json"),
        config.get("INCIDENTS_JSON", "incidents.json"),
        config.get("FACE_DATA_DIR", "face_data")
    )

# -------------------------------------------------------------
# Students Management
# -------------------------------------------------------------
def get_all_students():
    """Retrieve all registered student metadata"""
    _, students_file, _, _ = get_paths()
    if os.path.exists(students_file):
        try:
            with open(students_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading students.json: {e}")
    return []

def get_student_by_name(name):
    """Find a student profile by name"""
    students = get_all_students()
    for s in students:
        if s.get("name", "").strip().lower() == name.strip().lower():
            return s
    return None

def get_student_by_roll(roll_no):
    """Find a student profile by roll number"""
    students = get_all_students()
    for s in students:
        if s.get("roll_no", "").strip().lower() == roll_no.strip().lower():
            return s
    return None

def save_student(name, roll_no="", email="", department="Computer Science & Engineering"):
    """Add or update student in students.json"""
    _, students_file, _, _ = get_paths()
    students = get_all_students()
    
    # Check if student exists
    updated = False
    for s in students:
        if s.get("name", "").strip().lower() == name.strip().lower():
            if roll_no: s["roll_no"] = roll_no
            if email: s["email"] = email
            if department: s["department"] = department
            updated = True
            break
            
    if not updated:
        students.append({
            "name": name.strip(),
            "roll_no": roll_no.strip() or f"STU-{len(students)+101}",
            "email": email.strip(),
            "department": department.strip(),
            "enrolled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    try:
        with open(students_file, "w") as f:
            json.dump(students, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving students: {e}")
        return False

def delete_student_record(name):
    """Remove student from students.json and delete .npy file"""
    _, students_file, _, face_dir = get_paths()
    
    # Remove from JSON
    students = get_all_students()
    students = [s for s in students if s.get("name", "").strip().lower() != name.strip().lower()]
    try:
        with open(students_file, "w") as f:
            json.dump(students, f, indent=4)
    except Exception as e:
        print(f"Error updating students.json: {e}")

    # Remove face file
    face_file = os.path.join(face_dir, f"{name}.npy")
    if os.path.exists(face_file):
        try:
            os.remove(face_file)
        except Exception as e:
            print(f"Error deleting {face_file}: {e}")
    return True

# -------------------------------------------------------------
# Attendance Records Management
# -------------------------------------------------------------
def get_attendance_df():
    """Load attendance.csv as a cleaned pandas DataFrame"""
    csv_file, _, _, _ = get_paths()
    if not os.path.exists(csv_file):
        with open(csv_file, "w") as f:
            pass
        return pd.DataFrame(columns=["Name", "Date", "Time"])
        
    try:
        df = pd.read_csv(csv_file, names=["Name", "Date", "Time"], header=None, dtype=str)
        df.dropna(subset=["Name", "Date"], inplace=True)
        df["Name"] = df["Name"].str.strip()
        df["Date"] = df["Date"].str.strip()
        df["Time"] = df["Time"].str.strip()
        return df
    except Exception as e:
        print(f"Error loading attendance CSV: {e}")
        return pd.DataFrame(columns=["Name", "Date", "Time"])

def mark_attendance_record(name):
    """Mark attendance in attendance.csv if not already marked today"""
    csv_file, _, _, _ = get_paths()
    today = datetime.now().strftime('%Y-%m-%d')
    time_now = datetime.now().strftime('%H:%M:%S')
    
    df = get_attendance_df()
    if not df.empty:
        already_present = ((df['Name'].str.lower() == name.lower()) & (df['Date'] == today)).any()
        if already_present:
            return False, "Already marked today"
            
    try:
        with open(csv_file, "a") as f:
            f.write(f"{name},{today},{time_now}\n")
        return True, time_now
    except Exception as e:
        return False, str(e)

def get_today_attendance():
    """Get list of students present today"""
    today = datetime.now().strftime('%Y-%m-%d')
    df = get_attendance_df()
    if df.empty:
        return []
        
    today_df = df[df['Date'] == today].sort_values(by='Time', ascending=False)
    students = get_all_students()
    student_map = {s["name"].lower(): s for s in students}
    
    results = []
    for _, row in today_df.iterrows():
        name = row['Name']
        meta = student_map.get(name.lower(), {})
        results.append({
            "name": name,
            "roll_no": meta.get("roll_no", "N/A"),
            "department": meta.get("department", "N/A"),
            "email": meta.get("email", "N/A"),
            "date": row['Date'],
            "time": row['Time']
        })
    return results

def get_student_attendance_stats(student_name_or_roll):
    """Detailed attendance report for a specific student"""
    df = get_attendance_df()
    student = get_student_by_name(student_name_or_roll) or get_student_by_roll(student_name_or_roll)
    
    if not student:
        target_name = student_name_or_roll.lower()
    else:
        target_name = student["name"].lower()
        
    if df.empty:
        records = []
        total_days = 0
    else:
        matched_df = df[df['Name'].str.lower() == target_name].sort_values(by=['Date', 'Time'], ascending=[False, False])
        records = matched_df.to_dict('records')
        total_days = len(df['Date'].unique())
        
    present_days = len(set(r['Date'] for r in records))
    attendance_rate = int((present_days / total_days * 100)) if total_days > 0 else 100
    
    return {
        "student": student or {"name": student_name_or_roll, "roll_no": "N/A", "department": "General", "email": "N/A"},
        "present_count": present_days,
        "total_active_days": total_days,
        "rate": min(100, attendance_rate),
        "history": records
    }

# -------------------------------------------------------------
# Incidents & Distraction Logs
# -------------------------------------------------------------
def log_incident(incident_type, details, severity="warning"):
    """Log security, proctoring, or distraction incidents"""
    _, _, incidents_file, _ = get_paths()
    incidents = []
    if os.path.exists(incidents_file):
        try:
            with open(incidents_file, "r") as f:
                incidents = json.load(f)
        except Exception:
            incidents = []
            
    incident_entry = {
        "id": f"INC-{len(incidents)+1:04d}",
        "type": incident_type,
        "severity": severity,
        "details": details,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    incidents.insert(0, incident_entry) # newest first
    # Keep last 200 incidents
    incidents = incidents[:200]
    
    try:
        with open(incidents_file, "w") as f:
            json.dump(incidents, f, indent=4)
        return incident_entry
    except Exception as e:
        print(f"Error logging incident: {e}")
        return None

def get_recent_incidents(limit=10):
    """Retrieve recent incidents"""
    _, _, incidents_file, _ = get_paths()
    if os.path.exists(incidents_file):
        try:
            with open(incidents_file, "r") as f:
                data = json.load(f)
                return data[:limit]
        except Exception:
            pass
    return []

# -------------------------------------------------------------
# Analytics & Dashboard Insights
# -------------------------------------------------------------
def get_dashboard_summary():
    """Aggregates all system metrics for the executive dashboard"""
    students = get_all_students()
    enrolled_count = len(students)
    
    # Attendance count
    today_records = get_today_attendance()
    today_count = len(today_records)
    
    # Attendance rate
    rate = int((today_count / enrolled_count) * 100) if enrolled_count > 0 else 0
    
    # Historical days
    df = get_attendance_df()
    dates = []
    daily_counts = []
    if not df.empty:
        grouped = df.groupby('Date').size().reset_index(name='count')
        grouped = grouped.sort_values('Date').tail(7)
        dates = grouped['Date'].tolist()
        daily_counts = grouped['count'].tolist()
        
    # Department breakdown
    dept_counts = {}
    for s in students:
        dept = s.get("department", "Other")
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    # Incidents summary
    incidents = get_recent_incidents(15)
    phone_incident_count = len([i for i in incidents if i.get("type") == "Phone Usage"])
    
    # Calculate Engagement Score (Base 92% - deductions for phone infractions)
    engagement_score = max(55, min(98, 92 - (phone_incident_count * 2)))

    return {
        "enrolled_count": enrolled_count,
        "today_count": today_count,
        "attendance_rate": rate,
        "engagement_score": engagement_score,
        "active_incidents": len(incidents),
        "recent_incidents": incidents[:6],
        "today_records": today_records[:6],
        "chart_dates": dates,
        "chart_counts": daily_counts,
        "dept_labels": list(dept_counts.keys()),
        "dept_values": list(dept_counts.values())
    }
