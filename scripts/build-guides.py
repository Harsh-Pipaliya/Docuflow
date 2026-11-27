"""Generate the assessment and walkthrough from local test evidence (python-docx)."""

import json
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from PIL import Image, ImageDraw, ImageFont
from tempfile import TemporaryDirectory

root = Path("docs")


def new(title):
    d = Document()
    d.add_heading(title, 0)
    d.sections[0].header.paragraphs[0].text = "DOCUFLOW     /     CLOUD COMPUTING LAB"
    d.sections[0].footer.paragraphs[
        0
    ].text = "DocuFlow     ·     Local assessment     ·     November 2026"
    d.styles["Normal"].font.name = "Calibri"
    d.styles["Normal"].font.size = Pt(11)
    return d


def section(d, h, p):
    d.add_heading(h, 2)
    d.add_paragraph(p)


def diagram(d, names):
    with TemporaryDirectory() as tmp:
        im = Image.new("RGB", (1050, len(names) * 75), "white")
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 23)
        for i, name in enumerate(names):
            y = i * 75
            draw.rounded_rectangle(
                (65, y + 2, 985, y + 57),
                radius=12,
                outline="#593b47",
                fill="#ffe4e8",
                width=2,
            )
            draw.text((525, y + 27), name, fill="#20151b", font=font, anchor="mm")
            if i < len(names) - 1:
                draw.line((525, y + 57, 525, y + 73), fill="#593b47", width=3)
        p = Path(tmp) / "figure.png"
        im.save(p)
        d.add_picture(str(p), width=Inches(5.8))


r = new("DocuFlow — Cloud Project / Security Assessment Report")
r.add_paragraph(
    "Draft assessment for the five-person project team. A synthetic PDF completed the local upload workflow; a replay preserved every recorded state. The emulator delivered the storage event. Docker Compose hosted the worker."
)
section(
    r,
    "Readiness and boundaries",
    "The team ran Floci GCP 0.13.0 on Docker Desktop. The Google Storage client wrote, listed, read and deleted objects; an unauthenticated REST read returned 403. A Firestore transaction committed and the document could be read and deleted. Local integration results describe the emulator configuration only.",
)
diagram(
    r,
    [
        "Browser and authenticated Flask upload",
        "Private Cloud Storage object and generated key",
        "Eventarc finalized event",
        "Flask processor in Docker Compose",
        "Firestore state and history · Cloud Logging entries",
    ],
)
r.add_page_break()
r.add_heading("File policy and state changes", 1)
section(
    r,
    "Two validation decisions",
    "The API measures the stream, checks the declared MIME and filename extension, and accepts up to 10,485,760 bytes. It assigns a UUID and generated object key. The worker then checks the signature, structural parsing, encryption, page count and content warnings.",
)
section(
    r,
    "Why ownership of state matters",
    "A 201 upload response confirms receipt. Processing success requires a successful deep parse and committed metadata. The worker conditions each write on the expected state and active attempt. A manual reprocess allocates a new attempt while retaining earlier history.",
)
diagram(
    r,
    [
        "Received · API created the document",
        "Validating · worker claimed the attempt",
        "Validated · structural checks passed",
        "Processed · result recorded",
    ],
)
section(
    r,
    "Failure branch",
    "Each active state can end in Failed. Failure reason and error code stay visible on the detail page. Download reads the private bytes through the authenticated API.",
)
r.add_page_break()
r.add_heading("Results and remaining risks", 1)
results = json.loads(Path("evidence/after/test-results.json").read_text())
for k in sorted(x for x in results if x.startswith("T")):
    r.add_paragraph(k + "   " + str(results[k]["actual"]), style="List Bullet")
section(
    r,
    "Severity and limitations",
    "High impact outside the demonstration environment: the shared local account and emulator are unsuitable for confidential material. Medium reliability risk: killing a worker immediately after an event claim may leave an active attempt without a terminal outcome. This version demonstrates transient retries inside a running worker. A durable claim lease and reconciliation job would address process loss.",
)
section(
    r,
    "Integration limitation",
    "The Cloud Run control plane accepted the deployment request but the runtime reported a missing Docker socket. The tested path uses real emulator Eventarc HTTP delivery to the Compose processor. The Integration Status page labels worker hosting Simulated.",
)
r.add_page_break()
r.add_heading("Appendix   Evidence and comparison", 1)
section(
    r,
    "Before and after",
    "The frozen harness rejected a wrong extension but accepted excess bytes. Replaying an event incremented its effect counter twice; a failed worker left Validating behind. The live API returned 413 before storing the oversized file, replay left both Firestore snapshots unchanged and processing failures became visible.",
)
for path in [
    "baseline/results.jsonl",
    "after/matrix.md",
    "after/event-trace.json",
    "after/replay.json",
    "after/redacted.jsonl",
    "integration-status.json",
    "setup/cloud-run.json",
]:
    r.add_paragraph("evidence/" + path, style="List Bullet")
