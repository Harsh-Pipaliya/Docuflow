from google.cloud import firestore
from infra.cloud import db, history, now

@firestore.transactional
def restart(tx,ref,attempt):
    doc=ref.get(transaction=tx).to_dict()
    if not doc or doc["status"]!="Failed":
        return False
    tx.update(ref,{"current_attempt_id":attempt,"attempt_count":doc["attempt_count"]+1,
                   "status":"Received","failure_reason":None,"error_code":None,"updated_at":now()})
    tx.set(ref.collection("history").document(),history("Received",attempt,"manual-reprocess"))
    return True

def fail_upload(ref,attempt):
    batch=db.batch()
    batch.update(ref,{"status":"Failed","failure_reason":"Storage unavailable","error_code":"UPLOAD_ERROR","updated_at":now()})
    batch.create(ref.collection("history").document(),history("Failed",attempt,"upload-event","UPLOAD_ERROR"))
    batch.commit()
