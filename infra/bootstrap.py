import requests
from google.api_core.exceptions import Conflict
from infra.cloud import BASE, BUCKET, storage_client

try:
    storage_client().create_bucket(BUCKET)
except Conflict:
    pass
url = BASE + "/v1/projects/docuflow/locations/us-central1/triggers"
trigger = {
    "eventFilters": [
        {"attribute": "type", "value": "google.cloud.storage.object.v1.finalized"},
        {"attribute": "bucket", "value": BUCKET},
    ],
    "destination": {"httpEndpoint": {"uri": "http://processor:8080/events"}},
}
r = requests.post(
    url, params={"triggerId": "docuflow-finalized"}, json=trigger, timeout=10
)
if r.status_code != 409:
    r.raise_for_status()
print("Bucket and Eventarc trigger configured.")
