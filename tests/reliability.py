"""Inject temporary I/O failures while keeping real SDK writes and transactions."""

from unittest.mock import patch
from uuid import uuid4
from io import BytesIO
from pypdf import PdfWriter
from processor.app import process, advance
from infra.cloud import db, now

writer = PdfWriter()
writer.add_blank_page(72, 72)
data = BytesIO()
writer.write(data)
fid, attempt = uuid4().hex, uuid4().hex
key = f"uploads/{fid}/{uuid4().hex}.pdf"
ref = db.collection("documents").document(fid)
ref.create(
    dict(
        file_id=fid,
        original_filename="retry.pdf",
        size_bytes=len(data.getvalue()),
        uploaded_at=now(),
        storage_key=key,
        current_attempt_id=attempt,
        attempt_count=1,
        status="Received",
    )
)
with patch("processor.app.bucket") as store:
    store.return_value.blob.return_value.download_as_bytes.side_effect = [
        TimeoutError(),
        TimeoutError(),
        data.getvalue(),
    ]
    process(key, "123", uuid4().hex)
    assert store.return_value.blob.return_value.download_as_bytes.call_count == 3
assert ref.get().get("status") == "Processed"
assert sum(h.get("outcome") == "retry" for h in ref.collection("history").stream()) == 2
assert not advance(
    db.transaction(), ref, attempt, "Received", "Failed", "upload-event", {}
)
assert ref.get().get("status") == "Processed"
for h in ref.collection("history").stream():
    h.reference.delete()
ref.delete()
db.collection("idempotency").document(attempt).delete()
print(
    "Two injected timeouts preceded success. A late transition could not overwrite the terminal state."
)
