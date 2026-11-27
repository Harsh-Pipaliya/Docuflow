"""Frozen offline harness for the local synthetic baseline."""
import json
from io import BytesIO
from pypdf import PdfWriter

def upload(name, data):
    if not name.lower().endswith(".pdf"):
        return {"status": "Rejected", "effects": 0}
    return {"status": "Received", "effects": 0, "bytes": len(data)}

def deliver(record, fail=False):
    record["status"] = "Validating"
    if fail:
        return
    record["effects"] += 1
    record["status"] = "Processed"

writer = PdfWriter()
writer.add_blank_page(72, 72)
stream = BytesIO()
writer.write(stream)
pdf = stream.getvalue()
for case, name, data in [("valid","sample.pdf",pdf),("unsupported","sample.txt",pdf),
                         ("oversized","large.pdf",bytes(10485761)),("replay","copy.pdf",pdf),
                         ("failure","failure.pdf",pdf)]:
    record = upload(name, data)
    if record["status"] == "Received":
        deliver(record, case == "failure")
        if case == "replay":
            deliver(record)
    print(json.dumps({"case":case, **record}))
