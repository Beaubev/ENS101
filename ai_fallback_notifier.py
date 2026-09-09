#!/usr/bin/env python3
"""AI Fallback Notifier Module.

Alerts Rob Bagley (robbagley@ensign.edu) via email and creates a Mem agent note
whenever the primary local inference engine (Qwen Local via LM Studio) fails,
times out, or becomes overwhelmed, and a secondary engine (Google Gemini or
the offline Python engine) takes over.

Features:
- Asynchronous background dispatch (zero latency impact on user chat).
- 15-minute cooldown throttling per service to prevent inbox flooding.
- Mail.app AppleScript email delivery to robbagley@ensign.edu.
- Mem note creation via local Odysseus mem_offload (with direct Mem API and save@mem.ai fallback).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

RECIPIENT_EMAIL = "robbagley@ensign.edu"
ALERT_COOLDOWN_SECONDS = 900  # 15 minutes per service
STATE_FILE = Path("/tmp/qwen_fallback_alert_state.json")
ODYSSEUS_MEM_OFFLOAD = Path(
    os.path.expanduser(
        "~/Library/CloudStorage/OneDrive-Personal/CCowork/Projects/ODYSSEUS/mem_offload.py"
    )
)
MEM_KEY_FILE = Path(os.path.expanduser("~/.config/ccowork/mem_api_key"))


def get_mountain_time_str() -> str:
    """Return human-readable Mountain Time timestamp."""
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("America/Denver"))
        return now.strftime("%Y-%m-%d %I:%M:%S %p %Z")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _read_alert_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_alert_state(state: Dict[str, Any]) -> None:
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[AI Alert State Error] Failed to write state: {e}", file=sys.stderr)


def should_send_alert(service_name: str, fallback_engine: str, error_reason: str) -> bool:
    """Determine whether alert should be sent based on cooldown."""
    state = _read_alert_state()
    now = time.time()
    service_state = state.get(service_name)

    if not service_state:
        return True

    last_alert_time = service_state.get("last_alert_time", 0)
    elapsed = now - last_alert_time
    if elapsed >= ALERT_COOLDOWN_SECONDS:
        return True

    # Also alert if the fallback engine escalated (e.g. from Gemini down to Python engine)
    last_engine = service_state.get("fallback_engine", "")
    if "python" in fallback_engine.lower() and "gemini" in last_engine.lower():
        return True

    return False


def _record_alert_sent(service_name: str, fallback_engine: str, error_reason: str) -> None:
    state = _read_alert_state()
    state[service_name] = {
        "last_alert_time": time.time(),
        "last_alert_readable": get_mountain_time_str(),
        "fallback_engine": fallback_engine,
        "error_reason": error_reason[:400],
    }
    _write_alert_state(state)


def send_email_alert(
    service_name: str,
    fallback_engine: str,
    error_reason: str,
    timestamp_str: str,
    prompt_snippet: str = "",
) -> bool:
    """Send alert email to robbagley@ensign.edu using macOS Mail.app via AppleScript."""
    subject = f"[ALERT] Qwen Local Down -> {fallback_engine} Takeover ({service_name})"

    snippet_block = ""
    if prompt_snippet:
        clean_snippet = prompt_snippet.strip().replace('"', "'")[:200]
        snippet_block = f"\nUser Prompt Excerpt: \"{clean_snippet}\"\n"

    body_text = f"""URGENT: Primary Local AI Engine (Qwen Local) is down or overwhelmed.

Timestamp: {timestamp_str}
Affected Service: {service_name}
Active Takeover Engine: {fallback_engine}
Error Encountered:
{error_reason}
{snippet_block}
System Details:
- Host Machine: Mac Studio
- Primary Target: http://127.0.0.1:1234/v1
- Model: qwen3-vl-30b-a3b-instruct-mlx

Actions Taken:
The service has automatically shifted inference to {fallback_engine} to ensure continuity for students and mentors.

Quick Diagnostic Commands:
1. Verify LM Studio process:
   lsof -i :1234
2. Query LM Studio models:
   curl -s http://127.0.0.1:1234/v1/models
