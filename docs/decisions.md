# Engineering decisions

- Use Python and Flask for the API and independent processor, and serve vanilla HTML/CSS/JS from the API origin, as specified in the brief.
- Keep credentials blank in the example configuration. Use a Python standard-library staged secret check for the initial commit. The check detects selected patterns and complements the later CI scan.
- Reserve deep signature and structural checks for the processor so a syntactically acceptable upload can demonstrate a visible processing failure.
- Plan to probe google-cloud-storage and google-cloud-firestore in Phase 2. Floci documents emulator host settings. The installed floci/floci image targets AWS. The GCP image is floci/floci-gcp. Runtime compatibility, access control and native delivery all await operation-level tests. [Official GCP setup](https://floci.io/floci-gcp/getting-started/installation/)
