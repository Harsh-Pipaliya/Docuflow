# Controls and evidence

- Session theft and forged writes. The API uses bcrypt, random server-side session IDs, HttpOnly and SameSite cookies, expiry and CSRF checks. Unauthorized and CSRF checks are in tests/verify.py.
- File substitution and traversal. The API generates a UUID and random storage key, sanitizes the display name and rejects excess bytes before storage. T02–T03 cover input rejection.
- Unsafe content. The separate worker checks signature, parses structure, rejects encryption and zero pages, and flags active features without executing them. Parser tests cover corrupt and encrypted synthetic files.
- Private storage. The emulator is internal to Compose and enforces REST IAM for the application bucket. The anonymous probe returned 403. GCS gRPC IAM is a documented emulator limitation.
- Disclosure in logs. Operational messages contain opaque IDs and fixed fields. T07 scans API and processor output. Downloads and deletion require the shared authenticated session.
- Duplicate effects. Firestore checks the attempt and prior state in a transaction. T04 exercises delivery replay. Crash recovery from a process kill during an active claim is a separate reliability case.
