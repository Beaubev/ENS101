#!/usr/bin/env python3
"""Zero-dependency backend for the ENS 101 Mentor Desk.

The app can use an optional OpenAI-compatible local endpoint, then an optional
Gemini key, and always retains a useful offline guidance layer. No AI endpoint
is contacted unless it is explicitly configured in the environment.
"""

import base64
import ipaddress
import json
import os
import re
import secrets
import sqlite3
import ssl
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections import defaultdict
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

try:
    from ai_fallback_notifier import notify_qwen_fallback
except ImportError:
    def notify_qwen_fallback(*args, **kwargs):
        pass

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================

# Load .env file manually if present (no external packages needed)
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# Optional primary engine: any OpenAI-compatible local or hosted endpoint.
# It is deliberately disabled by default; configure it in .env when desired.
LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "").strip().rstrip("/")
QWEN_MODEL = os.environ.get("MODEL_NAME", "qwen3-vl-30b-a3b-instruct-mlx").strip()

# Fallback Engine: Google Gemini API (optional, used if Qwen is unreachable)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()

# Server Settings
PORT = int(os.environ.get("PORT", "5050"))
HOST = os.environ.get("HOST", "0.0.0.0")
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "50"))

STATIC_DIR = Path(__file__).resolve().parent / "static"
DB_PATH = Path(__file__).resolve().parent / "feedback.db"
ROOT_DIR = Path(__file__).resolve().parent

try:
    from pathwayu_admin_client import (
        HAVE_PLAYWRIGHT,
        check_admin_session,
        lookup_student_completion,
    )
except ImportError:
    HAVE_PLAYWRIGHT = False
    check_admin_session = None
    lookup_student_completion = None

ENSIGN_EMAIL_PATTERN = re.compile(r"^[^@\s]+@ensign\.edu$", re.IGNORECASE)
PATHWAYU_LOGIN_PROCESS = None

# ==============================================================================
# 2. LOCAL FEEDBACK & SUGGESTIONS DATABASE (SQLITE) & ADMIN CREDENTIALS
# ==============================================================================

def default_data_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / "ENS 101 Mentor Desk"


class AdminCredential:
    """Owner-readable local admin password with no secret in source control."""

    MIN_PASSWORD_CHARACTERS = 8
    MAX_PASSWORD_CHARACTERS = 128

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.RLock()
        self._ensure_exists()

    def _ensure_exists(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            self.path.parent.chmod(0o700)
        except OSError:
            pass
        if not self.path.exists():
            env_pwd = os.environ.get("ENS101_ADMIN_PASSWORD", "").strip()
            password = env_pwd if len(env_pwd) >= self.MIN_PASSWORD_CHARACTERS else secrets.token_urlsafe(24)
            descriptor = os.open(
                self.path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(password + "\n")
        try:
            self.path.chmod(0o600)
        except OSError:
            pass
        if len(self._read()) < self.MIN_PASSWORD_CHARACTERS:
            raise RuntimeError("The ENS 101 Mentor Desk admin credential is invalid.")

    def _read(self) -> str:
        file_stat = self.path.lstat()
        if not stat.S_ISREG(file_stat.st_mode):
            raise RuntimeError("The ENS 101 Mentor Desk admin credential is invalid.")
        return self.path.read_text(encoding="utf-8").rstrip("\n")

    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("New password must be text.")
        if value != value.strip():
            raise ValueError("New password cannot begin or end with whitespace.")
        if not (cls.MIN_PASSWORD_CHARACTERS <= len(value) <= cls.MAX_PASSWORD_CHARACTERS):
            raise ValueError(f"New password must be {cls.MIN_PASSWORD_CHARACTERS} to {cls.MAX_PASSWORD_CHARACTERS} characters.")
        if any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError("New password cannot contain control characters.")
        return value

    def _write_atomic(self, password: str) -> None:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".admin-password-",
            dir=self.path.parent,
            text=True,
        )
        temporary_path = Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(password + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
            self.path.chmod(0o600)
        finally:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass

    def verify(self, supplied: str) -> bool:
        if not isinstance(supplied, str) or len(supplied) > 256:
            return False
        with self._lock:
            return secrets.compare_digest(self._read(), supplied)

    def change(self, current_password: str, new_password: str) -> None:
        validated = self.validate_new_password(new_password)
        with self._lock:
            current = self._read()
            if not secrets.compare_digest(current, current_password):
                raise PermissionError("Current admin password was not accepted.")
            if secrets.compare_digest(current, validated):
                raise ValueError("New password must be different from current password.")
            self._write_atomic(validated)

    def replace_for_local_recovery(self, new_password: str) -> None:
        validated = self.validate_new_password(new_password)
        with self._lock:
            if secrets.compare_digest(self._read(), validated):
                raise ValueError("New password must be different from current password.")
            self._write_atomic(validated)


ADMIN_PASSWORD_PATH = Path(
    os.environ.get(
        "ENS101_ADMIN_PASSWORD_FILE",
        str(default_data_dir() / "admin-password"),
    )
).expanduser()

ADMIN_CREDENTIAL = AdminCredential(ADMIN_PASSWORD_PATH)


def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    response_id TEXT NOT NULL,
                    mode TEXT,
                    rating TEXT NOT NULL,
                    question TEXT,
                    answer TEXT,
                    comment TEXT,
                    client_ip TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    category TEXT NOT NULL,
                    suggestion TEXT NOT NULL,
                    submitter TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    admin_notes TEXT,
                    implemented_at TEXT,
                    client_ip TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id TEXT PRIMARY KEY,
                    student_email TEXT NOT NULL,
                    student_name TEXT,
                    program TEXT,
                    career TEXT,
                    confidence TEXT DEFAULT '5',
                    roadmap_status TEXT,
                    followup_track TEXT,
                    assessment_data TEXT,
                    prep_notes TEXT,
                    session_notes TEXT,
                    student_next TEXT,
                    mentor_follow TEXT,
                    checked_tasks TEXT,
                    current_task TEXT DEFAULT 'prepare',
                    current_step INTEGER DEFAULT 0,
                    civitas_recorded INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"[DB Init Error] {e}")

init_db()


def save_feedback(response_id: str, rating: str, comment: str = "", question: str = "", answer: str = "", mode: str = "", client_ip: str = ""):
    now = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO feedback (created_at, response_id, mode, rating, question, answer, comment, client_ip)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, response_id, mode, rating, question, answer, comment, client_ip))
        conn.commit()


