#!/usr/bin/env python3
"""Open the dedicated PathwayU browser profile for staff SSO authentication."""

from pathwayu_admin_client import launch_interactive_login


if __name__ == "__main__":
    launch_interactive_login()
