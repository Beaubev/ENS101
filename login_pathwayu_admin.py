#!/usr/bin/env python3
"""Open the dedicated PathwayU browser profile for staff SSO authentication.

Imports from the shared pathwayu_admin_client module so all apps
share a single browser profile and SSO session.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'AI AGENTS LOCAL LLM', 'shared'))
from pathwayu_admin_client import launch_interactive_login


if __name__ == "__main__":
    launch_interactive_login()
