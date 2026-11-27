"""Exercise expiry deterministically in the API container with a private SQLite file."""

import tempfile
from unittest.mock import patch
from pathlib import Path
from backend import app as api

with (
    tempfile.TemporaryDirectory() as tmp,
    patch.object(api, "sessions", str(Path(tmp) / "test.sqlite")),
):
    c = api.create_app().test_client()
    c.get("/api/auth/me")
    with api.connection() as db:
        db.execute("UPDATE sessions SET actor='demo'")
    assert c.get("/api/documents").status_code == 200
    with api.connection() as db:
        db.execute("UPDATE sessions SET expires=0")
    assert c.get("/api/documents").status_code == 401
print("Expired server-side session denied after previously authenticated request.")