3. Restart suite agents if needed:
   /Users/robbagley/CCowork-Local-Apps/"AI AGENTS LOCAL LLM"/start_all_agents.sh

(Duplicate alerts for {service_name} are throttled for 15 minutes.)
"""

    temp_dir = tempfile.gettempdir()
    body_file = os.path.join(temp_dir, f"qwen_alert_{os.getpid()}_{int(time.time())}.txt")
    script_file = os.path.join(temp_dir, f"qwen_alert_{os.getpid()}_{int(time.time())}.applescript")

    try:
        with open(body_file, "w", encoding="utf-8") as bf:
            bf.write(body_text)

        safe_subject = subject.replace('"', '\\"')
        safe_body_file = body_file.replace("'", "'\\''")

        applescript_content = f"""tell application "Mail"
  set bodyText to do shell script "cat '{safe_body_file}'"
  set msg to make new outgoing message with properties {{subject:"{safe_subject}", content:bodyText, visible:false}}
  tell msg
    make new to recipient with properties {{address:"{RECIPIENT_EMAIL}"}}
  end tell
  send msg
end tell
"""
        with open(script_file, "w", encoding="utf-8") as sf:
            sf.write(applescript_content)

        proc = subprocess.run(
            ["osascript", script_file],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            print(f"[AI Fallback Notifier] Email alert delivered to {RECIPIENT_EMAIL} for {service_name}")
            return True
        else:
            print(f"[AI Fallback Notifier] Mail.app AppleScript error: {proc.stderr.strip()}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"[AI Fallback Notifier] Email dispatch failed: {e}", file=sys.stderr)
        return False
    finally:
        for fpath in (body_file, script_file):
            try:
                if os.path.exists(fpath):
                    os.remove(fpath)
            except Exception:
                pass


def create_mem_agent_note(
    service_name: str,
    fallback_engine: str,
    error_reason: str,
    timestamp_str: str,
    prompt_snippet: str = "",
) -> bool:
    """Create a Mem agent note documenting the fallback incident."""
    title = f"# Incident: Qwen Local Fallback to {fallback_engine} on {service_name}"
    body = f"""{title}
Last updated: {timestamp_str[:10]}

**Incident Time**: {timestamp_str}
**Affected Service**: {service_name}
**Takeover Engine**: {fallback_engine}
**Host**: Mac Studio (LM Studio port 1234)

### Failure Diagnostics
```text
{error_reason.strip()}
```

### System Status
- Primary LLM: `qwen3-vl-30b-a3b-instruct-mlx`
- Endpoint: `http://127.0.0.1:1234/v1`
- Impact: Student/mentor traffic successfully rerouted to {fallback_engine}.

### Recovery Commands
```bash
# Check if LM Studio is running
lsof -i :1234
# Verify models endpoint
curl -s http://127.0.0.1:1234/v1/models
# Restart AI agents suite
/Users/robbagley/CCowork-Local-Apps/"AI AGENTS LOCAL LLM"/start_all_agents.sh
```
"""

    # 1. Try Odysseus Mem Offload CLI (token-light, fast HTTP/docker transport)
    if ODYSSEUS_MEM_OFFLOAD.exists():
        try:
            cmd = [
                sys.executable,
                str(ODYSSEUS_MEM_OFFLOAD),
                "create",
                "--title",
                f"Incident: Qwen Local Fallback to {fallback_engine} ({service_name})",
                "--body",
                body,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            if proc.returncode == 0:
                print(f"[AI Fallback Notifier] Mem note created via Odysseus offload for {service_name}")
                return True
            else:
                print(f"[AI Fallback Notifier] Odysseus mem_offload failed: {proc.stderr.strip()}", file=sys.stderr)
        except Exception as e:
            print(f"[AI Fallback Notifier] Odysseus mem offload error: {e}", file=sys.stderr)

    # 2. Try direct Mem REST API with MEM_KEY_FILE if configured
    if MEM_KEY_FILE.exists():
        try:
            api_key = MEM_KEY_FILE.read_text(encoding="utf-8").strip()
            if api_key:
                req_data = json.dumps({"content": body}).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.mem.ai/v2/notes",
                    data=req_data,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "AIFallbackNotifier/1.0",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in (200, 201):
                        print(f"[AI Fallback Notifier] Mem note created via Mem REST API for {service_name}")
                        return True
        except Exception as e:
            print(f"[AI Fallback Notifier] Mem REST API error: {e}", file=sys.stderr)

    # 3. Fallback: Email to save@mem.ai via Mail.app
    try:
        temp_dir = tempfile.gettempdir()
        mem_body_file = os.path.join(temp_dir, f"mem_note_{os.getpid()}_{int(time.time())}.txt")
        mem_script_file = os.path.join(temp_dir, f"mem_note_{os.getpid()}_{int(time.time())}.applescript")
        with open(mem_body_file, "w", encoding="utf-8") as mbf:
            mbf.write(body)

        safe_subj = f"Incident: Qwen Local Fallback to {fallback_engine} ({service_name})".replace('"', '\\"')
        safe_path = mem_body_file.replace("'", "'\\''")
        as_content = f"""tell application "Mail"
  set bodyText to do shell script "cat '{safe_path}'"
  set msg to make new outgoing message with properties {{subject:"{safe_subj}", content:bodyText, visible:false}}
  tell msg
    make new to recipient with properties {{address:"save@mem.ai"}}
  end tell
  send msg
