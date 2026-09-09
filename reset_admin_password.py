#!/usr/bin/env python3
"""Owner-only recovery utility for the ENS 101 Mentor Desk admin password.

The password is collected with hidden terminal input. It is never accepted as
a command-line argument and is never printed or logged.
"""

from __future__ import annotations

import os
from getpass import getpass
from pathlib import Path

from app import AdminCredential, default_data_dir


def main() -> int:
    password_path = Path(
        os.environ.get(
            "ENS101_ADMIN_PASSWORD_FILE",
            str(default_data_dir() / "admin-password"),
        )
    ).expanduser()
    credential = AdminCredential(password_path)
    first = getpass("New ENS 101 Mentor Desk admin password: ")
    second = getpass("Confirm new admin password: ")
    if first != second:
        print("Passwords did not match. Nothing changed.")
        return 1
    try:
        credential.replace_for_local_recovery(first)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Password was not changed: {exc}")
        return 1
    finally:
        first = ""
        second = ""
    print("ENS 101 Mentor Desk admin password changed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
