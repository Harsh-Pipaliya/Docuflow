import hashlib
import io
import os
import re
import time
from uuid import UUID

from flask import Flask, Blueprint, request
from google.cloud import firestore
from pypdf import PdfReader
from infra.cloud import BUCKET, bucket, db, history, log, now

routes = Blueprint("processor", __name__)

class InvalidPDF(Exception):
    pass

def inspect_pdf(data):
    if not data.startswith(b"%PDF-"):
        raise InvalidPDF("INVALID_SIGNATURE")
    try:
        pdf = PdfReader(io.BytesIO(data), strict=True)
        if pdf.is_encrypted:
            raise InvalidPDF("ENCRYPTED")
        pages = len(pdf.pages)
        if not 1 <= pages <= 5000:
            raise InvalidPDF("PAGE_COUNT")
        if sum(len(group) for group in pdf.xref.values()) > 50000:
            raise InvalidPDF("OBJECT_LIMIT")
        warnings = set()
        from pypdf.generic import IndirectObject
        for generation, objects in pdf.xref.items():
            for number in objects:
                if not number or generation == 65535:
                    continue
                obj = pdf.get_object(IndirectObject(number,generation,pdf))
                if isinstance(obj,dict):
                    if obj.get("/S") == "/JavaScript" or "/JavaScript" in obj:
                        warnings.add("has_javascript")
                    if obj.get("/Type") == "/EmbeddedFile" or "/EmbeddedFiles" in obj:
                        warnings.add("has_embedded_files")
        return {"page_count":pages,"pdf_version":pdf.pdf_header[5:],"sha256":hashlib.sha256(data).hexdigest(),
                "warnings":sorted(warnings)}
    except InvalidPDF:
        raise
    except Exception:
        raise InvalidPDF("INVALID_STRUCTURE") from None

@firestore.transactional
def advance(tx, ref, attempt, prior, stage, trigger, values):
    doc = ref.get(transaction=tx).to_dict()
    if not doc or doc["current_attempt_id"] != attempt or doc["status"] != prior:
        return False
    tx.update(ref,{"status":stage,"updated_at":now(),**values})
    tx.set(ref.collection("history").document(),history(stage,attempt,trigger,values.get("error_code")))
    return True

def process(key, generation, event_id, manual=False):
    fid = key.split("/")[1]
    ref = db.collection("documents").document(fid)
    doc = ref.get().to_dict()
    if not doc or doc["storage_key"] != key or (doc.get("generation") and str(doc["generation"]) != generation):
        return
    attempt = doc["current_attempt_id"]
    if manual != (doc["attempt_count"] > 1):
        return
    trigger = "manual-reprocess" if manual else "upload-event"
    if not advance(db.transaction(),ref,attempt,"Received","Validating",trigger,{"generation":generation}):
        log("event",fid,"duplicate_ignored")
        return
    claim = db.collection("idempotency").document(attempt)
    claim.set({"file_id":fid,"event_id":event_id,"generation":generation,"first_seen_at":now(),"outcome":"Validating"})
    start = time.monotonic()
    prior = "Validating"
    for retry in range(3):
        try:
            if os.getenv("FORCE_FAILURE_FILE_ID")==fid:
                raise InvalidPDF("CONTROLLED_FAILURE")
            data = bucket().blob(key,generation=int(generation)).download_as_bytes(timeout=10,retry=None)
            values = inspect_pdf(data)
            if prior == "Validating":
                if not advance(db.transaction(),ref,attempt,prior,"Validated",trigger,{}):
                    return
                prior = "Validated"
            matches = db.collection("documents").where("sha256","==",values["sha256"]).limit(1).get()
            values.update(content_duplicate=bool(matches),content_duplicate_of=matches[0].id if matches else None,
                          processing_duration_ms=int((time.monotonic()-start)*1000))
            advance(db.transaction(),ref,attempt,prior,"Processed",trigger,values)
            claim.update({"outcome":"Processed"})
            log("process",fid,"Processed",duration_ms=values["processing_duration_ms"],attempt_id=attempt)
            return
        except InvalidPDF as exc:
            code = str(exc)
            break
        except Exception:
            code = "DEPENDENCY_ERROR"
            if retry < 2:
                ref.collection("history").document().set({**history(prior,attempt,trigger,code),"outcome":"retry"})
                time.sleep(0.25*2**retry)
    advance(db.transaction(),ref,attempt,prior,"Failed",trigger,{"error_code":code,"failure_reason":code.replace("_"," ").capitalize()})
    claim.update({"outcome":"Failed"})
    log("process",fid,"Failed",error_code=code,attempt_id=attempt,duration_ms=int((time.monotonic()-start)*1000))

@routes.post("/events")
def events():
    data = request.get_json()
    key = data.get("name","")
    if data.get("bucket") != BUCKET or not re.fullmatch(r"uploads/[a-f0-9]{32}/[a-f0-9]{32}\.pdf",key):
        return "",400
    manual = request.headers.get("ce-type") == "docuflow.manual"
    if not manual and request.headers.get("ce-type") != "google.cloud.storage.object.v1.finalized":
        return "",400
    process(key,str(data["generation"]),request.headers["ce-id"],manual)
    return "",204

@routes.get("/healthz")
def health():
    return {"status":"ok"}

def create_app():
    app = Flask(__name__)
    app.register_blueprint(routes)
    return app
