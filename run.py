import os
import sys
import subprocess
import webbrowser
import threading
import time

# Auto-redirect to Python 3.12 if running under Python 3.14 without libraries
try:
    import flask
except ImportError:
    py312 = r"C:\Users\kuchi\AppData\Local\Programs\Python\Python312\python.exe"
    if os.path.exists(py312) and os.path.abspath(sys.executable) != os.path.abspath(py312):
        print(f"[VidNetra] Redirecting to Python 3.12 environment with all AI packages...")
        sys.exit(subprocess.call([py312] + sys.argv))

def open_browser():
    """Wait 1.5 seconds for Flask to initialize and automatically open browser"""
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    print("\n" + "="*65)
    print("           VIDNETRA - SECURING EVERY LEARNING MOMENT")
    print("      AI & Computer Vision Classroom Intelligence Platform")
    print("="*65)
    print(" Parul University - Faculty of Engineering & Technology")
    print(" Mentored by: Md Mehedi Hasan")
    print(" Lead by: Kuchipudi Lakshmi Venkatesh & Team")
    print("="*65)
    print("\n [INFO] Starting Flask Server on http://127.0.0.1:5000...")
    
    # Launch browser thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Import and run app
    from app import app
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
