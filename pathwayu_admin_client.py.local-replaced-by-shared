#!/usr/bin/env python3
"""Minimal, privacy-conscious PathwayU admin lookup for ENS 101 mentors.

The optional Playwright integration keeps a dedicated local browser profile so
the mentor can authenticate through Ensign SSO. Lookups return only completion
status for the four Career Explorer assessments; no report is downloaded and
the student's email is not written to disk by this module.
"""

import os
from pathlib import Path
from typing import Any

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    HAVE_PLAYWRIGHT = True
except ImportError:
    PlaywrightTimeoutError = TimeoutError
    sync_playwright = None
    HAVE_PLAYWRIGHT = False


PATHWAYU_BASE_URL = "https://ensign.pathwayu.com"
ASSESSMENTS = ("Interests", "Values", "Personality", "Workplace Preferences")
_configured_profile = os.environ.get("ENS101_PATHWAYU_PROFILE_DIR", "").strip()
PERSISTENT_PROFILE_DIR = Path(
    _configured_profile or Path(__file__).resolve().parent / ".pathwayu-profile"
).expanduser()


def _profile_dir() -> Path:
    PERSISTENT_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return PERSISTENT_PROFILE_DIR


def _looks_like_login(page) -> bool:
    current_url = page.url.lower()
    return (
        any(word in current_url for word in ("login", "signin", "auth", "sso"))
        or page.locator('input[type="password"]').count() > 0
        or page.locator('button:has-text("Log In"), button:has-text("Sign In")').count() > 0
    )


def classify_assessments(page_html: str) -> dict[str, Any]:
    """Classify the four assessment cards using the reference app's markers."""
    html_lower = page_html.lower()
    completed: list[str] = []
    missing: list[str] = []

    for assessment in ASSESSMENTS:
        heading = f">{assessment.lower()}</h2>"
        position = html_lower.find(heading)
        if position < 0:
            missing.append(assessment)
            continue

        card = html_lower[max(0, position - 300) : min(len(html_lower), position + 2500)]
        incomplete = any(
            marker in card for marker in ("has yet to take", "not started", "#e2e2e2")
        )
        complete = "#3b863f" in card or 'role="progressbar"' in card
        (completed if complete and not incomplete else missing).append(assessment)

    return {
        "completed": completed,
        "missing": missing,
        "completed_count": len(completed),
        "total": len(ASSESSMENTS),
    }


def check_admin_session() -> dict[str, Any]:
    if not HAVE_PLAYWRIGHT:
        return {
            "authenticated": False,
            "available": False,
            "status": "unavailable",
            "message": "Career Explorer lookup needs the optional Playwright setup.",
        }

    try:
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(_profile_dir()),
                headless=True,
                viewport={"width": 1280, "height": 900},
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(PATHWAYU_BASE_URL, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(1500)
                authenticated = not _looks_like_login(page)
                return {
                    "authenticated": authenticated,
                    "available": True,
                    "status": "authenticated" if authenticated else "auth_required",
                    "message": (
                        "PathwayU admin session is ready."
                        if authenticated
                        else "Authenticate with your Ensign staff account to enable lookup."
                    ),
                }
            finally:
                context.close()
    except Exception as error:
        message = str(error)
        if any(marker in message for marker in ("SingletonLock", "already in use", "ProcessSingleton")):
            return {
                "authenticated": False,
                "available": True,
                "in_progress": True,
                "status": "login_in_progress",
                "message": "The authentication window is open. Complete sign-in, then close it.",
            }
        return {
            "authenticated": False,
            "available": True,
            "status": "error",
            "message": "PathwayU session could not be verified.",
        }


def launch_interactive_login() -> None:
    if not HAVE_PLAYWRIGHT:
        raise RuntimeError("Playwright is not installed.")

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(_profile_dir()),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--no-sandbox"],
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(PATHWAYU_BASE_URL)
            # Keeping this process alive keeps the interactive sign-in window open.
            while context.pages:
                page.wait_for_timeout(1000)
        finally:
            context.close()


def lookup_student_completion(email: str) -> dict[str, Any]:
    """Return completion status without returning or persisting the email."""
    if not HAVE_PLAYWRIGHT:
        return {
            "success": False,
            "status": "unavailable",
            "message": "Career Explorer lookup needs the optional Playwright setup.",
        }

    session = check_admin_session()
    if not session.get("authenticated"):
        return {
            "success": False,
            "status": "auth_required" if session.get("available") else "unavailable",
            "message": session.get("message", "PathwayU authentication is required."),
        }

    normalized_email = email.strip().lower()
    try:
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(_profile_dir()),
                headless=True,
                viewport={"width": 1280, "height": 900},
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(PATHWAYU_BASE_URL, wait_until="networkidle", timeout=20000)
                if _looks_like_login(page):
                    return {
                        "success": False,
                        "status": "auth_required",
                        "message": "The PathwayU admin session expired. Authenticate again.",
                    }

                search_input = (
                    page.locator("#student-search-box")
                    .or_(page.locator('input[placeholder*="Search" i]'))
                    .or_(page.locator('input[type="search"]'))
                    .first
                )
                if search_input.count() == 0:
                    return {
                        "success": False,
                        "status": "error",
                        "message": "The PathwayU student search control was not found.",
                    }

                search_input.fill(normalized_email)
                search_input.press("Enter")
                page.wait_for_timeout(2500)

                username = normalized_email.split("@", 1)[0]
                result_links = page.locator('a[href*="/result/"]').all()
                target = None
                for link in result_links:
                    text = link.inner_text().lower()
                    if normalized_email in text or username in text:
                        target = link
                        break
                if target is None and len(result_links) == 1:
                    target = result_links[0]
                if target is None:
                    return {
                        "success": False,
                        "status": "not_found",
                        "message": "No matching student was found. Verify the @ensign.edu address.",
                    }

                target.click()
                page.wait_for_load_state("networkidle", timeout=15000)
                page.wait_for_timeout(1500)
                result = classify_assessments(page.content())
                all_complete = result["completed_count"] == result["total"]
                return {
                    "success": all_complete,
                    "status": "complete" if all_complete else "incomplete",
                    **result,
                    "message": (
                        "All four Career Explorer assessments are complete."
                        if all_complete
                        else f"{result['completed_count']} of {result['total']} assessments are complete."
                    ),
                }
            finally:
                context.close()
    except PlaywrightTimeoutError:
        return {
            "success": False,
            "status": "timeout",
            "message": "PathwayU took too long to respond. Please try again.",
        }
    except Exception:
        return {
            "success": False,
            "status": "error",
            "message": "The Career Explorer lookup could not be completed.",
        }
