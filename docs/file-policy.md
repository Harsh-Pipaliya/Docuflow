# File policy

Each authenticated request carries one synthetic PDF. Multi-file uploads send separate requests. The API requires a nonempty display name with a case-insensitive .pdf suffix and declared application/pdf MIME type. Normalize the basename, strip path components and control characters, and keep the result solely as a display label. Generate a UUID and an independent random object name for each upload.

Stream and count bytes. Accept 1 through 10,485,760 bytes inclusive. Stop at the first excess byte and return 413. Reject wrong type, wrong extension or empty input before storing an object or creating document metadata. Never trust Content-Length alone.

After storage, the processor checks the initial %PDF- signature, parses structure under resource limits, rejects encryption, truncation and zero pages, and records a safe failure code and reason. Detect JavaScript actions and embedded files by inspecting structure and record warnings. Never render, extract attachments or execute content.

Repeated names are allowed. Equal SHA-256 fingerprints flag content duplicates while keeping separate document IDs. Store bytes in a private bucket. Stream downloads through the authenticated API. Record opaque identifiers in operational logs and retain a content-free audit entry on deletion.
