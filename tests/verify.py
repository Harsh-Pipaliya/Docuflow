"""Black-box local workflow and security verification. Run from the repository root."""

import io
import json
import os
import re
import subprocess
import time
from pathlib import Path

import requests
from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    TextStringObject,
)

base = "http://127.0.0.1:8080"
out = Path("evidence/after")
out.mkdir(parents=True, exist_ok=True)
s = requests.Session()


def api(method, path, sess=None, **kw):
    return (sess or s).request(method, base + path, timeout=30, **kw)


def upload(name, data, mime="application/pdf", sess=None):
    return api("POST", "/api/documents", sess=sess, files={"file": (name, data, mime)})


def snapshot(fid):
    path = "/api/documents/" + fid
    return [api("GET", path).json(), api("GET", path + "/history").json()]


def wait(fid):
    d = {}
    for _ in range(50):
        d, h = snapshot(fid)
        if d.get("status") in ("Processed", "Failed"):
            return d, h
        time.sleep(0.2)
    raise AssertionError("No terminal state: " + str(d.get("status")))


def pdf(pages=1, encrypted=False, js=False, embedded=False):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(72, 72)
    if js:
        writer._root_object.update(
            {
                NameObject("/OpenAction"): DictionaryObject(
                    {
                        NameObject("/S"): NameObject("/JavaScript"),
                        NameObject("/JS"): TextStringObject(
                            "/* synthetic inert marker */"
                        ),
                    }
                )
            }
        )
    if embedded:
        ef = DecodedStreamObject()
        ef.set_data(b"synthetic")
        ef.update({NameObject("/Type"): NameObject("/EmbeddedFile")})
        ref = writer._add_object(ef)
        writer._root_object.update(
            {
                NameObject("/Names"): DictionaryObject(
                    {
                        NameObject("/EmbeddedFiles"): DictionaryObject(
                            {
                                NameObject("/Names"): ArrayObject(
                                    [
                                        TextStringObject("a.txt"),
                                        DictionaryObject(
                                            {
                                                NameObject("/EF"): DictionaryObject(
                                                    {NameObject("/F"): ref}
                                                )
                                            }
                                        ),
                                    ]
                                )
                            }
                        )
                    }
                )
            }
        )
    if encrypted:
        writer.encrypt("synthetic")
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


def login_new_session(password):
    sess = requests.Session()
    tok = api("GET", "/api/auth/me", sess=sess).json()["csrf"]
    sess.headers.update({"X-CSRF-Token": tok})
    resp = api(
        "POST",
        "/api/auth/login",
        sess=sess,
        json={"username": "demo", "password": password},
    )
    resp.raise_for_status()
    sess.headers.update({"X-CSRF-Token": resp.json()["csrf"]})
    return sess


results = {}


