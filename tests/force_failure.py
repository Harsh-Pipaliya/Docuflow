"""In-container synthetic failure fixture, isolated by a generated file ID."""

import os
from uuid import uuid4
from infra.cloud import db, history, now
from processor.app import process

fid, attempt = uuid4().hex, uuid4().hex
ref = db.collection("documents").document(fid)
key = f"uploads/{fid}/{uuid4().hex}.pdf"
ref.create(
    {
        "file_id": fid,
        "storage_key": key,
        "current_attempt_id": attempt,
        "generation": "1",
        "attempt_count": 1,
        "status": "Received",
        "original_filename": "controlled.pdf",
        "uploaded_at": now(),
        "size_bytes": 1,
    }
)
ref.collection("history").document().set(history("Received", attempt, "upload-event"))
os.environ["FORCE_FAILURE_FILE_ID"] = fid
process(key, "1", uuid4().hex)
d = ref.get().to_dict()
assert d["status"] == "Failed" and d["error_code"] == "CONTROLLED_FAILURE"
assert any(
    h.get("error_code") == "CONTROLLED_FAILURE"
    for h in ref.collection("history").stream()
)
print("Controlled worker failure reached Failed with matching history code.")
