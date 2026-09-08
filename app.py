#!/usr/bin/env python3
"""Zero-dependency backend for the ENS 101 Mentor Desk.

The app can use an optional OpenAI-compatible local endpoint, then an optional
Gemini key, and always retains a useful offline guidance layer. No AI endpoint
is contacted unless it is explicitly configured in the environment.
"""

import json
import os
import re
import sqlite3
import ssl
import time
import uuid
from collections import defaultdict
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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

# ==============================================================================
# 2. LOCAL FEEDBACK DATABASE (SQLITE)
# ==============================================================================

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
8. Page 1 of Appointment 1a includes: joining Ensign Connect and a major group; reviewing notification preferences, alumni, and informational interviews; explaining internship planning and early CAR 201 preparation; asking for the student's major, career direction, and 1-10 confidence; checking the PathwayU Career Explorer roadmap; selecting a Career Explorer or Create Resume follow-up; confirming Roadmap 2 through Step 5; and taking the appointment selfie.
9. Treat internship-course details and international-student work rules as items to verify against current Ensign policy. Never present immigration guidance as a definitive personal determination.
"""

MODE_CONTEXTS = {
    "begin": "Appointment 1a stage: Begin. Help the mentor open warmly and ask about the student's major and intended career.",
    "ensign-connect": "Appointment 1a stage: Ensign Connect. Guide the mentor through joining, major groups, preferences, alumni discovery, and informational interviews.",
    "internship": "Appointment 1a stage: Internship Plan. Explain general preparation, course pairing, timelines, and which details require current-policy verification.",
    "career-direction": "Appointment 1a stage: Career Direction. Use confidence and PathwayU progress to choose a Career Explorer or Create Resume follow-up.",
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

def fallback_reply(message: str, mode: str) -> str:
    """Useful, deterministic guidance when no AI engine is configured."""
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
        "temperature": 0.4,
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
            "temperature": 0.4,
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


def ask_coach(message: str, mode: str, history: list[dict[str, str]]) -> tuple[str, bool, str]:
    """
    Guidance coordinator:
    1. Try the configured OpenAI-compatible endpoint
    2. Fallback to Gemini (if a key is configured)
    3. Fallback to offline guidance
    Returns (reply_text, is_live_ai, engine_name).
    """
    # 1. Optional primary: OpenAI-compatible endpoint
    if LM_STUDIO_URL:
        try:
            reply = query_qwen(message, mode, history)
            if reply:
                return reply, True, "local"
        except Exception as e:
            print(f"[Primary AI Unavailable] {e}")

    # 2. Fallback: Google Gemini
    if GEMINI_API_KEY:
        try:
            print("[Inference] Switching to Google Gemini fallback...")
            reply = query_gemini(message, mode, history)
            if reply:
                return reply, True, "gemini"
        except Exception as e:
            print(f"[Fallback Gemini Error] {e}")

    # 3. Final Fallback: Offline guidance
    return fallback_reply(message, mode), False, "fallback"


# ==============================================================================
# 7. HTTP REQUEST HANDLER
# ==============================================================================

class CoachHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def _json(self, payload: dict, status: int = HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Health & status endpoints
        if self.path in ("/healthz", "/api/status"):
            self._json({
                "status": "ok",
                "service": "ENS 101 Mentor Desk",
                "ai_configured": bool(LM_STUDIO_URL or GEMINI_API_KEY),
                "primary_engine": "OpenAI-compatible endpoint" if LM_STUDIO_URL else "Not configured",
                "primary_model": QWEN_MODEL,
                "primary_configured": bool(LM_STUDIO_URL),
                "fallback_engine": "Google Gemini" if GEMINI_API_KEY else "Static Fallback",
                "fallback_configured": bool(GEMINI_API_KEY),
                "rate_limit_per_min": RATE_LIMIT,
            })
            return
        super().do_GET()

    def do_POST(self):
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
        reply, is_live, engine = ask_coach(message, mode, history)
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