def save_suggestion(category: str, suggestion: str, submitter: str = "", client_ip: str = "") -> int:
    now = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO suggestions (created_at, category, suggestion, submitter, status, client_ip)
            VALUES (?, ?, ?, ?, 'pending', ?)
        """, (now, category, suggestion, submitter, client_ip))
        conn.commit()
        return cursor.lastrowid


def get_suggestions():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, created_at, category, suggestion, submitter, status, admin_notes, implemented_at
            FROM suggestions
            ORDER BY 
                CASE status
                    WHEN 'pending' THEN 1
                    WHEN 'in_progress' THEN 2
                    WHEN 'implemented' THEN 3
                    ELSE 4
                END,
                id DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        stats = {
            "total": len(rows),
            "pending": sum(1 for r in rows if r["status"] == "pending"),
            "in_progress": sum(1 for r in rows if r["status"] == "in_progress"),
            "implemented": sum(1 for r in rows if r["status"] == "implemented"),
            "dismissed": sum(1 for r in rows if r["status"] == "dismissed"),
        }
        return rows, stats


def update_suggestion_status(suggestion_id: int, status: str, admin_notes: str | None = None) -> bool:
    now = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if status == "implemented":
            if admin_notes is not None:
                cursor.execute("""
                    UPDATE suggestions 
                    SET status = ?, admin_notes = ?, implemented_at = COALESCE(implemented_at, ?)
                    WHERE id = ?
                """, (status, admin_notes, now, suggestion_id))
            else:
                cursor.execute("""
                    UPDATE suggestions 
                    SET status = ?, implemented_at = COALESCE(implemented_at, ?)
                    WHERE id = ?
                """, (status, now, suggestion_id))
        else:
            if admin_notes is not None:
                cursor.execute("""
                    UPDATE suggestions 
                    SET status = ?, admin_notes = ?
                    WHERE id = ?
                """, (status, admin_notes, suggestion_id))
            else:
                cursor.execute("""
                    UPDATE suggestions 
                    SET status = ?
                    WHERE id = ?
                """, (status, suggestion_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_suggestion(suggestion_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM suggestions WHERE id = ?", (suggestion_id,))
        conn.commit()
        return cursor.rowcount > 0


# ==============================================================================
# 2B. APPOINTMENTS & PREPARATION PERSISTENCE (SQLITE)
# ==============================================================================

def get_all_appointments() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, student_email, student_name, program, career, confidence,
                   roadmap_status, followup_track, assessment_data, prep_notes,
                   current_task, current_step, civitas_recorded, created_at, updated_at
            FROM appointments
            ORDER BY updated_at DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        for r in rows:
            if r.get("assessment_data"):
                try:
                    r["assessment_data"] = json.loads(r["assessment_data"])
                except Exception:
                    pass
        return rows


def get_appointment_by_id(appointment_id: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments WHERE id = ? OR student_email = ?", (appointment_id, appointment_id.lower()))
        row = cursor.fetchone()
        if not row:
            return None
        data = dict(row)
        if data.get("assessment_data"):
            try:
                data["assessment_data"] = json.loads(data["assessment_data"])
            except Exception:
                pass
        if data.get("checked_tasks"):
            try:
                data["checked_tasks"] = json.loads(data["checked_tasks"])
            except Exception:
                data["checked_tasks"] = {}
        return data


def save_appointment(data: dict) -> dict:
    now = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    app_id = str(data.get("id") or "").strip()
    student_email = str(data.get("student_email") or "").strip().lower()
    if not app_id:
        email_prefix = re.sub(r'[^a-zA-Z0-9]', '-', (student_email or "student").split("@")[0])
        app_id = f"appt-{email_prefix}-{secrets.token_hex(4)}"

    student_name = str(data.get("student_name") or "").strip()
    program = str(data.get("program") or "").strip()
    career = str(data.get("career") or "").strip()
    confidence = str(data.get("confidence") or "5").strip()
    roadmap_status = str(data.get("roadmap_status") or "").strip()
    followup_track = str(data.get("followup_track") or "").strip()

    assessment_data = data.get("assessment_data")
    if isinstance(assessment_data, (dict, list)):
        assessment_data = json.dumps(assessment_data)
    elif not isinstance(assessment_data, str):
        assessment_data = ""

    prep_notes = str(data.get("prep_notes") or "")
    session_notes = str(data.get("session_notes") or "")
    student_next = str(data.get("student_next") or "")
    mentor_follow = str(data.get("mentor_follow") or "")

    checked_tasks = data.get("checked_tasks")
    if isinstance(checked_tasks, (dict, list)):
        checked_tasks = json.dumps(checked_tasks)
    elif not isinstance(checked_tasks, str):
        checked_tasks = "{}"

    current_task = str(data.get("current_task") or "prepare")
    current_step = int(data.get("current_step") or 0)
    civitas_recorded = 1 if data.get("civitas_recorded") else 0

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, created_at FROM appointments WHERE id = ?", (app_id,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE appointments SET
                    student_email = ?, student_name = ?, program = ?, career = ?,
                    confidence = ?, roadmap_status = ?, followup_track = ?,
                    assessment_data = ?, prep_notes = ?, session_notes = ?,
                    student_next = ?, mentor_follow = ?, checked_tasks = ?,
                    current_task = ?, current_step = ?, civitas_recorded = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                student_email, student_name, program, career,
                confidence, roadmap_status, followup_track,
                assessment_data, prep_notes, session_notes,
                student_next, mentor_follow, checked_tasks,
                current_task, current_step, civitas_recorded,
                now, app_id
            ))
        else:
            cursor.execute("""
                INSERT INTO appointments (
                    id, student_email, student_name, program, career,
                    confidence, roadmap_status, followup_track,
                    assessment_data, prep_notes, session_notes,
                    student_next, mentor_follow, checked_tasks,
                    current_task, current_step, civitas_recorded,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                app_id, student_email, student_name, program, career,
                confidence, roadmap_status, followup_track,
                assessment_data, prep_notes, session_notes,
                student_next, mentor_follow, checked_tasks,
                current_task, current_step, civitas_recorded,
                now, now
            ))
        conn.commit()

    return get_appointment_by_id(app_id)


