#!/usr/bin/env python3
"""Ensign Connect (PeopleGrove) admin lookup for ENS 101 mentors.

Mirrors the Career Explorer (PathwayU) admin client pattern: a persistent
local browser profile keeps the mentor's SSO session alive so headless
lookups can check whether a student has an Ensign Connect account.

Privacy: the student's email is used only for the search query and is not
written to disk by this module.
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


CONNECT_BASE_URL = "https://ces.peoplegrove.com"
CONNECT_ADMIN_URL = f"{CONNECT_BASE_URL}/hub/ces/site-admin-v2"
CONNECT_USERS_URL = f"{CONNECT_BASE_URL}/hub/ces/site-admin/users-and-analytics/explore-users-v2"

_configured_profile = os.environ.get("ENS101_CONNECT_PROFILE_DIR", "").strip()
PERSISTENT_PROFILE_DIR = Path(
    _configured_profile or Path(__file__).resolve().parent / ".ensign-connect-profile"
).expanduser()


def _profile_dir() -> Path:
    PERSISTENT_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return PERSISTENT_PROFILE_DIR


def _looks_like_login(page) -> bool:
    current_url = page.url.lower()
    return (
        any(word in current_url for word in ("login", "signin", "auth", "sso", "cas/"))
        or page.locator('input[type="password"]').count() > 0
        or page.locator('button:has-text("Log In"), button:has-text("Sign In")').count() > 0
    )


def check_connect_session() -> dict[str, Any]:
    """Check whether the PeopleGrove admin SSO session is active."""
    if not HAVE_PLAYWRIGHT:
        return {
            "authenticated": False,
            "available": False,
            "status": "unavailable",
            "message": "Ensign Connect lookup needs the optional Playwright setup.",
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
                page.goto(CONNECT_ADMIN_URL, wait_until="networkidle", timeout=15000)
                page.wait_for_timeout(1000)
                authenticated = not _looks_like_login(page)
                return {
                    "authenticated": authenticated,
                    "available": True,
                    "status": "authenticated" if authenticated else "auth_required",
                    "message": (
                        "Ensign Connect admin session is ready."
                        if authenticated
                        else "Authenticate with your Ensign staff account to enable Ensign Connect lookup."
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
                "message": "The Ensign Connect authentication window is open. Complete sign-in, then close it.",
            }
        return {
            "authenticated": False,
            "available": True,
            "status": "error",
            "message": "Ensign Connect session could not be verified.",
        }


def launch_connect_login() -> None:
    """Open a headed browser for the mentor to complete PeopleGrove SSO authentication."""
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
            page.goto(CONNECT_ADMIN_URL)
            # Keep the process alive while the sign-in window is open.
            while context.pages:
                page.wait_for_timeout(1000)
        finally:
            context.close()


def lookup_student_connect(email: str) -> dict[str, Any]:
    """Search the PeopleGrove admin Explore Users page for a student by email.

    Returns whether the student has an Ensign Connect account.
    Does not persist the student's email to disk.
    """
    if not HAVE_PLAYWRIGHT:
        return {
            "found": False,
            "status": "unavailable",
            "message": "Ensign Connect lookup needs the optional Playwright setup.",
        }

    session = check_connect_session()
    if not session.get("authenticated"):
        return {
            "found": False,
            "status": "auth_required" if session.get("available") else "unavailable",
            "message": session.get("message", "Ensign Connect authentication is required."),
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
                page.goto(CONNECT_USERS_URL, wait_until="networkidle", timeout=20000)
                page.wait_for_timeout(1500)

                if _looks_like_login(page):
                    return {
                        "found": False,
                        "status": "auth_required",
                        "message": "The Ensign Connect admin session expired. Authenticate again.",
                    }

                # Look for a search input on the Explore Users page
                search_input = (
                    page.locator('input[placeholder*="Search" i]')
                    .or_(page.locator('input[type="search"]'))
                    .or_(page.locator('input[placeholder*="email" i]'))
                    .or_(page.locator('input[placeholder*="user" i]'))
                    .first
                )

                if search_input.count() == 0:
                    # Try clicking a search/filter button first
                    filter_btn = page.locator('button:has-text("Search"), button:has-text("Filter")').first
                    if filter_btn.count() > 0:
                        filter_btn.click()
                        page.wait_for_timeout(1000)
                        search_input = page.locator('input[placeholder*="Search" i], input[type="search"]').first

                if search_input.count() == 0:
                    return {
                        "found": False,
                        "status": "error",
                        "message": "The Ensign Connect user search control was not found on the admin page.",
                    }

                search_input.fill(normalized_email)
                search_input.press("Enter")
                page.wait_for_timeout(3000)

                # Check for matching results
                page_content = page.content().lower()
                username = normalized_email.split("@", 1)[0]

                # Check if the email or username appears in the results
                found = normalized_email in page_content or username in page_content

                # Try to find a profile URL if available
                profile_url = None
                if found:
                    profile_links = page.locator('a[href*="/person/"]').all()
                    for link in profile_links:
                        text = link.inner_text().lower()
                        if username in text or normalized_email in text:
                            href = link.get_attribute("href")
                            if href:
                                profile_url = href if href.startswith("http") else f"{CONNECT_BASE_URL}{href}"
                            break

                # Also check for "no results" indicators
                no_results = any(
                    marker in page_content
                    for marker in ("no results", "no users found", "0 results", "no matching")
                )

                if no_results:
                    found = False

                return {
                    "found": found,
                    "status": "found" if found else "not_found",
                    "profile_url": profile_url,
                    "message": (
                        "Student has an Ensign Connect account."
                        if found
                        else "No Ensign Connect account found for this student."
                    ),
                }
            finally:
                context.close()
    except PlaywrightTimeoutError:
        return {
            "found": False,
            "status": "timeout",
            "message": "Ensign Connect took too long to respond. Please try again.",
        }
    except Exception:
        return {
            "found": False,
            "status": "error",
            "message": "The Ensign Connect lookup could not be completed.",
        }
