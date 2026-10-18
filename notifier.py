import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import load_config

# Global variable to track alert timestamps for cooldown
_last_alert_time = {}

def send_email_async(subject, html_content, receiver_email=None):
    """Sends an email in a background thread to prevent blocking the UI"""
    config = load_config()
    
    if not config.get("EMAIL_ENABLED", True):
        print("[NOTIFIER] Email notifications are disabled in settings.")
        return False

    receiver = receiver_email or config.get("FACULTY_ALERT_EMAIL")
    if not receiver:
        print("[NOTIFIER] No receiver email provided.")
        return False
        
    thread = threading.Thread(target=_send_email_worker, args=(subject, html_content, receiver, config))
    thread.daemon = True
    thread.start()
    return True

def _send_email_worker(subject, html_content, receiver, config):
    sender = config.get("SENDER_EMAIL")
    password = config.get("SENDER_PASSWORD")
    server_addr = config.get("SMTP_SERVER", "smtp.gmail.com")
    port = config.get("SMTP_PORT", 587)

    if not sender or not password or not receiver:
        print("[NOTIFIER ERROR] Incomplete SMTP credentials.")
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = f"VidNetra AI <{sender}>"
    msg["To"] = receiver
    msg["Subject"] = f"[VidNetra AI] {subject}"

    # Attach HTML body
    part = MIMEText(html_content, "html")
    msg.attach(part)

    try:
        server = smtplib.SMTP(server_addr, port, timeout=15)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        print(f"[NOTIFIER SUCCESS] Email '{subject}' delivered to {receiver}")
    except Exception as e:
        print(f"[NOTIFIER ERROR] Failed to send email: {e}")

def send_distraction_alert(student_count, phone_count, room_name="Classroom A-101"):
    """Trigger email notification to faculty when phone is detected (with cooldown)"""
    global _last_alert_time
    config = load_config()
    cooldown = config.get("PHONE_DETECTION_COOLDOWN", 180)
    current_time = time.time()
    
    last_sent = _last_alert_time.get("distraction", 0)
    if current_time - last_sent < cooldown:
        remaining = int(cooldown - (current_time - last_sent))
        print(f"[NOTIFIER] Phone detection alert on cooldown ({remaining}s remaining).")
        return False
    
    _last_alert_time["distraction"] = current_time
    
    subject = f"ALERT: Phone Usage Detected in {room_name}"
    html = f"""
    <div style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 24px; border-radius: 12px; max-width: 600px; margin: auto;">
        <div style="text-align: center; border-bottom: 2px solid #ef4444; padding-bottom: 15px;">
            <h1 style="color: #ef4444; margin: 0; font-size: 24px;">VIDNETRA ALERT SYSTEM</h1>
            <p style="color: #94a3b8; margin: 5px 0 0 0;">Securing Every Learning Moment</p>
        </div>
        <div style="padding: 20px 0;">
            <h2 style="color: #f1f5f9; font-size: 18px;">⚠️ Distraction Activity Detected</h2>
            <p style="color: #cbd5e1; line-height: 1.6;">
                Our AI Computer Vision system has detected <strong>unauthorized mobile phone usage</strong> during an active session in <strong>{room_name}</strong>.
            </p>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #1e293b; border-radius: 8px; overflow: hidden;">
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 12px 16px; color: #94a3b8;">Total Students Present:</td>
                    <td style="padding: 12px 16px; color: #f8fafc; font-weight: bold;">{student_count}</td>
                </tr>
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 12px 16px; color: #94a3b8;">Phone Users Detected:</td>
                    <td style="padding: 12px 16px; color: #ef4444; font-weight: bold;">{phone_count}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 16px; color: #94a3b8;">Timestamp:</td>
                    <td style="padding: 12px 16px; color: #38bdf8;">{time.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </table>
            <p style="color: #94a3b8; font-size: 13px;">
                Please review the classroom dashboard or interact with the students to ensure uninterrupted engagement.
            </p>
        </div>
        <div style="border-top: 1px solid #334155; padding-top: 15px; text-align: center; color: #64748b; font-size: 12px;">
            Team VidNetra &bull; Parul University &bull; Faculty of Engineering & Technology
        </div>
    </div>
    """
    return send_email_async(subject, html)

def send_enrollment_confirmation(student_name, student_email, roll_no, department):
    """Sends confirmation email to the student upon successful facial enrollment"""
    subject = f"Enrollment Confirmation - Welcome to VidNetra"
    html = f"""
    <div style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 24px; border-radius: 12px; max-width: 600px; margin: auto;">
        <div style="text-align: center; border-bottom: 2px solid #38bdf8; padding-bottom: 15px;">
            <h1 style="color: #38bdf8; margin: 0; font-size: 24px;">VIDNETRA PLATFORM</h1>
            <p style="color: #94a3b8; margin: 5px 0 0 0;">Securing Every Learning Moment</p>
        </div>
        <div style="padding: 20px 0;">
            <h2 style="color: #10b981; font-size: 18px;">🎉 Facial Profile Enrolled Successfully!</h2>
            <p style="color: #cbd5e1; line-height: 1.6;">
                Hello <strong>{student_name}</strong>,<br><br>
                This email confirms your facial registration on the <strong>VidNetra Smart Attendance & Learning Insights Platform</strong>. 
                Your facial embeddings have been safely encoded for contactless attendance tracking.
            </p>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #1e293b; border-radius: 8px; overflow: hidden;">
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 12px 16px; color: #94a3b8;">Student Name:</td>
                    <td style="padding: 12px 16px; color: #f8fafc; font-weight: bold;">{student_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 12px 16px; color: #94a3b8;">Roll / Enrollment No:</td>
                    <td style="padding: 12px 16px; color: #38bdf8; font-weight: bold;">{roll_no}</td>
                </tr>
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 12px 16px; color: #94a3b8;">Department:</td>
                    <td style="padding: 12px 16px; color: #f8fafc;">{department}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 16px; color: #94a3b8;">Registration Date:</td>
                    <td style="padding: 12px 16px; color: #10b981;">{time.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </table>
            <p style="color: #94a3b8; font-size: 13px;">
                You can now mark your attendance seamlessly as you enter the classroom. Enjoy our smart learning features!
            </p>
        </div>
        <div style="border-top: 1px solid #334155; padding-top: 15px; text-align: center; color: #64748b; font-size: 12px;">
            Team VidNetra &bull; Parul University &bull; Mentored by Md Mehedi Hasan
        </div>
    </div>
    """
    return send_email_async(subject, html, receiver_email=student_email)