def confirm_civitas_recorded(app_id: str) -> bool:
    now = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE appointments
            SET civitas_recorded = 1, updated_at = ?
            WHERE id = ?
        """, (now, app_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_appointment(app_id: str, force: bool = False) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if not force:
            cursor.execute("SELECT civitas_recorded FROM appointments WHERE id = ?", (app_id,))
            row = cursor.fetchone()
            if not row or not row[0]:
                return False
        cursor.execute("DELETE FROM appointments WHERE id = ?", (app_id,))
        conn.commit()
        return cursor.rowcount > 0


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts text from PDF bytes using PyMuPDF (fitz) if available, falling back to regex parsing."""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_pages = [page.get_text() for page in doc]
        doc.close()
        full_text = "\n".join(text_pages).strip()
        if full_text:
            return full_text
    except Exception:
        pass

    try:
        raw = pdf_bytes.decode("latin1", errors="ignore")
        strings = re.findall(r"\((.*?)\)Tj", raw)
        if strings:
            return " ".join(strings)
    except Exception:
        pass
    return ""


def parse_pathwayu_text(text: str) -> dict:
    """Extracts student name, Holland code, interests, values, and assessment status."""
    data = {
        "student_name": "",
        "holland_code": "",
        "primary_interests": [],
        "supporting_interests": [],
        "primary_values": [],
        "primary_workplace_preferences": [],
        "completed_count": 0,
        "total": 4,
        "status": "incomplete",
        "missing": []
    }
    if not text:
        return data

    name_match = re.search(r'^(?:[A-Z\s]+\n+)?([A-Z][a-z]+ [A-Z][a-z]+)\s*\n+PathwayU', text, re.MULTILINE)
    if not name_match:
        name_match = re.search(r'(?:pathway\s*u\s*\n+|ENSIGN COLLEGE\s*\n+)([A-Z][a-z]+ [A-Z][a-z]+)', text)
    if name_match:
        data["student_name"] = name_match.group(1).strip()

    pi_m = re.search(r'Your primary Interests are\s+([A-Za-z]+)\s+and\s+([A-Za-z]+)', text, re.IGNORECASE)
    primary_ints = [pi_m.group(1).capitalize(), pi_m.group(2).capitalize()] if pi_m else []
    data["primary_interests"] = primary_ints

    si_m = re.search(r'SUPPORTING INTERESTS\s*\n+([A-Za-z]+)', text, re.IGNORECASE)
    supp_ints = [si_m.group(1).capitalize()] if si_m else []
    data["supporting_interests"] = supp_ints

    all_ints = primary_ints + supp_ints
    if all_ints:
        code_letters = "".join([i[0] for i in all_ints])
        data["holland_code"] = f"{'-'.join(all_ints)} ({code_letters})"
    else:
        letters_match = re.search(r'\b([R|I|A|S|E|C]{2,3})\b', text)
        data["holland_code"] = letters_match.group(1) if letters_match else "Not detected"

    pv_m = re.search(r'Your primary Values are\s+([A-Za-z]+)\s+and\s+([A-Za-z]+)', text, re.IGNORECASE)
    if pv_m:
        data["primary_values"] = [pv_m.group(1).capitalize(), pv_m.group(2).capitalize()]

    wp_m = re.search(r'Your primary Workplace Preferences are\s+([A-Za-z\s]+?)\s+and\s+([A-Za-z\s]+?)\.', text, re.IGNORECASE)
    if wp_m:
        data["primary_workplace_preferences"] = [wp_m.group(1).strip().capitalize(), wp_m.group(2).strip().capitalize()]

    # Check for assessment presence in report text
    completed = []
    missing = []
    for section in ["Interests", "Values", "Personality", "Workplace Preferences"]:
        if section.lower() in text.lower():
            completed.append(section)
        else:
            missing.append(section)
    data["completed_count"] = len(completed)
    data["missing"] = missing
    data["status"] = "complete" if len(completed) == 4 else "incomplete"
    return data


def generate_career_guidance(student_name: str, program: str, career: str, assessment_data: dict | None = None) -> dict:
    """Generates tailored guidance from Career Explorer assessment results and student context."""
    assessment_data = assessment_data or {}
    holland_code = assessment_data.get("holland_code", "")
    completed_count = assessment_data.get("completed_count", 0)
    missing = assessment_data.get("missing", [])

    name_str = f" for {student_name}" if student_name else ""
    code_letters = re.findall(r'[RIASCE]', holland_code.upper())

    trait_explanations = {
        "S": "Social (helpers, communicators, teachers, mentors)",
        "E": "Enterprising (persuaders, leaders, entrepreneurs, project drivers)",
        "C": "Conventional (organizers, detail-oriented planners, data/systems analysts)",
        "I": "Investigative (thinkers, researchers, problem solvers, engineers)",
        "A": "Artistic (creators, visual/UI designers, expressive innovators)",
        "R": "Realistic (builders, hands-on technologists, practical problem-solvers)",
    }

    major_alignments = {
        "S": ["Medical Assisting", "Communication", "Integrated Studies (Healthcare/Education)"],
        "E": ["Business Management", "Digital Marketing", "Entrepreneurship", "Professional Sales"],
        "C": ["Accounting", "Project Management", "Administrative Support", "Finance"],
        "I": ["Information Technology", "Cybersecurity", "Software Engineering", "Data Analytics"],
        "A": ["Graphic Design", "Interior Design", "Digital Media", "Content Creation"],
        "R": ["Network Engineering", "Computer Support Specialist", "Applied Technology"],
    }

    career_alignments = {
        "S": ["Student Advisor", "Healthcare Coordinator", "Human Resources Specialist", "Community Outreach Manager"],
        "E": ["Marketing Coordinator", "Operations Supervisor", "Account Executive", "Business Development Representative"],
        "C": ["Financial Analyst", "Compliance Specialist", "Logistics Coordinator", "Database Administrator"],
        "I": ["Systems Analyst", "Information Security Analyst", "Full Stack Web Developer", "Quality Assurance Analyst"],
        "A": ["UI/UX Designer", "Brand Content Strategist", "Multimedia Artist", "Creative Director"],
        "R": ["Cloud Support Associate", "Field Systems Technician", "Network Administrator", "Hardware Specialist"],
    }

    aligned_majors = []
    aligned_careers = []
    traits_described = []

    for letter in (code_letters if code_letters else ["S", "E", "C"]):
        if letter in trait_explanations:
            traits_described.append(trait_explanations[letter])
        if letter in major_alignments:
            aligned_majors.extend(major_alignments[letter])
        if letter in career_alignments:
            aligned_careers.extend(career_alignments[letter])

    aligned_majors = list(dict.fromkeys(aligned_majors))[:4]
    aligned_careers = list(dict.fromkeys(aligned_careers))[:4]

    guidance_sections = []

    if completed_count == 4 or assessment_data.get("status") == "complete":
        status_summary = "All four Career Explorer assessments (Interests, Values, Personality, Workplace Preferences) are complete."
    elif completed_count > 0:
        missing_str = ", ".join(missing) if missing else "remaining sections"
        status_summary = f"{completed_count} of 4 assessments complete. Still needed: {missing_str}."
    else:
        status_summary = "Career Explorer assessments have not yet been completed. Encourage the student to complete all four sections before or during this session."

    guidance_sections.append({
        "title": "Assessment Completion Status",
        "content": status_summary
    })

    if traits_described:
        guidance_sections.append({
            "title": f"Holland Code Profile: {holland_code or 'Social-Enterprising-Conventional (SEC)'}",
            "content": "• " + "\n• ".join(traits_described)
        })

    if aligned_majors:
        guidance_sections.append({
            "title": "Aligned Ensign College Majors",
            "content": "• " + "\n• ".join(aligned_majors)
        })

    if aligned_careers:
        guidance_sections.append({
            "title": "Possible Career Pathways",
            "content": "• " + "\n• ".join(aligned_careers)
        })

    discussion_points = [
        "Ask how their top interests connect to what they enjoy doing when solving problems or working with others.",
        "Compare their stated career direction with their assessment results to identify natural strengths and confidence gaps.",
        "Highlight how certificate courses in their major can lead to an internship and early professional momentum."
    ]
    if program:
        discussion_points.append(f"Explore how their interest in {program} connects to specific industry projects and CAR 398/399/499 internships.")

    guidance_sections.append({
        "title": "Recommended Appointment Discussion Strategy",
        "content": "• " + "\n• ".join(discussion_points)
    })

    return {
        "status": "ok",
        "summary": f"Personalized Career Explorer Guidance{name_str}",
        "sections": guidance_sections,
        "holland_code": holland_code or "SEC",
        "aligned_majors": aligned_majors,
        "aligned_careers": aligned_careers
    }


