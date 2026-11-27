# Firestore schema

Each documents/{file_id} record describes one upload. Nullable result fields start empty until the owning stage writes them. Examples below are illustrative.

| Field | Type and example | Writer and purpose |
|---|---|---|
| file_id | UUID string | API generates stable lookup ID |
| original_filename | string, sample.pdf | API stores sanitized display label |
| content_type | string, application/pdf | API records declared MIME |
| size_bytes | integer, 512 | API records measured size |
| storage_key, generation | strings, uploads/{uuid}/{random}.pdf and 1 | API links the exact private object |
| owner_id | string, demo | API reserves future ownership |
| uploaded_at, updated_at | UTC timestamps | API sets creation time, each transition updates modification time |
| status | enum, Received | API initializes, worker advances state |
| failure_reason, error_code | nullable strings, PDF has no pages / ZERO_PAGES | Worker explains failure safely |
| sha256 | nullable 64-character hex string | Worker fingerprints bytes |
| content_duplicate, content_duplicate_of | boolean, nullable UUID | Worker links an earlier equal fingerprint |
| page_count, pdf_version | nullable integer and string, 2 and 1.7 | Worker records parser results |
| warnings | string array, e.g. has_javascript | Worker records has_javascript and has_embedded_files flags |
| processing_duration_ms | nullable integer, 130 | Worker measures attempt duration |
| attempt_count, current_attempt_id | integer and UUID | API/worker identify active attempt and guard conditional writes |

History at documents/{file_id}/history/{entry_id} stores stage, outcome, UTC timestamp, attempt_id, trigger (upload-event, simulated-event or manual-reprocess) and optional error_code. The transition writer appends the entry atomically with the state update.

Idempotency records at idempotency/{key} identify file, generation and attempt, record the delivery ID, first_seen_at, claim state and outcome. An atomic claim prevents concurrent duplicates. A manual retry creates a new attempt while a replay stays associated with the original delivery.

The API appends audit/{entry_id} with file_id where applicable, action, UTC timestamp and actor ID. Delete removes private bytes, document metadata and history while retaining the content-free audit record.
