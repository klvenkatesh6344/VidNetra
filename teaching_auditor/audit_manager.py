import os
import json
import time
import uuid
from datetime import datetime

from .audio_analytics import audio_analytics
from .vision_analytics import vision_analytics
from .pedagogy_engine import pedagogy_engine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_STORAGE_DIR = os.path.join(BASE_DIR, "teaching_audits")
REPORTS_FILE = os.path.join(AUDIT_STORAGE_DIR, "reports.json")

# In-memory progress tracking for real-time frontend updates
AUDIT_PROGRESS = {}

# Pre-configured academic benchmark test cases for instant proof-of-concept testing
SAMPLE_BENCHMARKS = [
    {
        "id": "sample_ml_svm",
        "faculty_name": "Dr. Ramesh Sharma",
        "subject": "Machine Learning & AI",
        "topic": "Support Vector Machines & Kernel Tricks",
        "duration_min": 45,
        "test_video_duration": "12 mins (Sampled POC)",
        "department": "Computer Science & Engineering",
        "date": "2026-08-20",
        "description": "Lecture covering hyperplane margin optimization, support vectors, RBF kernels, and dual formulation."
    },
    {
        "id": "sample_dsa_bst",
        "faculty_name": "Prof. Ananya Verma",
        "subject": "Data Structures & Algorithms",
        "topic": "Binary Search Trees & AVL Rotations",
        "duration_min": 50,
        "test_video_duration": "14 mins (Sampled POC)",
        "department": "Information Technology",
        "date": "2026-08-21",
        "description": "Classroom session on BST properties, insertion tracing, O(N) worst-case degradation, and AVL self-balancing."
    },
    {
        "id": "sample_os_deadlock",
        "faculty_name": "Dr. Md Mehedi Hasan",
        "subject": "Operating Systems & Systems Programming",
        "topic": "Deadlock Conditions & Banker's Algorithm",
        "duration_min": 45,
        "test_video_duration": "10 mins (Sampled POC)",
        "department": "Faculty of Engineering & Technology",
        "date": "2026-08-22",
        "description": "Analysis of 4 Coffman conditions, Resource Allocation Graphs, and Banker's safety state execution."
    }
]

class AuditManager:
    def __init__(self):
        os.makedirs(AUDIT_STORAGE_DIR, exist_ok=True)
        if not os.path.exists(REPORTS_FILE):
            self._save_reports([])

    def _get_reports(self):
        if os.path.exists(REPORTS_FILE):
            try:
                with open(REPORTS_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[AUDIT ERROR] Failed reading reports: {e}")
        return []

    def _save_reports(self, reports):
        try:
            with open(REPORTS_FILE, "w") as f:
                json.dump(reports, f, indent=4)
            return True
        except Exception as e:
            print(f"[AUDIT ERROR] Failed saving reports: {e}")
            return False

    def get_all_reports(self):
        """Returns list of past audit reports sorted by newest first"""
        reports = self._get_reports()
        return sorted(reports, key=lambda x: x.get("timestamp", ""), reverse=True)

    def get_report_by_id(self, audit_id):
        """Finds a single audit report by unique ID"""
        for r in self._get_reports():
            if r.get("audit_id") == audit_id:
                return r
        return None

    def delete_report(self, audit_id):
        """Removes a report from database"""
        reports = [r for r in self._get_reports() if r.get("audit_id") != audit_id]
        return self._save_reports(reports)

    def get_sample_benchmarks(self):
        """Returns pre-loaded benchmark case studies"""
        return SAMPLE_BENCHMARKS

    def execute_audit(self, video_path, faculty_name, subject, topic, department="Computer Science & Engineering", duration_sec=600):
        """
        Executes full multimodal audit pipeline across 5 stages:
        Stage 1: Video Ingestion & Keyframe Sampling
        Stage 2: Audio Extraction & Speech Transcription
        Stage 3: Language Detection & Pacing Analytics
        Stage 4: Vision & Teacher Traversal Analysis
        Stage 5: Pedagogical Concept Depth & Leftover Extraction
        """
        audit_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        AUDIT_PROGRESS[audit_id] = {
            "status": "in_progress",
            "stage": 1,
            "stage_text": "Extracting audio and sampling keyframes...",
            "progress_pct": 20
        }

        # Stage 1 & 2: Audio & Transcription
        time.sleep(0.3)
        AUDIT_PROGRESS[audit_id].update({
            "stage": 2,
            "stage_text": "Transcribing speech and measuring linguistic code-switching...",
            "progress_pct": 45
        })
        audio_res = audio_analytics.analyze_audio_stream(video_path, duration_sec)

        # Stage 3: Vision & Traversal
        time.sleep(0.3)
        AUDIT_PROGRESS[audit_id].update({
            "stage": 3,
            "stage_text": "Analyzing teacher positioning (Board vs Podium) and movement dynamics...",
            "progress_pct": 70
        })
        vision_res = vision_analytics.analyze_video_frames(video_path)

        # Stage 4 & 5: Pedagogy, Bloom's Taxonomy & Leftover Extraction
        time.sleep(0.3)
        AUDIT_PROGRESS[audit_id].update({
            "stage": 4,
            "stage_text": "Evaluating Bloom's Taxonomy depth and leftover topics...",
            "progress_pct": 90
        })
        pedagogy_res = pedagogy_engine.evaluate_pedagogy(
            topic, audio_res, vision_res, audio_res.get("transcript_sample", "")
        )

        # Compile Complete Audit Dossier
        final_report = {
            "audit_id": audit_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "faculty_name": faculty_name,
            "subject": subject,
            "topic": topic,
            "department": department,
            "video_source": os.path.basename(video_path) if video_path else "Benchmark CCTV Feed",
            "video_duration_minutes": audio_res["duration_minutes"],
            
            # Scores & Performance
            "overall_score": pedagogy_res["overall_score"],
            "performance_tier": pedagogy_res["performance_tier"],
            "tier_color": pedagogy_res["tier_color"],
            
            # Sub-Analytics Packages
            "audio_analytics": audio_res,
            "vision_analytics": vision_res,
            "concept_depth": pedagogy_res["concept_depth"],
            "leftover_analysis": pedagogy_res["leftover_analysis"],
            "interaction_metrics": pedagogy_res["interaction_metrics"],
            "actionable_suggestions": pedagogy_res["actionable_suggestions"]
        }

        # Save to JSON storage
        reports = self._get_reports()
        reports.insert(0, final_report)
        self._save_reports(reports)

        AUDIT_PROGRESS[audit_id] = {
            "status": "completed",
            "stage": 5,
            "stage_text": "Audit Report Generated Successfully!",
            "progress_pct": 100,
            "report_id": audit_id
        }

        return final_report

    def get_progress(self, audit_id):
        """Returns live progress for the audit modal poller"""
        return AUDIT_PROGRESS.get(audit_id, {"status": "not_found", "progress_pct": 0})

# Global instance
audit_manager = AuditManager()
