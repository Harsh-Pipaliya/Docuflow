"""Black-box local workflow verification. Run from the repository root."""
import io
import json
import os
import subprocess
import time
from pathlib import Path

import requests
from pypdf import PdfWriter

base = "http://127.0.0.1:8080"
out = Path("evidence/after")
out.mkdir(exist_ok=True)
s = requests.Session()
def api(method,path,**kw):
    return s.request(method,base+path,timeout=30,**kw)
def upload(name,data,mime="application/pdf"):
    return api("POST","/api/documents",files={"file":(name,data,mime)})
def snapshot(fid):
    path="/api/documents/"+fid
    return [api("GET",path).json(),api("GET",path+"/history").json()]
def wait(fid):
    for _ in range(50):
        d,h=snapshot(fid)
        if d.get("status") in ("Processed","Failed"):
            return d,h
        time.sleep(.2)
    raise AssertionError("No terminal state: "+str(d.get("status")))
def pdf(pages=1, encrypted=False):
    writer=PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(72,72)
    if encrypted:
        writer.encrypt("synthetic")
    stream=io.BytesIO()
    writer.write(stream)
    return stream.getvalue()
results={}
def check(name,ok,detail):
    results[name]={"status":"Passed" if ok else "Failed","actual":detail}
    (out/"test-results.json").write_text(json.dumps(results,indent=2))
    print(name,results[name])
    assert ok,name

check("Unauthorized",api("GET","/api/documents").status_code==401,"Unauthenticated document list requires login")
token=api("GET","/api/auth/me").json()["csrf"]
check("CSRF",api("POST","/api/auth/login",json={}).status_code==403,"Missing token rejected")
s.headers.update({"X-CSRF-Token":token})
password=os.getenv("DOCUFLOW_DEMO_PASSWORD") or Path(".env.demo-login").read_text().strip()
r=api("POST","/api/auth/login",json={"username":"demo","password":password})
r.raise_for_status()
s.headers.update({"X-CSRF-Token":r.json()["csrf"]})
data=pdf()
r=upload("synthetic-check.pdf",data)
r.raise_for_status()
fid=r.json()["file_id"]
d,h=wait(fid)
(out/"event-trace.json").write_text(json.dumps({"file_id":fid,"generation":d.get("generation"),"history":h},indent=2))
check("T01",d["status"]=="Processed" and [e["stage"] for e in h]==["Received","Validating","Validated","Processed"],[x["stage"] for x in h])
check("T02",upload("sample.txt",b"test","text/plain").status_code==415,"Wrong MIME and extension returned 415")
before=len(api("GET","/api/documents").json())
r=upload("large.pdf",bytes(10485761))
check("T03",r.status_code==413 and len(api("GET","/api/documents").json())==before,"413 and unchanged metadata count")
payload={"name":d["storage_key"],"generation":d["generation"],"bucket":"docuflow-uploads"}
cmd="import requests; from infra.cloud import db; a=db.collection('idempotency').document("+repr(d["current_attempt_id"])+").get().to_dict();r=requests.post('http://processor:8080/events',json="+repr(payload)+",headers={'ce-type':'google.cloud.storage.object.v1.finalized','ce-id':a['event_id']});r.raise_for_status()"
subprocess.run(["docker","compose","exec","-T","api","python","-c",cmd],check=True)
after=snapshot(fid)
(out/"replay.json").write_text(json.dumps({"before":[d,h],"after":after},indent=2))
check("T04",[d,h]==after,"Identical document and history after same-event delivery")
for label,content in [("corrupt",b"%PDF-1.4 invalid"),("encrypted",pdf(encrypted=True)),("zero",pdf(0)),("signature",b"ordinary text")]:
    r=upload(label+".pdf",content)
    r.raise_for_status()
    bad=r.json()["file_id"]
    bad_doc,bad_history=wait(bad)
    check(label,bad_doc["status"]=="Failed" and bool(bad_doc.get("error_code")),bad_doc.get("error_code"))
check("T06",api("GET","/api/documents/"+fid).json()["status"]=="Processed","Detail returned Processed")
check("Download",api("GET","/api/documents/"+fid+"/download").content==data,"Byte-identical authenticated download")
r=api("POST","/api/documents/"+bad+"/reprocess")
r.raise_for_status()
d2,h2=wait(bad)
check("Reprocess",d2["attempt_count"]==2 and h2[:len(bad_history)]==bad_history,"New attempt preserves history")
r=upload("synthetic-copy.pdf",data)
r.raise_for_status()
copy,_=wait(r.json()["file_id"])
check("Duplicate content",copy["content_duplicate"] and copy["file_id"]!=fid,"Equal digest with independent ID")
check("Delete",api("DELETE","/api/documents/"+bad).status_code==204 and api("GET","/api/documents/"+bad).status_code==404,"Deleted failed record")
