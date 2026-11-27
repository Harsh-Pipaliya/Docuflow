import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import requests
from google.auth.credentials import Credentials
from google.cloud import firestore, storage

BASE = os.environ["EMULATOR_URL"]
PROJECT = "docuflow"
BUCKET = "docuflow-uploads"
ACCOUNT = "api@docuflow.iam.gserviceaccount.com"
db = firestore.Client(project=PROJECT)


class EmulatorCredentials(Credentials):
    def refresh(self, request):
        response = requests.post(
            f"{BASE}/v1/projects/-/serviceAccounts/{ACCOUNT}:generateAccessToken",
            json={"scope": ["https://www.googleapis.com/auth/cloud-platform"]},
            timeout=8,
        )
        response.raise_for_status()
        token = response.json()
        self.token = token["accessToken"]
        self.expiry = (
            datetime.fromisoformat(token["expireTime"].replace("Z", "+00:00"))
            .astimezone(timezone.utc)
            .replace(tzinfo=None)
        )


def storage_client():
    return storage.Client(
        project=PROJECT,
        credentials=EmulatorCredentials(),
        client_options={"api_endpoint": BASE},
    )


def bucket():
    return storage_client().bucket(BUCKET)


def now():
    return datetime.now(timezone.utc).isoformat()


def log(stage, file_id, outcome, **extra):
    item = {
        "timestamp": now(),
        "severity": "INFO",
        "stage": stage,
        "file_id": file_id,
        "outcome": outcome,
        "component": os.getenv("COMPONENT", "api"),
        "integration": "simulated"
        if os.getenv("COMPONENT") == "processor"
        else "native",
    }
    item.update(
        {
            k: v
            for k, v in extra.items()
            if k in {"duration_ms", "error_code", "attempt_id", "request_id"}
        }
    )
    print(json.dumps(item), flush=True)
    try:
        requests.post(
            BASE + "/v2/entries:write",
            json={
                "logName": "projects/docuflow/logs/docuflow",
                "resource": {"type": "global"},
                "entries": [{"jsonPayload": item}],
            },
            timeout=3,
        ).raise_for_status()
    except requests.RequestException:
        print(
            json.dumps({"stage": "logging", "outcome": "delivery_failed"}), flush=True
        )


def history(stage, attempt, trigger, code=None):
    return {
        "stage": stage,
        "timestamp": now(),
        "attempt_id": attempt,
        "trigger": trigger,
        "outcome": stage,
        "error_code": code,
    }


def audit(action, file_id=None):
    db.collection("audit").document(uuid4().hex).set(
        {"action": action, "file_id": file_id, "actor": "demo", "timestamp": now()}
    )
