# Engineering decisions

- Use Python and Flask for the API and independent processor, and serve vanilla HTML/CSS/JS from the API origin, as specified in the brief.
- Keep credentials blank in the example configuration. Use a Python standard-library staged secret check for the initial commit. The check detects selected patterns and complements the later CI scan.
- Reserve deep signature and structural checks for the processor so a syntactically acceptable upload can demonstrate a visible processing failure.
- Plan to probe google-cloud-storage and google-cloud-firestore in Phase 2. Floci documents emulator host settings. The installed floci/floci image targets AWS. The GCP image is floci/floci-gcp. Runtime compatibility, access control and native delivery all await operation-level tests. [Official GCP setup](https://floci.io/floci-gcp/getting-started/installation/)

- Verified google-cloud-storage and google-cloud-firestore against the local GCP emulator. requests supports the emulator credential and Cloud Logging REST calls. bcrypt hashes the shared demo password, Gunicorn serves Flask, and pypdf inspects structure. See evidence/setup/sdk-probe.txt.
- SQLite keeps HTTP sessions server-side. Floci owns metadata and private bytes. Compose publishes only the browser-facing API; the named cloud data volume uses hybrid storage for persistence.
- Worker hosting uses Docker Compose. The native Cloud Run probe produced CONDITION_FAILED with a missing socket. The Eventarc trigger itself delivered events natively to an HTTP destination.
- Test and authoring tools are separate from runtime. Ruff checks Python; pip-audit scans packages; Playwright drives Edge for browser verification; python-docx and Pillow generate the report and guides.