def check(name, ok, detail):
    results[name] = {"status": "Passed" if ok else "Failed", "actual": detail}
    (out / "test-results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print(name, results[name])
    assert ok, name


check(
    "Unauthorized",
    api("GET", "/api/documents").status_code == 401,
    "Unauthenticated document list requires login",
)
token = api("GET", "/api/auth/me").json()["csrf"]
check(
    "CSRF",
    api("POST", "/api/auth/login", json={}).status_code == 403,
    "Missing token rejected",
)

password = (
    os.getenv("DOCUFLOW_DEMO_PASSWORD") or Path(".env.demo-login").read_text().strip()
)
s = login_new_session(password)

data = pdf()
r = upload("synthetic-check.pdf", data)
r.raise_for_status()
fid = r.json()["file_id"]
d, h = wait(fid)
(out / "event-trace.json").write_text(
    json.dumps(
        {"file_id": fid, "generation": d.get("generation"), "history": h}, indent=2
    ),
    encoding="utf-8",
)
check(
    "T01",
    d["status"] == "Processed"
    and [e["stage"] for e in h] == ["Received", "Validating", "Validated", "Processed"],
    [x["stage"] for x in h],
)
check(
    "T02",
    upload("sample.txt", b"test", "text/plain").status_code == 415,
    "Wrong MIME and extension returned 415",
)
check(
    "Empty file", upload("empty.pdf", b"").status_code == 400, "0-byte PDF returned 400"
)

before = len(api("GET", "/api/documents").json())
r = upload("large.pdf", bytes(10485761))
check(
    "T03",
    r.status_code == 413 and len(api("GET", "/api/documents").json()) == before,
    "413 and unchanged metadata count",
)

payload = {
    "name": d["storage_key"],
    "generation": d["generation"],
    "bucket": "docuflow-uploads",
}
cmd = (
    "import requests; from infra.cloud import db; "
    "a=db.collection('idempotency').document("
    + repr(d["current_attempt_id"])
    + ").get().to_dict(); "
    "r=requests.post('http://processor:8080/events',json="
    + repr(payload)
    + ",headers={'ce-type':'google.cloud.storage.object.v1.finalized','ce-id':a['event_id']}); r.raise_for_status()"
)
subprocess.run(
    ["docker", "compose", "exec", "-T", "api", "python", "-c", cmd], check=True
)
after = snapshot(fid)
(out / "replay.json").write_text(
    json.dumps({"before": [d, h], "after": after}, indent=2), encoding="utf-8"
)
check(
    "T04", [d, h] == after, "Identical document and history after same-event delivery"
)

bad = None
bad_history = None
for label, content in [
    ("corrupt", b"%PDF-1.4 invalid"),
    ("encrypted", pdf(encrypted=True)),
    ("zero", pdf(0)),
    ("signature", b"ordinary text"),
]:
    r = upload(label + ".pdf", content)
    r.raise_for_status()
    bad = r.json()["file_id"]
    bad_doc, bad_history = wait(bad)
    check(
        label,
        bad_doc["status"] == "Failed" and bool(bad_doc.get("error_code")),
        bad_doc.get("error_code"),
    )

check(
    "T06",
    api("GET", "/api/documents/" + fid).json()["status"] == "Processed",
    "Detail returned Processed",
)
dl = api("GET", "/api/documents/" + fid + "/download")
check(
    "Download",
    dl.content == data and dl.headers.get("X-Content-Type-Options") == "nosniff",
    "Byte-identical authenticated download with nosniff header",
)

r = api("POST", "/api/documents/" + bad + "/reprocess")
r.raise_for_status()
d2, h2 = wait(bad)
check(
    "Reprocess",
    d2["attempt_count"] == 2 and h2[: len(bad_history)] == bad_history,
    "New attempt preserves history",
)

r = upload("synthetic-copy.pdf", data)
r.raise_for_status()
copy, _ = wait(r.json()["file_id"])
check(
    "Duplicate content",
    copy["content_duplicate"] and copy["file_id"] != fid,
    "Equal digest with independent ID",
)
check(
    "Delete",
    api("DELETE", "/api/documents/" + bad).status_code == 204
    and api("GET", "/api/documents/" + bad).status_code == 404,
    "Deleted failed record",
)

# Fresh session to stay within per-session upload rate limit
s2 = login_new_session(password)
r = upload("js-embedded.pdf", pdf(pages=1, js=True, embedded=True), sess=s2)
r.raise_for_status()
js_doc, _ = wait(r.json()["file_id"])
check(
    "JS and embedded warnings",
    js_doc["status"] == "Processed"
    and "has_javascript" in js_doc.get("warnings", [])
    and "has_embedded_files" in js_doc.get("warnings", []),
    js_doc.get("warnings"),
)

r = upload("..\\..\\evil.pdf", data, sess=s2)
r.raise_for_status()
trav_doc, _ = wait(r.json()["file_id"])
check(
    "Path traversal",
    trav_doc["status"] == "Processed"
    and trav_doc["original_filename"] == "evil.pdf"
    and bool(
        re.fullmatch(r"uploads/[a-f0-9]{32}/[a-f0-9]{32}\.pdf", trav_doc["storage_key"])
    ),
    trav_doc["storage_key"],
)

r1 = upload("shared-name.pdf", pdf(pages=1), sess=s2)
r2 = upload("shared-name.pdf", pdf(pages=2), sess=s2)
r1.raise_for_status()
r2.raise_for_status()
fn1, _ = wait(r1.json()["file_id"])
fn2, _ = wait(r2.json()["file_id"])
check(
    "Duplicate filename",
    fn1["file_id"] != fn2["file_id"]
    and fn1["storage_key"] != fn2["storage_key"]
    and fn1["original_filename"] == fn2["original_filename"] == "shared-name.pdf",
    "Independent IDs and storage keys for matching filenames",
)

filtered = api(
    "GET", "/api/documents?status=Processed&q=shared-name&sort=name&limit=5", sess=s2
)
bad_filter = api("GET", "/api/documents?status=INVALID", sess=s2)
check(
    "Query filter validation",
    filtered.status_code == 200
    and len(filtered.json()) >= 2
    and bad_filter.status_code == 400,
    f"valid={len(filtered.json())}, invalid_status={bad_filter.status_code}",
)

# Upload rate limit test on its own session
s3 = login_new_session(password)
codes = [upload("rate.txt", b"x", "text/plain", sess=s3).status_code for _ in range(11)]
check("Upload rate limit", codes[:10] == [415] * 10 and codes[10] == 429, codes)

# Login rate limit test isolated to synthetic test IP so localhost remains usable for manual demo
rate_cmd = (
    "from backend.app import create_app, connection; "
    "app=create_app(); c=app.test_client(); "
    "tok=c.get('/api/auth/me').get_json()['csrf']; "
    "bad=[c.post('/api/auth/login', json={'username':'demo','password':'wrong'}, headers={'X-CSRF-Token':tok}, environ_base={'REMOTE_ADDR':'198.51.100.77'}).status_code for _ in range(6)]; "
    "blocked=c.post('/api/auth/login', json={'username':'demo','password':"
    + "__import__('sys').stdin.read()"
    + "}, headers={'X-CSRF-Token':tok}, environ_base={'REMOTE_ADDR':'198.51.100.77'}).status_code; "
    "conn=connection(); conn.execute(\"DELETE FROM hits WHERE scope='login:198.51.100.77'\"); conn.commit(); "
    "assert bad[:5]==[401]*5 and bad[5]==429 and blocked==429, (bad, blocked)"
)
subprocess.run(
    ["docker", "compose", "exec", "-T", "api", "python", "-c", rate_cmd], input=password, text=True, check=True
)
check(
    "Login rate limit",
    True,
    "5 failed attempts -> 401; 6th and subsequent valid attempt -> 429",
)
