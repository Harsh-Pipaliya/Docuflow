# Local verification results

- **Unauthorized** Passed — Unauthenticated document list requires login
- **CSRF** Passed — Missing token rejected
- **T01** Passed — ['Received', 'Validating', 'Validated', 'Processed']
- **T02** Passed — Wrong MIME and extension returned 415
- **T03** Passed — 413 and unchanged metadata count
- **T04** Passed — Identical document and history after same-event delivery
- **corrupt** Passed — INVALID_STRUCTURE
- **encrypted** Passed — ENCRYPTED
- **zero** Passed — PAGE_COUNT
- **signature** Passed — INVALID_SIGNATURE
- **T06** Passed — Detail returned Processed
- **Download** Passed — Byte-identical authenticated download
- **Reprocess** Passed — New attempt preserves history
- **Duplicate content** Passed — Equal digest with independent ID
- **Delete** Passed — Deleted failed record
- **T05** Passed — Forced worker failure produced Failed state, CONTROLLED_FAILURE history and structured failure log.
- **T07** Passed — Scanned API and processor output; 14 structured entries passed allowlist and sentinel checks.
- **T08** Passed — Five integration claims linked to local evidence; Cloud Run marked Simulated.