import hmac
import os
import secrets
import sqlite3
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import bcrypt
import requests
from flask import Blueprint, Flask, abort, g, jsonify, request, send_file, send_from_directory
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from processor_state import begin_attempt
from infra.cloud import BUCKET, audit, bucket, db, history, log, now

routes = Blueprint("api",__name__)
limit = int(os.getenv("MAX_UPLOAD_BYTES","10485760"))
frontend = Path(__file__).resolve().parents[1]/"frontend"
sessions = os.getenv("SESSION_DB","/tmp/docuflow-sessions.sqlite")

def connection():
    conn = sqlite3.connect(sessions,timeout=10)
    conn.executescript("CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,csrf TEXT,expires REAL,actor TEXT); CREATE TABLE IF NOT EXISTS hits(scope TEXT,ts REAL);")
    return conn

def rate(scope, maximum):
    with connection() as c:
        c.execute("BEGIN IMMEDIATE")
        c.execute("DELETE FROM hits WHERE ts < ?",(time.time()-60,))
        if c.execute("SELECT COUNT(*) FROM hits WHERE scope=?",(scope,)).fetchone()[0]>=maximum:
            abort(429)
        c.execute("INSERT INTO hits VALUES(?,?)",(scope,time.time()))

def new_session(actor):
    sid,csrf = secrets.token_urlsafe(32),secrets.token_urlsafe(32)
    with connection() as c:
        c.execute("DELETE FROM sessions WHERE id=? OR expires<?",(request.cookies.get("sid",""),time.time()))
        c.execute("INSERT INTO sessions VALUES(?,?,?,?)",(sid,csrf,time.time()+60*int(os.getenv("SESSION_IDLE_MINUTES","30")),actor))
    response=jsonify({"csrf":csrf,"authenticated":bool(actor)})
    response.set_cookie("sid",sid,httponly=True,samesite="Strict",secure=request.is_secure)
    return response

@routes.before_app_request
def protect():
    if not request.path.startswith("/api/"):
        return
    sid=request.cookies.get("sid","")
    with connection() as c:
        session=c.execute("SELECT csrf,actor FROM sessions WHERE id=? AND expires>?",(sid,time.time())).fetchone()
        if session:
            c.execute("UPDATE sessions SET expires=? WHERE id=?",(time.time()+60*int(os.getenv("SESSION_IDLE_MINUTES","30")),sid))
    if request.path=="/api/auth/me" and request.method=="GET":
        return jsonify({"csrf":session[0],"authenticated":bool(session[1])}) if session else new_session("")
    if not session or (not session[1] and request.path!="/api/auth/login"):
        abort(401)
    if request.method not in ("GET","HEAD","OPTIONS") and not hmac.compare_digest(session[0],request.headers.get("X-CSRF-Token","")):
        abort(403)

@routes.post("/api/auth/login")
def login():
    data=request.get_json()
    password=str(data.get("password","")).encode()
    if len(password)>72 or not bcrypt.checkpw(password,os.environ["DEMO_PASSWORD_HASH"].encode()) or data.get("username")!="demo":
        rate("login:"+str(request.remote_addr),int(os.getenv("LOGIN_FAILURES_PER_MINUTE","5")))
        abort(401)
    audit("login")
    return new_session("demo")

@routes.post("/api/auth/logout")
def logout():
    return new_session("")