# ==============================================================================
# 3. COACH SYSTEM PROMPT & PERSONA
# ==============================================================================
# Customize this prompt for your agent's specific focus and purpose!

SYSTEM_PROMPT = """You are Mentor Copilot, a concise support tool for Ensign College career mentors conducting ENS 101 Appointment 1a: Ensign Connect and Internship Plan.
Your user is the mentor, not the student. Help the mentor complete the appointment guide accurately, explain Ensign Connect and internship preparation, choose the appropriate career follow-up, summarize non-sensitive notes, and draft warm follow-up messages.

ENS 101 (College Success) helps students understand Ensign College's mission and Honor Code, become effective stewards of their education, learn Ensign's instructional approach, and identify academic, career, health, financial, and other college resources.

Guidelines:
1. Be warm, practical, and brief. Prefer 2-4 useful bullets or one short draft.
2. Strengthen the mentor's judgment; do not pretend to know private student records or replace college staff.
3. When suggesting a referral, explain why it fits and give one clear first action.
4. Ask at most one focused follow-up question.
5. Do not diagnose, investigate, or invite sensitive details. If safety, health, financial, legal, or crisis concerns appear, advise the mentor to follow Ensign College policy and contact the appropriate professional or supervisor.
6. Never request student IDs, passwords, financial account information, health details, immigration documents, or other protected information.
7. Preserve the mentor's authentic, encouraging voice in drafts.
8. Page 1 of Appointment 1a includes: joining Ensign Connect and a major group; reviewing notification preferences, alumni, and informational interviews; explaining internship planning and early CAR 201 preparation; asking for the student's major, career direction, and 1-10 confidence; checking the Career Explorer roadmap; selecting a Career Explorer or Create Resume follow-up; confirming Roadmap 2 through Step 5; and taking the appointment selfie.
9. Treat internship-course details and international-student work rules as items to verify against current Ensign policy. Never present immigration guidance as a definitive personal determination.
10. INTERNSHIP DIRECTIVE: If the mentor asks ANY question regarding internships, internship requirements, finding or applying for an internship, internship courses (CAR 201, CAR 398, CAR 399, CAR 499), PBWE, practical training, or CPT, DO NOT answer the question in the ENS 101 app. Instead, direct them to the Ensign Internship Expert app with the markdown link: [Ensign Internship Expert](/internship/).
"""

MODE_CONTEXTS = {
    "begin": "Appointment 1a stage: Begin. Help the mentor open warmly and ask about the student's major and intended career.",
    "ensign-connect": "Appointment 1a stage: Ensign Connect. Guide the mentor through joining, major groups, preferences, alumni discovery, and informational interviews.",
    "internship": "Appointment 1a stage: Internship Plan. Explain general preparation, course pairing, timelines, and which details require current-policy verification.",
    "career-direction": "Appointment 1a stage: Career Direction. Use confidence and Career Explorer progress to choose a Career Explorer or Create Resume follow-up.",
    "complete": "Appointment 1a stage: Complete. Confirm the student and mentor actions, then finish the page 1 checklist with the appointment selfie.",
}

# ==============================================================================
# 4. PRIVACY FILTER & GUARDRAILS
# ==============================================================================