end tell
"""
        with open(mem_script_file, "w", encoding="utf-8") as msf:
            msf.write(as_content)

        subprocess.run(["osascript", mem_script_file], capture_output=True, timeout=10)
        print(f"[AI Fallback Notifier] Mem note dispatched to save@mem.ai via Mail.app for {service_name}")
        return True
    except Exception as e:
        print(f"[AI Fallback Notifier] save@mem.ai dispatch failed: {e}", file=sys.stderr)
        return False


_DISPATCH_LOCK = threading.Lock()


def _dispatch_worker(
    service_name: str,
    fallback_engine: str,
    error_reason: str,
    timestamp_str: str,
    prompt_snippet: str = "",
) -> None:
    """Worker function executed in background thread."""
    send_email_alert(service_name, fallback_engine, error_reason, timestamp_str, prompt_snippet)
    create_mem_agent_note(service_name, fallback_engine, error_reason, timestamp_str, prompt_snippet)


def notify_qwen_fallback(
    service_name: str,
    fallback_engine: str,
    error_reason: str,
    prompt_snippet: str = "",
    force: bool = False,
) -> bool:
    """
    Main entrypoint called when Qwen Local fails and fallback takes over.
    Runs asynchronously in a daemon thread so it never adds latency to user requests.
    Throttled by 15-minute cooldown per service unless force=True.
    """
    with _DISPATCH_LOCK:
        if not force and not should_send_alert(service_name, fallback_engine, error_reason):
            print(
                f"[AI Fallback Notifier] Alert for {service_name} suppressed (within {ALERT_COOLDOWN_SECONDS}s cooldown)."
            )
            return False
        # Record immediately to prevent race conditions from concurrent requests
        _record_alert_sent(service_name, fallback_engine, error_reason)

    timestamp_str = get_mountain_time_str()
    thread = threading.Thread(
        target=_dispatch_worker,
        args=(service_name, fallback_engine, error_reason, timestamp_str, prompt_snippet),
        daemon=True,
    )
    thread.start()
    return True


if __name__ == "__main__":
    print(f"Testing AI Fallback Notifier for Rob Bagley ({RECIPIENT_EMAIL})...")
    test_service = "ENS 101 Mentor Desk (Test)"
    test_fallback = "Google Gemini"
    test_error = "Connection refused to http://127.0.0.1:1234/v1/chat/completions (LM Studio offline or overwhelmed)"
    
    # Run synchronously for CLI test
    ts = get_mountain_time_str()
    print(f"Timestamp: {ts}")
    email_res = send_email_alert(test_service, test_fallback, test_error, ts)
    print(f"Email Alert Result: {email_res}")
    mem_res = create_mem_agent_note(test_service, test_fallback, test_error, ts)
    print(f"Mem Note Result: {mem_res}")
    print("Test complete.")