@routes.route("/api/documents",methods=["GET","POST"])
def documents():
    if request.method=="GET":
        rows=[s.to_dict() for s in db.collection("documents").stream()]
        return jsonify(sorted(rows,key=lambda s:s["uploaded_at"],reverse=True))
    rate("upload:"+request.cookies["sid"],int(os.getenv("UPLOADS_PER_MINUTE","10")))
    f=request.files.get("file")
    if not f or f.mimetype!="application/pdf":
        abort(415)
    label=secure_filename(f.filename.replace(chr(92),"/").split("/")[-1])[:240]
    if not label.lower().endswith(".pdf"):
        abort(415)
    with tempfile.SpooledTemporaryFile(max_size=524288) as stream:
        while chunk:=f.stream.read(65536):
            if stream.tell()+len(chunk)>limit:
                abort(413)
            stream.write(chunk)
        size=stream.tell()
        if not size:
            abort(400)
        fid,attempt=uuid4().hex,uuid4().hex
        key=f"uploads/{fid}/{uuid4().hex}.pdf"
        ref=db.collection("documents").document(fid)
        stamp=now()
        doc=dict(file_id=fid,original_filename=label,size_bytes=size,content_type=f.mimetype,storage_key=key,
                 status="Received",uploaded_at=stamp,updated_at=stamp,owner_id="demo",attempt_count=1,current_attempt_id=attempt)
        batch=db.batch()
        batch.create(ref,doc)
        batch.create(ref.collection("history").document(),history("Received",attempt,"upload-event"))
        batch.commit()
        stream.seek(0)
        try:
            bucket().blob(key).upload_from_file(stream,size=size,content_type=f.mimetype,if_generation_match=0)
        except Exception:
            begin_attempt.fail_upload(ref,attempt)
            abort(503)
    audit("upload",fid)
    log("upload",fid,"accepted",attempt_id=attempt)
    return {"file_id":fid},201

def reference(fid):
    if len(fid)!=32 or any(c not in "0123456789abcdef" for c in fid):
        abort(404)
    ref=db.collection("documents").document(fid)
    doc=ref.get().to_dict()
    if not doc:
        abort(404)
    return ref,doc

@routes.route("/api/documents/<fid>",methods=["GET","DELETE"])
def detail(fid):
    ref,doc=reference(fid)
    if request.method=="GET":
        return doc
    if doc["status"] not in ("Processed","Failed"):
        abort(409)
    from google.api_core.exceptions import NotFound
    try:
        bucket().blob(doc["storage_key"]).delete()
    except NotFound:
        pass
    for row in ref.collection("history").stream():
        row.reference.delete()
    ref.delete()
    audit("delete",fid)
    return "",204

@routes.get("/api/documents/<fid>/history")
def timeline(fid):
    ref,_=reference(fid)
    return jsonify([s.to_dict() for s in ref.collection("history").order_by("timestamp").stream()])

@routes.get("/api/documents/<fid>/download")
def download(fid):
    _,doc=reference(fid)
    stream=tempfile.SpooledTemporaryFile(max_size=524288)
    bucket().blob(doc["storage_key"]).download_to_file(stream)
    stream.seek(0)
    audit("download",fid)
    return send_file(stream,as_attachment=True,download_name=doc["original_filename"],mimetype="application/pdf")

@routes.post("/api/documents/<fid>/reprocess")
def reprocess(fid):
    ref,doc=reference(fid)
    attempt=uuid4().hex
    if not doc.get("generation") or not begin_attempt.restart(db.transaction(),ref,attempt):
        abort(409)
    requests.post("http://processor:8080/events",json={"name":doc["storage_key"],"bucket":BUCKET,"generation":doc["generation"]},
                  headers={"ce-type":"docuflow.manual","ce-id":attempt},timeout=60).raise_for_status()
    audit("reprocess",fid)
    return {"attempt_id":attempt}

@routes.get("/api/integrations")
def integrations():
    return send_from_directory(frontend.parent/"evidence","integration-status.json")

@routes.get("/api/stats")
def stats():
    counts={s:0 for s in ("Received","Validating","Validated","Processed","Failed")}
    for s in db.collection("documents").stream():
        counts[s.get("status")]+=1
    return counts

@routes.get("/healthz")
def health():
    return {"status":"ok"}

@routes.get("/")
@routes.get("/<path:path>")
def static_page(path="index.html"):
    return send_from_directory(frontend,path)

def create_app():
    app=Flask(__name__,static_folder=None)
    app.config["MAX_CONTENT_LENGTH"]=limit+65536
    app.register_blueprint(routes)
    @app.errorhandler(Exception)
    def error(exc):
        code=exc.code if isinstance(exc,HTTPException) else 500
        return {"error":{ "code":code,"message":{401:"Invalid credentials or expired session",413:"File exceeds 10 MB",415:"Select a PDF file"}.get(code,"Request could not be completed")}},code
    @app.after_request
    def headers(response):
        response.headers.update({"Content-Security-Policy":"default-src 'self'; frame-ancestors 'none'; object-src 'none'",
             "X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer","X-Frame-Options":"DENY","Cache-Control":"no-store"})
        return response
    return app