PII_PATTERNS = [
    # Social Security Numbers (e.g., 000-00-0000 or 000 00 0000)
    (re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"), "Social Security numbers"),
    # Credit Card Numbers (13 to 19 digits with dashes or spaces)
    (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{1,4}\b"), "payment card numbers"),
    # Password disclosures
    (re.compile(r"\b(?:password|pwd|passcode|secret_key)\s*[:=]\s*\S+", re.IGNORECASE), "passwords"),
]

def check_privacy(text: str) -> str | None:
    """Returns a warning message if sensitive PII is detected, else None."""
    for pattern, label in PII_PATTERNS:
        if pattern.search(text):
            return f"For your privacy and safety, please remove {label} or private identifiers before submitting."
    return None

# ==============================================================================
# 5. SLIDING-WINDOW RATE LIMITER (DEFAULT: 50 REQ/MIN)
# ==============================================================================

class SlidingWindowRateLimiter:
    def __init__(self, limit_per_minute: int = 50):
        self.limit = limit_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]
        if len(self.requests[client_ip]) >= self.limit:
            return False
        self.requests[client_ip].append(now)
        return True

RATE_LIMITER = SlidingWindowRateLimiter(limit_per_minute=RATE_LIMIT)

# ==============================================================================
# 6. GUIDANCE ENGINES (OPTIONAL COMPATIBLE API -> GEMINI -> OFFLINE)
# ==============================================================================

def extract_user_query(message: str) -> str:
    marker = "\n\nNon-sensitive appointment context:"
    if marker in message:
        return message.split(marker, 1)[0].strip()
    return message.strip()

def is_internship_question(message: str) -> bool:
    """Checks if the user's query asks questions about internships or CPT."""
    query = extract_user_query(message)
    pattern = r"\b(internships?|interns?|cpt|car\s*-?(?:201|398|399|499)|pbwe|practical training)\b"
    return bool(re.search(pattern, query, re.IGNORECASE))

def get_internship_expert_url(headers=None) -> str:
    """Returns the URL for Internship Expert based on host/headers."""
    if headers:
        host = headers.get("Host", "").lower()
        referer = headers.get("Referer", "").lower()
        if "tail299fc7.ts.net" in host or "tail299fc7.ts.net" in referer or "/ens101" in referer or "/mentor-desk" in referer:
            return "/internship/"
        if "127.0.0.1" in host or "localhost" in host:
            host_name = host.split(":")[0]
            return f"http://{host_name}:5035/"
    return "/internship/"

def fallback_reply(message: str, mode: str, headers=None) -> str:
    """Useful, deterministic guidance when no AI engine is configured."""
    if is_internship_question(message):
        url = get_internship_expert_url(headers)
        return (
            "For all questions regarding internships, degree requirements, course pairing, timelines, and CPT authorization, "
            f"please consult the [Ensign Internship Expert]({url}) app. "
            "The ENS 101 Mentor Desk does not answer internship questions directly—official internship policies and source-grounded answers are maintained in the Internship Expert."
        )
    lower = message.lower()
    if "follow-up" in lower or "message" in lower or "email" in lower:
        return (
            "Here is a concise draft:\n\n"
            "Hi! Thank you for meeting with me today. I appreciated hearing about what you are working toward. "
            "Your next step is [student action], and I will [mentor follow-up]. I’m cheering you on—please reach out if you need help finding the resource we discussed."
        )
    if "summar" in lower or "next step" in lower:
        return (
            "Use this three-part summary:\n"
            "• Focus: the main goal or barrier discussed\n"
            "• Student action: one specific step and intended time frame\n"
            "• Mentor follow-up: the resource, introduction, or check-in you agreed to provide"
        )
    if "refer" in lower or "resource" in lower or "where" in lower:
        return (
            "Match the need to one clear starting point: Academic Advisors for course or graduation planning; "
            "Student Success Coaches for habits, time management, and college-life barriers; Career Mentors or "
            "Handshake for résumés, interviews, internships, and career direction. Explain why the resource fits, then help the student open it."
        )
    fallbacks = {
        "begin": "Begin with the prayer direction in the guide, then ask: “What is your major?” and “What type of career do you see yourself doing when you graduate?”",
        "ensign-connect": "Open Ensign Connect, complete Join Now, join the student's major group, review notification preferences, and show how to explore alumni for informational interviews.",
        "internship": "Explain that internship planning starts early: connect the experience to the major, review the appropriate internship course, discuss recruiting timelines, and verify international-student rules with the appropriate office.",
        "career-direction": "Ask for career confidence from 1–10 and check the Career Explorer roadmap. If the student is still exploring, plan a Career Explorer follow-up; if confident, consider a Create Resume appointment.",
        "complete": "Confirm the student action and mentor follow-up, then finish the page 1 checklist with the appointment selfie after obtaining consent.",
    }
    return fallbacks.get(mode, "Choose one open question, one useful resource, and one specific next step. What part would you like help drafting?")


def query_qwen(message: str, mode: str, history: list[dict[str, str]]) -> str | None:
    """Queries LM Studio Qwen via OpenAI-compatible /v1/chat/completions."""
    if not LM_STUDIO_URL:
        return None
    mode_context = MODE_CONTEXTS.get(mode, "")
    system_content = f"{SYSTEM_PROMPT}\n\n{mode_context}".strip()

    messages = [{"role": "system", "content": system_content}]
    for item in history[-8:]:
        role = item.get("role", "user")
        content = str(item.get("content", "")).strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    payload = {
        "model": QWEN_MODEL,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 1024,
    }

    url = f"{LM_STUDIO_URL}/chat/completions"
    req_data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    request = Request(url, data=req_data, headers=headers, method="POST")
    with urlopen(request, timeout=35, context=ssl.create_default_context()) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    choices = data.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "").strip() or None
    return None


def query_gemini(message: str, mode: str, history: list[dict[str, str]]) -> str | None:
    """Queries Google Gemini GenerateContent API as fallback."""
    if not GEMINI_API_KEY:
        return None

    mode_context = MODE_CONTEXTS.get(mode, "")
    system_instruction = f"{SYSTEM_PROMPT}\n\n{mode_context}".strip()

    contents = []
    for item in history[-8:]:
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role == "user" and content:
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant" and content:
            contents.append({"role": "model", "parts": [{"text": content}]})

    contents.append({"role": "user", "parts": [{"text": message}]})

    payload = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 2048,
        },
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    req_data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }

    request = Request(url, data=req_data, headers=headers, method="POST")
    with urlopen(request, timeout=30, context=ssl.create_default_context()) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        if parts:
            return parts[0].get("text", "").strip() or None
    return None


def ask_coach(message: str, mode: str, history: list[dict[str, str]], headers=None) -> tuple[str, bool, str]:
    """
    Guidance coordinator:
    1. Intercept internship questions and redirect to Internship Expert
    2. Try the configured OpenAI-compatible endpoint
    3. Fallback to Gemini (if a key is configured)
    4. Fallback to offline guidance
    Returns (reply_text, is_live_ai, engine_name).
    """
    # Guardrail: Do not answer internship questions in the ENS 101 app
    if is_internship_question(message):
        url = get_internship_expert_url(headers)
        reply = (
            "For all questions regarding internships, degree requirements, course pairing, timelines, and CPT authorization, "
            f"please consult the [Ensign Internship Expert]({url}) app. "
            "The ENS 101 Mentor Desk does not answer internship questions directly—official internship policies and source-grounded answers are maintained in the Internship Expert."
        )
        return reply, True, "internship_redirect"

    # 1. Optional primary: OpenAI-compatible endpoint
    qwen_error: str | None = None
    if LM_STUDIO_URL:
        try:
            reply = query_qwen(message, mode, history)
            if reply:
                return reply, True, "local"
            qwen_error = "Qwen Local returned an empty response"
        except Exception as e:
            qwen_error = f"Qwen Local error: {e}"
            print(f"[Primary AI Unavailable] {e}")
    else:
        qwen_error = "LM Studio endpoint is not configured"

    # 2. Fallback: Google Gemini
    if GEMINI_API_KEY:
        try:
            print("[Inference] Switching to Google Gemini fallback...")
            reply = query_gemini(message, mode, history)
            if reply:
                notify_qwen_fallback(
                    service_name="ENS 101 Mentor Desk",
                    fallback_engine="Google Gemini",
                    error_reason=qwen_error or "Qwen Local unavailable",
                    prompt_snippet=message,
                )
                return reply, True, "gemini"
        except Exception as e:
            print(f"[Fallback Gemini Error] {e}")

    # 3. Final Fallback: Offline guidance
    notify_qwen_fallback(
        service_name="ENS 101 Mentor Desk",
        fallback_engine="Offline Python Engine",
        error_reason=qwen_error or "Qwen Local and Gemini unavailable",
        prompt_snippet=message,
    )
    return fallback_reply(message, mode, headers), False, "fallback"


