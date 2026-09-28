"""Imports app.py safely and serves CoachHandler on an ephemeral local port.

app.py initializes SQLite and the admin credential at import time, so the
paths are redirected to a temporary directory before the first import.
"""

import http.client
import json
import os
import tempfile
import threading
from http.server import ThreadingHTTPServer

_DATA_DIR = tempfile.mkdtemp(prefix="ens101-tests-")
os.environ["ENS101_DB_PATH"] = os.path.join(_DATA_DIR, "test.db")
os.environ["ENS101_ADMIN_PASSWORD_FILE"] = os.path.join(_DATA_DIR, "admin-password")

import app  # noqa: E402  (must follow the environment setup above)


class LocalServer:
    def __enter__(self):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), app.CoachHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.httpd.shutdown()
        self.httpd.server_close()
        return False

    def request(self, method, path, body=None, raw_body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.httpd.server_address[1], timeout=5)
        try:
            data = raw_body if raw_body is not None else (
                json.dumps(body).encode("utf-8") if body is not None else None
            )
            headers = {"Content-Type": "application/json"} if data is not None else {}
            connection.request(method, path, body=data, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            try:
                payload = json.loads(raw.decode("utf-8"))
            except ValueError:
                payload = None
            return response.status, payload, raw
        finally:
            connection.close()
