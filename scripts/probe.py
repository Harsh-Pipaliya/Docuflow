"""Run against the isolated, IAM-enforcing readiness container on loopback."""
import os
import uuid
import requests
from google.cloud import firestore, storage
from google.oauth2.credentials import Credentials

base = "http://127.0.0.1:4589"
project = "docuflow"
account = "api@docuflow.iam.gserviceaccount.com"
os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:4589"
token = requests.post(f"{base}/v1/projects/-/serviceAccounts/{account}:generateAccessToken",
    json={"scope":["https://www.googleapis.com/auth/cloud-platform"]}, timeout=10)
token.raise_for_status()
client = storage.Client(project=project, credentials=Credentials(token.json()["accessToken"]),
    client_options={"api_endpoint":base})
bucket = client.create_bucket("docuflow-probe-" + uuid.uuid4().hex)
blob = bucket.blob("sample")
blob.upload_from_string(b"synthetic")
assert blob.download_as_bytes() == b"synthetic"
assert [item.name for item in client.list_blobs(bucket)] == ["sample"]
response = requests.get(f"{base}/storage/v1/b/{bucket.name}/o/sample?alt=media",timeout=5)
assert response.status_code == 403, response.status_code
blob.delete()
bucket.delete()
print("Cloud Storage SDK create/write/read/list/delete passed; anonymous REST download returned 403.")
db = firestore.Client(project=project)
ref = db.collection("readiness").document()
ref.create({"count":0})
@firestore.transactional
def increment(tx):
    current = ref.get(transaction=tx)
    tx.update(ref, {"count":current.get("count")+1})
increment(db.transaction())
assert ref.get().get("count")==1
ref.delete()
print("Firestore SDK create/read/transaction/update/delete passed.")