# ==============================================================================
# 7. HTTP REQUEST HANDLER
# ==============================================================================

def is_lm_studio_online() -> bool:
    if not LM_STUDIO_URL:
        return False
    try:
        req = Request(f"{LM_STUDIO_URL}/models", headers={"User-Agent": "ens-101"})
        with urlopen(req, timeout=0.8) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_active_engine() -> str:
    if is_lm_studio_online():
        return "Qwen Local"
    if GEMINI_API_KEY:
        return "Google Gemini"
    return "Offline Guidance"


class CoachHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def do_HEAD(self):
        clean_path = self.path.split("?")[0]
        if clean_path in ("/healthz", "/api/status"):
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        if clean_path in ("/admin", "/admin/"):
            self.path = "/admin.html"
        super().do_HEAD()

    def _json(self, payload: dict, status: int = HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _is_admin_authenticated(self) -> bool:
        auth_header = self.headers.get("X-ENS101-Admin", "").strip()
        if not auth_header:
            return False
        return ADMIN_CREDENTIAL.verify(auth_header)

    def _career_lookup_is_local(self) -> bool:
        try:
            return ipaddress.ip_address(self.client_address[0]).is_loopback
        except ValueError:
            return False

    def do_GET(self):
        clean_path = self.path.split("?")[0]
        if clean_path == "/api/career-explorer/admin-status":
            if not self._career_lookup_is_local():
                self._json({
                    "authenticated": False,
                    "available": False,
                    "status": "local_only",
                    "message": "Career Explorer lookup is available only on the mentor workstation.",
                }, HTTPStatus.FORBIDDEN)
                return
            if not check_admin_session:
                self._json({
                    "authenticated": False,
                    "available": False,
                    "status": "unavailable",
                    "message": "Career Explorer lookup is not installed.",
                }, HTTPStatus.SERVICE_UNAVAILABLE)
                return
            result = check_admin_session()
            self._json(result)
            return

        # Health & status endpoints
        if clean_path in ("/healthz", "/api/status"):
            active_eng = get_active_engine()
            self._json({
                "status": "ok",
                "service": "ENS 101 Mentor Desk",
                "active_engine": active_eng,
                "ai_configured": bool(LM_STUDIO_URL or GEMINI_API_KEY),
                "primary_engine": "LM Studio Qwen" if LM_STUDIO_URL else "Not configured",
                "primary_model": QWEN_MODEL,
                "primary_configured": bool(LM_STUDIO_URL),
                "fallback_engine": "Google Gemini" if GEMINI_API_KEY else "Static Fallback",
                "fallback_configured": bool(GEMINI_API_KEY),
                "career_explorer_lookup_available": HAVE_PLAYWRIGHT,
                "rate_limit_per_min": RATE_LIMIT,
            })
            return

        if clean_path in ("/admin", "/admin/"):
            self.path = "/admin.html"
            super().do_GET()
            return

        if clean_path == "/api/admin/suggestions":
            if not self._is_admin_authenticated():
                self._json({"error": "Unauthorized. Provide valid admin credentials in X-ENS101-Admin header."}, HTTPStatus.UNAUTHORIZED)
                return
            try:
                suggestions, stats = get_suggestions()
                self._json({"status": "ok", "stats": stats, "suggestions": suggestions})
            except Exception as e:
                print(f"[Admin Suggestions Error] {e}")
                self._json({"error": "Failed to retrieve suggestions."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if clean_path == "/api/appointments":
            try:
                appointments = get_all_appointments()
                self._json({"status": "ok", "appointments": appointments})
            except Exception as e:
                print(f"[Appointments GET error] {e}")
                self._json({"error": "Failed to fetch appointments."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if clean_path == "/api/appointments/get":
            query = parse_qs(urlparse(self.path).query)
            app_id = query.get("id", [""])[0].strip()
            if not app_id:
                self._json({"error": "Missing appointment id."}, HTTPStatus.BAD_REQUEST)
                return
            appointment = get_appointment_by_id(app_id)
            if not appointment:
                self._json({"error": "Appointment not found."}, HTTPStatus.NOT_FOUND)
                return
            self._json({"status": "ok", "appointment": appointment})
            return

        super().do_GET()

    def do_POST(self):
        # ----------------------------------------------------------------------
        # Career Explorer completion lookup (optional local Playwright helper)
        # ----------------------------------------------------------------------
        if self.path == "/api/career-explorer/launch-login":
            global PATHWAYU_LOGIN_PROCESS
            if not self._career_lookup_is_local():
                self._json({
                    "status": "local_only",
                    "message": "Career Explorer authentication is available only on the mentor workstation.",
                }, HTTPStatus.FORBIDDEN)
                return
            if not HAVE_PLAYWRIGHT:
                self._json({
                    "status": "unavailable",
                    "message": "Install the optional Career Explorer lookup before authenticating.",
                }, HTTPStatus.SERVICE_UNAVAILABLE)
                return

            if PATHWAYU_LOGIN_PROCESS and PATHWAYU_LOGIN_PROCESS.poll() is None:
                self._json({
                    "status": "login_in_progress",
                    "message": "The authentication window is already open.",
                })
                return

            try:
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                PATHWAYU_LOGIN_PROCESS = subprocess.Popen(
                    [sys.executable, str(ROOT_DIR / "login_pathwayu_admin.py")],
                    cwd=str(ROOT_DIR),
                    creationflags=creation_flags,
                )
                self._json({
                    "status": "login_started",
                    "message": "The Career Explorer authentication window is opening.",
                })
            except Exception as error:
                print(f"[PathwayU Login Error] {error}")
                self._json({
                    "status": "error",
                    "message": "The Career Explorer authentication window could not be opened.",
                }, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if self.path == "/api/career-explorer/lookup":
            if not self._career_lookup_is_local():
                self._json({
                    "status": "local_only",
                    "message": "Career Explorer lookup is available only on the mentor workstation.",
                }, HTTPStatus.FORBIDDEN)
                return
            client_ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
            if not RATE_LIMITER.is_allowed(client_ip):
                self._json({
                    "status": "rate_limited",
                    "message": "Please wait a moment before checking another student.",
                }, HTTPStatus.TOO_MANY_REQUESTS)
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length <= 0 or content_length > 8192:
                    raise ValueError("Invalid body size")
                data = json.loads(self.rfile.read(content_length).decode("utf-8"))
            except Exception:
                self._json({"status": "error", "message": "Invalid request."}, HTTPStatus.BAD_REQUEST)
                return

            email = str(data.get("email", "")).strip().lower()
            if not ENSIGN_EMAIL_PATTERN.fullmatch(email):
                self._json({
                    "status": "invalid_email",
                    "message": "Enter the student's @ensign.edu email address.",
                }, HTTPStatus.BAD_REQUEST)
                return

            if not lookup_student_completion:
                self._json({
                    "status": "unavailable",
                    "message": "Career Explorer lookup is not installed.",
                }, HTTPStatus.SERVICE_UNAVAILABLE)
                return

            result = lookup_student_completion(email)
            response_status = {
                "unavailable": HTTPStatus.SERVICE_UNAVAILABLE,
                "auth_required": HTTPStatus.UNAUTHORIZED,
                "timeout": HTTPStatus.GATEWAY_TIMEOUT,
                "error": HTTPStatus.BAD_GATEWAY,
            }.get(result.get("status"), HTTPStatus.OK)
            self._json(result, response_status)
            return

        # ----------------------------------------------------------------------
        # Appointments Endpoints (Multi-student persistence & Civitas lifecycle)
        # ----------------------------------------------------------------------
        if self.path == "/api/appointments/save":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            try:
                saved = save_appointment(data)
                self._json({"status": "ok", "appointment": saved})
            except Exception as e:
                print(f"[Save Appointment Error] {e}")
                self._json({"error": "Failed to save appointment."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if self.path == "/api/appointments/civitas-confirm":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            app_id = str(data.get("id", "")).strip()
            if not app_id:
                self._json({"error": "Missing appointment id."}, HTTPStatus.BAD_REQUEST)
                return

            success = confirm_civitas_recorded(app_id)
            if success:
                self._json({"status": "ok", "message": "Civitas recording confirmed."})
            else:
                self._json({"error": "Appointment not found."}, HTTPStatus.NOT_FOUND)
            return

        if self.path == "/api/appointments/delete":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            app_id = str(data.get("id", "")).strip()
            force = bool(data.get("force", False))
            if not app_id:
                self._json({"error": "Missing appointment id."}, HTTPStatus.BAD_REQUEST)
                return

            appt = get_appointment_by_id(app_id)
            if not appt:
                self._json({"error": "Appointment not found."}, HTTPStatus.NOT_FOUND)
                return

            if not force and not appt.get("civitas_recorded"):
                self._json({
                    "error": "Appointment cannot be deleted until recording in Civitas is confirmed.",
                    "civitas_recorded": False
                }, HTTPStatus.BAD_REQUEST)
                return

            deleted = delete_appointment(app_id, force=True)
            if deleted:
                self._json({"status": "ok", "message": "Appointment record deleted successfully."})
            else:
                self._json({"error": "Failed to delete appointment."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        # ----------------------------------------------------------------------
        # Career Explorer Guidance Endpoint
        # ----------------------------------------------------------------------
        if self.path == "/api/career-explorer/guidance":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            student_name = str(data.get("student_name", "")).strip()
            program = str(data.get("program", "")).strip()
            career = str(data.get("career", "")).strip()
            assessment_data = data.get("assessment_data") or {}

            guidance = generate_career_guidance(student_name, program, career, assessment_data)
            self._json(guidance)
            return

        # ----------------------------------------------------------------------
        # Career Explorer PDF Upload & Parse Endpoint
        # ----------------------------------------------------------------------
        if self.path == "/api/career-explorer/parse-pdf":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            pdf_base64 = data.get("pdf_base64", "")
            if not pdf_base64:
                self._json({"error": "Missing pdf_base64 data."}, HTTPStatus.BAD_REQUEST)
                return

            try:
                if "," in pdf_base64:
                    pdf_base64 = pdf_base64.split(",", 1)[1]
                pdf_bytes = base64.b64decode(pdf_base64)
                extracted_text = extract_text_from_pdf(pdf_bytes)
                parsed = parse_pathwayu_text(extracted_text)
                self._json({"status": "ok", "data": parsed, "extracted_length": len(extracted_text)})
            except Exception as e:
                print(f"[PDF Parse Error] {e}")
                self._json({"error": f"Failed to parse PDF report: {e}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        # Suggestion Submission Endpoint (Public, Rate-limited, Privacy-checked)
        # ----------------------------------------------------------------------
        if self.path == "/api/suggestions":
            client_ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
            if not RATE_LIMITER.is_allowed(client_ip):
                self._json(
                    {"error": f"Rate limit exceeded. Please wait a moment before submitting again."},
                    HTTPStatus.TOO_MANY_REQUESTS,
                )
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            category = str(data.get("category", "General")).strip()
            suggestion = str(data.get("suggestion", "")).strip()
            submitter = str(data.get("submitter", "")).strip()

            if not suggestion:
                self._json({"error": "Suggestion text is required."}, HTTPStatus.BAD_REQUEST)
                return

            warning = check_privacy(suggestion)
            if not warning and submitter:
                warning = check_privacy(submitter)
            if warning:
                self._json({"error": warning}, HTTPStatus.BAD_REQUEST)
                return

            try:
                new_id = save_suggestion(category, suggestion, submitter, client_ip)
                self._json({
                    "status": "ok",
                    "message": "Thank you! Your suggestion has been received for staff review.",
                    "id": new_id,
                })
            except Exception as e:
                print(f"[Suggestion Save Error] {e}")
                self._json({"error": "Failed to save suggestion."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        # ----------------------------------------------------------------------
        # Admin Authentication Verification Endpoint
        # ----------------------------------------------------------------------
        if self.path == "/api/admin/verify":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            password = str(data.get("password", ""))
            if ADMIN_CREDENTIAL.verify(password):
                self._json({"status": "ok", "message": "Admin authenticated successfully."})
            else:
                self._json({"error": "Incorrect admin password."}, HTTPStatus.UNAUTHORIZED)
            return

        # ----------------------------------------------------------------------
        # Admin Update Suggestion Status & Notes Endpoint
        # ----------------------------------------------------------------------
        if self.path == "/api/admin/suggestions/status":
            if not self._is_admin_authenticated():
                self._json({"error": "Unauthorized."}, HTTPStatus.UNAUTHORIZED)
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            suggestion_id = data.get("id")
            new_status = str(data.get("status", "")).strip().lower()
            admin_notes = data.get("admin_notes")
            if admin_notes is not None:
                admin_notes = str(admin_notes).strip()

            if not suggestion_id or new_status not in ("pending", "in_progress", "implemented", "dismissed"):
                self._json({"error": "Invalid id or status. Status must be pending, in_progress, implemented, or dismissed."}, HTTPStatus.BAD_REQUEST)
                return

            try:
                updated = update_suggestion_status(int(suggestion_id), new_status, admin_notes)
                if updated:
                    self._json({"status": "ok", "message": "Suggestion status updated successfully."})
                else:
                    self._json({"error": "Suggestion not found."}, HTTPStatus.NOT_FOUND)
            except Exception as e:
                print(f"[Suggestion Status Update Error] {e}")
                self._json({"error": "Failed to update suggestion status."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        # ----------------------------------------------------------------------
        # Admin Delete Suggestion Endpoint
        # ----------------------------------------------------------------------
        if self.path == "/api/admin/suggestions/delete":
            if not self._is_admin_authenticated():
                self._json({"error": "Unauthorized."}, HTTPStatus.UNAUTHORIZED)
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            suggestion_id = data.get("id")
            if not suggestion_id:
                self._json({"error": "Missing suggestion id."}, HTTPStatus.BAD_REQUEST)
                return

            try:
                deleted = delete_suggestion(int(suggestion_id))
                if deleted:
                    self._json({"status": "ok", "message": "Suggestion deleted."})
                else:
                    self._json({"error": "Suggestion not found."}, HTTPStatus.NOT_FOUND)
            except Exception as e:
                print(f"[Suggestion Delete Error] {e}")
                self._json({"error": "Failed to delete suggestion."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        # ----------------------------------------------------------------------
        # Admin Password Change Endpoint
        # ----------------------------------------------------------------------
        if self.path == "/api/admin/password":
            if not self._is_admin_authenticated():
                self._json({"error": "Unauthorized."}, HTTPStatus.UNAUTHORIZED)
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            current_password = str(data.get("current_password", ""))
            new_password = str(data.get("new_password", ""))

            try:
                ADMIN_CREDENTIAL.change(current_password, new_password)
                self._json({"status": "ok", "message": "Admin password changed successfully."})
            except (ValueError, PermissionError) as pe:
                self._json({"error": str(pe)}, HTTPStatus.BAD_REQUEST)
            except Exception as e:
                print(f"[Admin Password Change Error] {e}")
                self._json({"error": "Failed to change admin password."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        # ----------------------------------------------------------------------
        # Feedback Submission Endpoint
        # ----------------------------------------------------------------------
        if self.path == "/api/feedback":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            response_id = str(data.get("response_id", "")).strip()
            rating = str(data.get("rating", "")).strip().lower()
            comment = str(data.get("comment", "")).strip()
            question = str(data.get("question", "")).strip()
            answer = str(data.get("answer", "")).strip()
            mode = str(data.get("mode", "")).strip()

            if rating not in ("up", "down"):
                self._json({"error": "Rating must be 'up' or 'down'."}, HTTPStatus.BAD_REQUEST)
                return

            if comment:
                warning = check_privacy(comment)
                if warning:
                    self._json({"error": warning}, HTTPStatus.BAD_REQUEST)
                    return

            client_ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
            try:
                save_feedback(response_id, rating, comment, question, answer, mode, client_ip)
                self._json({"status": "ok", "message": "Feedback saved."})
            except Exception as e:
                print(f"[Feedback Save Error] {e}")
                self._json({"error": "Failed to save feedback."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        # ----------------------------------------------------------------------
        # Chat Generation Endpoint
        # ----------------------------------------------------------------------
        if self.path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        # 1. Rate Limiting Check
        client_ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        if not RATE_LIMITER.is_allowed(client_ip):
            self._json(
                {"error": f"Rate limit of {RATE_LIMIT} req/min exceeded. Please wait a moment before sending another message."},
                HTTPStatus.TOO_MANY_REQUESTS,
            )
            return

        # 2. Parse JSON body
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(raw_body)
        except Exception:
            self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
            return

        message = str(data.get("message", "")).strip()
        mode = str(data.get("mode", "step1")).strip()
        history = data.get("history", [])

        if not message:
            self._json({"error": "Message is required."}, HTTPStatus.BAD_REQUEST)
            return

        # 3. Privacy Guardrail Check
        privacy_warning = check_privacy(message)
        if privacy_warning:
            self._json({"error": privacy_warning}, HTTPStatus.BAD_REQUEST)
            return

        # 4. Generate Coach Response via Dual-Engine Coordinator
        reply, is_live, engine = ask_coach(message, mode, history, headers=self.headers)
        response_id = f"resp-{uuid.uuid4().hex[:12]}"
        self._json({
            "reply": reply,
            "live": is_live,
            "engine": engine,
            "response_id": response_id
        })


# ==============================================================================
# 8. SERVER ENTRYPOINT
# ==============================================================================

def main():
    server_address = (HOST, PORT)
    with ThreadingHTTPServer(server_address, CoachHandler) as httpd:
        print("================================================================")
        print(f"ENS 101 Mentor Desk running at http://localhost:{PORT}")
        print(f"   Primary Engine:   {'OpenAI-compatible (' + QWEN_MODEL + ')' if LM_STUDIO_URL else 'Not configured'}")
        print(f"   Fallback Engine:  {'Google Gemini (' + GEMINI_MODEL + ')' if GEMINI_API_KEY else 'Offline Fallback (Set GEMINI_API_KEY to enable Gemini)'}")
        print(f"   Rate Limit:       {RATE_LIMIT} req/min per IP")
        print(f"   Feedback Store:   SQLite ({DB_PATH.name})")
        print("================================================================")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    main()
