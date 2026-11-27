# Object-finalized event (verified emulator binding)

The worker expects a CloudEvents 1.0 envelope with id, source, type, time and data. The target type is google.cloud.storage.object.v1.finalized. The data fields bucket, name (generated storage key) and generation identify an immutable object version. Resolve the file ID through the registered key and verify the bucket and generation before processing. Timestamps use UTC. No filename, PDF bytes or credentials travel in the envelope.

Floci Eventarc delivered binary-mode HTTP POST requests to /events. The worker reads ce-id and ce-type headers. The object metadata body supplies bucket, name and generation. The tested trigger matches the exact finalized event type and docuflow-uploads bucket. See infra/bootstrap.py, tests/verify.py and evidence/after/replay.json. Manual reprocess uses a separate internal event type and a fresh attempt ID.