r.save(root / "Assessment.docx")

d = new("DocuFlow team walkthrough and demo")
d.add_paragraph(
    "Use this guide to start the local stack and explain a file from receipt to its terminal state. Use only synthetic PDFs."
)
section(
    d,
    "Start from a clone",
    "Open PowerShell in the checkout. Run .\\scripts\\setup.ps1. Visit http://127.0.0.1:8080 and sign in as demo using the generated password. On this machine Get-Content .env.demo-login displays the local password. Run .\\scripts\\run-all-tests.ps1 to exercise the API and save results.",
)
section(
    d,
    "Check the services",
    "Run docker compose ps -a. The bootstrap container should exit with code 0. API, processor and cloud should stay up. Inspect docker compose logs --tail 30 bootstrap or processor if uploads stay active. The cloud service has no published port. For a clean synthetic demo use scripts/reset-demo.ps1 and scripts/load-demo-scenario.ps1.",
)
section(
    d,
    "Reproduce the demonstration",
    "Minute 0–1: the architect shows the architecture and state diagram. Minutes 1–3: the API engineer uploads a generated PDF and opens the detail page. Minutes 3–5: the reliability engineer reads the history, hash and attempt count. Minutes 5–6: upload corrupt.pdf and show Failed. Minutes 6–7: the test engineer compares replay snapshots. Minutes 7–9: the cloud engineer shows Integrations, the Cloud Run probe and the anonymous 403. If live services fail, identify the failure and show the saved evidence explicitly as a previous run.",
)
d.add_page_break()
d.add_heading("Five roles and reviewer questions", 1)
for h, p in [
    (
        "Workflow architect",
        "Which states exist? Trace Received, Validating, Validated and Processed. Show the failure branch in docs/diagrams/states.svg. Explain why a 201 response alone cannot establish processing success.",
    ),
    (
        "Cloud environment engineer",
        "Which components ran natively? Point to the Storage SDK probe, Firestore transaction, finalized event and logging readback. Explain the runtime failure and Compose hosting.",
    ),
    (
        "Upload and API engineer",
        "How is the object identified? Open backend/app.py. The API generates the file ID and storage key independently of the display name, limits bytes and requires an authenticated session.",
    ),
    (
        "Processing and reliability engineer",
        "What happens on a repeat? Open processor/app.py and the replay snapshots. Conditional writes admit one active attempt. Manual reprocess deliberately creates another attempt.",
    ),
    (
        "Testing and documentation engineer",
        "How do we know failure is visible? Compare baseline/results.jsonl with after/forced-failure.txt, after/redacted.jsonl and the actual detail view. A test is recorded only after its assertions run.",
    ),
]:
    section(d, h, p)
d.add_page_break()
d.add_heading("Components and ownership", 1)
for h, p in [
    (
        "Frontend and authentication",
        "Flask serves six same-origin HTML pages. frontend/js/api.js attaches CSRF tokens. The dashboard and document views poll for changes. backend/app.py validates the demo password and stores session state server-side. Sign out, revisit a protected page, and observe the redirect.",
    ),
    (
        "Metadata and database",
        "Every document has a generated file_id, storage_key, status, upload timestamp and attempt ID. Firestore history records transitions. Content hashes identify equal files. Open docs/metadata-schema.md alongside the document detail page.",
    ),
    (
        "Storage and event processing",
        "Cloud Storage holds the PDF bytes. Eventarc delivers object metadata and ce-* headers to the worker. A private bucket and per-generation reads keep identity stable. See infra/bootstrap.py, infra/cloud.py and processor/app.py.",
    ),
    (
        "Validation and failures",
        "A pypdf reader checks structure and page count without rendering pages. Inspect an encrypted or zero-page synthetic upload to see its code. Reprocess a failed document to demonstrate retained history.",
    ),
    (
        "Logging, testing and deployment",
        "The API and worker emit structured events and post them to local Cloud Logging. Run the log scanner through the test runner. Compose launches the services on a private network with the UI bound to loopback.",
    ),
]:
    section(d, h, p)
d.save(root / "Team-guide.docx")
