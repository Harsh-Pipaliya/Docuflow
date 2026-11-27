# Object-finalized event (draft)

The worker expects a CloudEvents 1.0 envelope with id, source, type, time and data. The target type is google.cloud.storage.object.v1.finalized. The data fields bucket, name (generated storage key) and generation identify an immutable object version. Resolve the file ID through the registered key and verify the bucket and generation before processing. Timestamps use UTC. No filename, PDF bytes or credentials travel in the envelope.

Phase 2 will capture the actual emulator delivery, including binding and field types, before freezing this contract. If a simulated adapter is needed it must reproduce that contract and retain the original identity on replay. The processor must recognize both redelivery of one event and multiple notifications for the same generation.
