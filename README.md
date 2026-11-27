# DocuFlow

DocuFlow is a local PDF-processing demonstration for a five-person college cloud computing team. Upload a synthetic PDF, follow the storage event into the worker, then inspect the resulting metadata, history or failure reason.

## Run on Windows

Install Docker Desktop with the Linux engine and Python 3.13. In PowerShell:

```powershell
git clone https://github.com/Harsh-Pipaliya/Docuflow.git
Set-Location Docuflow
.\scripts\setup.ps1
```

Visit http://127.0.0.1:8080. The username is **demo**. Setup prints the generated password and saves it locally in the Git-ignored .env.demo-login file. To see it again, run `Get-Content .env.demo-login`. The first build fetches the pinned Floci GCP image and Python dependencies. The setup script can be run again with the same login. Enable the local staged secret scan with `git config core.hooksPath .githooks`.

## Verify the project

Run `.\scripts\run-all-tests.ps1` in PowerShell. It installs the pinned client dependencies in a local virtual environment, uploads synthetic files, exercises event replay and failures, and writes evidence under evidence/after. Run `.\scripts\reset-demo.ps1` only when you intend to clear this demo's stored objects, documents, sessions and logs.

## How the workflow fits together

The browser uses a Flask API for login, upload, status, download and deletion. A private Cloud Storage bucket in Floci emits a finalized event. Floci Eventarc delivers it to a separate Flask processor. The processor inspects the exact object generation and commits its state and history to Firestore. Operational events go to the local Cloud Logging API. Floci Cloud Run deployment returned a runtime error in the tested configuration, so processor hosting is labelled **Simulated**. The remaining four services were exercised against the local emulator.

![Workflow](docs/diagrams/architecture.svg)

- [Test matrix](evidence/after/matrix.md), [before and after](docs/before-after.md) and [integration evidence](evidence/integration-status.json)
- [Eight-minute presentation walkthrough for five speakers](docs/Presentation-walkthrough.docx) with click paths, speaking notes, rehearsal screenshots and reviewer questions
- [Assessment report](docs/Assessment.docx), [team walkthrough and demo](docs/Team-guide.docx) and [19-topic technical reference](docs/Technical-reference.docx)
- [File policy](docs/file-policy.md), [metadata schema](docs/metadata-schema.md), [state transitions](docs/state-machine.md), [HTTP API](docs/api.md) and [configuration](docs/configuration.md)
- [Manual test walkthrough](docs/manual-test-checklist.md) and [team workflow](CONTRIBUTING.md)

The baseline-v0 tag preserves the original synthetic harness. Checkpoint tags record the scope, baseline, implementation, verification and review revisions. GitHub Actions is configured for pull requests; local Floci integration tests require Docker.
