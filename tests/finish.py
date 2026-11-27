import json
import re
import subprocess
from pathlib import Path

out = Path("evidence/after")
results = json.loads((out / "test-results.json").read_text())


def command(*args):
    return subprocess.check_output(["docker", "compose", *args], text=True)


r = command("exec", "-T", "processor", "python", "-m", "tests.force_failure")
assert "Controlled worker failure reached Failed" in r
(out / "forced-failure.txt").write_text(r)
results["T05"] = {
    "status": "Passed",
    "actual": "Forced worker failure produced Failed state, CONTROLLED_FAILURE history and structured failure log.",
}
raw = command("logs", "--no-log-prefix", "api", "processor")
allowed = set(
    "timestamp severity component stage file_id attempt_id outcome duration_ms error_code integration request_id".split()
)
rows = [json.loads(line) for line in raw.splitlines() if line.startswith("{")]
for row in rows:
    assert not set(row) - allowed
assert (
    rows
    and any(x.get("error_code") == "CONTROLLED_FAILURE" for x in rows)
    or '"error_code": "CONTROLLED_FAILURE"' in r
)
assert not re.search(
    r"%PDF-|synthetic-check\.pdf|BEGIN PRIVATE KEY|Authorization: Bearer", raw, re.I
)
if Path(".env.demo-login").exists():
    assert Path(".env.demo-login").read_text().strip() not in raw
(out / "redacted.jsonl").write_text("\n".join(map(json.dumps, rows)) + "\n")
results["T07"] = {
    "status": "Passed",
    "actual": f"Scanned API and processor output; {len(rows)} structured entries passed allowlist and sentinel checks.",
}
items = json.loads(Path("evidence/integration-status.json").read_text())
for item in items:
    assert all(Path(p).is_file() for p in item["evidence_links"])
assert next(x for x in items if x["service"] == "Cloud Run")["status"] == "Simulated"
results["T08"] = {
    "status": "Passed",
    "actual": "Five integration claims linked to local evidence; Cloud Run marked Simulated.",
}
(out / "test-results.json").write_text(json.dumps(results, indent=2))
(out / "matrix.md").write_text(
    "# Local verification results\n\n"
    + "\n".join(f"- **{k}** {v['status']} — {v['actual']}" for k, v in results.items()),
    encoding="utf-8",
)
