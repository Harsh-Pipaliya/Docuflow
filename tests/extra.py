"""Additional authenticated checks using fresh sessions per rate-limit group."""

import os
import time
import json
from pathlib import Path
import requests

base = "http://127.0.0.1:8080"


def client():
    s = requests.Session()
    token = s.get(base + "/api/auth/me").json()["csrf"]
    s.headers["X-CSRF-Token"] = token
    return s


s = client()
password = (
    os.getenv("DOCUFLOW_DEMO_PASSWORD") or Path(".env.demo-login").read_text().strip()
)
r = s.post(base + "/api/auth/login", json={"username": "demo", "password": password})
r.raise_for_status()
s.headers["X-CSRF-Token"] = r.json()["csrf"]
root = Path("samples/generated")
reports = {}
for name, sample, warning in [
    ("../../sample.pdf", "valid.pdf", None),
    ("sample.pdf", "multipage.pdf", None),
    ("attachment.pdf", "attachment.pdf", "has_embedded_files"),
    ("marker.pdf", "marker.pdf", "has_javascript"),
]:
    r = s.post(
        base + "/api/documents",
        files={"file": (name, (root / sample).read_bytes(), "application/pdf")},
    )
    r.raise_for_status()
    fid = r.json()["file_id"]
    for _ in range(50):
        d = s.get(base + "/api/documents/" + fid).json()
        if d["status"] in ("Processed", "Failed"):
            break
        time.sleep(0.1)
    assert (
        d["status"] == "Processed"
        and d["original_filename"] == name.split("/")[-1]
        and name not in d["storage_key"]
    )
    if warning:
        assert warning in d["warnings"], d["warnings"]
    reports[name] = "Passed"
for _ in range(6):
    r = s.post(
        base + "/api/documents", files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert r.status_code == 400
assert (
    s.post(
        base + "/api/documents", files={"file": ("empty.pdf", b"", "application/pdf")}
    ).status_code
    == 429
)
reports["empty file and upload limit"] = "Passed"
Path("evidence/after/security.json").write_text(json.dumps(reports, indent=2))
print(reports)
